# MIT License
#
# Copyright (c) 2014 Gaetan Guidet
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


import sys
import excons


def GetOptionsString():
    return """SZIP OPTIONS
  with-szip=<path>     : SZIP root directory.
  with-szip-inc=<path> : SZIP headers directory.     [<root>/include]
  with-szip-lib=<path> : SZIP libraries directory.   [<root>/lib]
  szip-static=0|1      : Use SZIP static library.    [1]
  szip-name=<str>      : Override SZIP library name. []
                         (default library name is libszip on windows, sz on linux)
  szip-prefix=<str>    : SZIP library name prefix.   ['']
                         (ignored when szip-name is set)
  szip-suffix=<str>    : SZIP library name suffix.   ['']
                         (ignored when szip-name is set)"""

def Require(env):
    szip_inc, szip_lib = excons.GetDirs("szip")

    if szip_inc:
        env.Append(CPPPATH=[szip_inc])

    if szip_lib:
        env.Append(LIBPATH=[szip_lib])

    szip_static = (excons.GetArgument("szip-static", 0, int) != 0)

    if not szip_static:
        env.Append(CPPDEFINES=["SZ_BUILT_AS_DYNAMIC_LIB"])

    szip_libname = excons.GetArgument("szip-name", None)
    if not szip_libname:
        szip_libprefix = excons.GetArgument("szip-prefix", "")
        szip_libsuffix = excons.GetArgument("szip-suffix", "")
        szip_libname = "%s%s%s" % (szip_libprefix, ("sz" if sys.platform != "win32" else "libszip"), szip_libsuffix)

    excons.Link(env, szip_libname, static=szip_static, force=True, silent=True)

    excons.AddHelpOptions(szip=GetOptionsString())
