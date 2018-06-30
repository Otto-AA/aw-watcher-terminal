#!/usr/bin/env python3
import traceback
import os
from typing import Union, Callable, Any

from time import sleep
from aw_client import ActivityWatchClient
import config
import message_handler


def main() -> None:
    """Start aw-watcher-terminal"""
    """
    Usage:
    To pass events to the terminal, write the message to the named pipe
    (e.g. echo "$my_message" > "$pipe_path").
    The message arguments which are needed are specified in the init
    message_parser function.
    Messages need to be properly escaped. You gonna need to add a backslash
    in front of every
    double quote (") and every backslash preceeding a double quote (\")
    For instance, the command 'echo "Hello \"World\""' should be escaped
    like '--command echo \"Hello \\\"World\\\"\"'
    """
    # Load configurations
    config.load_config()
    config.logger.info("Starting aw-watcher-terminal")

    init_client()
    fifo_path = "{}/aw-watcher-terminal-fifo".format(config.data_dir)
    setup_named_pipe(fifo_path)
    on_named_pipe_message(fifo_path, message_handler.handle_fifo_message)


def init_client() -> None:
    """Initialize the AW client and bucket"""

    # Create client in testing mode
    config.client = ActivityWatchClient(config.client_id,
                                        testing=config.testing)
    config.logger.info("Initialized AW Client")

    # Create Bucket if not already existing
    config.bucket_id = "{}_{}".format(config.watcher_name,
                                      config.client.hostname)
    config.client.create_bucket(config.bucket_id, event_type=config.event_type)
    config.logger.info("Created bucket: {}".format(config.bucket_id))


def setup_named_pipe(pipe_path: str) -> None:
    """Delete and create named pipe at specified path"""
    if os.path.exists(pipe_path):
        os.remove(pipe_path)
    if not os.path.exists(pipe_path):
        config.logger.debug("Creating pipe {}".format(pipe_path))
        os.mkfifo(pipe_path)


def on_named_pipe_message(pipe_path: str,
                          callback: Callable[[str], Any]) -> None:
    """Call callback everytime a new message is passed to the named pipe"""
    pipe_fd = os.open(pipe_path, os.O_RDONLY | os.O_NONBLOCK)
    with os.fdopen(pipe_fd) as pipe:
        config.logger.info("Listening to pipe: {}".format(pipe_path))
        while True:
            message = pipe.read()
            if message:
                try:
                    callback(message)
                except Exception as e:
                    config.logger.error(e)
                    traceback.print_exc()

            sleep(1)


if __name__ == '__main__':
    main()
