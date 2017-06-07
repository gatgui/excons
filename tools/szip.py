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

def GetOptionsString():
  return """SZIP OPTIONS
  with-szip=<path>     : SZIP prefix                []
  with-szip-inc=<path> : SZIP headers directory     [<prefix>/include]
  with-szip-lib=<path> : SZIP libraries directory   [<prefix>/lib]
  szip-name=<str>      : Override SZIP library name []
                         (default library name is libszip on windows, sz on linux)
  szip-suffix=<str>    : SZIP library suffix        ['']
                         (ignored when szip-name is set)
  szip-static=0|1      : Use SZIP static library    [1]"""

def Require(env):
  szip_inc, szip_lib = excons.GetDirs("szip")
  
  if szip_inc:
    env.Append(CPPPATH=[szip_inc])
  
  if szip_lib:
    env.Append(LIBPATH=[szip_lib])
  
  szip_static = (excons.GetArgument("szip-static", 0, int) == 0)

  if szip_static:
    env.Append(CPPDEFINES=["SZ_BUILT_AS_DYNAMIC_LIB"])
  
  szip_libname = excons.GetArgument("szip-name", None)
  if not szip_libname:
    szip_libsuffix = excons.GetArgument("szip_suffix", "")
    szip_libname = "%s%s" % (("sz" if sys.platform != "win32" else "libszip"), szip_libsuffix)
  
  excons.Link(env, szip_libname, static=szip_static, force=True, silent=True)
