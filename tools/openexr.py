# MIT License
#
# Copyright (c) 2015 Gaetan Guidet
#
# This file is part of excons.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


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

