# Copyright (C) 2013  Gaetan Guidet
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
import sys

def PluginExt():
  if str(Platform()) == "darwin":
    return ".dylib"
  elif str(Platform()) == "win32":
    return ".dll"
  else:
    return ".so"

def Require(env):
  arnoldinc = ARGUMENTS.get("with-arnold-inc", None)
  arnoldlib = ARGUMENTS.get("with-arnold-lib", None)
  arnolddir = ARGUMENTS.get("with-arnold", None)
  
  if arnolddir:
    if arnoldinc is None:
      arnoldinc = "%s/include" % arnolddir
    if arnoldlib is None:
      if sys.platform == "win32":
        arnoldlib = "%s/lib" % arnolddir
      else:
        arnoldlib = "%s/bin" % arnolddir
  
  if not arnoldinc or not os.path.isdir(arnoldinc):
    raise Exception("Invalid Arnold directory: %s" % arnoldinc)
  
  if not arnoldlib or not os.path.isdir(arnoldlib):
    raise Exception("Invalid Arnold directory: %s" % arnoldlib)
  
  env.Append(CPPPATH = [arnoldinc])
  env.Append(LIBPATH = [arnoldlib])
  env.Append(LIBS = ["ai"])

