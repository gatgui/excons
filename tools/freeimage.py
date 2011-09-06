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
import platform

def Require(env):
  fiinc = None
  filib = None
  
  fidir = ARGUMENTS.get("with-freeimage", None)
  
  if fidir != None:
    fiinc = os.path.join(fidir, "include")
    if str(Platform()) == "win32":
      if platform.architecture()[0] == "32bit":
        filib = os.path.join(fidir, "lib", "x86")
      else:
        filib = os.path.join(fidir, "lib", "x64")
    else:
      filib = os.path.join(fidir, "lib")
  else:
    fiinc = ARGUMENTS.get("with-freeimage-inc", None)
    filib = ARGUMENTS.get("with-freeimage-lib", None)
  
  if fiinc != None:
    env.Append(CPPPATH=[fiinc])
  
  if filib != None:
    env.Append(LIBPATH=[filib])
  
  env.Append(LIBS = ["freeimage"])


def RequireStatic(env):
  Require(env)
  env.Append(CPPDEFINES=["FREEIMAGE_LIB"])


