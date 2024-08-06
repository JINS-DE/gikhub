#!/bin/sh

cd "$(dirname "$0")" || exit
export ENVIRONMENT=production
if [ -d "venv-jungle" ]; then
    . ./venv-jungle/bin/activate
    flask --app app run --debug
fi