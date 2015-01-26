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
import glob
import sys

def FindFileIn(filename, directory):
  for item in glob.glob(directory+"/*"):
    if os.path.isdir(item):
      rv = FindFileIn(filename, item)
      if rv is not None:
        return rv
    else:
      basename = os.path.basename(item)
      if basename.lower() == filename:
        return directory
  return None

def PluginExt():
  if str(Platform()) == "darwin":
    return ".bundle"
  elif str(Platform()) == "win32":
    return ".dll"
  else:
    return ".so"

def Require(env):
  vrayinc, vraylib = excons.GetDirs("vray")
  
  if vrayinc:
    env.Append(CPPPATH = [vrayinc])
  
  if vraylib:
    if sys.platform == "win32":
      lookfor = "plugman_s.lib"
    else:
      lookfor = "libplugman_s.a"
    vraylib = FindFileIn(lookfor, vraylib)
    if vraylib:
      env.Append(LIBPATH = [vraylib])
  
  env.Append(LIBS = ["vray", "plugman_s", "vutils_s"])

