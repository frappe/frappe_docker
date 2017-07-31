#
# Copyright 2017, Martin Owens <doctormo@gmail.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3.0 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library.
#
"""
from crontab import CronTab
import sys

# Create a new non-installed crontab
cron = CronTab(tab='')
job  = cron.new(command='/usr/bin/echo')

job.minute.during(5,50).every(5)
job.hour.every(4)

job.dow.on('SUN')
job.month.during('APR', 'JUN')
job.month.also.during('OCT', 'DEC')

job.every(2).days()
job.setall(1, 12, None, None, None)

job2 = cron.new(command='/foo/bar', comment='SomeID')
job2.every_reboot()

jobs = list(cron.find_command('bar'))
job3 = jobs[0]
job3.clear()
job3.minute.every(1)

sys.stdout.write(str(cron.render()))

job3.enable(False)

for job4 in cron.find_command('echo'):
    sys.stdout.write(job4)

for job5 in cron.find_comment('SomeID'):
    sys.stdout.write(job5)

for job6 in cron:
    sys.stdout.write(job6)

for job7 in cron:
    job7.every(3).hours()
    sys.stdout.write(job7)
    job7.every().dow()

cron.remove_all(command='/foo/bar')
cron.remove_all(comment='This command')
cron.remove_all(time='* * * * *')
cron.remove_all()

output = cron.render()

cron.write()

cron.write(filename='/tmp/output.txt')

#cron.write_to_user(user=True)

#cron.write_to_user(user='root')

# Croniter Extentions allow you to ask for the scheduled job times, make
# sure you have croniter installed, it's not a hard dependancy.

job3.schedule().get_next()
job3.schedule().get_prev()

"""

import os
import re
import shlex

import codecs
import logging
import tempfile
import subprocess as sp

from time import sleep
from datetime import time, date, datetime, timedelta

try:
    from collections import OrderedDict
except ImportError:
    # python 2.6 and below causes this error
    try:
        from ordereddict import OrderedDict
    except ImportError:
        raise ImportError("OrderedDict is required for python-crontab, you can"
                " install ordereddict 1.1 from pypi for python2.6")

__pkgname__ = 'python-crontab'
__version__ = '2.2.3'

ITEMREX = re.compile(r'^\s*([^@#\s]+)\s+([^@#\s]+)\s+([^@#\s]+)\s+([^@#\s]+)'
                     r'\s+([^@#\s]+)\s+([^#\n]*)(\s+#\s*([^\n]*)|$)')
SPECREX = re.compile(r'^\s*@(\w+)\s([^#\n]*)(\s+#\s*([^\n]*)|$)')
DEVNULL = ">/dev/null 2>&1"

WEEK_ENUM = ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']

MONTH_ENUM = [None, 'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug',
              'sep', 'oct', 'nov', 'dec']

SPECIALS = {"reboot":   '@reboot',
            "hourly":   '0 * * * *',
            "daily":    '0 0 * * *',
            "weekly":   '0 0 * * 0',
            "monthly":  '0 0 1 * *',
            "yearly":   '0 0 1 1 *',
            "annually": '0 0 1 1 *',
            "midnight": '0 0 * * *'}

SPECIAL_IGNORE = ['midnight', 'annually']

S_INFO = [
    {'max': 59, 'min': 0, 'name': 'Minutes'},
    {'max': 23, 'min': 0, 'name': 'Hours'},
    {'max': 31, 'min': 1, 'name': 'Day of Month'},
    {'max': 12, 'min': 1, 'name': 'Month', 'enum': MONTH_ENUM},
    {'max': 6, 'min': 0, 'name': 'Day of Week', 'enum': WEEK_ENUM},
]

# Detect Python3 and which OS for temperments.
import platform
PY3 = platform.python_version()[0] == '3'
WINOS = platform.system() == 'Windows'
SYSTEMV = not WINOS and os.uname()[0] in ["SunOS", "AIX", "HP-UX"]

LOG = logging.getLogger('crontab')

CRONCMD = "/usr/bin/crontab"
SHELL = os.environ.get('SHELL', '/bin/sh')
# The shell won't actually work on windows here, but
# it should be updated later in the below conditional.

# pylint: disable=W0622,invalid-name,too-many-public-methods
# pylint: disable=function-redefined,too-many-instance-attributes
current_user = lambda: None
if not WINOS:
    import pwd
    def current_user():
        """Returns the username of the current user"""
        return pwd.getpwuid(os.getuid())[0]

