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

### Start aw-watcher-bash.py

_Note: As of now, you always need to start before using the terminal_

```bash
python3 ./.local/bin/aw-watcher-bash.py`
```

### Add following code to the bottom of your ~/.bashrc file

```bash
# Send data to local ActivityWatch server
if [[ -f ~/.bash-preexec.sh ]]; then
  source ~/.bash-preexec.sh
  preexec() { aw-watcher-bash "$1"; }
fi
```

## Future plans

- also log execution time of commands (via precmd)
- check for performance issues
