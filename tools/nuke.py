# Copyright (C) 2009  Gaetan Guidet
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
import platform

def PluginExt():
  if str(Platform()) == "darwin":
    return ".dylib"
  elif str(Platform()) == "win32":
    return ".dll"
  else:
    return ".so"

def Require(env):
  ndkinc = None
  ndklib = None
  
  ndkdir = ARGUMENTS.get("with-nuke", None)
  
  if ndkdir != None:
    if str(Platform()) == "darwin":
      ndkdir = os.path.join(ndkdir, "Contents", "MacOS")
      ndkinc = os.path.join(ndkdir, "include")
      ndklib = ndkdir
    else:
      ndklib = ndkdir
      ndkinc = os.path.join(ndkdir, "include")
  else:
    ndkinc = ARGUMENTS.get("with-nuke-inc", None)
    ndklib = ARGUMENTS.get("with-nuke-lib", None)
  
  if ndkinc != None:
    env.Append(CPPPATH=[ndkinc])
  
  if ndklib != None:
    env.Append(LIBPATH=[ndklib])
  
  if str(Platform()) == "darwin":
    #env.Append(CCFLAGS=" -isysroot /Developer/SDKs/MacOSX10.4u.sdk")
    #env.Append(LINKFLAGS=" -Wl,-syslibroot,/Developer/SDKs/MacOSX10.4u.sdk")
    #env.Append(LINKFLAGS=" -framework QuartzCore -framework IOKit -framework CoreFoundation -framework Carbon -framework ApplicationServices -framework OpenGL -framework AGL -framework Quicktime")
    pass
  
  env.Append(DEFINES = ["USE_GLEW"])
  if str(Platform()) != "win32":
    env.Append(LIBS = ["DDImage", "GLEW"])
  else:
    env.Append(LIBS = ["DDImage", "glew32"])
