#!/bin/bash
APP=garage-pi
SETTINGS=/var/garage-pi/garage-pi.cfg
LOG=/var/garage-pi/garage-pi-app.log
FLASK=/usr/local/bin/flask
IP=0.0.0.0
PORT=${1:-80}
cd /apps/garage-pi
exec > /apps/garage-pi-debug.log 2>&1
echo "===== garage-pi startup =========================="
date +%c
SETTINGS_FILE=$SETTINGS LOG_FILE=$LOG exec "$FLASK" --app=$APP run --host=$IP --port=$PORT
