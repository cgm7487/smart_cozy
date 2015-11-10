#!/bin/sh

sudo hciconfig hci0 up


if [ $? -ne 0 ]; then
	echo "bluetooth interface error"
	exit 1
fi 

python ble_controller_daemon.py start 34:B1:F7:D1:47:D5 00:15:83:00:77:2D &

python learning_engine.py start &

python weather_extractor_daemon.py start &

startx

exit 0
