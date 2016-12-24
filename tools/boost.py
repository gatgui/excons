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

def IsStaticallyLinked(lib):
  static = (excons.GetArgument("boost-static", 0, int) != 0)
  return (excons.GetArgument("boost-%s-static" % lib, (1 if static else 0), int) != 0)

def Require(libs=[]):
  
  def _RealRequire(env):
    boost_inc_dir, boost_lib_dir = excons.GetDirs("boost")
    
    if boost_inc_dir:
      env.Append(CPPPATH=boost_inc_dir)
    
    if boost_lib_dir:
      env.Append(LIBPATH=boost_lib_dir)

    static = (excons.GetArgument("boost-static", 0, int) != 0)
    
    boost_libsuffix = excons.GetArgument("boost-libsuffix", "")
    
    useautolink = False
    autolinkcount = 0
    if sys.platform == "win32":
      useautolink = (excons.GetArgument("boost-autolink", 1, int) != 0)
    
    defs = []

    # All libs but Boost.Python are statically linked by default
    # => use BOOST_PYTHON_STATIC_LIB to enable static linking
    
    # Libraries are auto-linked on windows by default
    # => disable for all libraries using BOOST_ALL_NO_LIB
    # => disable for a specific lib using BOOST_[libraryname]_NO_LIB
    
    for lib in libs:
      incdir, libdir = excons.GetDirs("boost-%s" % lib)
      if incdir:
        env.Append(CPPPATH=[incdir])
      
      if libdir:
        env.Append(LIBPATH=[libdir])
      
      libname = excons.GetArgument("boost-%s-libname" % lib, None)
      if not libname:
        libsuffix = excons.GetArgument("boost-%s-libsuffix" % lib, boost_libsuffix)
        libname = "boost_%s%s" % (lib, libsuffix)
      
      libstatic = (excons.GetArgument("boost-%s-static" % lib, (1 if static else 0), int) != 0)
      
      autolinklib = False
      
      if sys.platform == "win32":
        autolinklib = (excons.GetArgument("boost-%s-autolink" % lib, (1 if useautolink else 0), int) != 0)
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
        if not libstatic or not excons.StaticallyLink(env, libname):
          env.Append(LIBS=[libname])

    if sys.platform == "win32" and autolinkcount == 0:
      defs.append("BOOST_ALL_NO_LIB")
    
    env.Append(CPPDEFINES=defs)
  
  return _RealRequire
