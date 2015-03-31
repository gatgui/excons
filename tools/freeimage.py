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
import os
import sys
import excons

def Require(env):
  fiinc, filib = excons.GetDirs("freeimage")
  
  if fiinc:
    env.Append(CPPPATH=[fiinc])
  
  if filib:
    env.Append(LIBPATH=[filib])
  
  if excons.GetArgument("freeimage-static", 0, int) != 0:
    env.Append(CPPDEFINES=["FREEIMAGE_LIB"])
  
  env.Append(LIBS = ["freeimage"])

