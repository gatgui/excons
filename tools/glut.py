# Copyright (C) 2009, 2010  Gaetan Guidet
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
import sys
import excons
import excons.tools.gl as gl

def Require(env):
  gl.Require(env)
  
  glutinc = ARGUMENTS.get("with-glut-inc", None)
  glutlib = ARGUMENTS.get("with-glut-lib", None)
  glutdir = ARGUMENTS.get("with-glut", None)
  
  if glutdir:
    if glutinc is None:
      glutinc = os.path.join(glutdir, "include")
    if glutlib is None:
      if sys.platform == "win32":
        if excons.Build64():
          glutlib = os.path.join(glutdir, "lib", "x64")
        else:
          glutlib = os.path.join(glutdir, "lib", "x86")
      else:
        glutlib = os.path.join(glutdir, "lib")
  
  if glutinc is None or glutlib is None:
    print("WARNING - You may want to set GLUT include/library directories using with-glut=, with-glut-inc, with-glut-lib")

  if glutinc and not os.path.isdir(glutinc):
    print("WARNING - Invalid GLUT include directory: \"%s\"" % glutinc)
    return

  if glutlib and not os.path.isdir(glutlib):
    print("WARNING - Invalid GLUT library directory: \"%s\"" % glutlib)
    return

  if glutinc:
    env.Append(CPPPATH=[glutinc])
  if glutlib:
    env.Append(LIBPATH=[glutlib])
  
  if sys.platform == "win32":
    env.Append(CPPDEFINES=["GLUT_NO_LIB_PRAGMA"])
    if excons.Build64():
      env.Append(LIBS = ["glut64"])
    else:
      env.Append(LIBS = ["glut32"])
  elif sys.platform == "darwin":
    env.Append(LINKFLAGS = " -framework GLUT")
  else:
    env.Append(LIBS = ["glut"])