if PY3:
    unicode = str
    basestring = str

def open_pipe(cmd, *args, **flags):
    """Runs a program and orders the arguments for compatability.

    a. keyword args are flags and always appear /before/ arguments for bsd
    """
    cmd_args = tuple(shlex.split(cmd))
    for (key, value) in flags.items():
        if len(key) == 1:
            cmd_args += ("-%s" % key),
            if value is not None:
                cmd_args += unicode(value),
        else:
            cmd_args += ("--%s=%s" % (key, value)),
    args = tuple(arg for arg in (cmd_args + tuple(args)) if arg)
    return sp.Popen(args, stdout=sp.PIPE, stderr=sp.PIPE)

def _unicode(text):
    """Convert to the best string format for this python version"""
    if type(text) is str and not PY3:
        return unicode(text, 'utf-8')
    if type(text) is bytes and PY3:
        return text.decode('utf-8')
    return text


class CronTab(object):
    """
    Crontab object which can access any time based cron using the standard.

    user    - Set the user of the crontab (default: None)
      * 'user' = Load from $username's crontab (instead of tab or tabfile)
      * None   = Don't load anything from any user crontab.
      * True   = Load from current $USER's crontab (unix only)
      * False  = This is a system crontab, each command has a username

    tab     - Use a string variable as the crontab instead of installed crontab
    tabfile - Use a file for the crontab instead of installed crontab
    log     - Filename for logfile instead of /var/log/syslog

    """
    def __init__(self, user=None, tab=None, tabfile=None, log=None):
        self.lines = None
        self.crons = None
        self.filen = None
        self.env = None
        self._parked_env = OrderedDict()
        # Protect windows users
        self.root = not WINOS and os.getuid() == 0
        # Storing user flag / username
        self._user = user
        # Load string or filename as inital crontab
        self.intab = tab
        self.read(tabfile)
        self._log = log

    @property
    def log(self):
        """Returns the CronLog object for this tab (user or root tab only)"""
        from cronlog import CronLog
        if self._log is None or isinstance(self._log, basestring):
            self._log = CronLog(self._log, user=self.user or 'root')
        return self._log

    @property
    def user(self):
        """Return user's username of this crontab if applicable"""
        if self._user is True:
            return current_user()
        return self._user

    @property
    def user_opt(self):
        """Returns the user option for the crontab commandline"""
        # Fedora and Mac require the current user to not specify
        # But Ubuntu/Debian doesn't care. Be careful here.
        if self._user and self._user is not True:
            if self._user != current_user():
                return {'u': self._user}
        return {}

    def read(self, filename=None):
        """
        Read in the crontab from the system into the object, called
        automatically when listing or using the object. use for refresh.
        """
        self.crons = []
        self.lines = []
        self.env = OrderedVariableList()
        lines = []

        if self.intab is not None:
            lines = self.intab.split('\n')

        elif filename:
            self.filen = filename
            with codecs.open(filename, 'r', encoding='utf-8') as fhl:
                lines = fhl.readlines()

        elif self.user:
            (out, err) = open_pipe(CRONCMD, l='', **self.user_opt).communicate()
            if err and 'no crontab for' in unicode(err):
                pass
            elif err:
                raise IOError("Read crontab %s: %s" % (self.user, err))
            lines = out.decode('utf-8').split("\n")

        for line in lines:
            self.append(CronItem(line, cron=self), line, read=True)

    def append(self, item, line='', read=False):
        """Append a CronItem object to this CronTab"""
        if item.is_valid():
            item.env.update(self._parked_env)
            self._parked_env = OrderedDict()

            if read and not item.comment and self.lines and \
              self.lines[-1] and self.lines[-1][0] == '#':
                item.set_comment(self.lines.pop()[1:].strip())

            self.crons.append(item)
            self.lines.append(item)
            return item

        elif '=' in line:
            if ' ' not in line or line.index('=') < line.index(' '):
                (name, value) = line.split('=', 1)
                value = value.strip()
                for quot in "\"'":
                    if value[0] == quot and value[-1] == quot:
                        value = value.strip(quot)
                        break
                self._parked_env[name.strip()] = value
                return None

        elif not self.crons and self._parked_env:
            self.env.update(self._parked_env)
            self._parked_env = OrderedDict()

        self.lines.append(line.replace('\n', ''))

    def write(self, filename=None, user=None):
        """Write the crontab to it's source or a given filename."""
        if filename:
            self.filen = filename
        elif user is not None:
            self.filen = None
            self.intab = None
            self._user = user

        # Add to either the crontab or the internal tab.
        if self.intab is not None:
            self.intab = self.render()
            # And that's it if we never saved to a file
            if not self.filen:
                return

        if self.filen:
            fileh = open(self.filen, 'wb')
        else:
            filed, path = tempfile.mkstemp()
            fileh = os.fdopen(filed, 'wb')

        fileh.write(self.render().encode('utf-8'))
        fileh.close()

        if not self.filen:
            # Add the entire crontab back to the user crontab
            if self.user:
                proc = open_pipe(CRONCMD, path, **self.user_opt)
                # This could do with being cleaned up quite a bit
                proc.wait()
                proc.stdout.close()
                proc.stderr.close()
                os.unlink(path)
            else:
                os.unlink(path)
                raise IOError("Please specify user or filename to write.")

    def write_to_user(self, user=True):
        """Write the crontab to a user (or root) instead of a file."""
        return self.write(user=user)

    def run_pending(self, **kwargs):
        """Run all commands in this crontab if pending (generator)"""
        for job in self:
            ret = job.run_pending(**kwargs)
            if ret is not None:
                yield ret

    def run_scheduler(self, timeout=-1, **kwargs):
        """Run the CronTab as an internal scheduler (generator)"""
        count = 0
        self.run_pending()
        while count != timeout:
            count += 1
            sleep(kwargs.get('cadence', 60))
            now = datetime.now()
            if 'warp' in kwargs:
                now += timedelta(seconds=count * 60)
            for value in self.run_pending(now=now):
                yield value

    def render(self):
        """Render this crontab as it would be in the crontab."""
        crons = [unicode(cron) for cron in self.lines]
        result = unicode(self.env) + u'\n'.join(crons)
        if result and result[-1] not in (u'\n', u'\r'):
            result += u'\n'
        return result

    def new(self, command='', comment='', user=None):
        """
        Create a new cron with a command and comment.

        Returns the new CronItem object.
        """
        if not user and self.user is False:
            raise ValueError("User is required for system crontabs.")
        return self.append(CronItem(None, command, comment, user, self))

    def find_command(self, command):
        """Return an iter of jobs matching any part of the command."""
        for job in list(self.crons):
            if isinstance(command, re._pattern_type):
                if command.findall(job.command):
                    yield job
            elif command in job.command:
                yield job

    def find_comment(self, comment):
        """Return an iter of jobs that match the comment field exactly."""
        for job in list(self.crons):
            if isinstance(comment, re._pattern_type):
                if comment.findall(job.comment):
                    yield job
            elif comment == job.comment:
                yield job

    def find_time(self, *args):
        """Return an iter of jobs that match this time pattern"""
        for job in list(self.crons):
            if job.slices == CronSlices(*args):
                yield job

    @property
    def commands(self):
        """Return a generator of all unqiue commands used in this crontab"""
        returned = []
        for cron in self.crons:
            if cron.command not in returned:
                yield cron.command
                returned.append(cron.command)

    @property
    def comments(self):
        """Return a generator of all unique comments/Id used in this crontab"""
        returned = []
        for cron in self.crons:
            if cron.comment and cron.comment not in returned:
                yield cron.comment
                returned.append(cron.comment)

    def remove_all(self, *args, **kwargs):
        """Removes all crons using the stated command OR that have the
        stated comment OR removes everything if no arguments specified.

           command - Remove all with this command
           comment - Remove all with this comment or ID
           time    - Remove all with this time code
        """
        if args:
            raise AttributeError("Invalid use: remove_all(command='cmd')")
        if 'command' in kwargs:
            return self.remove(*self.find_command(kwargs['command']))
        elif 'comment' in kwargs:
            return self.remove(*self.find_comment(kwargs['comment']))
        elif 'time' in kwargs:
            return self.remove(*self.find_time(kwargs['time']))
        return self.remove(*self.crons[:])

    def remove(self, *items):
        """Remove a selected cron from the crontab."""
        result = 0
        for item in items:
            result += self._remove(item)
        return result

    def _remove(self, item):
        """Internal removal of an item"""
        # Manage siblings when items are deleted
        for sibling in self.lines[self.lines.index(item)+1:]:
            if isinstance(sibling, CronItem):
                env = sibling.env
                sibling.env = item.env
                sibling.env.update(env)
                sibling.env.job = sibling
                break
            elif sibling == '':
                self.lines.remove(sibling)
            else:
                break

        self.crons.remove(item)
        self.lines.remove(item)
        return 1

    def __repr__(self):
        kind = 'System ' if self._user == False else ''
        if self.filen:
            return "<%sCronTab '%s'>" % (kind, self.filen)
        elif self.user and not self.user_opt:
            return "<My CronTab>"
        elif self.user:
            return "<User CronTab '%s'>" % self.user
        return "<Unattached %sCronTab>" % kind

    def __iter__(self):
        """Return generator so we can track jobs after removal"""
        for job in list(self.crons.__iter__()):
            yield job

    def __getitem__(self, i):
        return self.crons[i]

    def __unicode__(self):
        return self.render()

    def __len__(self):
        return len(self.crons)

    def __str__(self):
        return self.render()


