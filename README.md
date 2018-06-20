# aw-watcher-bash

## Installation

### Install [bash-preexecute](https://github.com/rcaloras/bash-preexec#install)

`curl https://raw.githubusercontent.com/rcaloras/bash-preexec/master/bash-preexec.sh -o ~/.bash-preexec.sh`

### Run make build

`make build`

### Add following code to the bottom of your ~/.bashrc file

```bash
# Send data to local ActivityWatch server
if [[ -f ~/.bash-preexec.sh ]]; then
  source ~/.bash-preexec.sh
  preexec() { aw-watcher-bash "$1" &; }
fi
```

## Future plans

- also log execution time of commands (via precmd)
- use heartbeat flow
- check if an cleaner solution exists than _.bashrc -> aw-watcher-bash.sh -> aw-watcher-bash.py_
- check for performance issues
