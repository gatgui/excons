# Copyright (C) 2015~  Gaetan Guidet
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
import excons.tools.zlib
import excons.tools.ilmbase
import os

def Require(ilmbase=False, zlib=False):
   
   def _RequireOpenEXR(env):
      openexr_libsuffix = excons.GetArgument("openexr-libsuffix", "")

      openexr_libname = excons.GetArgument("openexr-libname", "IlmImf%s" % openexr_libsuffix)

      openexr_inc, openexr_lib = excons.GetDirs("openexr")

      openexr_static = (excons.GetArgument("openexr-static", 0, int) != 0)

      if openexr_inc and not openexr_inc.endswith("OpenEXR"):
         openexr_inc += "/OpenEXR"

      if sys.platform == "win32" and not openexr_static:
         env.Append(CPPDEFINES=["OPENEXR_DLL"])

      if openexr_inc:
         env.Append(CPPPATH=[openexr_inc, os.path.dirname(openexr_inc)])

      if openexr_lib:
         env.Append(LIBPATH=[openexr_lib])

      env.Append(LIBS=[openexr_libname])

      if ilmbase:
         excons.tools.ilmbase.Require()(env)

      if zlib:
         excons.tools.zlib.Require(env)

   return _RequireOpenEXR
