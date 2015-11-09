#!/bin/sh

sudo hciconfig hci0 up

python ble_controller.py 34:B1:F7:D1:47:D5 00:15:83:00:77:2D &

python learning_engine.py &

python weather_parser.py &

startx

exit 0
