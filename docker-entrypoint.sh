#!/bin/sh
set -e

# If the first argument is explicitly 'arr-oldies', strip it
if [ "$1" = "arr-oldies" ]; then
    shift
fi

# If no arguments provided, or first argument starts with a flag (e.g. --help, -v),
# or first argument is a recognized arr-oldies subcommand:
if [ $# -eq 0 ] || [ "${1#-}" != "$1" ] || [ "$1" = "scan" ] || [ "$1" = "clean" ] || [ "$1" = "validate-config" ]; then
    exec arr-oldies "$@"
fi

# Otherwise, pass through to execute arbitrary system binaries (e.g. whoami, sh, bash, python)
exec "$@"
