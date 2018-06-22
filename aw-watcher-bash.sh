#!/usr/bin/env bash

# escape "quotes" in command and path
escape_quotes() { echo "${1//\"/\\\"}"; }
command="$(escape_quotes "$1")"
path="$(escape_quotes "$PWD")"
pipe_path="/tmp/aw-watcher-bash-pipe"

# send message to pipe
echo "--command \"$command\" --path \"$path\"" > "$pipe_path"