import argparse
import logging
from aw_core.log import setup_logging
from aw_core.dirs import get_data_dir


def load_config() -> None:
    args = parse_args()

    global data_dir
    global client
    global client_id
    global bucket_id
    global event_type
    global logger
    global verbose
    global testing

    client_id = "aw-watcher-terminal"
    data_dir = get_data_dir(client_id)
    client = None
    bucket_id = None
    event_type = "app.terminal.activity"
    logger = logging.getLogger(__name__)
    verbose = args.verbose
    testing = args.testing

    setup_logging(name=client_id, testing=testing,
                  verbose=verbose, log_stderr=True, log_file=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Process terminal activity.')
    parser.add_argument("--testing", dest="testing", action="store_true")
    parser.add_argument("--verbose", dest="verbose", action="store_true")
    return parser.parse_args()
