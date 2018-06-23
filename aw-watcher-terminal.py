#!/usr/bin/env python3
import argparse
import logging
import traceback
import sys
import os
import shlex

from time import sleep
from datetime import datetime, timezone
from aw_core.models import Event
from aw_core.log import setup_logging
from aw_client import ActivityWatchClient

config = {
    'pipe_path': '/tmp/aw-watcher-terminal-pipe',
    'client_id': 'aw-watcher-terminal-test-client',
    'bucket_name': 'aw-watcher-terminal',
    'event_type': 'app.terminal.activity',
    'testing': True,
    'disabled': False,
    'log_file': '/dev/null',  # TODO: Change log file
    'verbose': True
}
client = None
bucket_id = None
parser = None
logger = logging.getLogger(__name__)

def main():
    load_config()

    setup_logging(name="aw-watcher-terminal", testing=config['testing'],
                verbose=config['verbose'], log_stderr=True, log_file=True)
    
    logger.info("Starting aw-watcher-terminal")

    init_client()
    init_message_parser()
    setup_named_pipe(config['pipe_path'])
    on_named_pipe_message(config['pipe_path'], handle_pipe_message)

    logger.info("Listening for pipe messages...")


def load_config():
    """[TODO] Load the configurations and parse the CLI arguments"""
    pass


def init_client():
    """Initialize the AW client and bucket"""
    global client
    global bucket_id

    # Create client in testing mode
    client = ActivityWatchClient(config['client_id'], testing=config['testing'])
    logger.info("Initialized AW Client")

    # Create Bucket if not already existing
    bucket_id = "{}_{}".format(config['bucket_name'], client.hostname)
    client.create_bucket(bucket_id, event_type=config['event_type'])
    logger.info("Created bucket: {}".format(bucket_id))


def init_message_parser():
    """Initializes the argparser for arguments from pipe messages"""
    global parser

    parser = argparse.ArgumentParser(description='Process bash activity.')
    parser.add_argument('--command', dest='command', help='the command entered by the user')
    parser.add_argument('--path', dest='path', help='the path of the shell')
    parser.add_argument('--shell', dest='shell', help='the name of the shell used')
    parser.add_argument('--shell-version', dest='shell_version', help='the version of the shell used')


def handle_pipe_message(message):
    try:
        if config['disabled']:
            logger.debug("Skipping because watcher is disabled")
            return
        
        for line in message.split('\n'):
            if not len(line):
                continue
            
            logger.debug('Received message: {}'.format(line))

            # Parse args
            args = parse_pipe_message(line)
            if not type(args) is argparse.Namespace:
                logger.debug("Skipping because no arguments could be passed")
                return
            args_dict = vars(args)

            send_event(args_dict)
    except Exception as e:
        logger.error("Unexpected Error: {}".format(e))
        traceback.print_exc()


def parse_pipe_message(message):
    try:
        return parser.parse_args(shlex.split(message))
    except argparse.ArgumentError as e:
        logger.error("Error while parsing args")
        logger.error("Parse error: {}".format(e))
        return None


def send_event(event_data):
    logger.debug("Sending event")
    logger.debug(event_data)
    now = datetime.now(timezone.utc)
    event = Event(timestamp=now, data=event_data)
    inserted_event = client.insert_event(bucket_id, event)

    # The event returned from insert_event has been assigned an id by aw-server
    assert inserted_event.id is not None
    logger.info("Successfully sent event")


def setup_named_pipe(pipe_path):
    if os.path.exists(pipe_path):
        os.remove(pipe_path)
    if not os.path.exists(pipe_path):
        logger.debug("Creating pipe {}".format(pipe_path))
        os.mkfifo(pipe_path)

def on_named_pipe_message(pipe_path, callback):
    pipe_fd = os.open(pipe_path, os.O_RDONLY | os.O_NONBLOCK)
    with os.fdopen(pipe_fd) as pipe:
        logger.info("Listening to pipe: {}".format(pipe_path))
        while True:
            message = pipe.read()
            if message:
                callback(message)
            sleep(1)


if __name__ == '__main__':
    main()