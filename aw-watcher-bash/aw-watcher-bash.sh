#!/usr/bin/env bash


# escape_quotes
# Prepends a backslash to every quote (") and every backslash followed by a quote (\") or backslash (\\)
#
# From: echo "\"" > "output"
# To:   echo \"\\\"\" > \"output\"
# From: echo "\\" > "output"
# To:   echo \"\\\\\" > \"output\"
escape_quotes() {
    original="$1"
    length=${#original}
    result=""

    # Iterate over chars and prepend a backslash to every quote and every backslash followed by a quote or a backslash
    for (( i=0; i<$length; i++ )); do
        char="${original:$i:1}"

        if [[ $char = \" ]]; then
            result+="\\"
        elif [[ $char = "\\" ]]; then
            next_char_index=$((i+1))
            if [[ $next_char_index -lt $length ]]; then
                next_char="${original:$next_char_index:1}"
                if [[ $next_char  = \" ]] || [[ $next_char = "\\" ]]; then
                    result+="\\"
                fi
            fi
        fi

        result+="$char"
    done

    echo "$result"
}

# Set variables
command="$(escape_quotes "$1")"
path="$(escape_quotes "$PWD")"
shell='bash'
shell_version="$BASH_VERSION"
pipe_path="/tmp/aw-watcher-terminal-pipe"

message="--command \"$command\" --path \"$path\" --shell \"$shell\" --shell-version \"$shell_version\""

# send message to pipe
echo "$message" > "$pipe_path" &

# The background process would keep open if the pipe was not opened for reading at the time of execution
# Therefore delete background process after delay
pipe_sender_pid="$!"
sleep 5 && kill "$pipe_sender_pid" &> /dev/null &