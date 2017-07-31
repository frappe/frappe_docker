from collections import defaultdict
from collections import namedtuple
import datetime
import errno
import shlex
import os
import re
import signal

from . import compat

if compat.ON_WINDOWS:
    import ctypes


PROCFILE_LINE = re.compile(r'^([A-Za-z0-9_]+):\s*(.+)$')


class Env(object):

    def now(self):
        return datetime.datetime.now()

    if compat.ON_WINDOWS:
        def terminate(self, pid):
            # The first argument to OpenProcess represents the desired access
            # to the process. 1 represents the PROCESS_TERMINATE access right.
            handle = ctypes.windll.kernel32.OpenProcess(1, False, pid)
            ctypes.windll.kernel32.TerminateProcess(handle, -1)
            ctypes.windll.kernel32.CloseHandle(handle)
    else:
        def terminate(self, pid):
            try:
                os.killpg(pid, signal.SIGTERM)
            except OSError as e:
                if e.errno not in [errno.EPERM, errno.ESRCH]:
                    raise

    if compat.ON_WINDOWS:
        def kill(self, pid):
            # There's no SIGKILL on Win32...
            self.terminate(pid)
    else:
        def kill(self, pid):
            try:
                os.killpg(pid, signal.SIGKILL)
            except OSError as e:
                if e.errno not in [errno.EPERM, errno.ESRCH]:
                    raise


class Procfile(object):
    """A data structure representing a Procfile"""

    def __init__(self):
        self.processes = compat.OrderedDict()

    def add_process(self, name, command):
        assert name not in self.processes, \
            "process names must be unique within a Procfile"
        self.processes[name] = command


def parse_procfile(contents):
    p = Procfile()
    for line in contents.splitlines():
        m = PROCFILE_LINE.match(line)
        if m:
            p.add_process(m.group(1), m.group(2))
    return p


def parse(content):
    """
    Parse the content of a .env file (a line-delimited KEY=value format) into a
    dictionary mapping keys to values.
    """
    values = {}
    for line in content.splitlines():
        lexer = shlex.shlex(line, posix=True)
        tokens = list(lexer)

        # parses the assignment statement
        if len(tokens) < 3:
            continue

        name, op = tokens[:2]
        value = ''.join(tokens[2:])

        if op != '=':
            continue
        if not re.match(r'[A-Za-z_][A-Za-z_0-9]*', name):
            continue

        value = value.replace(r'\n', '\n')
        value = value.replace(r'\t', '\t')
        values[name] = value

    return values


ProcessParams = namedtuple("ProcessParams", "name cmd quiet env")


def expand_processes(processes, concurrency=None, env=None, quiet=None, port=None):
    """
    Get a list of the processes that need to be started given the specified
    list of process types, concurrency, environment, quietness, and base port
    number.

    Returns a list of ProcessParams objects, which have `name`, `cmd`, `env`,
    and `quiet` attributes, corresponding to the parameters to the constructor
    of `honcho.process.Process`.
    """
    if env is not None and env.get("PORT") is not None:
        port = int(env.get("PORT"))

    if quiet is None:
        quiet = []

    con = defaultdict(lambda: 1)
    if concurrency is not None:
        con.update(concurrency)

    out = []

    for name, cmd in compat.iteritems(processes):
        for i in range(con[name]):
            n = "{0}.{1}".format(name, i + 1)
            c = cmd
            q = name in quiet
            e = {'HONCHO_PROCESS_NAME': n}
            if env is not None:
                e.update(env)
            if port is not None:
                e['PORT'] = str(port + i)

            params = ProcessParams(n, c, q, e)
            out.append(params)
        if port is not None:
            port += 100

    return out
