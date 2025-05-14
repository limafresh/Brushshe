#!/usr/bin/env bash

MAINDIR=$(dirname "$(readlink -f "$0")")

cd "$MAINDIR" || exit 1

type -P docker &>/dev/null || { echo "Docker not found. Aborted." >&2; exit 1; }

if [ ! -f ./.env ]; then
    echo ".env file not found. Aborted."
    exit 1
fi

function on_killed(){
    docker compose down
    #xhost +
    echo 'Exit'
}

trap on_killed EXIT

## It can be need for enable connect to X11.
#xhost -

docker compose up

on_killed

