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

def GetOptionsString():
  return """BOOST OPTIONS
  with-boost=<str>     : Boost root directory.
  with-boost-inc=<str> : Boost default headers directory.   [<root>/include]
  with-boost-lib=<str> : Boost default libraries directory. [<root>/lib]
  boost-static=0|1     : Link boost static libraries.       [0]
  boost-prefix=<str>   : Default boost library prefix.      ['']
  boost-suffix=<str>   : Default boost library suffix.      ['']
  boost-autolink=0|1   : Disable boost auto linking.        [1] (windows only)

  Additionally each boost library LIBNAME can have its overrides:

  with-boost-LIBNAME=<path>     : Boost LIBNAME root directory.        [inherit from boost]
  with-boost-LIBNAME-inc=<path> : Boost LIBNAME headers directory.     [inherit from boost]
  with-boost-LIBNAME-lib=<path> : Boost LIBNAME libraries directory.   [inherit from boost]
  boost-LIBNAME-static=0|1      : Link boost LIBNAME statically.       [inherit from boost]
  boost-LIBNAME-name=<str>      : Override boost LIBNAME library name. []
  boost-LIBNAME-prefix=<str>    : Boost LIBNAME library prefix.        [inherit from boost]
                                  (ignore when boost-LIBNAME-name is set)
  boost-LIBNAME-suffix=<str>    : Boost LIBNAME library suffix.        [inherit from boost]
                                  (ignore when boost-LIBNAME-name is set)
  boost-LIBNAME-autolink=0|1    : Disable boost LIBNAME auto linking.  [inherit from boost]"""

def IsStaticallyLinked(lib):
  static = (excons.GetArgument("boost-static", 0, int) != 0)
  return (excons.GetArgument("boost-%s-static" % lib, (1 if static else 0), int) != 0)

def Require(libs=[]):
  boost_inc_dir, boost_lib_dir = excons.GetDirs("boost")
  static = (excons.GetArgument("boost-static", 0, int) != 0)
  boost_libprefix = excons.GetArgument("boost-prefix", "")
  boost_libsuffix = excons.GetArgument("boost-suffix", "")
  useautolink = False
  if sys.platform == "win32":
    useautolink = (excons.GetArgument("boost-autolink", 1, int) != 0)

  libargs = {}
  for lib in libs:
    incdir, libdir = excons.GetDirs("boost-%s" % lib)
    libname = excons.GetArgument("boost-%s-name" % lib, None)
    if libname is None:
      libprefix = excons.GetArgument("boost-%s-prefix" % lib, boost_libprefix)
      libsuffix = excons.GetArgument("boost-%s-suffix" % lib, boost_libsuffix)
      libname = "%sboost_%s%s" % (libprefix, lib, libsuffix)
    libstatic = (excons.GetArgument("boost-%s-static" % lib, (1 if static else 0), int) != 0)
    autolinklib = False
    if sys.platform == "win32":
      autolinklib = (excons.GetArgument("boost-%s-autolink" % lib, (1 if useautolink else 0), int) != 0)
    libargs[lib] = {"incdir": incdir,
                    "libdir": libdir,
                    "name": libname,
                    "static": libstatic,
                    "autolink": autolinklib}

  def _RealRequire(env):
    if boost_inc_dir:
      env.Append(CPPPATH=boost_inc_dir)
    
    if boost_lib_dir:
      env.Append(LIBPATH=boost_lib_dir)
    
    autolinkcount = 0

    defs = []

    # All libs but Boost.Python are statically linked by default
    # => use BOOST_PYTHON_STATIC_LIB to enable static linking
    
    # Libraries are auto-linked on windows by default
    # => disable for all libraries using BOOST_ALL_NO_LIB
    # => disable for a specific lib using BOOST_[libraryname]_NO_LIB
    
    for lib in libs:
      incdir = libargs[lib]["incdir"]
      libdir = libargs[lib]["libdir"]
      libname = libargs[lib]["name"]
      libstatic = libargs[lib]["static"]
      autolinklib = libargs[lib]["autolink"]

      if incdir:
        env.Append(CPPPATH=[incdir])

      if libdir:
        env.Append(LIBPATH=[libdir])

      if sys.platform == "win32":
        if not autolinklib:
          defs.append("BOOST_%s_NO_LIB" % lib.upper())
        else:
          autolinkcount += 1
        
        if libstatic:
          if lib == "thread":
            # Not to confure with the 'LIB' meaning of BOOST_xxx_NO_LIB
            defs.append("BOOST_THREAD_USE_LIB")
          
          elif lib == "python":
            # Boost.Python is dynamically linked by 'default'
            defs.append("BOOST_PYTHON_STATIC_LIB")
        
        else:
          # Should not have to make a special case of Boost.Thread anymore, but
          # for backward compatibility sake
          if lib == "thread":
            defs.append("BOOST_THREAD_USE_DLL")
          
          elif lib != "python":
            defs.append("BOOST_%s_DYN_LINK" % lib.upper())
      
      if not autolinklib:
        excons.Link(env, libname, static=libstatic, force=True, silent=True)

    if sys.platform == "win32" and autolinkcount == 0:
      defs.append("BOOST_ALL_NO_LIB")
    
    env.Append(CPPDEFINES=defs)
    
    excons.AddHelpOptions(boost=GetOptionsString())
  
  return _RealRequire