class CronItem(object):
    """
    An item which objectifies a single line of a crontab and
    May be considered to be a cron job object.
    """
    def __init__(self, line=None, command='', comment='', user=None, cron=None):
        self.cron = cron
        self.user = user
        self.valid = False
        self.enabled = True
        self.special = False
        self.comment = None
        self.command = None
        self.last_run = None
        self.env = OrderedVariableList(job=self)

        self._log = None

        # Initalise five cron slices using static info.
        self.slices = CronSlices()

        self.set_comment(comment)

        if line and line.strip():
            self.parse(line.strip())
        elif command:
            self.set_command(command)
            self.valid = True

    def delete(self):
        """Delete this item and remove it from it's parent"""
        if not self.cron:
            raise UnboundLocalError("Cron item is not in a crontab!")
        else:
            self.cron.remove(self)

    def set_command(self, cmd):
        """Set the command and filter as needed"""
        self.command = cmd.strip()

    def set_comment(self, cmt):
        """Set the comment and don't filter"""
        self.comment = cmt

    def parse(self, line):
        """Parse a cron line string and save the info as the objects."""
        line = _unicode(line)
        if not line or line[0] == '#':
            self.enabled = False
            line = line[1:].strip()
        self._set_parse(ITEMREX.findall(line))
        self._set_parse(SPECREX.findall(line))

    def _set_parse(self, result):
        """Set all the parsed variables into the item"""
        if not result:
            return
        if self.cron.user == False:
            # Special flag to look for per-command user
            (self.user, cmd) = (result[0][-3] + ' ').split(' ', 1)
            self.set_command(cmd)
        else:
            self.set_command(result[0][-3])

        self.valid = self.setall(*result[0][:-3])
        self.comment = result[0][-1]
        self.enabled = self.enabled and self.valid

    def enable(self, enabled=True):
        """Set if this cron job is enabled or not"""
        if enabled in [True, False]:
            self.enabled = enabled
        return self.enabled

    def is_enabled(self):
        """Return true if this job is enabled (not commented out)"""
        return self.enabled

    def is_valid(self):
        """Return true if this job is valid"""
        return self.valid

    def render(self):
        """Render this set cron-job to a string"""
        self.command = _unicode(self.command)
        user = ''
        if self.cron and self.cron.user is False:
            if not self.user:
                raise ValueError("Job to system-cron format, no user set!")
            user = self.user + ' '
        result = u"%s %s%s" % (unicode(self.slices), user, self.command)
        if self.comment:
            self.comment = _unicode(self.comment)
            if SYSTEMV:
                result = "# " + self.comment + "\n" + result
            else:
                result += u" # " + self.comment
        if not self.enabled:
            result = u"# " + result
        return unicode(self.env) + result

    def every_reboot(self):
        """Set to every reboot instead of a time pattern: @reboot"""
        self.clear()
        return self.slices.setall('@reboot')

    def every(self, unit=1):
        """
        Replace existing time pattern with a single unit, setting all lower
        units to first value in valid range.

        For instance job.every(3).days() will be `0 0 */3 * *`
        while job.day().every(3) would be `* * */3 * *`

        Many of these patterns exist as special tokens on Linux, such as
        `@midnight` and `@hourly`
        """
        return Every(self.slices, unit)

    def setall(self, *args):
        """Replace existing time pattern with these five values given as args:

           job.setall("1 2 * * *")
           job.setall(1, 2) == '1 2 * * *'
           job.setall(0, 0, None, '>', 'SUN') == '0 0 * 12 SUN'
        """
        return self.slices.setall(*args)

    def clear(self):
        """Clear the special and set values"""
        return self.slices.clear()

    def frequency(self, year=None):
        """Returns the number of times this item will execute in a given year
           (defaults to this year)
        """
        return self.slices.frequency(year=year)

    def frequency_per_year(self, year=None):
        """Returns the number of /days/ this item will execute on in a year
           (defaults to this year)
        """
        return self.slices.frequency_per_year(year=year)

    def frequency_per_day(self):
        """Returns the number of time this item will execute in any day"""
        return self.slices.frequency_per_day()

    def frequency_per_hour(self):
        """Returns the number of times this item will execute in any hour"""
        return self.slices.frequency_per_hour()

    def run_pending(self, now=None):
        """Runs the command if scheduled"""
        now = now or datetime.now()
        if self.is_enabled():
            if self.last_run is not None:
                next_time = self.schedule(self.last_run).get_next()
                if next_time < now:
                    self.last_run = now
                    return self.run()
            else:
                self.last_run = now

    def run(self):
        """Runs the given command as a pipe"""
        shell = self.env.get('SHELL', SHELL)
        (out, err) = open_pipe(shell, '-c', self.command).communicate()
        if err:
            LOG.error(err.decode("utf-8"))
        return out.decode("utf-8").strip()

    def schedule(self, date_from=None):
        """Return a croniter schedule if available."""
        if not date_from:
            date_from = datetime.now()
        try:
            # Croniter is an optional import
            from croniter.croniter import croniter
        except ImportError:
            raise ImportError("Croniter not available. Please install croniter"
                          " python module via pip or your package manager")

        class Croniter(croniter):
            """Same as normal croniter, but always return datetime objects"""
            def get_next(self, type_ref=datetime):
                return croniter.get_next(self, type_ref)

            def get_prev(self, type_ref=datetime):
                return croniter.get_prev(self, type_ref)

            def get_current(self, type_ref=datetime):
                return croniter.get_current(self, type_ref)

        return Croniter(self.slices.clean_render(), date_from)

    def description(self, **kw):
        """
        Returns a description of the crontab's schedule (if available)
        
        **kw - Keyword arguments to pass to cron_descriptor (see docs)
        """
        try:
            from cron_descriptor import ExpressionDescriptor
        except ImportError:
            raise ImportError("cron_descriptor not available. Please install"
              "cron_descriptor python module via pip or your package manager")

        exdesc = ExpressionDescriptor(self.slices.clean_render(), **kw)
        return exdesc.get_description()

    @property
    def log(self):
        """Return a cron log specific for this job only"""
        if not self._log and self.cron:
            self._log = self.cron.log.for_program(self.command)
        return self._log

    @property
    def minute(self):
        """Return the minute slice"""
        return self.slices[0]

    @property
    def minutes(self):
        """Same as minute"""
        return self.minute

    @property
    def hour(self):
        """Return the hour slice"""
        return self.slices[1]

    @property
    def hours(self):
        """Same as hour"""
        return self.hour

    @property
    def day(self):
        """Return the day slice"""
        return self.dom

    @property
    def dom(self):
        """Return the day-of-the month slice"""
        return self.slices[2]

    @property
    def month(self):
        """Return the month slice"""
        return self.slices[3]

    @property
    def months(self):
        """Same as month"""
        return self.month

    @property
    def dow(self):
        """Return the day of the week slice"""
        return self.slices[4]

    def __repr__(self):
        return "<CronJob '%s'>" % unicode(self)

    def __len__(self):
        return len(unicode(self))

    def __getitem__(self, key):
        return self.slices[key]

    def __lt__(self, value):
        return self.frequency() < CronSlices(value).frequency()

    def __gt__(self, value):
        return self.frequency() > CronSlices(value).frequency()

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        if not self.is_valid():
            raise ValueError('Refusing to render invalid crontab.'
                             ' Disable to continue.')
        return self.render()


