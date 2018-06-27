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
from time import sleep
from aw_core.models import Event


# Parser preopen
parser_preopen = argparse.ArgumentParser(description='Parses preopen messages')
parser_preopen.add_argument('--pid', dest='pid', required=True,
                            help='the process id of the current terminal')

# Parser preexec
parser_preexec = argparse.ArgumentParser(description='Parses preexec messages')
parser_preexec.add_argument('--pid', dest='pid', required=True,
                            help='the process id of the current terminal')
parser_preexec.add_argument('--command', dest='command',
                            help='the command entered by the user')
parser_preexec.add_argument('--path', dest='path',
                            help='the path of the shell')
parser_preexec.add_argument('--shell', dest='shell',
                            help='the name of the shell used')
parser_preexec.add_argument('--shell-version', dest='shell_version',
                            help='the version of the shell used')

# Parser precmd
parser_precmd = argparse.ArgumentParser(description='Parses precmd messages')
parser_precmd.add_argument('--pid', dest='pid', required=True,
                           help='the process id of the current terminal')
parser_precmd.add_argument('--exit-code', dest='exit_code',
                           help='the exit code of the last command')

# Parser preclose
parser_preclose = argparse.ArgumentParser(description=('Parses preclose '
                                          'messages'))
parser_preclose.add_argument('--pid', dest='pid', required=True,
                             help='the process id of the current terminal')


# Dict containing statuses of process ids
# Keys are the process ids
terminal_processes = {}


class TerminalProcess:
    def __init__(self, pid: str):
        self.pid = pid

        """
            Status can be one of following:
            - waiting_for_prompt
            - processing (meaning, that this program is processing the pid)
            - executing
        """
        self.status = "waiting_for_prompt"
        self.event_id = None


def parse_fifo_message(parser: argparse.ArgumentParser) -> (argparse.Namespace, list):
    """Parse a fifo message with the specified parser"""

    def decorator(func):
        def decorated_function(message: str):
            for line in message.split('\n'):
                if not len(line):
                    continue

                args, unknown_args = parser.parse_known_args(shlex.split(line))

                return func(args, unknown_args)
        return decorated_function
    return decorator


@parse_fifo_message(parser_preopen)
def preopen(args, unknown_args):
    """Handle terminal creation"""
    terminal_proccess = TerminalProcess(args.pid)
    terminal_processes[args.pid] = TerminalProcess(args.pid)


@parse_fifo_message(parser_preexec)
def preexec(args, unknown_args):
    process = terminal_processes[args.pid]
    process.status = "processing"

    # Send event
    inserted_event = send_event(args)
    print(inserted_event)

    event_id = inserted_event.id
    process.event_id = event_id
    process.status = "executing"


@parse_fifo_message(parser_precmd)
def precmd(args, unknown_args):
    process = terminal_processes[args.pid]

    if process.status != "executing":
        print("Not implemented yet")

    event = get_event(process.event_id)
    event.duration = [...]
    event.exit_code = args.exit_code
    send_event(event)


@parse_fifo_message(parser_preclose)
def preclose(args, unknown_args):
    terminal_processes.pop(args.pid)


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


def send_event(event):
    return Event("1")


def get_event(event_id):
    return Event()
