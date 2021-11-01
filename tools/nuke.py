# MIT License
#
# Copyright (c) 2010 Gaetan Guidet
#
# This file is part of excons.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import sys
import excons
import re
import os
import SCons.Script # pylint: disable=import-error

# pylint: disable=bad-indentation


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
