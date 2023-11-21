#!/bin/bash

# Log file path
LOG_FILE="/home/jose/project/fetch_log.txt"

# Output timestamp and message to log file
echo "$(date +"%Y-%m-%d %H:%M:%S") Running fetch.py" >> "$LOG_FILE"

# Run fetch.py
/usr/bin/python3 /home/jose/project/fetch.py

