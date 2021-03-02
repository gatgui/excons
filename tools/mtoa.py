# Copyright (C) 2017~  Gaetan Guidet
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

import SCons.Script # pylint: disable=import-error
import excons
import sys
import re
import os

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
