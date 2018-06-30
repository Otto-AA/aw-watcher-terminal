"""
    Handle fifo message:
        preopen:
            store pid

        preexec:
            send event
            save event to pid

        precmd:
            update event:
                set duration
                set exit code
            send event
            rmove old event from pid

        preclose:
            remove pid

"""

import argparse
import shlex
from time import sleep
from aw_core.models import Event
import config


# Parser general
# general --event preexec
parser_general = argparse.ArgumentParser(description='Parses the event')
parser_general.add_argument('--event', dest='event', required=True,
                            help='the trigger event (e.g. preexec)')

# Parser preopen
# preopen --pid 1234
parser_preopen = argparse.ArgumentParser(description='Parses preopen messages')
parser_preopen.add_argument('--pid', dest='pid', required=True,
                            help='the process id of the current terminal')

# Parser preexec
# preopen --pid 1234 --command ls --path /my/path --shell bash
parser_preexec = argparse.ArgumentParser(description='Parses preexec messages')
parser_preexec.add_argument('--pid', dest='pid', required=True,
                            help='the process id of the current terminal')
parser_preexec.add_argument('--command', dest='command',
                            help='the command entered by the user')
parser_preexec.add_argument('--path', dest='path',
                            help='the path of the shell')
parser_preexec.add_argument('--shell', dest='shell',
                            help='the name of the shell used')

# Parser precmd
# precmd --pid 1234 --exit-code 0
parser_precmd = argparse.ArgumentParser(description='Parses precmd messages')
parser_precmd.add_argument('--pid', dest='pid', required=True,
                           help='the process id of the current terminal')
parser_precmd.add_argument('--exit-code', dest='exit_code',
                           help='the exit code of the last command')

# Parser preclose
# preclose --pid 1234
parser_preclose = argparse.ArgumentParser(description=('Parses preclose '
                                          'messages'))
parser_preclose.add_argument('--pid', dest='pid', required=True,
                             help='the process id of the current terminal')


# Dict containing data related to process ids
# Keys are the process ids
terminal_processes_data = {}


class TerminalProcessData:
    def __init__(self, pid: str):
        self.pid = pid
        self.event = None


def store_pid_if_not_existing(func):
    """Add the pid to terminal_processes_data if not existing"""
    def decorator(args, unknown_args):
        pid = args.pid

        if pid not in terminal_processes_data:
            terminal_processes_data[pid] = TerminalProcessData(pid)

        func(args, unknown_args)
    return decorator


def log_args(func_name: str, keys: list):
    """Log the given args (first parameter) in debug mode"""
    def decorator(func):
        def decorated_function(args, unknown_args):
            log_msg = func_name
            for key in keys:
                if key in vars(args):
                    log_msg += "\n| {}={}".format(key, vars(args)[key])

            config.logger.debug(log_msg)
            func(args, unknown_args)
        return decorated_function
    return decorator


def parse_args(parser: argparse.ArgumentParser) -> (argparse.Namespace, list):
    """Parse a list of arguments with the specified parser"""
    def decorator(func):
        def decorated_function(args_raw):
            args, unknown_args = parser.parse_known_args(args_raw)

            return func(args, unknown_args)
        return decorated_function
    return decorator


def split_str_into_cli_args(func):
    """Split a fifo message into command line arguments"""
    def decorator(message: str):
        cli_args = shlex.split(message)
        return func(cli_args)
    return decorator


def for_line_in_str(func):
    """Call the decorated function once per line of the string"""
    def decorator(message):
        for line in message.split('\n'):
            if len(line):
                func(line)
    return decorator


@for_line_in_str
@split_str_into_cli_args
@parse_args(parser_general)
def handle_fifo_message(args, unknown_args):
    possible_events = {
        "preopen": preopen,
        "preexec": preexec,
        "precmd": precmd,
        "preclose": preclose
    }

    if args.event not in possible_events:
        config.logger.error("Unknown event: {}".format(args.event))
    else:
        # Call the event handler with the remaining args
        possible_events[args.event](unknown_args)


@parse_args(parser_preopen)
@log_args("preopen", ["pid"])
@store_pid_if_not_existing
def preopen(args, unknown_args):
    """Handle terminal creation"""
    pass


@parse_args(parser_preexec)
@log_args("preexec", ["pid", "command"])
@store_pid_if_not_existing
def preexec(args, unknown_args):
    process = terminal_processes_data[args.pid]

    # Send event
    process.event = insert_event(vars(args))


@parse_args(parser_precmd)
@log_args("precmd", ["pid", "exit_code"])
@store_pid_if_not_existing
def precmd(args, unknown_args):
    process = terminal_processes_data[args.pid]

    # TODO: Check what happens if preexec and precmd order is swapped
    # (e.g. because aw-watcher-bash-preexec is too slow)
    if process.event is None:
        return

    # TODO: Alter execution_time / duration of the event
    event_data = process.event.data
    event_data["exit_code"] = args.exit_code
    insert_event(event_data, id=process.event.id)


@parse_args(parser_preclose)
@log_args("preclose", ["pid"])
def preclose(args, unknown_args):
    terminal_processes_data.pop(args.pid)


def insert_event(event_data: dict, **kwargs) -> Event:
    """Send event to the aw-server"""
    event = Event(data=event_data, **kwargs)
    inserted_event = config.client.insert_event(config.bucket_id, event)

    # The event returned from insert_event has been assigned an id by aw-server
    assert inserted_event.id is not None
    config.logger.info("Successfully sent event")

    return inserted_event