class Every(object):
    """Provide an interface to the job.every() method:
        Available Calls:
          minute, minutes, hour, hours, dom, doms, month, months, dow, dows

       Once run all units will be cleared (set to *) then proceeding units
       will be set to '0' and the target unit will be set as every x units.
    """
    def __init__(self, item, units):
        self.slices = item
        self.unit = units
        for (key, name) in enumerate(['minute', 'hour', 'dom', 'month', 'dow',
                                 'min', 'hour', 'day', 'moon', 'weekday']):
            setattr(self, name, self.set_attr(key % 5))
            setattr(self, name+'s', self.set_attr(key % 5))

    def set_attr(self, target):
        """Inner set target, returns function"""
        def innercall():
            """Returned inner call for setting slice targets"""
            self.slices.clear()
            # Day-of-week is actually a level 2 set, not level 4.
            for key in range(target == 4 and 2 or target):
                self.slices[key].on('<')
            self.slices[target].every(self.unit)
        return innercall

    def year(self):
        """Special every year target"""
        if self.unit > 1:
            raise ValueError("Invalid value '%s', outside 1 year" % self.unit)
        self.slices.setall('@yearly')


class CronSlices(list):
    """Controls a list of five time 'slices' which reprisent:
        minute frequency, hour frequency, day of month frequency,
        month requency and finally day of the week frequency.
     """
    def __init__(self, *args):
        super(CronSlices, self).__init__([CronSlice(info) for info in S_INFO])
        self.special = None
        if args and not self.setall(*args):
            raise ValueError("Can't set cron value to: %s" % unicode(args))
        self.is_valid = self.is_self_valid

    def is_self_valid(self, *args):
        """Object version of is_valid"""
        args = args or (self,)
        return CronSlices.is_valid(*args)

    @classmethod
    def is_valid(cls, *args):
        """Returns true if the arguments are valid cron pattern"""
        try:
            return bool(cls(*args))
        except Exception:
            return False

    def setall(self, value, *slices):
        """Parses the various ways date/time frequency can be specified"""
        self.clear()
        if isinstance(value, CronItem):
            slices = value.slices
        elif isinstance(value, datetime):
            slices = [value.minute, value.hour, value.day, value.month, '*']
        elif isinstance(value, time):
            slices = [value.minute, value.hour, '*', '*', '*']
        elif isinstance(value, date):
            slices = [0, 0, value.day, value.month, '*']
          # It might be possible to later understand timedelta objects
          # but there's no convincing mathematics to do the conversion yet.
        elif isinstance(value, list):
            slices = value
        elif slices:
            slices = (value,) + slices
        elif isinstance(value, basestring) and value:
            if value.count(' ') == 4:
                slices = value.strip().split(' ')
            elif value.strip()[0] == '@':
                value = value[1:]
                slices = None
            else:
                slices = [value]

            if 'reboot' in (value, value[1:]):
                self.special = '@reboot'
                return True
            elif value in SPECIALS.keys():
                return self.setall(SPECIALS[value])
            elif not slices:
                return False

        if id(slices) == id(self):
            raise AssertionError("Can not set cron to itself!")

        for set_a, set_b in zip(self, slices):
            try:
                set_a.parse(set_b)
            except ValueError as error:
                LOG.warning(unicode(error))
                return False
            except Exception:
                return False
        return True

    def clean_render(self):
        """Return just numbered parts of this crontab"""
        return ' '.join([unicode(s) for s in self])

    def render(self):
        "Return just the first part of a cron job (the numbers or special)"
        slices = self.clean_render()
        if self.special:
            return self.special
        elif not SYSTEMV:
            for (name, value) in SPECIALS.items():
                if value == slices and name not in SPECIAL_IGNORE:
                    return "@%s" % name
        return slices

    def clear(self):
        """Clear the special and set values"""
        self.special = None
        for item in self:
            item.clear()

    def frequency(self, year=None):
        """Return frequence per year times frequency per day"""
        return self.frequency_per_year(year=year) * self.frequency_per_day()

    def frequency_per_year(self, year=None):
        """Returns the number of times this item will execute
           in a given year (default is this year)"""
        result = 0
        if not year:
            year = date.today().year

        weekdays = list(self[4])

        for month in self[3]:
            for day in self[2]:
                try:
                    if date(year, month, day).weekday() in weekdays:
                        result += 1
                except ValueError:
                    continue
        return result

    def frequency_per_day(self):
        """Returns the number of times this item will execute in any day"""
        return len(self[0]) * len(self[1])

    def frequency_per_hour(self):
        """Returns the number of times this item will execute in any hour"""
        return len(self[0])

    def __str__(self):
        return self.render()

    def __eq__(self, arg):
        return self.render() == CronSlices(arg).render()


