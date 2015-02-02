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

def PluginExt():
  if str(Platform()) == "darwin":
    return ".bundle"
  elif str(Platform()) == "win32":
    return ".mll"
  else:
    return ".so"

def Plugin(env):
  if not sys.platform in ["win32", "darwin"]:
    env.Append(LINKFLAGS = " -Wl,-Bsymbolic")

def GetMayaRoot(noWarn=False):
  mayaspec = excons.GetArgument("with-maya")
  
  if not mayaspec:
    if not noWarn:
      print("WARNING - Please set Maya version or directory using with-maya=")
    return None
  
  if not os.path.isdir(mayaspec):
    if not re.match(r"\d+(\.\d+)?", mayaspec):
      if not noWarn:
        print("WARNING - Invalid Maya specification \"%s\": Must be a directory or a version number" % mayaspec)
      return None
    ver = mayaspec
    if sys.platform == "win32":
      if excons.arch_dir == "x64":
        mayadir = "C:/Program Files/Autodesk/Maya%s" % ver
      else:
        mayadir = "C:/Program Files (x86)/Autodesk/Maya%s" % ver
    elif sys.platform == "darwin":
      mayadir = "/Applications/Autodesk/maya%s" % ver
    else:
      mayadir = "/usr/autodesk/maya%s" % ver
      if excons.arch_dir == "x64":
        mayadir += "-x64"
  
  else:
    mayadir = mayaspec

  return mayadir

def Version(asString=True):
  mayadir = GetMayaRoot(noWarn=True)
  if not mayadir:
    return (None if not asString else "")
  
  if sys.platform == "darwin":
    mayainc = os.path.join(mayadir, "devkit", "include")
  else:
    mayainc = os.path.join(mayadir, "include")
  
  mtypes = os.path.join(mayainc, "maya", "MTypes.h")
  
  if os.path.isfile(mtypes):
    defexp = re.compile(r"^\s*#define\s+MAYA_API_VERSION\s+([0-9]+)")
    f = open(mtypes, "r")
    for line in f.readlines():
      m = defexp.match(line)
      if m:
        return (int(m.group(1)) if not asString else m.group(1))
    f.close()
  
  return None

def Require(env):
  mayadir = GetMayaRoot()
  if not mayadir:
    return

  if sys.platform == "darwin":
    env.Append(CPPDEFINES = ["CC_GNU_", "OSMac_", "OSMacOSX_", "REQUIRE_IOSTREAM", "OSMac_MachO_", "_LANGUAGE_C_PLUS_PLUS"])
    env.Append(CPPPATH = ["%s/devkit/include" % mayadir])
    env.Append(CCFLAGS = " -include \"%s/devkit/include/maya/OpenMayaMac.h\" -fno-gnu-keywords" % mayadir)
    env.Append(LIBPATH = ["%s/Maya.app/Contents/MacOS" % mayadir])
    env.Append(LINKFLAGS = " -framework System -framework SystemConfiguration -framework CoreServices -framework Carbon -framework Cocoa -framework ApplicationServices -framework IOKit -framework OpenGL -framework AGL")
  else:
    env.Append(CPPPATH = ["%s/include" % mayadir])
    env.Append(LIBPATH = ["%s/lib" % mayadir])
    if sys.platform == "win32":
      env.Append(CPPDEFINES = ["NT_PLUGIN", "AW_NEW_IOSTREAMS", "TRUE_AND_FALSE_DEFINED", "_BOOL"])
      env.Append(LIBS = ["opengl32", "glu32"])
    else:
      env.Append(CPPDEFINES = ["UNIX", "_BOOL", "LINUX", "FUNCPROTO", "_GNU_SOURCE", "REQUIRE_IOSTREAM"])
      if "x64" in mayadir:
        env.Append(CPPDEFINES = ["Bits64_", "LINUX_64"])
      else:
        # ? who uses 32 bits application anyway...
        pass
      env.Append(CCFLAGS = " -fno-strict-aliasing -Wno-comment -Wno-sign-compare -funsigned-char -Wno-reorder -fno-gnu-keywords -ftemplate-depth-25 -pthread")
      env.Append(LIBS = ["GL", "GLU"])
  
  env.Append(LIBS = ["Foundation", "OpenMaya", "OpenMayaRender", "OpenMayaFX", "OpenMayaAnim", "OpenMayaUI"])


