# MIT License
#
# Copyright (c) 2017 Gaetan Guidet
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


import SCons.Script # pylint: disable=import-error
import excons
import sys
import re
import os

# pylint: disable=bad-indentation


def GetOptionsString():
   return """MTOA OPTIONS
  with-mtoa=<path>     : MtoA root.
  with-mtoa-inc=<path> : MtoA headers directory.   [<root>/include]
  with-mtoa-lib=<path> : MtoA libraries directory. [<root>/bin or <root>/lib]"""

def ExtensionExt():
  if str(SCons.Script.Platform()) == "darwin":
    return ".dylib"
  elif str(SCons.Script.Platform()) == "win32":
    return ".dll"
  else:
    return ".so"

def Version(asString=True, compat=False):
   mtoa_inc, mtoa_lib = excons.GetDirs("mtoa", libdirname=("lib" if sys.platform == "win32" else "bin"))
   if mtoa_inc and mtoa_lib:
      versionh = excons.joinpath(mtoa_inc, "utils", "Version.h")
      varch, vmaj, vmin = 0, 0, 0
      if os.path.isfile(versionh):
         defexp = re.compile(r"^\s*#define\s+MTOA_(ARCH|MAJOR|MINOR)_VERSION_NUM\s+([^\s]+)")
         f = open(versionh, "r")
         for line in f.readlines():
            m = defexp.match(line)
            if m:
               which = m.group(1)
               if which == "ARCH":
                  varch = int(m.group(2))
               elif which == "MAJOR":
                  vmaj = int(m.group(2))
               elif which == "MINOR":
                  vmin = int(m.group(2))
         f.close()
      if compat:
         rv = (varch, vmaj)
         return ("%s.%s" % rv if asString else rv)
      else:
         rv = (varch, vmaj, vmin)
         return ("%s.%s.%s" % rv if asString else rv)
   else:
      if compat:
         return ("0.0" if asString else (0, 0))
      else:
         return ("0.0.0" if asString else (0, 0, 0))

def Require(env):
   mtoa_inc, mtoa_lib = excons.GetDirs("mtoa", libdirname=("lib" if sys.platform == "win32" else "bin"))
   if sys.platform == "darwin":
      env.Append(CPPDEFINES=["_DARWIN"])
   elif sys.platform == "win32":
      env.Append(CPPDEFINES=["_WIN32"])
   else:
      env.Append(CPPDEFINES=["_LINUX"])
   env.Append(CPPPATH=[mtoa_inc])
   env.Append(LIBPATH=[mtoa_lib])
   excons.Link(env, "mtoa_api", static=False, force=True, silent=True)
   excons.AddHelpOptions(mtoa=GetOptionsString())
