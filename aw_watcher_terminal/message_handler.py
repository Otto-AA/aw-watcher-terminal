import argparse
import wrapt
import shlex
from datetime import datetime, timezone
import iso8601
import uuid
from time import sleep
import logging
from typing import Any
from aw_client import ActivityWatchClient
from aw_core.models import Event

client_id = 'aw-watcher-terminal'
logger = logging.getLogger(client_id)


def parse_iso8601_str(timestamp_str: str) -> datetime:
    """Convert a iso8601 string into a datetime object"""
    timestamp = iso8601.parse_date(timestamp_str)
    if not timestamp.tzinfo:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return timestamp

# Event parsers
#
# base --event preexec --pid 1234 --time 2018-07-01T09:13:15,215744806+02:00
#      --path /home/me/ [--send-heartbeat]
parser_base = argparse.ArgumentParser(description='Parses the event',
                                      add_help=False)
parser_base.add_argument('--event', dest='event', required=True,
                         help='the trigger event (e.g. preexec)')
parser_base.add_argument('--pid', dest='pid', required=True,
                         help='the process id of the current terminal')
parser_base.add_argument('--time', dest='timestamp', required=True,
                         type=parse_iso8601_str,
                         help='the time the event got triggered in iso-8601')
parser_base.add_argument('--path', dest='path', required=True,
                         help='the path of the shell')
parser_base.add_argument('--send-heartbeat', dest='send_heartbeat',
                         action='store_true',
                         help=('pass this flag if you want to track '
                               'the time you use terminals'))
parser_base.add_argument('--shell', dest='shell', required=True,
                         help='the name of the shell used')

# preopen --pid 1234
parser_preopen = argparse.ArgumentParser(parents=[parser_base])
parser_preopen.description = 'Parses preopen events'

# preexec --pid 1234 --command ls --path /my/path --shell bash
parser_preexec = argparse.ArgumentParser(parents=[parser_base])
parser_preexec.description = 'Parses preexec events'
parser_preexec.add_argument('--command', dest='command', required=True,
                            help='the command entered by the user')

# precmd --pid 1234 --exit-code 0
parser_precmd = argparse.ArgumentParser(parents=[parser_base])
parser_precmd.description = 'Parses precmd events'
parser_precmd.add_argument('--exit-code', dest='exit_code', required=True,
                           help='the exit code of the last command')

# preclose --pid 1234
parser_preclose = argparse.ArgumentParser(parents=[parser_base])
parser_preclose.description = 'Parses preclose events'

# heartbeat
parser_heartbeat = argparse.ArgumentParser(parents=[parser_base])
parser_heartbeat.description = 'Parses activity heartbeats'


class TerminalSessionData:
    """Store data belonging to an opened terminal"""
    def __init__(self, pid: str):
        self.pid = pid
        self.unique_id = str(uuid.uuid1())
        self.event = None


