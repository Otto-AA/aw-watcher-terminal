import argparse
import shlex
from time import sleep
from typing import Callable, Any
from aw_core.models import Event
from aw_watcher_terminal import config


# Event parsers
#
# base --event preexec --pid 1234 --time 2018-07-01T09:13:15,215744806+02:00
#      --path /home/me/
parser_base = argparse.ArgumentParser(description='Parses the event',
                                      add_help=False)
parser_base.add_argument('--event', dest='event', required=True,
                         help='the trigger event (e.g. preexec)')
parser_base.add_argument('--pid', dest='pid', required=True,
                         help='the process id of the current terminal')
parser_base.add_argument('--time', dest='time', required=True,
                         help='the time the event got triggered in iso-8601')
parser_base.add_argument('--path', dest='path', required=True,
                         help='the path of the shell')

# preopen --pid 1234
parser_preopen = argparse.ArgumentParser(parents=[parser_base])
parser_preopen.description = 'Parses preopen events'

# preopen --pid 1234 --command ls --path /my/path --shell bash
parser_preexec = argparse.ArgumentParser(parents=[parser_base])
parser_preexec.description = 'Parses preexec events'
parser_preexec.add_argument('--command', dest='command', required=True,
                            help='the command entered by the user')
parser_preexec.add_argument('--shell', dest='shell', required=True,
                            help='the name of the shell used')

# precmd --pid 1234 --exit-code 0
parser_precmd = argparse.ArgumentParser(parents=[parser_base])
parser_precmd.description = 'Parses precmd events'
parser_precmd.add_argument('--exit-code', dest='exit_code', required=True,
                           help='the exit code of the last command')

# preclose --pid 1234
parser_preclose = argparse.ArgumentParser(parents=[parser_base])
parser_preclose.description = 'Parses preclose events'


# Dict containing data related to process ids
# Keys are the process ids
terminal_processes_data = {}


class TerminalProcessData:
    def __init__(self, pid: str):
        self.pid = pid
        self.event = None

# Type for event handler functions
EventHandler = Callable[[
    argparse.Namespace,
    list
    ], Any
]
EventHandlerDecorator = Callable[[EventHandler], EventHandler]


def store_pid_if_not_existing(func: EventHandler) -> EventHandler:
    """Add the pid to terminal_processes_data if not existing"""
    def decorator(args: argparse.Namespace, args_raw: list) -> Any:
        pid = args.pid

        if pid not in terminal_processes_data:
            terminal_processes_data[pid] = TerminalProcessData(pid)

        return func(args, args_raw)
    return decorator


def log_args(func_name: str, keys: list) -> EventHandlerDecorator:
    """Log the given args (first parameter) in debug mode"""
    def decorator(func: EventHandler) -> EventHandler:
        def decorated_function(args: argparse.Namespace,
                               args_raw: list) -> Any:
            config.logger.debug(func_name)
            for key in keys:
                if key in vars(args):
                    config.logger.debug("| {}={}".format(key, vars(args)[key]))

            return func(args, args_raw)
        return decorated_function
    return decorator


def parse_args(parser: argparse.ArgumentParser) -> EventHandlerDecorator:
    """Parse a list of arguments with the specified parser"""
    def decorator(func: EventHandler) -> Callable[[list], Any]:
        def decorated_function(args_raw: list) -> Any:
            try:
                args, unknown_args = parser.parse_known_args(args_raw)
                return func(args, args_raw)
            except (argparse.ArgumentError, argparse.ArgumentTypeError,
                    SystemExit) as e:
                config.logger.error("Error while parsing args")
        return decorated_function
    return decorator


def split_str_into_cli_args(func: Callable[
                                    [list], Any]) -> Callable[[str], Any]:
    """Split a string containing cli args into a list of cli args"""
    def decorator(message: str) -> Any:
        cli_args = shlex.split(message)
        return func(cli_args)
    return decorator


def for_line_in_str(func: Callable[[str], Any]) -> Callable[[str], Any]:
    """Call the decorated function once per line of the string"""
    def decorator(message: str) -> None:
        for line in message.split('\n'):
            if len(line):
                func(line)
    return decorator


@for_line_in_str
@split_str_into_cli_args
@parse_args(parser_base)
def handle_fifo_message(args: argparse.Namespace, args_raw: list) -> None:
    """Call the specified event handler with the remaining args"""

    # TODO: Check what happens if preexec and precmd order is swapped
    # (e.g. because aw-watcher-bash-preexec is too slow)

    possible_events = {
        "preopen": preopen,
        "preexec": preexec,
        "precmd": precmd,
        "preclose": preclose
    }

    if args.event not in possible_events:
        config.logger.error("Unknown event: {}".format(args.event))
    else:
        possible_events[args.event](args_raw)


@parse_args(parser_preopen)
@log_args("preopen", ["pid"])
@store_pid_if_not_existing
def preopen(args: argparse.Namespace, args_raw: list) -> None:
    """Handle terminal creation"""
    # work done by decorators
    pass


@parse_args(parser_preexec)
@log_args("preexec", ["pid", "command", "time"])
@store_pid_if_not_existing
def preexec(args: argparse.Namespace, args_raw: list) -> None:
    process = terminal_processes_data[args.pid]
    process.event = insert_event(vars(args))


@parse_args(parser_precmd)
@log_args("precmd", ["pid", "exit_code", "time"])
@store_pid_if_not_existing
def precmd(args: argparse.Namespace, args_raw: list) -> None:
    process = terminal_processes_data[args.pid]

    if process.event is None:
        return

    # TODO: Alter execution_time / duration of the event
    event_data = process.event.data
    event_data["exit_code"] = args.exit_code
    insert_event(event_data, id=process.event.id)

    process.event = None


@parse_args(parser_preclose)
@log_args("preclose", ["pid"])
def preclose(args: argparse.Namespace, args_raw: list) -> None:
    terminal_processes_data.pop(args.pid)


def insert_event(event_data: dict, **kwargs) -> Event:
    """Send event to the aw-server"""
    event = Event(data=event_data, **kwargs)
    inserted_event = config.client.insert_event(config.bucket_id, event)

    # The event returned from insert_event has been assigned an id by aw-server
    assert inserted_event.id is not None
    config.logger.info("Successfully sent event")

    return inserted_event
