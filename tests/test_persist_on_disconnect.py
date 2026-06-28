import os
import sys
from unittest import mock

test_dir = os.path.dirname(__file__)
sys.path.insert(1, os.path.join(test_dir, '..'))

# device.py imports device_service, which pulls in dbus/vedbus. Stub it with a tiny
# fake service so we can unit-test MQTTDevice's payload parsing + connected fan-out
# without a dbus stack (the other tests likewise avoid the dbus-coupled modules).
class _FakeService:
    def __init__(self, *args, **kwargs):
        self.set_connected = mock.MagicMock()

    def __del__(self):
        pass


_fake_device_service = mock.MagicMock()
_fake_device_service.MQTTDeviceService = _FakeService
sys.modules['device_service'] = _fake_device_service

import unittest
from device import MQTTDevice


def make_device(status):
    return MQTTDevice(device_mgr=mock.MagicMock(), device_status=status)


class TestPersistOnDisconnect(unittest.TestCase):

    def test_defaults_to_false_when_absent(self):
        d = make_device({"clientId": "fe001", "version": "v1",
                         "services": {"t1": "temperature"}})
        self.assertFalse(d.persist_on_disconnect)

    def test_opt_in_true(self):
        d = make_device({"clientId": "fe001", "version": "v1",
                         "persist_on_disconnect": True,
                         "services": {"t1": "temperature"}})
        self.assertTrue(d.persist_on_disconnect)

    def test_explicit_false(self):
        d = make_device({"clientId": "fe001", "version": "v1",
                         "persist_on_disconnect": False,
                         "services": {"t1": "temperature"}})
        self.assertFalse(d.persist_on_disconnect)

    def test_set_connected_fans_out_to_every_service(self):
        d = make_device({"clientId": "fe001", "version": "v1",
                         "services": {"t1": "temperature", "t2": "tank"}})
        d.set_connected(False)
        self.assertEqual(len(d.services), 2)
        for svc in d.services.values():
            svc.set_connected.assert_called_once_with(False)


if __name__ == "__main__":
    unittest.main()
