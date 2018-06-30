import argparse
import logging
from aw_core.log import setup_logging
from aw_core.dirs import get_data_dir


def load_config():
    args = parse_args()

    global watcher_name
    global data_dir
    global client
    global client_id
    global bucket_id
    global event_type
    global logger
    global verbose
    global testing

    watcher_name = "aw-watcher-terminal"
    data_dir = get_data_dir(watcher_name)
    client = None
    client_id = "{}-test-client".format(watcher_name)
    bucket_id = None
    event_type = "app.terminal.activity"
    logger = logging.getLogger(__name__)
    verbose = args.verbose
    testing = args.testing

    setup_logging(name=watcher_name, testing=testing,
                  verbose=verbose, log_stderr=True, log_file=True)


def parse_args():
    parser = argparse.ArgumentParser(description='Process terminal activity.')
    parser.add_argument("--testing", dest="testing", action="store_true")
    parser.add_argument("--verbose", dest="verbose", action="store_true")
    return parser.parse_args()
