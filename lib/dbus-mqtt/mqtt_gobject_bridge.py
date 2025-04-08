#!/usr/bin/env python
# -*- coding: utf-8 -*-
import errno
import logging
import os
import paho.mqtt.client as mqtt
import socket
import ssl
import sys
import traceback
from gi.repository import GLib


AppDir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.join(AppDir, 'ext', 'velib_python'))
from ve_utils import exit_on_error


class MqttGObjectBridge(object):
	def __init__(self, mqtt_server=None, client_id="", ca_cert=None, user=None, passwd=None, debug=False):
		self._ca_cert = ca_cert
		self._mqtt_user = user
		self._mqtt_passwd = passwd
		self._mqtt_server = mqtt_server or '127.0.0.1'
		
		if not hasattr(mqtt, "CallbackAPIVersion"):
            # paho-mqtt 1.x
			self.client = mqtt.Client(client_id)
		else:
            # paho-mqtt 2.x
			self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id)
		
		self._client.on_connect = self._on_connect
		self._client.on_message = self._on_message
		self._client.on_disconnect = self._on_disconnect
		if debug:
			self._client.on_log = self._on_log
		self._socket_watch = None
		self._socket_timer = None
		if self._init_mqtt():
			GLib.timeout_add_seconds(5, exit_on_error, self._init_mqtt)

	def _init_mqtt(self):
		try:
			logging.info('[Init] Connecting to local broker')
			if self._mqtt_user is not None and self._mqtt_passwd is not None:
				self._client.username_pw_set(self._mqtt_user, self._mqtt_passwd)
			if self._ca_cert is None:
				self._client.connect(self._mqtt_server, 1883, 60)
			else:
				self._client.tls_set(self._ca_cert, cert_reqs=ssl.CERT_REQUIRED)
				self._client.connect(self._mqtt_server, 8883, 60)
			self._init_socket_handlers()
			return False
		except socket.error as e:
			if e.errno == errno.ECONNREFUSED:
				return True
			raise

	def _init_socket_handlers(self):
		if self._socket_watch is not None:
			GLib.source_remove(self._socket_watch)
		self._socket_watch = GLib.io_add_watch(self._client.socket().fileno(), GLib.IO_IN,
			self._on_socket_in)
		if self._socket_timer is None:
			self._socket_timer = GLib.timeout_add_seconds(1, exit_on_error, self._on_socket_timer)

	def _on_log(self, client, userdata, level, log):
		print(log)

	def _on_socket_in(self, src, condition):
		exit_on_error(self._client.loop_read)
		return True

	def _on_socket_timer(self):
		self._client.loop_misc()
		while self._client.want_write():
			# Removed max_packets param value of 10 as this is not supported in paho-mqtt 2.x 
			if self._client.loop_write() != mqtt.MQTT_ERR_SUCCESS: 
				break
		return True

	def _on_connect(self, client, userdata, dict, rc):
		pass

	def _on_message(self, client, userdata, msg):
		pass

	def _on_disconnect(self, client, userdata, rc):
		logging.error('[Disconnected] Lost connection to broker')
		if self._socket_watch is not None:
			GLib.source_remove(self._socket_watch)
			self._socket_watch = None
		logging.info('[Disconnected] Set timer')
		GLib.timeout_add(5000, exit_on_error, self._reconnect)

	def _reconnect(self):
		try:
			logging.info('[Reconnect] start')
			self._client.reconnect()
			self._init_socket_handlers()
			logging.info('[Reconnect] success')
			return False
		except socket.error as e:
			logging.error('[Reconnect] failed' + traceback.format_exc())
			if e.errno == errno.ECONNREFUSED:
				return True
			raise
