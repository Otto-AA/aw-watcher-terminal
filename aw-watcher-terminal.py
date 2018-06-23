#!/usr/bin/env python3
import os
import argparse
import shlex

from time import sleep
from datetime import datetime, timezone
from aw_core.models import Event
from aw_client import ActivityWatchClient

config = {
    'pipe_path': '/tmp/aw-watcher-terminal-pipe',
    'client_id': 'aw-watcher-terminal-test-client',
    'bucket_name': 'aw-watcher-terminal',
    'event_type': 'app.terminal.activity',
    'testing': True,
    'disabled': False,
    'log_file': '/dev/null', # TODO: Change log file
}
client = None
bucket_id = None
parser = None

def main():
    load_config()
    init_client()
    init_message_parser()
    setup_named_pipe(config['pipe_path'])
    on_named_pipe_message(config['pipe_path'], handle_pipe_message)


def load_config():
    """[TODO] Load the configurations and parse the CLI arguments"""
    print('Loaded configurations')
    print(config)


def init_client():
    """Initialize the AW client and bucket"""
    global client
    global bucket_id

    # Create client in testing mode
    client = ActivityWatchClient(config['client_id'], testing=config['testing'])

    # Create Bucket if not already existing
    bucket_id = "{}_{}".format(config['bucket_name'], client.hostname)
    client.create_bucket(bucket_id, event_type=config['event_type'])


def init_message_parser():
    """Initializes the argparser for arguments from pipe messages"""
    global parser

    parser = argparse.ArgumentParser(description='Process bash activity.')
    parser.add_argument('--command', dest='command', help='the command entered by the user')
    parser.add_argument('--path', dest='path', help='the path of the shell')
    print("Initialized argparser")


def handle_pipe_message(message):
    if config['disabled']:
        return
    
    print('Received message: {}'.format(message))
    try:
        args = parse_pipe_message(message)
    except:
        return print("Error while parsing args")
    print(args)
    send_event({
        'command': args.command,
        'path': args.path
    })


def parse_pipe_message(message):
    return parser.parse_args(shlex.split(message))


def send_event(event_data):
    print("Sending event")
    print(event_data)
    now = datetime.now(timezone.utc)
    event = Event(timestamp=now, data=event_data)
    inserted_event = client.insert_event(bucket_id, event)

    # The event returned from insert_event has been assigned an id by aw-server
    assert inserted_event.id is not None
    print("Successfully sent event\n")


def setup_named_pipe(pipe_path):
    if os.path.exists(pipe_path):
        os.remove(pipe_path)
    if not os.path.exists(pipe_path):
        print("Creating pipe {}".format(pipe_path))
        os.mkfifo(pipe_path)

def on_named_pipe_message(pipe_path, callback):
    pipe_fd = os.open(pipe_path, os.O_RDONLY | os.O_NONBLOCK)
    with os.fdopen(pipe_fd) as pipe:
        print("Listening to pipe: {}".format(pipe_path))
        while True:
            message = pipe.read()
            if message:
                callback(message)
            sleep(1)


if __name__ == '__main__':
    main()