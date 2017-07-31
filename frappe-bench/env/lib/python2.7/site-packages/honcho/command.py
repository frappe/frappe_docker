import argparse
import codecs
import logging
import os
import sys
import signal
from collections import defaultdict
from pkg_resources import iter_entry_points

from honcho import __version__
from honcho.process import Popen
from honcho.manager import Manager
from honcho.printer import Printer
from honcho import compat, environ

logging.basicConfig(format='%(asctime)s [%(process)d] [%(levelname)s] '
                           '%(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)
log = logging.getLogger(__name__)

BASENAME = os.path.basename(os.getcwd())

export_choices = dict((_export.name, _export)
                      for _export in iter_entry_points('honcho_exporters'))


class CommandError(Exception):
    pass


def _add_common_args(parser, with_defaults=False):
    suppress = None if with_defaults else argparse.SUPPRESS
    parser.add_argument('-e', '--env',
                        default=(suppress or '.env'),
                        help='environment file[,file] (default: .env)')
    parser.add_argument('-d', '--app-root',
                        metavar='DIR',
                        default=(suppress or '.'),
                        help='procfile directory (default: .)')
    parser.add_argument('--no-colour',
                        action='store_true',
                        help='disable coloured output')
    parser.add_argument('--no-prefix',
                        action='store_true',
                        help='disable logging prefix')
    parser.add_argument('-f', '--procfile',
                        metavar='FILE',
                        default=suppress,
                        help='procfile path (default: Procfile)')
    parser.add_argument('-v', '--version',
                        action='version',
                        version='%(prog)s ' + __version__)


parser = argparse.ArgumentParser(
    'honcho',
    description='Manage Procfile-based applications')
_add_common_args(parser, with_defaults=True)

subparsers = parser.add_subparsers(title='tasks', dest='command')
subparsers.required = True


def command_check(args):
    procfile = _procfile(_procfile_path(args.app_root, _choose_procfile(args)))

    log.info('Valid procfile detected ({0})'.format(', '.join(procfile.processes)))


parser_check = subparsers.add_parser(
    'check',
    help="validate a Procfile")
_add_common_args(parser_check)


def command_export(args):
    if args.log == "/var/log/APP":
        args.log = args.log.replace('APP', args.app)

    procfile_path = _procfile_path(args.app_root, _choose_procfile(args))
    procfile = _procfile(procfile_path)
    env = _read_env(args.app_root, args.env)
    concurrency = _parse_concurrency(args.concurrency)
    port = _choose_port(args, env)

    processes = environ.expand_processes(procfile.processes,
                                         concurrency=concurrency,
                                         env=env,
                                         port=port)

    export_ctor = export_choices[args.format].load()
    export = export_ctor(template_dir=args.template_dir)

    context = {
        'app': args.app,
        'app_root': os.path.abspath(args.app_root),
        'log': args.log,
        'shell': args.shell,
        'user': args.user or args.app,
    }

    _mkdir(args.location)

    for f in export.render(processes, context):
        path = os.path.join(args.location, f.name)
        log.info("Writing '%s'", path)
        _write_file(path, f.content)
        if f.executable:
            os.chmod(path, 0o755)


parser_export = subparsers.add_parser(
    'export',
    help="export a Procfile to another format")
_add_common_args(parser_export)
parser_export.add_argument(
    '-a', '--app',
    help="alternative app name", default=BASENAME, type=str, metavar='APP')
parser_export.add_argument(
    '-l', '--log',
    help="directory to place process logs in",
    default="/var/log/APP", type=str, metavar='DIR')
parser_export.add_argument(
    '-p', '--port',
    help="starting port number (default: 5000)",
    default=argparse.SUPPRESS, type=int, metavar='N')
parser_export.add_argument(
    '-c', '--concurrency',
    help='number of each process type to run.',
    type=str, metavar='process=num,process=num')
parser_export.add_argument(
    '-u', '--user',
    help="user the application should run as",
    type=str)
parser_export.add_argument(
    '-s', '--shell',
    help="the shell that should run the application",
    default='/bin/sh', type=str)
parser_export.add_argument(
    '-t', '--template-dir',
    help="directory to search for custom templates",
    default=None, type=str, metavar='DIR')
parser_export.add_argument(
    'format',
    help="format to export to; one of %(choices)s",
    choices=sorted(export_choices.keys()),
    type=str, metavar="FORMAT")
parser_export.add_argument(
    'location',
    help="folder to export to",
    type=str, metavar="LOCATION")


def command_help(args):
    argv = ['--help']
    if args.task:
        argv.append(args.task)
    return parser.parse_args(argv[::-1])


parser_help = subparsers.add_parser(
    'help',
    help="describe available tasks or one specific task")
parser_help.add_argument('task', help='task to show help for', nargs='?')


def command_run(args):
    os.environ.update(_read_env(args.app_root, args.env))

    argv = args.argv

    # If the first of the remaining args is '--', skip it.
    if argv and argv[0] == '--':
        argv = argv[1:]

    if compat.ON_WINDOWS:
        # do not quote on Windows, subprocess will handle it for us
        # using the MSFT quoting rules
        cmd = argv
    else:
        cmd = ' '.join(compat.shellquote(arg) for arg in argv)

    p = Popen(cmd, stdout=sys.stdout, stderr=sys.stderr,
              start_new_session=False)
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    p.wait()
    sys.exit(p.returncode)


parser_run = subparsers.add_parser(
    'run',
    help="run a command using your application's environment")
_add_common_args(parser_run)
parser_run.add_argument(
    'argv',
    nargs=argparse.REMAINDER,
    help='command to run')


def command_start(args):
    procfile_path = _procfile_path(args.app_root, _choose_procfile(args))
    procfile = _procfile(procfile_path)

    concurrency = _parse_concurrency(args.concurrency)
    env = _read_env(args.app_root, args.env)
    quiet = _parse_quiet(args.quiet)
    port = _choose_port(args, env)

    if args.processes:
        processes = compat.OrderedDict()
        for name in args.processes:
            try:
                processes[name] = procfile.processes[name]
            except KeyError:
                raise CommandError("Process type '{0}' does not exist in Procfile".format(name))
    else:
        processes = procfile.processes

    manager = Manager(Printer(sys.stdout,
                              colour=(not args.no_colour),
                              prefix=(not args.no_prefix)))

    for p in environ.expand_processes(processes,
                                      concurrency=concurrency,
                                      env=env,
                                      quiet=quiet,
                                      port=port):
        e = os.environ.copy()
        e.update(p.env)
        manager.add_process(p.name, p.cmd, quiet=p.quiet, env=e)

    manager.loop()
    sys.exit(manager.returncode)


parser_start = subparsers.add_parser(
    'start',
    help="start the application (or a specific PROCESS)")
_add_common_args(parser_start)
parser_start.add_argument(
    '-p', '--port',
    help="starting port number (default: 5000)",
    type=int, default=argparse.SUPPRESS, metavar='N')
parser_start.add_argument(
    '-c', '--concurrency',
    help='the number of each process type to run.',
    type=str, metavar='process=num,process=num')
parser_start.add_argument(
    '-q', '--quiet',
    help='process names for which to suppress output',
    type=str, metavar='process1,process2,process3')
parser_start.add_argument(
    'processes', nargs='*',
    help='process(es) to start (default: all processes)')


def command_version(args):
    print('{prog} {version}'.format(
        prog=parser.prog,
        version=__version__))


parser_version = subparsers.add_parser(
    'version',
    help="display honcho version")


COMMANDS = {
    'check': command_check,
    'export': command_export,
    'help': command_help,
    'run': command_run,
    'start': command_start,
    'version': command_version,
}


def main(argv=None):
    if argv is not None:
        args = parser.parse_args(argv)
    else:
        args = parser.parse_args()

    try:
        _check_output_encoding()
        COMMANDS[args.command](args)
    except CommandError as e:
        log.error(str(e))
        sys.exit(1)


def _procfile_path(app_root, procfile):
    return os.path.join(app_root, procfile)


def _procfile(filename):
    try:
        with open(filename) as f:
            content = f.read()
    except IOError:
        raise CommandError('Procfile does not exist or is not a file')

    try:
        procfile = environ.parse_procfile(content)
    except AssertionError as e:
        raise CommandError(str(e))

    return procfile


def _read_env(app_root, env):
    files = [e.strip() for e in env.split(',')]
    content = []
    for envfile in files:
        try:
            with open(os.path.join(app_root, envfile)) as f:
                content.append(f.read())
        except IOError:
            pass

    return environ.parse('\n'.join(content))


def _parse_concurrency(desc):
    result = defaultdict(lambda: 1)
    if desc is None:
        return result
    for item in desc.split(','):
        key, concurrency = item.split('=', 1)
        result[key] = int(concurrency)
    return result


def _parse_quiet(desc):
    result = []
    if desc is None:
        return result
    result = desc.split(',')
    return result


def _choose_procfile(args):
    env = _read_env(args.app_root, args.env)
    env_procfile = env.pop('PROCFILE', None)

    if hasattr(args, 'procfile') and args.procfile is not None:
        return args.procfile
    elif env_procfile is not None:
        return env_procfile
    else:
        return "Procfile"


def _choose_port(args, env):
    env_port = env.pop('PORT', None)
    os_env_port = os.environ.pop('PORT', None)

    if hasattr(args, 'port'):
        return args.port
    elif env_port is not None:
        return int(env_port)
    elif os_env_port is not None:
        return int(os_env_port)
    else:
        return 5000


def _mkdir(path):
    if os.path.exists(path):
        return
    try:
        os.makedirs(path)
    except OSError as e:
        log.error("Could not create export directory")
        raise CommandError(e)


def _write_file(path, content):
    _mkdir(os.path.dirname(path))
    try:
        with open(path, 'w') as fp:
            fp.write(content)
    except IOError as e:
        log.error("Could not write to export file")
        raise CommandError(e)


def _check_output_encoding():
    no_encoding = sys.stdout.encoding is None
    utf8 = codecs.lookup('utf8')

    if not sys.stdout.isatty():
        return

    if no_encoding or codecs.lookup(sys.stdout.encoding) != utf8:
        log.warn('Your terminal is not configured to receive UTF-8 encoded '
                 'text. Please adjust your locale settings or force UTF-8 '
                 'output by setting PYTHONIOENCODING="utf-8".')


if __name__ == '__main__':
    main()
