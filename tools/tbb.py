# Copyright (C) 2015  Gaetan Guidet
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
  return """TBB OPTIONS
  with-tbb=<path>     : TBB prefix
  with-tbb-inc=<path> : TBB headers directory     [<prefix>/include]
  with-tbb-lib=<path> : TBB libraries directory   [<prefix>/lib]
  tbb-static=0|1      : Link static library       [0]
  tbb-libname=<str>   : Override TBB library name []
  tbb-libsuffix=<str> : TBB library suffix        ['']
                        (ignored when tbb-libname is set)
"""

def Require(env):
  tbbinc, tbblib = excons.GetDirs("tbb")
  
  if tbbinc:
    env.Append(CPPPATH=[tbbinc])
  
  if tbblib:
    env.Append(LIBPATH=[tbblib])
  
  static = (excons.GetArgument("tbb-static", 0, int) != 0)
  # Any specific defines?
  #env.Append(CPPDEFINES=[])
  
  tbblibname = excons.GetArgument("tbb-libname", None)
  if not tbblibname:
    tbblibname = "tbb%s" % excons.GetArgument("tbb-libsuffix", "")
  
  if not static or not excons.StaticallyLink(env, tbblibname):
    env.Append(LIBS=[tbblibname])
