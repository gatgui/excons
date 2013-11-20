# Copyright (C) 2013~  Gaetan Guidet
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

def Require(libs=[], static=False):
   boost_base_dir = ARGUMENTS.get("with-boost", None)
   if boost_base_dir is None:
      raise Exception("Please set boost base directory using with-boost=")

   boost_inc_dir = boost_base_dir + "/include"
   if sys.platform in ["win32", "darwin"]:
      boost_lib_dir = boost_base_dir + "/lib"
   else:
      boost_lib_dir = boost_base_dir + ("/lib64" if excons.Build64() else "/lib")

   if not os.path.isdir(boost_inc_dir):
      raise Exception("Invalid boost include directory: \"%s\"" % boost_inc_dir)

   if not os.path.isdir(boost_lib_dir):
      raise Exception("Invalid boost lib directory: \"%s\"" % boost_lib_dir)

   def _RealRequire(env):
      print("excons.tools.boost._RealRequire")
      linklibs = []
      defs = []

      if sys.platform == "win32":
         # All libs but Boost.Python are statically linked by default
         # Libraries are auto-linked on windows
         if static:
            for lib in libs:
               libname = lib.strip().split("-")[0]
               if libname == "python":
                  defs.append("BOOST_PYTHON_STATIC_LIB")
               elif libname == "thread":
                  defs.append("BOOST_THREAD_USE_LIB")
         else:
            for lib in boost_list:
               libname = lib.strip().split("-")[0]
               if libname == "thread":
                  defs.append("BOOST_THREAD_USE_DLL")
               elif libname != "python":
                  defs.append("BOOST_%s_DYN_LINK" % libname.upper())
      else:
         print("=> Linking boost libraries: %s" % libs)
         for lib in libs:
            linklibs.append("boost_%s" % lib.strip())

      env.Append(CPPDEFINES = defs)
      env.Append(CPPPATH = boost_inc_dir)
      env.Append(LIBPATH = boost_lib_dir)
      env.Append(LIBS = linklibs)

   return _RealRequire