class MessageHandler:
    def __init__(self, testing=False, send_commands=True,
                 send_heartbeats=True):
        # Create client
        self._client = ActivityWatchClient(client_id, testing=testing)
        self._client.connect()
        self._init_buckets()

        # Settings
        self.pulsetime = 10
        self.send_commands = send_commands
        self.send_heartbeats = send_heartbeats

        # Initialize the EventQueue
        self._event_queue = EventQueue(callback=self._handle_event,
                                       time_buffer=(self.pulsetime / 2))

        self._event_handlers = {
            'preopen': self._preopen,
            'preexec': self._preexec,
            'precmd': self._precmd,
            'preclose': self._preclose
        }

        self._terminal_sessions = {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._client.disconnect()

    def _init_buckets(self):
        """Set self._buckets and create these buckets if not existing"""
        self._buckets = {
            'commands': {
                'id': "{}-commands_{}".format(client_id,
                                              self._client.hostname),
                'event_type': 'app.terminal.command'
            },
            'activity': {
                'id': "{}-activity_{}".format(client_id,
                                              self._client.hostname),
                'event_type': 'app.terminal.activity'
            }
        }

        # Create buckets if not existing
        for key, bucket in self._buckets.items():
            logger.debug("Creating bucket: {}".format(bucket['id']))
            self._client.create_bucket(bucket['id'], bucket['event_type'],
                                       queued=True)

    def update_event_queue(self):
        self._event_queue.update()

    def handle_fifo_message(self, message):
        for line in message.split('\n'):
            if not len(line):
                continue

            cli_args = shlex.split(line)
            args, unknown_args = parser_base.parse_known_args(cli_args)

            # Make sure that events are called in the right order
            # (based on args.timestamp) by passing it to the event queue
            # The event queue will trigger the callback when the time_buffer
            # is exceeded
            logger.debug("adding event to event_queue: {}".format(cli_args))
            self._event_queue.add_event(cli_args, args.timestamp)

    def _handle_event(self, cli_args):
        logger.debug("handling event: {}".format(cli_args))
        args, unknown_args = parser_base.parse_known_args(cli_args)

        # Store terminal session if not already existing
        pid = args.pid
        if pid not in self._terminal_sessions:
            self._terminal_sessions[pid] = TerminalSessionData(pid)

        if self.send_commands:
            if args.event not in self._event_handlers:
                logger.error("Unknown event: {}".format(args.event))
            else:
                self._event_handlers[args.event](cli_args)

        if self.send_heartbeats:
            self._heartbeat(cli_args)

    def _preopen(self, cli_args: list) -> None:
        """Handle terminal creation"""
        pass

    def _preexec(self, cli_args: list) -> None:
        """Send event containing command execution data"""
        args, unknown_args = parser_preexec.parse_known_args(cli_args)

        process = self._terminal_sessions[args.pid]
        event_data = {
            'command': args.command,
            'path': args.path,
            'shell': args.shell,
            'exit_code': 'unknown',
            'session_id': process.unique_id
        }
        process.event = self._insert_event(data=event_data,
                                           timestamp=args.timestamp)

    def _precmd(self, cli_args: list) -> None:
        """Update the stored event with duration and exit_code"""
        args, unknown_args = parser_precmd.parse_known_args(cli_args)
        process = self._terminal_sessions[args.pid]

        if process.event is None:
            return

        event_data = process.event.data

        # Calculate time delta between preexec and precmd
        timestamp = process.event.timestamp
        cur_time = args.timestamp
        time_delta = cur_time - timestamp

        event_data['exit_code'] = args.exit_code

        self._insert_event(data=event_data,
                           id=process.event.id,
                           timestamp=timestamp,
                           duration=time_delta)
        process.event = None

    def _preclose(self, args: argparse.Namespace, args_raw: list) -> None:
        """Remove pid and related data from terminal_processes_data"""
        args, unknown_args = parser_preclose.parse_known_args(cli_args)
        self._terminal_sessions.pop(args.pid)

    def _heartbeat(self, cli_args: list) -> None:
        """Send heartbeat to activity bucket"""
        args, unknown_args = parser_heartbeat.parse_known_args(cli_args)
        process = self._terminal_sessions[args.pid]

        event_data = {
            'session_id': process.unique_id,
            'shell': args.shell,
            'path': args.path
        }
        event = Event(
            data=event_data,
            timestamp=args.timestamp
        )

        inserted_heartbeat = self._client.heartbeat(
            self._buckets['activity']['id'],
            event,
            pulsetime=self.pulsetime,
            queued=True
        )

        if inserted_heartbeat and inserted_heartbeat.id:
            logger.debug('Successfully sent heartbeat')

    def _insert_event(self, *args, **kwargs) -> Event:
        """Send event to the aw-server"""
        event = Event(*args, **kwargs)
        inserted_event = self._client.insert_event(
            self._buckets['commands']['id'], event)

        # aw-server assigned the event an id
        assert inserted_event.id is not None
        logger.debug("Successfully sent event")

        return inserted_event


class EventQueue:
    """
    Store events and trigger the callback when the specified timestamp
    is {time_buffer} seconds ago.
    """

    def __init__(self, *, callback, time_buffer=5):
        # events indexed by the timestamp
        self._events = {}
        # timestamp keys for the events sorted from oldest to newest
        self._sorted_timestamps = []

        # time_buffer specifies how much seconds have to pass before
        # the callback gets triggered (starting time is the timestamp)
        self.time_buffer = time_buffer

        self.callback = callback

    def add_event(self, event: Any, timestamp_iso8601: datetime) -> None:
        assert timestamp_iso8601 not in self._events
        self._events[timestamp_iso8601] = event

        self._sorted_timestamps.append(timestamp_iso8601)
        self._sorted_timestamps.sort(reverse=True)

    def update(self):
        """
        Handle events in the event_queue if they happened
        {time_buffer} or more seconds ago
        """
        if not len(self._sorted_timestamps):
            return

        # Only handle events which happened some time ago
        # to prevent processing them in a wrong order
        # if the shell-watcher sent them in a wrong order (with delay)

        while len(self._events):
            oldest_event_time = self._sorted_timestamps[0]

            if not self.event_should_be_processed(timestamp=oldest_event_time):
                break

            timestamp_key = self._sorted_timestamps.pop()
            event = self._events.pop(timestamp_key)
            self.callback(event)

    def event_should_be_processed(self, *, timestamp):
        # Return True if {time_buffer} seconds passed
        # since the timestamp

        cur_time = datetime.now(timezone.utc)
        oldest_event_time = self._sorted_timestamps[0]
        time_diff = cur_time - timestamp

        return time_diff.seconds > self.time_buffer
