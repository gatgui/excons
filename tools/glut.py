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

def GetOptionsString():
  return """GLUT OPTIONS
  with-glut=<path>     : GLUT prefix                []
  with-glut-inc=<path> : GLUT headers directory     [<prefix>/include]
  with-glut-lib=<path> : GLUT libraries directory   [<prefix>/lib]
  glut-libname=<str>   : Override GLUT library name []
  glut-libsuffix=<str> : GLUT library suffix        ['']
                         (ignored when glut-libname is set)
                         (default library name is glut32/glut64 on windows, glut on linux)
  glut-static=0|1      : Use GLUT static library    [1]
                         (additional 's' suffix to library name unless glut-libname is set)

  On OSX, library related options are ignored as the GLUT framework is used"""

def Require(env):
  glutinc, glutlib = excons.GetDirs("glut")
  
  if glutinc:
    env.Append(CPPPATH=[glutinc])
  
  if glutlib:
    env.Append(LIBPATH=[glutlib])
  
  static = (excons.GetArgument("glut-static", 0, int) != 0)

  libname = excons.GetArgument("glut-libname", "")
  if not libname:
    libsuffix = excons.GetArgument("glut-libsuffix", "")
    if sys.platform == "win32":
      libname = ("glut64" if excons.Build64() else "glut32") + libsuffix
    else:
      libname = "glut%s" % libsuffix

  if sys.platform == "win32":
    env.Append(CPPDEFINES=["GLUT_NO_LIB_PRAGMA"])
    env.Append(LIBS=[libname])
  
  elif sys.platform == "darwin":
    env.Append(LINKFLAGS=" -framework GLUT")
  
  else:
    if not static or not excons.StaticallyLink(env, libname):
      env.Append(LIBS=[libname])
  
  excons.AddHelpOptions(glut=GetOptionsString())
