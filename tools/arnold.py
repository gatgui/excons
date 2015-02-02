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
    return ".dylib"
  elif str(Platform()) == "win32":
    return ".dll"
  else:
    return ".so"

def Version(asString=True):
  arnoldinc, _ = excons.GetDirs("arnold", libdirname=("bin" if sys.platform != "win32" else "lib"))
  
  ai_version = os.path.join(arnoldinc, "ai_version.h")
  
  varch, vmaj, vmin, vpatch = 0, 0, 0, 0
  
  if os.path.isfile(ai_version):
    defexp = re.compile(r"^\s*#define\s+AI_VERSION_(ARCH_NUM|MAJOR_NUM|MINOR_NUM|FIX)\s+([^\s]+)")
    f = open(ai_version, "r")
    for line in f.readlines():
      m = defexp.match(line)
      if m:
        which = m.group(1)
        if which == "ARCH_NUM":
          varch = int(m.group(2))
        elif which == "MAJOR_NUM":
          vmaj = int(m.group(2))
        elif which == "MINOR_NUM":
          vmin = int(m.group(2))
        elif which == "FIX":
          m = re.search(r"\d+", m.group(2))
          vpatch = (0 if m is None else int(m.group(0)))
    f.close()
  
  rv = (varch, vmaj, vmin, vpatch)

  return ("%s.%s.%s.%s" % rv if asString else rv)

def Require(env):
  arnoldinc, arnoldlib = excons.GetDirs("arnold", libdirname=("bin" if sys.platform != "win32" else "lib"))
  
  if arnoldinc:
    env.Append(CPPPATH = [arnoldinc])
  if arnoldlib:
    env.Append(LIBPATH = [arnoldlib])
  env.Append(LIBS = ["ai"])

