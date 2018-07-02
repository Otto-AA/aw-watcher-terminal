# aw-watcher-terminal [WIP]

## Installation

### Run make build

```bash
make build
```

### Install the approbiate watcher for your shell

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

### Open a new terminal and start executing commands

```bash
echo "Finished installation"
```

## Future plans

- also log execution time of commands (via precmd)
- check for performance issues