class SundayError(KeyError):
    """Sunday was specified as 7 instead of 0"""
    pass

class Also(object):
    """Link range values together (appending instead of replacing)"""
    def __init__(self, obj):
        self.obj = obj

    def every(self, *a):
        """Also every one of these"""
        return self.obj.every(*a, also=True)

    def on(self, *a):
        """Also on these"""
        return self.obj.on(*a, also=True)

    def during(self, *a):
        """Also during these"""
        return self.obj.during(*a, also=True)

class CronSlice(object):
    """Cron slice object which shows a time pattern"""
    def __init__(self, info, value=None):
        if isinstance(info, int):
            info = S_INFO[info]
        self.min = info.get('min', None)
        self.max = info.get('max', None)
        self.name = info.get('name', None)
        self.enum = info.get('enum', None)
        self.parts = []
        if value:
            self.parse(value)

    def parse(self, value):
        """Set values into the slice."""
        self.parts = []
        if value is None:
            return self.clear()
        for part in unicode(value).split(','):
            if part.find("/") > 0 or part.find("-") > 0 or part == '*':
                self.parts += self.get_range(part)
                continue

            try:
                self.parts.append(self.parse_value(part, sunday=0))
            except ValueError as err:
                raise ValueError('%s:%s/%s' % (unicode(err), self.name, part))

    def render(self, resolve=False):
        """Return the slice rendered as a crontab.

        resolve - return integer values instead of enums (default False)

        """
        if len(self.parts) == 0:
            return '*'
        return _render_values(self.parts, ',', resolve)

    def __repr__(self):
        return "<CronSlice '%s'>" % unicode(self)

    def __eq__(self, value):
        return unicode(self) == unicode(value)

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return self.render()

    def every(self, n_value, also=False):
        """Set the every X units value"""
        if not also:
            self.clear()
        self.parts += self.get_range(int(n_value))
        return self.parts[-1]

    def on(self, *n_value, **opts):
        """Set the time values to the specified placements."""
        if not opts.get('also', False):
            self.clear()
        for set_a in n_value:
            self.parts += self.parse_value(set_a, sunday=0),
        return self.parts

    def during(self, vfrom, vto, also=False):
        """Set the During value, which sets a range"""
        if not also:
            self.clear()
        self.parts += self.get_range(unicode(vfrom) + '-' + unicode(vto))
        return self.parts[-1]

    @property
    def also(self):
        """Appends rather than replaces the new values"""
        return Also(self)

    def clear(self):
        """clear the slice ready for new vaues"""
        self.parts = []

    def get_range(self, *vrange):
        """Return a cron range for this slice"""
        ret = CronRange(self, *vrange)
        if ret.dangling is not None:
            return [ret.dangling, ret]
        return [ret]

    def __iter__(self):
        """Return the entire element as an iterable"""
        ret = {}
        # An empty part means '*' which is every(1)
        if not self.parts:
            self.every(1)
        for part in self.parts:
            if isinstance(part, CronRange):
                for bit in part.range():
                    ret[bit] = 1
            else:
                ret[int(part)] = 1
        for val in ret:
            yield val

    def __len__(self):
        """Returns the number of times this slice happens in it's range"""
        return len(list(self.__iter__()))

    def parse_value(self, val, sunday=None):
        """Parse the value of the cron slice and raise any errors needed"""
        if val == '>':
            val = self.max
        elif val == '<':
            val = self.min
        try:
            out = get_cronvalue(val, self.enum)
        except ValueError:
            raise ValueError("Unrecognised '%s'='%s'" % (self.name, val))
        except KeyError:
            raise KeyError("No enumeration '%s' got '%s'" % (self.name, val))

        if self.max == 6 and int(out) == 7:
            if sunday is not None:
                return sunday
            raise SundayError("Detected Sunday as 7 instead of 0!")

        if int(out) < self.min or int(out) > self.max:
            raise ValueError("Invalid value '%s', expected %d-%d for %s" % (
                unicode(val), self.min, self.max, self.name))
        return out


