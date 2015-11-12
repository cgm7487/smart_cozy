#!/bin/sh

TRAIN_FILE="train.csv"
LOCK_FILE="lockfile"
TEMP_FOLDER="tmp/"

sudo hciconfig hci0 up

if [ $? -ne 0 ]; then
	echo "bluetooth interface error"
	exit 1
fi

if [ -e $TRAIN_FILE ]; then
	echo $TRAIN_FILE exists
else
	echo $TRAIN_FILE does not exist, generate a new one
	python apparent_temperature_generator.py
fi

if [ ! -d $TEMP_FOLDER ]; then
	mkdir $TEMP_FOLDER && touch $TEMP_FOLDER$LOCK_FILE
elif [ ! -f $TEMP_FOLDER$LOCK_FILE ]; then
	touch $TEMP_FOLDER$LOCK_FILE
fi

python ble_controller_daemon.py start 34:B1:F7:D1:47:D5 00:15:83:00:77:2D &

python learning_engine.py start &

python weather_extractor_daemon.py start &

startx

exit 0
