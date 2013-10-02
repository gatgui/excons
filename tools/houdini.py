# Copyright (C) 2013  Gaetan Guidet
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
import excons
import sys
import re
import os
import subprocess

def PluginExt():
  if str(Platform()) == "darwin":
    return ".dylib"
  elif str(Platform()) == "win32":
    return ".dll"
  else:
    return ".so"

def Plugin(env):
  env.Append(CPPDEFINES = ["MAKING_DSO"])

def GetVersionAndDirectory(noexc=False):
  verexp = re.compile(r"\d+\.\d+\.\d+(\.\d+)?")
  hfs = ARGUMENTS.get("with-houdini", None)
  
  if not hfs:
    ver = ARGUMENTS.get("houdini-ver", None)
    if not ver:
      if not noexc:
        raise Exception("Please set Houdini version using houdini-ver=")
      else:
        return (None, None)
    if not verexp.match(ver):
      if not noexc:
        raise Exception("Invalid version format: \"%s\"" % ver)
      else:
        return (None, None)
    if sys.platform == "win32":
      if excons.arch_dir == "x64":
        hfs = "C:/Program Files/Side Effects Software/Houdini %s" % ver
      else:
        hfs = "C:/Program Files (x86)/Side Effects Software/Houdini %s" % ver
    elif sys.platform == "darwin":
      hfs = "/Library/Frameworks/Houdini.framework/Versions/%s" % ver
    else:
      hfs = "/opt/hfs%s" % ver
  else:
    # retrive version from hfs
    m = verexp.search(hfs)
    if not m:
      ver = ARGUMENTS.get("houdini-ver", None)
      if not ver:
        if not noexc:
          raise Exception("Could not figure out houdini version from path \"%s\". Please provide it using houdini-ver=" % hfs)
        else:
          return (None, None)
    else:
      ver = m.group(0)
  
  if not os.path.isdir(hfs):
    if not noexc:
      raise Exception("Invalid Houdini directory: %s" % hfs)
    else:
      return (None, None)
  
  return (ver, hfs)

def Require(env):
  ver, hfs = GetVersionAndDirectory()
  
  # Call hcustom -c, hcustom -m to setup compile and link flags
  
  hcustomenv = os.environ.copy()
  hcustomenv["HFS"] = hfs
  if sys.platform == "win32":
    # Oldver version of hcustom on windows require MSVCDir to be set
    cmntools = "VS%sCOMNTOOLS" % env["MSVC_VERSION"].replace(".", "")
    if cmntools in hcustomenv:
      cmntools = hcustomenv[cmntools]
      if cmntools.endswith("\\") or cmntools.endswith("/"):
        cmntools = cmntools[:-1]
      cmntools = os.path.join(os.path.split(os.path.split(cmntools)[0])[0], "VC")
      hcustomenv["MSVCDir"] = cmntools
  
  if sys.platform != "darwin":
    hcustom = "%s/bin/hcustom" % hfs
  else:
    hcustom = "%s/Resources/bin/hcustom" % hfs
  
  cmd = "\"%s\" -c" % hcustom
  p = subprocess.Popen(cmd, shell=True, env=hcustomenv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  out, err = p.communicate()
  ccflags = out.strip()
  if not "DLLEXPORT" in ccflags:
    if sys.platform == "win32":
      ccflags += ' /DDLLEXPORT="__declspec(dllexport)"'
    else:
      ccflags += ' -DDLLEXPORT='
  
  cmd = "\"%s\" -m" % hcustom
  p = subprocess.Popen(cmd, shell=True, env=hcustomenv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  out, err = p.communicate()
  linkflags = out.strip()
  if sys.platform == "win32":
    linkflags = re.sub(r"-link\s+", "", linkflags)
  elif sys.platform != "darwin":
    # On linux, $HFS/dsolib doesn't seem appear in linkflags
    linkflags += " -L %s/dsolib" % hfs
  
  env.Append(CCFLAGS=" %s" % ccflags)
  env.Append(LINKFLAGS=" %s" % linkflags)
