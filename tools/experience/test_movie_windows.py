"""Exercise production passive movie bounds discovery with Win32 API doubles."""
import ctypes as c
from unittest.mock import patch
import normal_lifecycle as n
class Function:
 def __init__(self,fn):self.fn=fn
 def __call__(self,*a):return self.fn(*a)
class User:
 def __init__(self):
  self.visible=True
  self.GetWindowThreadProcessId=Function(lambda h,p:setattr(p._obj,'value',123))
  self.GetClassNameW=Function(self.name)
  self.IsWindowVisible=Function(lambda h:self.visible)
  self.EnumWindows=Function(lambda cb,arg:cb(1,arg))
  self.EnumChildWindows=Function(lambda h,cb,arg:cb(2,arg))
  self.GetWindowRect=Function(self.rect)
 def name(self,h,b,size):b.value='AVIWnd32' if h==2 else 'VirtualONClass';return len(b.value)
 def rect(self,h,r):
  assert h==2
  r._obj.left=-1920;r._obj.top=0;r._obj.right=0;r._obj.bottom=1080;return 1
u=User()
with patch.object(c,'WinDLL',return_value=u,create=True),patch.object(c,'WINFUNCTYPE',c.CFUNCTYPE,create=True):
 assert n.movie_state(123)==(1,1,((-1920,0,1920,1080),))
 u.visible=False;assert n.movie_state(123)==(1,0,())
 assert n.movie_state(999)==(0,0,())
print('PASS passive production window bounds, negative desktop offset, visibility transition, process isolation; no frame access')
