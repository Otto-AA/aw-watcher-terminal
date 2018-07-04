# Writing a watcher

This tutorial will guide you through the steps to create a shell specific watcher.

## Table of Contents

- [Writing a watcher](#writing-a-watcher)
    - [Table of Contents](#table-of-contents)
    - [Prerequisites](#prerequisites)
    - [Quickstart](#quickstart)
    - [Sending events](#sending-events)
        - [Event types](#event-types)
        - [Message structure](#message-structure)
            - [Base message](#base-message)
            - [preopen message](#preopen-message)
            - [preexec message](#preexec-message)
            - [precmd message](#precmd-message)
            - [preclose message](#preclose-message)
        - [Examples](#examples)
    - [Listening for events](#listening-for-events)
        - [Setting up the hooks](#setting-up-the-hooks)
            - [preopen hook](#preopen-hook)
        - [preexec and precmd hook](#preexec-and-precmd-hook)
            - [preclose hook](#preclose-hook)
    - [Tips](#tips)
        - [Asynchronously sending events](#asynchronously-sending-events)
        - [Create a common event handler for all events](#create-a-common-event-handler-for-all-events)
        - [Use aw-watcher-bash if supported](#use-aw-watcher-bash-if-supported)

## Prerequisites

- [aw-server](https://github.com/ActivityWatch/aw-server.git)
- [aw-watcher-terminal](/)

## Quickstart

This is some pseudo code to demonstrate how your shell watcher could look like. If you want a real example, you can take a look at [aw-watcher-bash](https://github.com/otto-aa/aw-watcher-bash).

```javascript
// This function handles event calls
function send_aw_watcher_bash_event(args) {
    var base_args = [
        '--pid "1234"',
        '--shell "nutshell"',
        '--time "2006-08-14T02:34:56-06:00"',
        '--path "/home/me/my_dir/"
    ]

    var message = str(base_args + args)
    message = escape_double_quotes_and_backslashes(message)
    fifo_path = "HOME/.local/share/activitywatch/aw-watcher-terminal/aw-watcher-terminal-fifo"

    asynchronously write(message).to(fifo_path)
}

// You will need to somehow set up following hooks in your shell. See "Listening for events" if you have no idea how this could work.
preopen() {
    send_aw_watcher_bash_event('--event "preopen"')
}
preexec() {
    command = get_command_which_will_be_executed()
    send_aw_watcher_bash_event('--event "preexec"', `--command "${command}"`)
}
precmd() {
    exit_code = get_exit_code_from_last_command()
    send_aw_watcher_bash_event('--event "precmd"', `--exit-code "${exit_code}"`)
}
preclose() {
    send_aw_watcher_bash_event('--event "preclose"')
}
```

## Sending events

To send events to the aw-watcher-terminal you will need to write a message to a named pipe (also called fifo).
It will look similar to this:

```bash
echo "$message" > "$fifo";
```

Keep in mind, that the message should be escaped properly. You will need to add a `\` in front of every `"` and `\`.

```bash
# Following command
echo "He said \"Let's go\""
# should be escaped like
"echo \"He said \\\"Let's go\\\"\""
```

### Event types

The aw-watcher-terminal can receive several event types. It is recommended to set up hooks for all events, yet it also works only with preexec events.
Following events can be received:

**preopen**: Send this while/before opening a new terminal

**preexec event**: Send this before executing a command

**precmd event**: Send this before the command prompt (or when the previous command has finished)

**preclose event**: Send this before closing a terminal

### Message structure

The aw-watcher-terminal can receive several types of event types. Depending on the event type the message my vary a bit.

#### Base message

These arguments are required for all event types:

- `--pid`   _The process id of the terminal_
- `--shell` _The shell name which processes the command_
- `--path`  _The current path_
- `--time`  _The current time in iso8601 format_
- `--event` _The event to trigger (e.g. 'preexec')_

Optional flags:

- `--send-heartbeat`    _Pass this flag if you also want to send heartbeats to a separate bucket_

#### preopen message

- `--event preopen`

#### preexec message

- `--event preexec`
- `--commmand`  _The command which got executed_

#### precmd message

- `--event precmd`
- `--exit-code` _The exit code of the previous command_

#### preclose message

- `--event preclose`

### Examples

```bash
base_args="--pid \"1234\" --shell \"bash\" --path \"/home/me/Documents\" --time \"2006-08-14T02:34:56-06:00\""
preopen_msg="$base_args --event \"preopen\""
preexec_msg="$base_args --event \"preexec\" --command \"He said \\\"Hey you!\\\" and waved his hands.\""
precmd_msg="$base_args --event \"precmd\" --exit-code \"0\""
preclose_msg="$base_args --event \"preclose\""

messages=("$preopen_msg" "$preexec_msg" "$precmd_msg" "$preclose_msg")
fifo_path="${XDG_DATA_HOME:-$HOME/.local/share}/activitywatch/aw-watcher-terminal/aw-watcher-terminal-fifo"

echo "$preopen_msg" > "$fifo_path"
# Note: Following would fail as using exact the same timestamps for multiple events is unsupported
# do
#   echo "$message" > "$fifo_path"
# done
```

## Listening for events

This strongly depends on the shell you use, so you will have to do some research for that on your own (or ask for help in the [issues](/issues/)).

### Setting up the hooks

#### preopen hook

Most shell provide a way to listen to terminal startups. For example, in bash the file `.bashrc` is called every time before starting bash. For cmd you could [specify a init script in the Auto-Run registry key](https://stackoverflow.com/a/17405182).

### preexec and precmd hook

Some shells have in-builds for this (e.g. zsh with `preexec` and `precmd`), others can easily be extended (e.g. bash with [bash-preexec](https://github.com/rcaloras/bash-preexec)), and for some this may be a bit harder or not possible at all. Maybe you can also listen for changes to the command history file (if existing) and with information call `preexec`. If none of these works, making a watcher for this shell is likely not possible (feel free to file an issue for help).

#### preclose hook

In some shells you can do this with the `trap` command, others probably have an in-built command for that. If none of these is available you _could_ try to check if this specific process ended in an interval or set up a listener (But this seems a bit overkill.

## Tips

### Asynchronously sending events

To prevent the terminal from stalling, it is recommended to send events in a background task. Please note, that writing to the fifo _may_ stall until the fifo is read. So for the case, that aw-watcher-terminal is currently inactive consider killing the background tasks after some delay.

### Create a common event handler for all events

If you create an event handler which all event hooks use, you can more easily keep it DRY. The event handler could take care of creating the base arguments, escaping the quotes and backslashes and finally sending the event asynchronously.

```bash
precmd() {
    send_aw_watcher_bash_event 'precmd' "$?"
}
aw-watcher-terminal-preclose() {
    send_aw_watcher_bash_event 'preclose'
}
```

### Use aw-watcher-bash if supported

If bash is installed on the system you could use aw-watcher-bash.sh as an event handler to simplify things. You can find it [here](https://github.com/otto-aa/aw-watcher-bash).