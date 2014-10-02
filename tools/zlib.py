# Copyright (C) 2014  Gaetan Guidet
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

def Require(env):
  zlibinc, zliblib = excons.GetDirs("zlib")
  
  if zlibinc:
    env.Append(CPPPATH=[zlibinc])
  
  if zliblib:
    env.Append(LIBPATH=[zliblib])
  
  if str(Platform()) != "win32":
    env.Append(LIBS = ["z"])
  
  else:
    static = excons.GetArgument("zlib-static", None)
    if static is None:
      static = excons.GetArgument("static", "1")
    
    if int(static) == 0:
      env.Append(CPPDEFINES = ["ZLIB_DLL"])
      env.Append(LIBS = ["zdll"])
    else:
      env.Append(LIBS = ["zlib"])

