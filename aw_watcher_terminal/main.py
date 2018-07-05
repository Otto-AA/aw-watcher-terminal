#!/usr/bin/env python3
import traceback
import os
from typing import Union, Callable, Any
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_EXCEPTION
from time import sleep
from aw_client import ActivityWatchClient
from aw_watcher_terminal import config
from aw_watcher_terminal import message_handler


def main() -> None:
    """Start aw-watcher-terminal"""
    """
    Usage:
    To pass events to the terminal, write the message to the named pipe
    (e.g. echo "$my_message" > "$pipe_path").
    The message arguments which are needed for the individual events are
    specified in the parsers (base parser + event specific parser) in
    message_handler.py.
    Messages need to be properly escaped. You gonna need to add a backslash
    in front of every
    double quote (") and every backslash preceding a double quote (\")
    For instance, the command 'echo "Hello \"World\""' should be escaped
    like '--command echo \"Hello \\\"World\\\"\"'
    """
    # Load configurations
    config.load_config()
    config.logger.info("Starting aw-watcher-terminal")

    init_client()
    fifo_path = "{}/aw-watcher-terminal-fifo".format(config.data_dir)
    setup_named_pipe(fifo_path)

    """
    Periodically read pipe for new messages
    and update the event queue
    """
    pipe_fd = os.open(fifo_path, os.O_RDONLY | os.O_NONBLOCK)
    with os.fdopen(pipe_fd) as pipe:
        config.logger.info("Listening to pipe: {}".format(fifo_path))
        while True:
            # Read new messages from the named pipe
            try:
                message = pipe.read()
                if message:
                    message_handler.handle_fifo_message(message)
            except Exception as e:
                config.logger.error(e)
                traceback.print_exc()

            # Update event queue of the message handler
            try:
                message_handler.update_event_queue()
            except Exception as e:
                config.logger.error(e)
                traceback.print_exc()

            sleep(1)


def init_client() -> None:
    """Initialize the AW client and bucket"""

    # Create client
    config.client = ActivityWatchClient(config.client_id,
                                        testing=config.testing)
    config.client.connect()

    config.logger.info("Initialized AW Client")

    # Create Buckets if not already existing
    config.bucket_ids['command-watcher'] = "{}-{}_{}".format(
        config.client_id,
        'commands',
        config.client.hostname
    )
    config.bucket_ids['activity-watcher'] = "{}-{}_{}".format(
        config.client_id,
        'activity',
        config.client.hostname
    )

    for key, bucket_id in config.bucket_ids.items():
        event_type = config.event_types[key]
        config.client.create_bucket(bucket_id,
                                    event_type=event_type,
                                    queued=True)
        config.logger.info("Created bucket: {}".format(bucket_id))


def setup_named_pipe(pipe_path: str) -> None:
    """Delete and create named pipe at specified path"""
    if os.path.exists(pipe_path):
        os.remove(pipe_path)
    if not os.path.exists(pipe_path):
        config.logger.debug("Creating pipe {}".format(pipe_path))
        os.mkfifo(pipe_path)


if __name__ == '__main__':
    main()
