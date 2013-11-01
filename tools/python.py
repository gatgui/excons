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
import excons
from distutils import sysconfig

def _GetPythonVersionOSX(pythonPath):
  # On osx, pythonPath must be the path to the python framework
  # i.e.  with-python=/System/Library/Frameworks/Python.framework
  p = subprocess.Popen("ls -l %s/Versions | grep Current" % pythonPath, shell=True, stdout=subprocess.PIPE)
  out, err = p.communicate()
  m = re.search(r"Current\s+->\s+(%s/Versions/)?([0-9\.]+)" % pythonPath, out)
  if m != None:
    return m.group(2)
  return None

def _GetPythonVersionWIN(pythonPath):
  # On windows, pythonPath must be the path to the python executable
  # i.e.  with-python=C:/Python27/python.exe
  dn = os.path.dirname(pythonPath)
  fl = glob.glob(os.path.join(dn, "python*.dll"))
  if len(fl) == 1:
    m = re.match(r"python(\d)(\d)\.dll", fl[0], re.IGNORECASE)
    if m != None:
      return "%s.%s" % (m.group(1), m.group(2))
  return None

def _GetPythonVersionUNIX(pythonPath):
  # On unix, pythonPath must be the path to the python executable
  # i.e.  with-python=/usr/local/bin/python
  p = subprocess.Popen("ldd %s | grep libpython" % pythonPath, shell=True, stdout=subprocess.PIPE)
  out, err = p.communicate()
  m = re.search(r"libpython([0-9\.]+)\.so", out)
  if m != None:
    return m.group(1)
  return None

_specCache = {}

def _GetPythonSpec(specString):
  global _specCache

  if specString in _specCache:
    return _specCache[specString]

  spec = None

  plat = str(Platform())

  if re.match(r"\d+\.\d+", specString):
    ver = specString

    # Look in standard locations

    if plat == "darwin":
      searchPaths = ["/System/Library/Frameworks", "/Library/Frameworks"]
      for searchPath in searchPaths:
        pythonPath = os.path.join(searchPath, "Python.framework", "Versions", ver)
        if os.path.isdir(pythonPath):
          if ver == _GetPythonVersionOSX(os.path.join(searchPath, "Python.framework")):
            spec = (ver, "%s/Headers" % pythonPath, searchPath, "Python")
            break
          else:
            spec = (ver, "%s/Headers" % pythonPath, None, "%s/Python" % (pythonPath))
            break

    elif plat == "win32":
      pythonPath = "C:\\Python%s" % ver.replace(".", "")
      if os.path.isdir(pythonPath):
        incdir = os.path.join(pythonPath, "include")
        libdir = os.path.join(pythonPath, "libs")
        lib = "python%s" % ver.replace(".", "")
        spec = (ver, incdir, libdir, lib)

    else:
      searchPaths = ["/usr", "/usr/local"]
      for searchPath in searchPaths:
        pythonPath = os.path.join(searchPath, "bin", "python%s" % ver)
        if not os.path.isfile(pythonPath):
          pythonPath = os.path.join(searchPath, "python")
          if os.path.isfile(pythonPath) and _GetPythonVersionUNIX() == ver:
            spec = (ver, searchPath)
            break
        else:
          spec = (ver, searchPath)
          break

      if spec:
        ver, prefix = spec
        incdir = os.path.join(prefix, "include", "python%s" % ver)
        libdir = os.path.join(prefix, ("lib64" if excons.Build64() else "lib"))
        lib = "python%s" % ver
        spec = (ver, incdir, libdir, lib)

  else:
    if plat == "darwin":
      m = re.search(r"/([^/]+)\.framework/Versions/([^/]+)/?$", specString)
      if m:
        fwn = m.group(1)
        fw = "%s/%s" % (specString, fwn)
        fwh = "%s/Headers" % specString
        if os.path.isfile(fw) and os.path.isdir(fwh):
          # if it is the current version, use framework directory
          ver = m.group(2)
          fwd = re.sub(r"/Versions/.*$", "", specString)
          if ver == _GetPythonVersionOSX(fwd):
            spec = (ver, fwd)
          else:
            spec = (ver, fw)
      else:
        ver = _GetPythonVersionOSX(specString)
        if ver != None:
          spec = (ver, specString)
    
    elif plat == "win32":
      ver = _GetPythonVersionWIN(specString)
      if ver != None:
        incdir = os.path.join(specString, "include")
        libdir = os.path.join(specString, "libs")
        lib = "python%s" % ver.replace(".", "")
        spec = (ver, incdir, libdir, lib)
    
    else:
      ver = _GetPythonVersionUNIX(specString)
      if ver != None:
        # not specString but 2 dirs up (as specString is the path to the python executable)
        d = os.path.dirname(specString)
        if os.path.basename(d) == "bin":
          d = os.path.dirname(d)
          incdir = os.path.join(d, "include", "python%s" % ver)
          libdir = os.path.join(d, ("lib64" if excons.Build64() else "lib"))
          lib = "python%s" % ver
          spec = (ver, incdir, libdir, lib)

  # check setup validity
  if spec is not None:
    if plat == "darwin":
      _, incdir, fwdir, fw = spec
      if fwdir is None:
        # directly linking version specific framework
        if not os.path.isdir(incdir) or not os.path.isfile(fw):
          spec = None
      else:
        if not os.path.isdir(incdir) or not os.path.isdir(fwdir):
          spec = None
    else:
      ver, incdir, libdir, lib = spec
      if not os.path.isdir(incdir) or not os.path.isdir(libdir):
        spec = None
      else:
        if plat == "win32":
          if not os.path.isfile(os.path.join(libdir, "%s.lib" % lib)):
            spec = None
        else:
          if not os.path.isfile(os.path.join(libdir, "lib%s.so" % lib)):
            spec = None

  print("Python spec for \"%s\": %s" % (specString, spec))
  
  _specCache[specString] = spec

  return spec

def Version():
  po = ARGUMENTS.get("with-python", None)

  if po is not None:
    rv = _GetPythonSpec(po)
    if rv is not None:
      return rv[0]

  return str(sysconfig.get_python_version())

def Require(e, ignoreLinkFlags=False):
  po = ARGUMENTS.get("with-python", None)
  
  if po is not None:
    rv = _GetPythonSpec(po)

    if rv is not None:
      ver, incdir, libdir, lib = rv
      plat = str(Platform())

      e.Append(CCFLAGS=" -DPY_VER=%s" % ver)
      e.Append(CPPPATH=[incdir])

      if not ignoreLinkFlags:
        if plat == "darwin":
          if libdir:
            e.Append(LINKFLAGS=" -F%s -framework %s" % (libdir, lib))
          else:
            e.Append(LINKFLAGS=" %s" % lib)
        else:
          e.Append(LIBPATH=[libdir])
          e.Append(LIBS=[lib])

      return
  
  # Default settings: use the python that this script runs on
  
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

def SoftRequire(e):
  if str(Platform()) == "darwin":
    e.Append(LINKFLAGS=" -undefined dynamic_lookup")
    Require(e, ignoreLinkFlags=True)
  else:
    Require(e)

def ModulePrefix():
  return "lib/python/"

def ModuleExtension():
  return sysconfig.get_config_var("SO")


