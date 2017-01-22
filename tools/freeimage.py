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
import excons

def GetOptionsString():
  return """FREEIMAGE OPTIONS
  with-freeimage=<path>     : FreeImage prefix                []
  with-freeimage-inc=<path> : FreeImage headers directory     [<prefix>/include]
  with-freeimage-lib=<path> : FreeImage libraries directory   [<prefix>/lib]
  freeimage-static=0|1      : Link FreeImage static lib       [0]
  freeimage-libname=<str>   : Override FreeImage library name []
  freeimage-libsuffix=<str> : FreeImage library suffix        ['']
                              (ignored when freeimage-libname is set)"""

def Require(env):
  fiinc, filib = excons.GetDirs("freeimage")
  
  if fiinc:
    env.Append(CPPPATH=[fiinc])
  
  if filib:
    env.Append(LIBPATH=[filib])
  
  static = (excons.GetArgument("freeimage-static", 0, int) != 0)
  if static:
    env.Append(CPPDEFINES=["FREEIMAGE_LIB"])
  
  filibname = excons.GetArgument("freeimage-libname", None)
  if not filibname:
    filibsuffix = excons.GetArgument("freeimage-libsuffix", "")
    filibname = "freeimage%s" % filibsuffix
  
  if not static or not excons.StaticallyLink(env, filibname):
    env.Append(LIBS=[filibname])
  
  excons.AddHelpOptions(freeimage=GetOptionsString())
