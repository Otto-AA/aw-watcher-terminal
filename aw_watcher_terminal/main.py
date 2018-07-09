#!/usr/bin/env python3

import os
from time import sleep
import argparse
import logging
import traceback
from aw_core.log import setup_logging
from aw_core.dirs import get_data_dir
from aw_client import ActivityWatchClient
from aw_watcher_terminal.message_handler import MessageHandler


client_id = 'aw-watcher-terminal'
logger = logging.getLogger(client_id)


def main() -> None:
    """
    Start aw-watcher-terminal
    See the docs for usage
    """

    args = parse_args()

    # Load configurations
    setup_logging(client_id,
                  testing=args.testing, verbose=args.verbose,
                  log_stderr=True, log_file=True)

    # Create MessageHandler to which the fifo messages will be passed
    with MessageHandler(testing=args.testing) as message_handler:

        # Setup and open named pipe
        fifo_path = "{}/aw-watcher-terminal-fifo".format(
            get_data_dir(client_id)
        )
        setup_named_pipe(fifo_path)
        pipe_fd = os.open(fifo_path, os.O_RDONLY | os.O_NONBLOCK)

        with os.fdopen(pipe_fd) as pipe:
            logger.info("Listening to pipe: {}".format(fifo_path))

            """
            Periodically read pipe for new messages
            and update the event queue
            """
            while True:
                # Read new messages from the named pipe
                try:
                    message = pipe.read()
                    if message:
                        message_handler.handle_fifo_message(message)
                except Exception as e:
                    logger.error(e)
                    traceback.print_exc()

                # Update event queue of the message handler
                try:
                    message_handler.update_event_queue()
                except Exception as e:
                    logger.error(e)
                    traceback.print_exc()

                sleep(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Terminal activity watcher.')
    parser.add_argument('--testing', dest='testing', action='store_true')
    parser.add_argument('--verbose', dest='verbose', action='store_true')
    return parser.parse_args()


def setup_named_pipe(pipe_path: str) -> None:
    """Delete and create named pipe at specified path"""
    if os.path.exists(pipe_path):
        os.remove(pipe_path)
    if not os.path.exists(pipe_path):
        os.mkfifo(pipe_path)


if __name__ == '__main__':
    main()
