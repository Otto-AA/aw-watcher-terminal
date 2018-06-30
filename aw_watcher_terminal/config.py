import argparse
import logging
from aw_core.log import setup_logging
from aw_core.dirs import get_data_dir


def load_config():
    args = parse_args()

    global watcher_name
    watcher_name = "aw-watcher-terminal"
    global data_dir
    data_dir = get_data_dir(watcher_name)
    global client
    client = None
    global client_id
    client_id = "{}-test-client".format(watcher_name)
    global bucket_id
    bucket_id = None
    global event_type
    event_type = "app.terminal.activity"
    global logger
    logger = logging.getLogger(__name__)
    global verbose
    verbose = args.verbose
    global testing
    testing = args.testing

    setup_logging(name=watcher_name, testing=testing,
                  verbose=verbose, log_stderr=True, log_file=True)


def parse_args():
    parser = argparse.ArgumentParser(description='Process terminal activity.')
    parser.add_argument("--testing", dest="testing", action="store_true")
    parser.add_argument("--verbose", dest="verbose", action="store_true")
    return parser.parse_args()
