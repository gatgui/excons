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
  m = re.search(r"Current\s+->\s+(%s/Versions/)?([0-9\.]+)" % frameworkPath, out)
  if m != None:
    return m.group(2)
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

def Require(e, ignoreLinkFlags=False):
  po = ARGUMENTS.get("with-python", None)
  if po != None:
    if str(Platform()) == "darwin":
      # Can either be the .framework path or the path to the framework version
      m = re.search(r"/([^/]+)\.framework/Versions/([^/]+)/?$", po)
      if m:
        fw = "%s/%s" % (po, m.group(1))
        hd = "%s/Headers" % po
        if os.path.isfile(fw) and os.path.isdir(hd):
          v = m.group(2)
          e.Append(CCFLAGS=" -DPY_VER=%s" % v)
          e.Append(CPPPATH=[hd])
          if not ignoreLinkFlags:
            e.Append(LINKFLAGS=" %s" % fw)
          return
        else:
          print("python specified by with-python is not useable, use default settings")
      else:
        # Try to figure framework "Current" version
        v = _GetPythonVersionOSX(po)
        if v != None:
          a = " -F%s" % os.path.dirname(po)
          b = " -framework %s" % os.path.splitext(os.path.basename(po))[0]
          e.Append(CCFLAGS=" -DPY_VER=%s" % v)
          e.Append(CPPPATH=["%s/Versions/%s/Headers" % (po, v)])
          if not ignoreLinkFlags:
            e.Append(LINKFLAGS=a+b)
          return
        else:
          print("python specified by with-python is not useable, use default settings")
    
    elif str(Platform()) == "win32":
      v = _GetPythonVersionWIN(po)
      if v != None:
        e.Append(CCFLAGS=" -DPY_VER=%s" % v)
        e.Append(CPPPATH=[po+'\\include'])
        if not ignoreLinkFlags:
          e.Append(LIBPATH=[po+'\\libs'])
          e.Append(LIBS=["python%s" % v.replace(".", "")])
        return
      else:
        print("python specified by with-python is not useable, use default settings")
    
    else:
      print("with-python not yet supported on this platform, use default settings")
  
  # default settings: use the python that this script
  
  pyver = sysconfig.get_python_version()
  e.Append(CCFLAGS=" -DPY_VER=%s" % pyver)
  e.Append(CPPPATH=[sysconfig.get_python_inc()])
  
  if sysconfig.get_config_var("PYTHONFRAMEWORK"):
    if not ignoreLinkFlags:
      fwdir = sysconfig.get_config_var("PYTHONFRAMEWORKPREFIX")
      fwname = sysconfig.get_config_var("PYTHONFRAMEWORK")
      if _GetPythonVersionOSX("%s/%s.framework") != pyver:
        e.Append(LINKFLAGS=" %s/%s.framework/Versions/%s" % (fwdir, fwname, pyver, fwname))
      else:
        e.Append(LINKFLAGS=" -F%s -framework %s" % (fwdir, fwname))
  else:
    if str(Platform()) == "win32":
      e.Append(LIBPATH=[sysconfig.PREFIX+'\\libs'])
      e.Append(LIBS=["python%s" % pyver.replace(".", "")])
    else:
      e.Append(CCFLAGS=" %s" % sysconfig.get_config_var("CFLAGS"))
      if not ignoreLinkFlags:
        e.Append(LINKFLAGS=" %s" % sysconfig.get_config_var("LINKFORSHARED"))
        e.Append(LIBS=["python%s" % pyver])

def BuildModule(e):
  if str(Platform()) == "darwin":
    e.Append(LINKFLAGS=" -undefined dynamic_lookup")
    Require(e, ignoreLinkFlags=True)
  else:
    Require(e)

def ModulePrefix():
  return "lib/python/"

def ModuleExtension():
  return sysconfig.get_config_var("SO")


