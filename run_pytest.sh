#!/bin/bash
export PYTHONPATH=/home/jose/project:$PYTHONPATH
coverage run -m pytest "$@"
coverage report
