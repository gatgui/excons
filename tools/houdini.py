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
  hspec = excons.GetArgument("with-houdini")
  
  if hspec is None:
    msg = "Please set Houdini version or directory using with-houdini="
    if not noexc:
      raise Exception(msg)
    else:
      print("WARNING - %s" % msg)
      return (None, None)
  
  if not os.path.isdir(hspec):
    ver = hspec
    if not verexp.match(ver):
      msg = "Invalid Houdini version format: \"%s\"" % ver
      if not noexc:
        raise Exception(msg)
      else:
        print("WARNING - %s" % msg)
        return (None, None)
    if sys.platform == "win32":
      if excons.arch_dir == "x64":
        hfs = "C:/Program Files/Side Effects Software/Houdini %s" % ver
      else:
        hfs = "C:/Program Files (x86)/Side Effects Software/Houdini %s" % ver
    elif sys.platform == "darwin":
      hfs = "/Library/Frameworks/Houdini.framework/Versions/%s/Resources" % ver
    else:
      hfs = "/opt/hfs%s" % ver
  
  else:
    # retrive version from hfs
    hfs = hspec
    m = verexp.search(hfs)
    if not m:
      msg = "Could not figure out houdini version from path \"%s\". Please provide it using houdini-ver=" % hfs
      if not noexc:
        raise Exception(msg)
      else:
        print("WARNING - %s" % msg)
        return (None, None)
    else:
      ver = m.group(0)
    
    if sys.platform == "darwin":
      # Path specified by with-houdini should point the the version folder
      # Append the "Resources" as is expected in HFS environment variable
      hfs += "/Resources"
  
  if not os.path.isdir(hfs):
    msg = "Invalid Houdini directory: %s" % hfs
    if not noexc:
      raise Exception(msg)
    else:
      print("WARNING - %s" % msg)
      return (None, None)
  
  return (ver, hfs)

def Require(env):
  ver, hfs = GetVersionAndDirectory(noexc=True)
  if not ver or not hfs:
    return
  
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
  
  hcustom = "%s/bin/hcustom" % hfs
  
  cmd = "\"%s\" -c" % hcustom
  p = subprocess.Popen(cmd, shell=True, env=hcustomenv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  out, err = p.communicate()
  ccflags = out.strip()
  if not "DLLEXPORT" in ccflags:
    if sys.platform == "win32":
      ccflags += ' /DDLLEXPORT="__declspec(dllexport)"'
    else:
      ccflags += ' -DDLLEXPORT='
  if sys.platform != "win32":
    if int(ver.split(".")[0]) >= 14:
      if not "-std=c++11" in ccflags:
        ccflags += ' -DBOOST_NO_DEFAULTED_FUNCTIONS -DBOOST_NO_DELETED_FUNCTIONS'
  
  cmd = "\"%s\" -m" % hcustom
  p = subprocess.Popen(cmd, shell=True, env=hcustomenv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  out, err = p.communicate()
  linkflags = out.strip()
  if sys.platform == "win32":
    linkflags = re.sub(r"-link\s+", "", linkflags)
  elif sys.platform != "darwin":
    # On linux, $HFS/dsolib doesn't seem appear in linkflags
    linkflags += " -L %s/dsolib" % hfs
  else:
    # On OSX, linkflags does not provide frameworks or libraries to link
    libs = ["HoudiniUI", "HoudiniOPZ", "HoudiniOP3", "HoudiniOP2", "HoudiniOP1",
            "HoudiniSIM", "HoudiniGEO", "HoudiniPRM", "HoudiniUT"]
    
    libdir = "%s/Libraries" % "/".join(hfs.split("/")[:-1])
    linkflags += " -flat_namespace -L %s -l%s" % (libdir, " -l".join(libs))
  
  env.Append(CCFLAGS=" %s" % ccflags)
  env.Append(LINKFLAGS=" %s" % linkflags)
