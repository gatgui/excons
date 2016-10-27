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

_maya_mscver = {"2013": "9.0",
                "2013.5": "9.0",
                "2014": "10.0",
                "2015": "11.0",
                "2016": "11.0",
                "2016.5": "11.0",
                "2017": "11.0"}

def SetupMscver():
  mayaver = Version(nice=True)
  if sys.platform == "win32":
    mscver = ARGUMENTS.get("mscver", None)
    if mscver is None:
      mscver = _maya_mscver.get(mayaver, None)
      if mscver is not None:
        print("Using msvc %s" % mscver)
        ARGUMENTS["mscver"] = mscver

def PluginExt():
  if str(Platform()) == "darwin":
    return ".bundle"
  elif str(Platform()) == "win32":
    return ".mll"
  else:
    return ".so"

def Plugin(env):
  if not sys.platform in ["win32", "darwin"]:
    env.Append(LINKFLAGS=" -Wl,-Bsymbolic")

def GetMayaRoot(noWarn=False):
  mayaspec = excons.GetArgument("with-maya")
  
  if "MAYA_LOCATION" in os.environ:
    if not "with-maya" in ARGUMENTS:
      # MAYA_LOCATION environment is set and with-maya is either undefined or read from cache
      excons.PrintOnce("Using MAYA_LOCATION environment.", tool="maya")
      mayadir = os.environ["MAYA_LOCATION"]
      return mayadir
    else:
      excons.PrintOnce("Ignoring MAYA_LOCATION environment.", tool="maya")
  
  if not mayaspec:
    if not noWarn:
      excons.WarnOnce("Please set Maya version or directory using with-maya=", tool="maya")
    return None
  
  if not os.path.isdir(mayaspec):
    if not re.match(r"\d+(\.\d+)?", mayaspec):
      if not noWarn:
        excons.WarnOnce("Invalid Maya specification \"%s\": Must be a directory or a version number" % mayaspec, tool="maya")
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
      if excons.arch_dir == "x64" and os.path.isdir(mayadir+"-x64"):
        mayadir += "-x64"
  
  else:
    mayadir = mayaspec.replace("\\", "/")
    if len(mayadir) > 0 and mayadir[-1] == "/":
      mayadir = mayadir[:-1]

  return mayadir

def GetMayaInc(mayadir):
  # Starting maya 2016, the base install doesn't come with include files
  require_mdk = False
  if sys.platform == "darwin":
    require_mdk = not os.path.isdir(mayadir + "/devkit/include/maya")
  else:
    require_mdk = not os.path.isdir(mayadir + "/include/maya")
  
  mdk = (None if not require_mdk else excons.GetArgument("with-mayadevkit"))
  
  if "MAYA_INCLUDE" in os.environ:
    if not require_mdk or "with-mayadevkit" not in ARGUMENTS:
      # MAYA_INCLUDE environment is set and maya is older than 2016 or with-mayadevkit is either undefined or read from cache
      excons.PrintOnce("Using MAYA_INCLUDE environment.", tool="maya")
      mayainc = os.environ["MAYA_INCLUDE"]
      return mayainc
    else:
      excons.PrintOnce("Ignoring MAYA_INCLUDE environment.", tool="maya")
  
  if mdk is None:
    if sys.platform == "darwin":
      mayainc = mayadir + "/devkit/include"
    else:
      mayainc = mayadir + "/include"
  
  else:
    mdk = mdk.replace("\\", "/")
    if len(mdk) > 0 and mdk[-1] == "/":
      mdk = mdk[:-1]
    
    if os.path.isabs(mdk):
      mayainc = mdk + "/include"
    else:
      mayainc = mayadir + "/" + mdk + "/include"
  
  return mayainc

def Version(asString=True, nice=False):
  mayadir = GetMayaRoot(noWarn=True)
  if not mayadir:
    return (None if not asString else "")
  
  mayainc = GetMayaInc(mayadir)
  
  mtypes = os.path.join(mayainc, "maya", "MTypes.h")
  
  if os.path.isfile(mtypes):
    defexp = re.compile(r"^\s*#define\s+MAYA_API_VERSION\s+([0-9]+)")
    f = open(mtypes, "r")
    for line in f.readlines():
      m = defexp.match(line)
      if m:
        if nice:
          year = int(m.group(1)[:4])
          sub = int(m.group(1)[5])
          # Maya 2013 and 2016 have a binary incompatible .5 version
          if sub >= 5 and year in (2013, 2016):
            return (year+0.5 if not asString else "%d.5" % year)
          else:
            return (year if not asString else str(year))
        else:
          return (int(m.group(1)) if not asString else m.group(1))
    f.close()
  
  return None

def Require(env):
  mayadir = GetMayaRoot()
  if not mayadir:
    return

  env.Append(CPPPATH=[GetMayaInc(mayadir)])
  
  if sys.platform == "darwin":
    env.Append(CPPDEFINES=["CC_GNU_", "OSMac_", "OSMacOSX_", "REQUIRE_IOSTREAM", "OSMac_MachO_", "_LANGUAGE_C_PLUS_PLUS"])
    mach = "%s/maya/OpenMayaMac.h" % GetMayaInc(mayadir)
    if os.path.isfile(mach):
      env.Append(CCFLAGS=" -include \"%s\" -fno-gnu-keywords" % mach)
    env.Append(LIBPATH=["%s/Maya.app/Contents/MacOS" % mayadir])
    env.Append(LINKFLAGS=" -framework System -framework SystemConfiguration -framework CoreServices -framework Carbon -framework Cocoa -framework ApplicationServices -framework IOKit -framework OpenGL -framework AGL")
  
  else:
    env.Append(LIBPATH=["%s/lib" % mayadir])
    
    if sys.platform == "win32":
      env.Append(CPPDEFINES=["NT_PLUGIN", "AW_NEW_IOSTREAMS", "TRUE_AND_FALSE_DEFINED", "_BOOL"])
      env.Append(LIBS=["opengl32", "glu32"])
    
    else:
      env.Append(CPPDEFINES=["UNIX", "_BOOL", "LINUX", "FUNCPROTO", "_GNU_SOURCE", "REQUIRE_IOSTREAM"])
      
      if "x64" in mayadir:
        env.Append(CPPDEFINES=["Bits64_", "LINUX_64"])
      
      else:
        # ? who uses 32 bits application anyway...
        pass
      
      env.Append(CCFLAGS=" -fno-strict-aliasing -Wno-comment -Wno-sign-compare -funsigned-char -Wno-reorder -fno-gnu-keywords -ftemplate-depth-25 -pthread")
      env.Append(LIBS=["GL", "GLU"])
  
  env.Append(LIBS=["Foundation", "OpenMaya", "OpenMayaRender", "OpenMayaFX", "OpenMayaAnim", "OpenMayaUI"])
