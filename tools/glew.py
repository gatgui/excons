# Copyright (C) 2014~  Gaetan Guidet
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

def GetOptionsString():
  return """GLEW OPTIONS
  with-glew=<path>     : GLEW root directory.
  with-glew-inc=<path> : GLEW headers directory.     [<root>/include]
  with-glew-lib=<path> : GLEW libraries directory.   [<root>/lib]
  glew-name=<str>      : Override GLEW library name. []
                         (default library name is glew32 on windows, GLEW on osx/linux)
  glew-prefix=<str>    : GLEW library name prefix.   ['']
                         (ignored when glew-name is set)
  glew-suffix=<str>    : GLEW library name suffix.   ['']
                         (ignored when glew-name is set)
  glew-static=0|1      : Use GLEW static library.    [1]
                         (additional 's' suffix to library name unless glew-name is set)
  glew-noglu=0|1       : Don't use GLU.              [1]
  glew-mx=0|1          : Use GLEW MX variant.        [0]
                         (additional 'mx' suffix to library name unless glew-name is set)"""

def Require(env):
  glew_inc, glew_lib = excons.GetDirs("glew")
  glew_static = (excons.GetArgument("glew-static", 1, int) != 0)
  glew_no_glu = (excons.GetArgument("glew-noglu", 1, int) != 0)
  glew_mx = (excons.GetArgument("glew-mx", 0, int) != 0)
  
  if glew_inc:
    env.Append(CPPPATH=[glew_inc])
  
  if glew_lib:
    env.Append(LIBPATH=[glew_lib])
  
  defs = []
  
  if glew_no_glu:
    defs.append("GLEW_NO_GLU")
  
  if glew_static:
    defs.append("GLEW_STATIC")
  
  if glew_mx:
    defs.append("GLEW_MX")
  
  env.Append(CPPDEFINES=defs)

  glew_libname = excons.GetArgument("glew-name", None)
  if not glew_libname:
    glew_libprefix = excons.GetArgument("glew-prefix", "")
    glew_libsuffix = excons.GetArgument("glew-suffix", "")
    
    glew_libname = glew_libprefix + ("glew32" if sys.platform == "win32" else "GLEW") + glew_libsuffix
    
    if glew_mx:
      glew_libname += "mx"

    if sys.platform == "win32" and glew_static:
      glew_libname += "s"

  excons.Link(env, glew_libname, static=glew_static, force=True, silent=True)
  
  excons.AddHelpOptions(glew=GetOptionsString())
