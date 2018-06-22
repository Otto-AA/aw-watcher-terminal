#!/usr/bin/env python3
import sys
import os
import argparse
import shlex


from time import sleep
from datetime import datetime, timedelta, timezone

from aw_core.models import Event
from aw_client import ActivityWatchClient

# Create client in testing mode
client = ActivityWatchClient("test-client", testing=True)


bucket_id = "{}_{}".format("aw-watcher-bash", client.hostname)
event_type = "dummydata"

# First we need a bucket to send events/heartbeats to.
# If the bucket already exists aw-server will simply return 304 NOT MODIFIED,
# so run this every time the clients starts up to verify that the bucket exists.
# If the client was unable to connect to aw-server or something failed
# during the creation of the bucket, an exception will be raised.
client.create_bucket(bucket_id, event_type=event_type)

# Synchronous example, insert an event
command = sys.argv[1].split()[0]
shell_path = sys.argv[2]

def send_event(event_data):
    now = datetime.now(timezone.utc)
    event = Event(timestamp=now, data=event_data)
    inserted_event = client.insert_event(bucket_id, event)

    # The event returned from insert_event has been assigned an id by aw-server
    assert inserted_event.id is not None
    
# Define parser for bash activity events
parser = argparse.ArgumentParser(description='Process bash activity.')
parser.add_argument('--command', dest='command', help='the command entered by the user')
parser.add_argument('--path', dest='path', help='the path of the shell')

def on_pipe_message(message):
    print('Received message')
    print(message)
    args = parse_pipe_message(message)
    send_event({
        'command': args.command,
        'path': args.path
    })
    
def parse_pipe_message(message):
    return args = parser.parse_args(shlex.split(message))    


def listen_to_named_pipe(pipe_path, callback):
    if not os.path.exists(pipe_path):
        os.mkfifo(pipe_path)

    pipe_fd = os.open(pipe_path, os.O_RDONLY | os.O_NONBLOCK)
    with os.fdopen(pipe_fd) as pipe:
        while True:
            message = pipe.read()
            if message:
                callback(message)
            sleep(0.5)
            
listen_to_named_pipe("~/aw-watcher-bash-pipe", on_pipe_message)
