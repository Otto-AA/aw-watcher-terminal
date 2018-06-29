#!/usr/bin/env python3
import argparse
import logging
import traceback
import sys
import os
import shlex
from typing import Union, Callable, Any
import asyncio

from time import sleep
from datetime import datetime, timezone
from aw_core.models import Event
from aw_core.log import setup_logging
from aw_client import ActivityWatchClient
from config import load_config
import shared_vars
import message_handler


def main():
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
    global config

    shared_vars.init()
    shared_vars.config = load_config()
    shared_vars.logger = logging.getLogger(__name__)

    setup_logging(name=shared_vars.config['bucket_name'], testing=shared_vars.config['testing'],
                  verbose=shared_vars.config['verbose'], log_stderr=True, log_file=True)

    shared_vars.logger.info("Starting aw-watcher-terminal")

    init_client()
    # futures = init_fifo_listeners()
    fifo_path = "{}/aw-watcher-terminal-fifo".format(shared_vars.config["data_dir"])
    setup_named_pipe(fifo_path)
    futures = [on_named_pipe_message(fifo_path, message_handler.handle_fifo_message)]

    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait(futures))


def init_client():
    """Initialize the AW client and bucket"""

    # Create client in testing mode
    shared_vars.client = ActivityWatchClient(shared_vars.config['client_id'],
                                             testing=shared_vars.config['testing'])
    shared_vars.logger.info("Initialized AW Client")

    # Create Bucket if not already existing
    shared_vars.bucket_id = "{}_{}".format(shared_vars.config['bucket_name'], shared_vars.client.hostname)
    shared_vars.client.create_bucket(shared_vars.bucket_id, event_type=shared_vars.config['event_type'])
    shared_vars.logger.info("Created bucket: {}".format(shared_vars.bucket_id))


def init_fifo_listeners():
    fifo_listeners = {
        "preopen":  message_handler.preopen,
        "preexec":  message_handler.preexec,
        "precmd":   message_handler.precmd,
        "preclose": message_handler.preclose
    }
    futures = []
    for listener_name, listener in fifo_listeners.items():
        fifo_path = "{}/fifo-{}".format(shared_vars.config["data_dir"],
                                        listener_name)
        setup_named_pipe(fifo_path)
        futures.append(on_named_pipe_message(fifo_path, listener))

    return futures


def setup_named_pipe(pipe_path: str):
    """Delete and create named pipe at specified path"""
    if os.path.exists(pipe_path):
        os.remove(pipe_path)
    if not os.path.exists(pipe_path):
        shared_vars.logger.debug("Creating pipe {}".format(pipe_path))
        os.mkfifo(pipe_path)


async def on_named_pipe_message(pipe_path: str, callback: Callable[[str], Any]):
    """Call callback everytime a new message is passed to the named pipe"""
    pipe_fd = os.open(pipe_path, os.O_RDONLY | os.O_NONBLOCK)
    with os.fdopen(pipe_fd) as pipe:
        shared_vars.logger.info("Listening to pipe: {}".format(pipe_path))
        while True:
            message = pipe.read()
            if message:
                try:
                    callback(message)
                except Exception as e:
                    shared_vars.logger.error(e)
                    traceback.print_exc()

            await asyncio.sleep(1)


if __name__ == '__main__':
    main()
