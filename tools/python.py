# Copyright (C) 2009  Gaetan Guidet
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

def Require(e):
  from distutils import sysconfig
  e.Append(CCFLAGS=" -DLWC_PYVER=%s" % sysconfig.get_python_version())
  e.Append(CPPPATH=[sysconfig.get_python_inc()])
  if sysconfig.get_config_var("PYTHONFRAMEWORK"):
    a = ' -F' + sysconfig.get_config_var("PYTHONFRAMEWORKPREFIX")
    b = ' -framework ' + sysconfig.get_config_var("PYTHONFRAMEWORK")
    e.Append(LINKFLAGS=a+b)
  else:
    if str(Platform()) == "win32":
      e.Append(LIBPATH=[sysconfig.PREFIX+'\\libs'])
      e.Append(LIBS=["python%s" % sysconfig.get_python_version().replace(".", "")])
    else:
      e.Append(LINKFLAGS=" %s" % sysconfig.get_config_var("LINKFORSHARED"))
      e.Append(LIBS=["python%s" % sysconfig.get_python_version()])

def ModulePrefix():
  return "lib/python/"

def ModuleExtension():
  from distutils import sysconfig
  return sysconfig.get_config_var("SO")
