import logging
import argparse
#import dbus
import os
import sys
import signal
import traceback
from functools import partial
from gi.repository import GLib
from dbus.mainloop.glib import DBusGMainLoop

AppDir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.join(AppDir, 'ext', 'velib_python'))

from logger import setup_logging
from ve_utils import get_vrm_portal_id, exit_on_error, wrap_dbus_value, unwrap_dbus_value

from device_manager import MQTTDeviceManager

SoftwareVersion = '0.10'

def dumpstacks(signal, frame):
	import threading
	id2name = dict((t.ident, t.name) for t in threading.enumerate())
	for tid, stack in sys._current_frames().items():
		logging.info ("=== {} ===".format(id2name[tid]))
		traceback.print_stack(f=stack)

def main():
	parser = argparse.ArgumentParser(description='Publishes values from the D-Bus to an MQTT broker')
	parser.add_argument('-d', '--debug', help='set logging level to debug', action='store_true')
	parser.add_argument('-q', '--mqtt-server', nargs='?', default=None, help='name of the mqtt server')
	parser.add_argument('-u', '--mqtt-user', default=None, help='mqtt user name')
	parser.add_argument('-P', '--mqtt-password', default=None, help='mqtt password')
	parser.add_argument('-c', '--mqtt-certificate', default=None, help='path to CA certificate used for SSL communication')
	parser.add_argument('-b', '--dbus', default=None, help='dbus address')
	parser.add_argument('-i', '--init-broker', action='store_true', help='Tries to setup communication with VRM MQTT broker')
	args = parser.parse_args()

	print("-------- dbus_mqtt_devices, v{} is starting up --------".format(SoftwareVersion))
	logger = setup_logging(args.debug)

	mainloop = GLib.MainLoop()
	# Have a mainloop, so we can send/receive asynchronous calls to and from dbus
	DBusGMainLoop(set_as_default=True)
	keep_alive_interval = args.keep_alive if args.keep_alive > 0 else None
	handler = MQTTDeviceManager(
		mqtt_server=args.mqtt_server, ca_cert=args.mqtt_certificate, user=args.mqtt_user,
		passwd=args.mqtt_password, dbus_address=args.dbus, keep_alive_interval=keep_alive_interval,
		init_broker=args.init_broker, debug=args.debug)

	# Quit the mainloop on ctrl+C
	signal.signal(signal.SIGINT, partial(exit, mainloop))

	# Handle SIGUSR1 and dump a stack trace
	signal.signal(signal.SIGUSR1, dumpstacks)

	# Start and run the mainloop
	try:
		mainloop.run()
	except KeyboardInterrupt:
		pass

if __name__ == '__main__':
	main()