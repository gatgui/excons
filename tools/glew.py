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
  glewinc, glewlib = excons.GetDirs("glew")
  glew_static = (excons.GetArgument("glew-static", 1, int) != 0)
  glew_no_glu = (excons.GetArgument("glew-noglu", 1, int) != 0)
  glew_mx = (excons.GetArgument("glew-mx", 0, int) != 0)
  glewlibsuffix = excons.GetArgument("glew-libsuffix", "")
  
  if glewinc:
    env.Append(CPPPATH=[glewinc])
  
  if glewlib:
    env.Append(LIBPATH=[glewlib])
  
  defs = []
  
  if glew_no_glu:
    defs.append("GLEW_NO_GLU")
  
  if glew_static:
    defs.append("GLEW_STATIC")
  
  if glew_mx:
    defs.append("GLEW_MX")
  
  env.Append(CPPDEFINES=defs)
  
  lib = "%s%s" % (("GLEW" if not glew_mx else "GLEW"), glewlibsuffix)
  
  env.Append(LIBS=[lib])
