"""Metadata-only Windows discovery; no device paths, serials or input reads."""
import ctypes as c
from ctypes import wintypes as w
import os


def snapshot():
    if os.name != 'nt':
        return {'controllers': [], 'displays': [], 'available': False}
    user = c.WinDLL('user32', use_last_error=True)
    displays = []
    callback_type = c.WINFUNCTYPE(w.BOOL, w.HANDLE, w.HDC, c.POINTER(w.RECT), w.LPARAM)
    def monitor(handle, dc, rect, data):
        r = rect.contents
        displays.append({'width': r.right-r.left, 'height': r.bottom-r.top})
        return True
    user.EnumDisplayMonitors.argtypes = [w.HDC, c.POINTER(w.RECT), callback_type, w.LPARAM]
    if not user.EnumDisplayMonitors(None, None, callback_type(monitor), 0):
        raise OSError('Display discovery unavailable')
    class Device(c.Structure):
        _fields_ = [('handle', w.HANDLE), ('type', w.DWORD)]
    count = w.UINT()
    user.GetRawInputDeviceList.argtypes = [c.POINTER(Device), c.POINTER(w.UINT), w.UINT]
    user.GetRawInputDeviceList.restype = w.UINT
    if user.GetRawInputDeviceList(None, c.byref(count), c.sizeof(Device)) == 0xffffffff or count.value > 1024:
        raise OSError('Controller discovery unavailable')
    devices = (Device * count.value)()
    n = user.GetRawInputDeviceList(devices, c.byref(count), c.sizeof(Device))
    if n == 0xffffffff:
        raise OSError('Controller discovery changed')
    user.GetRawInputDeviceInfoW.argtypes = [w.HANDLE, w.UINT, c.c_void_p, c.POINTER(w.UINT)]
    user.GetRawInputDeviceInfoW.restype = w.UINT
    controllers = []
    for device in devices[:n]:
        if device.type != 2:
            continue
        # RID_DEVICE_INFO: header (8), HID DWORD vid/pid/version, USHORT page/usage.
        info = (w.DWORD * 8)(); info[0] = 32; size = w.UINT(32)
        if user.GetRawInputDeviceInfoW(device.handle, 0x2000000b, info, c.byref(size)) == 0xffffffff:
            continue
        page, usage = info[5] & 65535, info[5] >> 16
        if page == 1 and usage in (4, 5):
            controllers.append({'type': 2, 'vid': int(info[2]), 'pid': int(info[3])})
    for dll in ('xinput1_4.dll', 'xinput1_3.dll', 'xinput9_1_0.dll'):
        try:
            xi = c.WinDLL(dll)
            xi.XInputGetCapabilities.argtypes = [w.DWORD, w.DWORD, c.c_void_p]
            xi.XInputGetCapabilities.restype = w.DWORD
            for slot in range(4):
                caps = c.create_string_buffer(64)
                if xi.XInputGetCapabilities(slot, 0, caps) == 0:
                    controllers.append({'type': 1, 'xinput_slot': slot})
            break
        except OSError:
            continue
    return {'controllers': controllers, 'displays': displays, 'available': True}