def get_cronvalue(value, enums):
    """Returns a value as int (pass-through) or a special enum value"""
    if isinstance(value, int):
        return value
    elif unicode(value).isdigit():
        return int(str(value))
    if not enums:
        raise KeyError("No enumeration allowed")
    return CronValue(unicode(value), enums)


class CronValue(object):
    """Represent a special value in the cron line"""
    def __init__(self, value, enums):
        self.enum = value
        self.value = enums.index(value.lower())

    def __lt__(self, value):
        return self.value < int(value)

    def __repr__(self):
        return unicode(self)

    def __str__(self):
        return self.enum

    def __int__(self):
        return self.value


def _render_values(values, sep=',', resolve=False):
    """Returns a rendered list, sorted and optionally resolved"""
    if len(values) > 1:
        values.sort()
    return sep.join([_render(val, resolve) for val in values])


def _render(value, resolve=False):
    """Return a single value rendered"""
    if isinstance(value, CronRange):
        return value.render(resolve)
    if resolve:
        return str(int(value))
    return unicode(value)


class CronRange(object):
    """A range between one value and another for a time range."""
    def __init__(self, vslice, *vrange):
        # holds an extra dangling entry, for example sundays.
        self.dangling = None
        self.slice = vslice
        self.cron = None
        self.seq = 1

        if not vrange:
            self.all()
        elif isinstance(vrange[0], basestring):
            self.parse(vrange[0])
        elif isinstance(vrange[0], int) or isinstance(vrange[0], CronValue):
            if len(vrange) == 2:
                (self.vfrom, self.vto) = vrange
            else:
                self.seq = vrange[0]
                self.all()

    def parse(self, value):
        """Parse a ranged value in a cronjob"""
        if value.count('/') == 1:
            value, seq = value.split('/')
            try:
                self.seq = self.slice.parse_value(seq)
            except SundayError:
                self.seq = 1
                value = "0-0"
            if self.seq < 1 or self.seq > self.slice.max - 1:
                raise ValueError("Sequence can not be divided by zero or max")
        if value.count('-') == 1:
            vfrom, vto = value.split('-')
            self.vfrom = self.slice.parse_value(vfrom, sunday=0)
            try:
                self.vto = self.slice.parse_value(vto)
            except SundayError:
                if self.vfrom == 1:
                    self.vfrom = 0
                else:
                    self.dangling = 0
                self.vto = self.slice.parse_value(vto, sunday=6)
            if self.vto < self.vfrom:
                logging.warning("Cron range is backwards '%d-%d'" % \
                        (self.vfrom, self.vto))
        elif value == '*':
            self.all()
        else:
            raise ValueError('Unknown cron range value "%s"' % value)

    def all(self):
        """Set this slice to all units between the miniumum and maximum"""
        self.vfrom = self.slice.min
        self.vto = self.slice.max

    def render(self, resolve=False):
        """Render the ranged value for a cronjob"""
        value = '*'
        if int(self.vfrom) > self.slice.min or int(self.vto) < self.slice.max:
            if self.vfrom == self.vto:
                value = unicode(self.vfrom)
            else:
                value = _render_values([self.vfrom, self.vto], '-', resolve)
        if self.seq != 1:
            value += "/%d" % self.seq
        if value != '*' and SYSTEMV:
            value = ','.join([unicode(val) for val in self.range()])
        return value

    def range(self):
        """Returns the range of this cron slice as a iterable list"""
        return range(int(self.vfrom), int(self.vto)+1, self.seq)

    def every(self, value):
        """Set the sequence value for this range."""
        self.seq = int(value)

    def __lt__(self, value):
        return int(self.vfrom) < int(value)

    def __gt__(self, value):
        return int(self.vto) > int(value)

    def __int__(self):
        return int(self.vfrom)

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return self.render()


