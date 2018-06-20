#!/usr/bin/env python3
import sys


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

event_data = {
    "command": command,
    "path": shell_path
}
now = datetime.now(timezone.utc)
event = Event(timestamp=now, data=event_data)
inserted_event = client.insert_event(bucket_id, event)

# The event returned from insert_event has been assigned an id by aw-server
assert inserted_event.id is not None