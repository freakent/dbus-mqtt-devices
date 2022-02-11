#!/bin/sh
#!/bin/sh
BASE=/data/drivers/dbus-mqtt-devices
cd $BASE
python -m ensurepip
python -m pip install -r requirements.txt
chmod -R a+rwx $BASE/bin/service
ln -s $BASE/bin/service /service/dbus-mqtt-devices