class OrderedVariableList(OrderedDict):
    """An ordered dictionary with a linked list containing
    the previous OrderedVariableList which this list depends.

    Duplicates in this list are weeded out in favour of the previous
    list in the chain.

    This is all in aid of the ENV variables list which must exist one
    per job in the chain.
    """
    def __init__(self, *args, **kw):
        self.job = kw.pop('job', None)
        super(OrderedVariableList, self).__init__(*args, **kw)

    @property
    def previous(self):
        """Returns the previous env in the list of jobs in the cron"""
        if self.job is not None and self.job.cron is not None:
            index = self.job.cron.crons.index(self.job)
            if index == 0:
                return self.job.cron.env
            else:
                return self.job.cron[index-1].env
        return None

    def all(self):
        """
        Returns the full dictionary, everything from this dictionary
        plus all those in the chain above us.
        """
        if self.job is not None:
            ret = self.previous.all().copy()
            ret.update(self)
            return ret
        return self.copy()

    def __getitem__(self, key):
        previous = self.previous
        if key in self:
            return super(OrderedVariableList, self).__getitem__(key)
        elif previous is not None:
            return previous.all()[key]
        raise KeyError("Environment Variable '%s' not found." % key)

    def __str__(self):
        """Constructs to variable list output used in cron jobs"""
        ret = []
        previous = self.previous.all() if self.previous else None
        for key, value in self.items():
            if self.previous:
                if self.previous.all().get(key, None) == value:
                    continue
            if ' ' in unicode(value):
                value = '"%s"' % value
            ret.append("%s=%s" % (key, unicode(value)))
        ret.append('')
        return "\n".join(ret)


