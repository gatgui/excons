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

def PluginExt():
  if str(Platform()) == "darwin":
    return ".bundle"
  elif str(Platform()) == "win32":
    return ".dll"
  else:
    return ".so"

def Require(env):
  mayadir = ARGUMENTS.get("with-maya", None)
  
  if not mayadir:
    ver = ARGUMENTS.get("maya-ver", None)
    if not ver:
      raise Exception("Please set maya version using maya-ver=")
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
        maya += "-x64"
  
  if sys.platform == "darwin":
    env.Append(CPPDEFINES = ["CC_GNU_", "OSMac_", "OSMacOSX_", "REQUIRE_IOSTREAM", "OSMac_MachO_", "_LANGUAGE_C_PLUS_PLUS"])
    env.Append(CPPPATH = ["%s/devkit/include" % mayadir])
    env.Append(CCFLAGS = " -O3 -include \"%s/devkit/include/maya/OpenMayaMac.h\" -fno-gnu-keywords" % mayadir)
    env.Append(LIBPATH = ["%s/Maya.app/Contents/MacOS" % mayadir])
    env.Append(LINKFLAGS = " -framework System -framework SystemConfiguration -framework CoreServices -framework Carbon -framework Cocoa -framework ApplicationServices -framework IOKit -framework OpenGL -framework AGL")
  else:
    env.Append(CPPPATH = ["%s/include" % mayadir])
    env.Append(LIBPATH = ["%s/lib" % mayadir])
    if sys.platform == "win32":
      # TODO
      pass
    else:
      # TODO
      pass
  env.Append(LIBS = ["Foundation", "OpenMaya", "OpenMayaRender", "OpenMayaFX", "OpenMayaAnim", "OpenMayaUI"])


