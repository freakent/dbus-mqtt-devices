#!/bin/sh
#BASE=/data/drivers/dbus-mqtt-devices
BASE=$(dirname $(dirname $(realpath "$0")))
cd $BASE
echo "Ensure Python's Pip is installed..."
python -m ensurepip
echo "Pip install module dependencies..."
python -m pip install -r requirements.txt
echo "Set up device service to autorun on restart"
chmod -R a+rwx $BASE/bin/service
rm -fq /service/dbus-mqtt-devices
ln -s $BASE/bin/service /service/dbus-mqtt-devices
echo "ln -s $BASE/bin/service /service/dbus-mqtt-devices" >> /data/rc.local
echo "Install complete"