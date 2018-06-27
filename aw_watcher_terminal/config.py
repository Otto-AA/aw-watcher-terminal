import argparse
from aw_core.dirs import get_data_dir

watcher_name = "aw-watcher-terminal"


def load_config():
    default_config = {
        "data_dir": get_data_dir((watcher_name)),
        "client_id": "{}-test-client".format(watcher_name),
        "bucket_name": watcher_name,
        "event_type": "app.terminal.activity",
        "disabled": False,
        "verbose": False,
        "testing": False
    }

    args = vars(parse_args())
    config = {**default_config, **args}

    return config


def parse_args():
    parser = argparse.ArgumentParser(description='Process terminal activity.')
    parser.add_argument("--testing", dest="testing", action="store_true")
    parser.add_argument("--verbose", dest="verbose", action="store_true")
    return parser.parse_args()
