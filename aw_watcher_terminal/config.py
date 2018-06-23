import argparse


def load_config():
    default_config = {
        "pipe_path": "/tmp/aw-watcher-terminal-pipe",
        "client_id": "aw-watcher-terminal-test-client",
        "bucket_name": "aw-watcher-terminal",
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