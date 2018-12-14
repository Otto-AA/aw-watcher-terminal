[![No Maintenance Intended](http://unmaintained.tech/badge.svg)](http://unmaintained.tech/)
# aw-watcher-terminal [Unmaintained]

Extension to [ActivityWatch](https://github.com/activitywatch/activitywatch) which allows you to track the commands you've written and time spent in terminals.

[![Build Status](https://travis-ci.com/Otto-AA/aw-watcher-terminal.svg?branch=master)](https://travis-ci.com/Otto-AA/aw-watcher-terminal)

---------------

## Features

### Tracking commands and metadata

Automatically track following data for every command execution:

- the executed command
- path of the shell
- shell name
- exit code of the command
- execution time
- session id (automatically created)

### Tracking activity time

For simpler analysis on how long you've worked in the terminal (and in which directories and paths) this data is stored in a separate bucket. Following data is tracked there:

- shell name
- path
- session id

### Restoring specific terminal sessions (Not implemented yet)

_With the data stored it is theoretically possible to write all commands executed in a specific terminal session into a file. This feature is not yet implemented._

---------------

## Installation

### Prerequisites

You need to have [ActivityWatch](https://github.com/activitywatch/activitywatch) installed.

### Install aw-watcher-terminal

```bash
git clone https://github.com/otto-aa/aw-watcher-terminal.git
cd aw-watcher-terminal
make build
```

### Install the appropriate watcher for your shell

_If your preferred shell is missing, feel free to [file an issue][issues] or create the shell watcher on your own ([see docs](/docs))._

- [bash or zsh](https://github.com/Otto-AA/aw-watcher-bash)

### Start aw-watcher-terminal

```bash
# If the aw-server is not started yet (e.g. by aw-qt), then start it in a separate terminal
aw-server
```

```bash
# Start the terminal watcher
aw-watcher-terminal
```

Currently, you can pass it the flags `--testing` for using the test server and `--verbose` for more detailed logging

_Note: If you want it to autostart with aw-qt, take a look at this [this issue](https://github.com/ActivityWatch/aw-qt/issues/35)_

### Open a new terminal and start executing commands

```bash

echo "Finished installation"
```

[issues]: https://github.com/otto-aa/aw-watcher-terminal/issues
