import argparse
import shlex
from datetime import datetime, timezone
import iso8601
from time import sleep
from typing import Callable, Any
from aw_core.models import Event
from aw_watcher_terminal import config


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


def parse_iso8601_str(timestamp_str: str) -> datetime:
    """
    Takes something representing a timestamp and
    returns a timestamp in the representation we want.
    """
    timestamp = iso8601.parse_date(timestamp_str)
    if not timestamp.tzinfo:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return timestamp


# __events_in_queue contains all events indexed by the timestamp
__events_in_queue = {}
# __sorted_event_keys contains all keys sorted from oldest to newest
__sorted_event_keys = []


def _add_event_to_queue(event: Any, timestamp_iso8601: datetime) -> None:
    assert timestamp_iso8601 not in __events_in_queue
    __events_in_queue[timestamp_iso8601] = event

    # TODO: Predetermine index and insert into that position to prevent other
    # threads from using an unsorted list
    # (in case they operate between following two commands)
    __sorted_event_keys.append(timestamp_iso8601)
    __sorted_event_keys.sort(reverse=True)


def update_event_queue():
    """
    Handle events in the event_queue if they happened
    n or more seconds ago, whereas n=time_buffer
    """
    if not len(__sorted_event_keys):
        return

    # Only handle events which happened some time ago
    # to prevent processing them in a wrong order
    # if the shell-watcher sent them in a wrong order (with delay)
    time_buffer = 5

    cur_time = datetime.now(timezone.utc)
    oldest_event_time = __sorted_event_keys[0]
    time_diff = cur_time - oldest_event_time

    if time_diff.seconds > time_buffer:
        timestamp_key = __sorted_event_keys.pop()
        event = __events_in_queue.pop(timestamp_key)
        handle_event(event)

        # Call update_event_queue in case other events
        # are also ready to be processed
        update_event_queue()


class TerminalProcessData:
    def __init__(self, pid: str):
        self.pid = pid
        self.event = None

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
                         type=parse_iso8601_str,
                         help='the time the event got triggered in iso-8601')
parser_base.add_argument('--path', dest='path', required=True,
                         help='the path of the shell')

# preopen --pid 1234
parser_preopen = argparse.ArgumentParser(parents=[parser_base])
parser_preopen.description = 'Parses preopen events'

# preexec --pid 1234 --command ls --path /my/path --shell bash
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


@for_line_in_str
@split_str_into_cli_args
@parse_args(parser_base)
@log_args("handle_fifo_message", ["event"])
def handle_fifo_message(args: argparse.Namespace, args_raw: list) -> None:
    _add_event_to_queue(args_raw, args.time)


@parse_args(parser_base)
@log_args("handle_event", ["event"])
def handle_event(args: argparse.Namespace, args_raw: list) -> None:
    """Call the specified event"""
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
    event_data = {
        'pid': args.pid,
        'command': args.command,
        'path': args.path,
        'shell': args.path
    }
    process.event = insert_event(event_data, timestamp=args.time)


@parse_args(parser_precmd)
@log_args("precmd", ["pid", "exit_code", "time"])
@store_pid_if_not_existing
def precmd(args: argparse.Namespace, args_raw: list) -> None:
    process = terminal_processes_data[args.pid]

    if process.event is None:
        return

    event_data = process.event.data

    # Calculate time delta between preexec and precmd
    timestamp = process.event.timestamp
    cur_time = args.time
    time_delta = cur_time - timestamp

    event_data['exit_code'] = args.exit_code

    insert_event(event_data,
                 id=process.event.id,
                 timestamp=timestamp,
                 duration=time_delta)

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
