#!/bin/bash
export PYTHONPATH=/home/jose/project:$PYTHONPATH
pytest "$@"
