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

import SCons.Script # pylint: disable=import-error
import excons

def GetOptionsString():
  return """ZLIB OPTIONS
  with-zlib=<path>     : Zlib root directory.
  with-zlib-inc=<path> : Zlib headers directory.           [<root>/include]
  with-zlib-lib=<path> : Zlib libraries directory.         [<root>/lib]
  zlib-static=0|1      : Link Zlib statically.             [0]
  zlib-name=<str>      : Override Zlib library name.       []
                         (default name is 'z' on osx and linux, 'zlib' (static) or 'zdll' (shared) on windows)
  zlib-prefix=<str>    : Default Zlib library name prefix. []
                         (ignored when zlib-name is set)
  zlib-suffix=<str>    : Default Zlib library name suffix. []
                         (ignored when zlib-name is set)"""
                         

def Require(env):
  zlibinc, zliblib = excons.GetDirs("zlib")
  
  if zlibinc:
    env.Append(CPPPATH=[zlibinc])
  
  if zliblib:
    env.Append(LIBPATH=[zliblib])
  
  static = (excons.GetArgument("zlib-static", 0, int) != 0)

  if str(SCons.Script.Platform()) != "win32":
    zlib_name = excons.GetArgument("zlib-name", None)
    if not zlib_name:
      zlib_name = "%sz%s" % (excons.GetArgument("zlib-prefix", ""), excons.GetArgument("zlib-suffix", ""))
  
  else:
    if static:
      zlib_name = excons.GetArgument("zlib-name", None)
      if not zlib_name:
        zlib_name = "zlib%s" % excons.GetArgument("zlib-suffix", "")
    
    else:
      zlib_name = excons.GetArgument("zlib-name", None)
      if not zlib_name:
        zlib_name = "zdll%s" % excons.GetArgument("zlib-suffix", "")
      
      env.Append(CPPDEFINES=["ZLIB_DLL"])
  
  excons.Link(env, zlib_name, static=static, force=True, silent=True)
  
  excons.AddHelpOptions(zlib=GetOptionsString())

