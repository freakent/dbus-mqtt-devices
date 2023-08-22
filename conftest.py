# conftest.py
import sys

print("Creating MOCK dbus and dbus.service modules")
module = type(sys)('dbus')
module.Array = lambda arr, signature, variant_level: [arr, signature, variant_level]
module.Signature = lambda sig: sig
module.Int32 = False
module.UInt32 = False
module.Byte = False
module.Int16 = False
module.UInt16 = False
module.Int64 = False
module.UInt64 = False

module.service = type(sys)('dbus.service')
module.service.Object = object
module.service.method = lambda path, in_signature = "", out_signature = "": lambda self: False # Decorator function
module.service.signal = lambda path, signature = "": lambda self: False # Decorator function


sys.modules['dbus'] = module
sys.modules['dbus.service'] = module

