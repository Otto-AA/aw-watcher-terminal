# aw-watcher-bash [WIP]

## Installation

### Install [bash-preexecute](https://github.com/rcaloras/bash-preexec#install)

```bash
curl https://raw.githubusercontent.com/rcaloras/bash-preexec/master/bash-preexec.sh -o ~/.bash-preexec.sh
```

### Run make build

```bash
make build
```

### Start aw-watcher-terminal.py

```bash
# If not already running, start the aw-server in a different terminal
aw-server &
# Start aw-watcher-terminal.py
python3 ./.local/bin/aw-watcher-terminal.py
```

Currently, you can pass it the flags `--testing` for using the test server and `--verbose` for more detailed logging

### Add following code to the bottom of your ~/.bashrc file

```bash
# Send data to local ActivityWatch server
if [[ -f ~/.bash-preexec.sh ]]; then
  source ~/.bash-preexec.sh
  preexec() {
    # Call aw-watcher-bash in a background process to
    # prevent blocking and in a subshell to prevent logging
    (aw-watcher-bash "$1" &)
  }
fi
```

### Open a new terminal and start executing commands

```bash
echo "Finished installation"
```

## Future plans

- also log execution time of commands (via precmd)
- check for performance issues
