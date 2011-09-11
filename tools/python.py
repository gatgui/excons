# Copyright (C) 2009, 2010  Gaetan Guidet
# 
# This file is part of excons.
# 
# excons is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation; either version 2.1 of the License, or (at
# your option) any later version.
# 
# excons is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301,
# USA.

from SCons.Script import *
import os
import re
import subprocess
from distutils import sysconfig

def _GetPythonVersionOSX(frameworkPath):
  p = subprocess.Popen("ls -l %s/Versions | grep Current" % frameworkPath, shell=True, stdout=subprocess.PIPE)
  out, err = p.communicate()
  m = re.search(r"Current\s+->\s+%s/Versions/([0-9\.]+)" % frameworkPath, out)
  if m != None:
    return m.group(1)
  return None

def _GetPythonVersionWIN(pythonPath):
  fl = glob.glob(os.path.join(pythonPath, "python*.dll"))
  if len(fl) == 1:
    m = re.match(r"python(\d)(\d)\.dll", fl[0], re.IGNORECASE)
    if m != None:
      return "%s.%s" % (m.group(1), m.group(2))
  return None


def Version():
  po = ARGUMENTS.get("with-python", None)
  if po != None:
    if str(Platform()) == "darwin":
      v = _GetPythonVersionOSX(po)
      if v != None:
        return v
    elif str(Platform()) == "win32":
      v = _GetPythonVersionWIN(po)
      if v != None:
        return v
  return str(sysconfig.get_python_version())

def Require(e):
  po = ARGUMENTS.get("with-python", None)
  if po != None:
    if str(Platform()) == "darwin":
      v = _GetPythonVersionOSX(po)
      if v != None:
        a = ' -F%s' % os.path.dirname(po)
        b = ' -framework %s' % os.path.splitext(os.path.basename(po))[0]
        e.Append(CCFLAGS=" -DPY_VER=%s" % v)
        e.Append(CPPPATH=["%s/Headers" % po])
        e.Append(LINKFLAGS=a+b)
        return
      else:
        print("python specified by with-python is not useable, use default settings")
    
    elif str(Platform()) == "win32":
      v = _GetPythonVersionWIN(po)
      if v != None:
        e.Append(CCFLAGS=" -DPY_VER=%s" % v)
        e.Append(CPPPATH=[po+'\\include'])
        e.Append(LIBPATH=[po+'\\libs'])
        e.Append(LIBS=["python%s" % v.replace(".", "")])
        return
      else:
        print("python specified by with-python is not useable, use default settings")
    
    else:
      print("with-python not yet supported on this platform, use default settings")
  
  # default settings: use the python that this script
  
  e.Append(CCFLAGS=" -DPY_VER=%s" % sysconfig.get_python_version())
  e.Append(CPPPATH=[sysconfig.get_python_inc()])
  
  if sysconfig.get_config_var("PYTHONFRAMEWORK"):
    a = ' -F' + sysconfig.get_config_var("PYTHONFRAMEWORKPREFIX")
    b = ' -framework ' + sysconfig.get_config_var("PYTHONFRAMEWORK")
    e.Append(LINKFLAGS=a+b)
  else:
    if str(Platform()) == "win32":
      e.Append(LIBPATH=[sysconfig.PREFIX+'\\libs'])
      e.Append(LIBS=["python%s" % sysconfig.get_python_version().replace(".", "")])
    else:
      e.Append(CCFLAGS=" %s" % sysconfig.get_config_var("CFLAGS"))
      e.Append(LINKFLAGS=" %s" % sysconfig.get_config_var("LINKFORSHARED"))
      e.Append(LIBS=["python%s" % sysconfig.get_python_version()])

def ModulePrefix():
  return "lib/python/"

def ModuleExtension():
  return sysconfig.get_config_var("SO")


