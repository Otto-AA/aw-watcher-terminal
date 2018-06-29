"""
    Handle fifo message:
        preopen:
            store pid

        preexec:
            set pid status processing
            parse args
            send event
            save eventid to pid
            set pid status executing

        precmd:
            if pid status == processing:
                sleep (x) and repeat
            if pid_status == executing:
                pid_status = waiting_for_prompt
                remove eventid from pid
                get event by pid and eventid
                set duration
                set exit code
                send event

        preclose:
            remove pid

"""

import argparse
import shlex
from datetime import datetime, timezone
from time import sleep
from aw_core.models import Event
import shared_vars


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

        """
            Status can be one of following:
            - waiting_for_prompt
            - processing (meaning, that this program is processing the pid)
            - executing
        """
        self.status = "waiting_for_prompt"
        self.event = None


def parse_args(parser: argparse.ArgumentParser) -> (argparse.Namespace, list):
    """Parse a list of arguments with the specified parser"""
    def decorator(func):
        def decorated_function(args_raw):
            args, unknown_args = parser.parse_known_args(args_raw)

            return func(args, unknown_args)
        return decorated_function
    return decorator


def split_fifo_message_into_cli_args(func):
    """Split a fifo message into command line arguments"""
    def decorated_function(message: str):
        for line in message.split('\n'):
            if not len(line):
                continue
            cli_args = shlex.split(line)
            return func(cli_args)
    return decorated_function


@split_fifo_message_into_cli_args
@parse_args(parser_general)
def handle_fifo_message(args, unknown_args):
    shared_vars.logger.debug("Handling fifo message: {}".format(args))

    possible_events = {
        "preopen": preopen,
        "preexec": preexec,
        "precmd": precmd,
        "preclose": preclose
    }

    if args.event not in possible_events:
        shared_vars.logger.error("Unknown event: {}".format(args.event))
    else:
        # Call the event handler with the remaining args
        possible_events[args.event](unknown_args)


@parse_args(parser_preopen)
def preopen(args, unknown_args):
    """Handle terminal creation"""
    shared_vars.logger.debug("preopen | pid={}".format(args.pid))
    terminal_processes_data[args.pid] = TerminalProcessData(args.pid)


@parse_args(parser_preexec)
def preexec(args, unknown_args):
    shared_vars.logger.debug("preexec | command={}".format(args.command))
    process = terminal_processes_data[args.pid]
    process.status = "processing"

    # Send event
    process.event = insert_event(vars(args))

    process.status = "executing"


@parse_args(parser_precmd)
def precmd(args, unknown_args):
    shared_vars.logger.debug("precmd | exit_code={}".format(args.exit_code))
    process = terminal_processes_data[args.pid]

    if process.status != "executing":
        shared_vars.logger.error("Not implemented yet")

    # TODO: Alter execution_time / duration of the event
    print(process.event.data)
    print(type(process.event.data))
    event_data = process.event.data
    print(type(event_data))
    print(event_data)
    event_data["exit_code"] = args.exit_code
    insert_event(event_data)


@parse_args(parser_preclose)
def preclose(args, unknown_args):
    shared_vars.logger.debug("preclose | pid={}".format(args.pid))
    terminal_processes_data.pop(args.pid)


def insert_event(event_data: dict) -> Event:
    """Send event to the aw-server"""
    shared_vars.logger.debug("Sending event")
    shared_vars.logger.debug(event_data)
    now = datetime.now(timezone.utc)
    event = Event(timestamp=now, data=event_data)
    inserted_event = shared_vars.client.insert_event(shared_vars.bucket_id,
                                                     event)

    # The event returned from insert_event has been assigned an id by aw-server
    assert inserted_event.id is not None
    shared_vars.logger.info("Successfully sent event")

    return inserted_event
