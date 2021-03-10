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

import os
import sys
import excons
import excons.tools.zlib
import excons.tools.ilmbase

def GetOptionsString():
   return """OPENEXR OPTIONS
  with-openexr=<path>     : OpenEXR root directory.
  with-openexr-inc=<path> : OpenEXR headers directory.     [<root>/include]
  with-openexr-lib=<path> : OpenEXR libraries directory.   [<root>/lib]
  openexr-static=0|1      : Link static libraries.         [0]
  openexr-name=<str>      : Override OpenEXR library name. []
  openexr-prefix=<str>    : OpenEXR library name prefix.   ['']
                            (ignored when openexr-name is set)
  openexr-suffix=<str>    : OpenEXR library name suffix.   ['']
                            (ignored when openexr-name is set)"""

def Require(ilmbase=False, zlib=False):
   openexr_libprefix = excons.GetArgument("openexr-prefix", "")
   openexr_libsuffix = excons.GetArgument("openexr-suffix", "")

   openexr_libname = excons.GetArgument("openexr-name", "%sIlmImf%s" % (openexr_libprefix, openexr_libsuffix))

   openexr_inc, openexr_lib = excons.GetDirs("openexr")
   if openexr_inc and not openexr_inc.endswith("OpenEXR"):
      openexr_inc += "/OpenEXR"

   openexr_static = (excons.GetArgument("openexr-static", 0, int) != 0)

   excons.AddHelpOptions(openexr=GetOptionsString())
   
   def _RequireOpenEXR(env):
      if sys.platform == "win32" and not openexr_static:
         env.Append(CPPDEFINES=["OPENEXR_DLL"])

      if openexr_inc:
         env.Append(CPPPATH=[openexr_inc, os.path.dirname(openexr_inc)])

      if openexr_lib:
         env.Append(LIBPATH=[openexr_lib])

      excons.Link(env, openexr_libname, static=openexr_static, force=True, silent=True)

      if ilmbase:
         excons.tools.ilmbase.Require()(env)

      if zlib:
         excons.tools.zlib.Require(env)

   return _RequireOpenEXR

