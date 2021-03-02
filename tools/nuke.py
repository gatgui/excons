# Copyright (C) 2010~  Gaetan Guidet
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

import sys
import excons
import re
import os
import SCons.Script # pylint: disable=import-error


def GetOptionsString():
  return """NUKE OPTIONS
  with-nuke=<str> : Nuke version or install directory []"""

def PluginExt():
  if str(SCons.Script.Platform()) == "darwin":
    return ".dylib"
  elif str(SCons.Script.Platform()) == "win32":
    return ".dll"
  else:
    return ".so"

def Require(env):
  excons.AddHelpOptions(nuke=GetOptionsString())

  nukespec = excons.GetArgument("with-nuke")
  
  if nukespec is None:
    excons.WarnOnce("Please set Nuke version or directory using with-nuke=", tool="nuke")
    return
  
  idn = ("Contents/MacOS/include" if sys.platform == "darwin" else "include")
  ldn = ("Contents/MacOS" if sys.platform == "darwin" else "")
  
  if os.path.isdir(nukespec):
    if sys.platform == "darwin":
      bn = os.path.basename(nukespec)
      _, ext = os.path.splitext(bn)
      if ext != ".app":
        nukespec += "/%s.app" % bn
        excons.SetArgument("with-nuke", nukespec)
    
    ndkinc, ndklib = excons.GetDirs("nuke", incdirname=idn, libdirname=ldn, libdirarch="none")
  
  else:
    if not re.match(r"\d+\.\d+v\d+", nukespec):
      excons.WarnOnce("Invalid Nuke version format: \"%s\"" % nukespec, tool="nuke")
      return
    
    if sys.platform == "win32":
      ndkbase = "C:/Program Files/Nuke%s" % nukespec
    elif sys.platform == "darwin":
      ndkbase = "/Applications/Nuke%s/Nuke%s.app" % (nukespec, nukespec)
    else:
      ndkbase = "/usr/local/Nuke%s" % nukespec
    
    ndkinc = "%s/%s" % (ndkbase, idn)
    ndklib = "%s/%s" % (ndkbase, ldn) if ldn else ndkbase
  
  if ndkinc:
    env.Append(CPPPATH=[ndkinc])
  
  if ndklib:
    env.Append(LIBPATH=[ndklib])
  
  if sys.platform == "darwin":
    #env.Append(CCFLAGS=" -isysroot /Developer/SDKs/MacOSX10.4u.sdk")
    #env.Append(LINKFLAGS=" -Wl,-syslibroot,/Developer/SDKs/MacOSX10.4u.sdk")
    #env.Append(LINKFLAGS=" -framework QuartzCore -framework IOKit -framework CoreFoundation -framework Carbon -framework ApplicationServices -framework OpenGL -framework AGL -framework Quicktime")
    pass
  
  env.Append(DEFINES=["USE_GLEW"])
  
  if sys.platform != "win32":
    env.Append(CCFLAGS=" -Wno-unused-variable -Wno-unused-parameter")
    env.Append(LIBS=["DDImage", "GLEW"])
  
  else:
    env.Append(LIBS=["DDImage", "glew32"])
