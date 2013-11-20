# Copyright (C) 2010  Gaetan Guidet
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
import sys

def PluginExt():
  if str(Platform()) == "darwin":
    return ".dylib"
  elif str(Platform()) == "win32":
    return ".dll"
  else:
    return ".so"

def Require(env):
  idn = ("Contents/MacOS/include" if sys.platform == "darwin" else "include")
  ndkinc, ndklib = excons.GetDirs("nuke", incdirname=idn, libdirname="", libdirarch="none")
  
  if ndkinc:
    env.Append(CPPPATH=[ndkinc])
  
  if ndklib:
    env.Append(LIBPATH=[ndklib])
  
  if sys.platform == "darwin":
    #env.Append(CCFLAGS=" -isysroot /Developer/SDKs/MacOSX10.4u.sdk")
    #env.Append(LINKFLAGS=" -Wl,-syslibroot,/Developer/SDKs/MacOSX10.4u.sdk")
    #env.Append(LINKFLAGS=" -framework QuartzCore -framework IOKit -framework CoreFoundation -framework Carbon -framework ApplicationServices -framework OpenGL -framework AGL -framework Quicktime")
    pass
  
  env.Append(DEFINES = ["USE_GLEW"])
  if sys.platform != "win32":
    env.Append(CCFLAGS = " -Wno-unused-variable -Wno-unused-parameter")
    env.Append(LIBS = ["DDImage", "GLEW"])
  else:
    env.Append(LIBS = ["DDImage", "glew32"])



