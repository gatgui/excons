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
import excons.tools.gl as gl
#import platform

def Require(env):
  gl.Require(env)
  glutinc = None
  glutlib = None
  glutdir = ARGUMENTS.get("with-glut", None)
  if glutdir != None:
    glutinc = os.path.join(glutdir, "include")
    if str(Platform()) == "win32":
      #if platform.architecture()[0] == "32bit":
      if env["TARGET_ARCH"] == "x86":
        glutlib = os.path.join(glutdir, "lib", "x86")
      else:
        glutlib = os.path.join(glutdir, "lib", "x64")
    else:
      glutlib = os.path.join(glutdir, "lib")
  else:
    glutinc = ARGUMENTS.get("with-glut-inc", None)
    glutlib = ARGUMENTS.get("with-glut-lib", None)
  if glutinc != None:
    env.Append(CPPPATH=[glutinc])
  if glutlib != None:
    env.Append(LIBPATH=[glutlib])
  if str(Platform()) == "win32":
    env.Append(CPPDEFINES=["GLUT_NO_LIB_PRAGMA"])
    #if platform.architecture()[0] == "32bit":
    if env["TARGET_ARCH"] == "x86":
      env.Append(LIBS = ["glut32"])
    else:
      env.Append(LIBS = ["glut64"])
  elif str(Platform()) == "darwin":
    env.Append(LINKFLAGS = " -framework GLUT")
  else:
    env.Append(LIBS = ["glut"])


