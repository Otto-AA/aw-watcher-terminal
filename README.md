# aw-watcher-terminal [WIP]

[![Build Status](https://travis-ci.com/Otto-AA/aw-watcher-terminal.svg?branch=master)](https://travis-ci.com/Otto-AA/aw-watcher-terminal)

## Installation

### Install

```bash
make build
```

### Install the appropriate watcher for your shell

_If your preferred shell is missing, feel free to [file an issue](/issues) or create the shell watcher on your own ([see docs](/docs))._

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