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


import SCons.Script # pylint: disable=import-error
import excons


def GetOptionsString():
    return """ZLIB OPTIONS
  with-zlib=<path>     : Zlib root directory.
  with-zlib-inc=<path> : Zlib headers directory.           [<root>/include]
  with-zlib-lib=<path> : Zlib libraries directory.         [<root>/lib]
  zlib-static=0|1      : Link Zlib statically.             [0]
  zlib-name=<str>      : Override Zlib library name.       []
                         (default name is 'z' on osx and linux, 'zlib' (static) or 'zdll' (shared) on windows)
  zlib-prefix=<str>    : Default Zlib library name prefix. []
                         (ignored when zlib-name is set)
  zlib-suffix=<str>    : Default Zlib library name suffix. []
                         (ignored when zlib-name is set)"""


def Require(env):
    zlibinc, zliblib = excons.GetDirs("zlib")

    if zlibinc:
        env.Append(CPPPATH=[zlibinc])

    if zliblib:
        env.Append(LIBPATH=[zliblib])

    static = (excons.GetArgument("zlib-static", 0, int) != 0)

    if str(SCons.Script.Platform()) != "win32":
        zlib_name = excons.GetArgument("zlib-name", None)
        if not zlib_name:
            zlib_name = "%sz%s" % (excons.GetArgument("zlib-prefix", ""), excons.GetArgument("zlib-suffix", ""))

    else:
        if static:
            zlib_name = excons.GetArgument("zlib-name", None)
            if not zlib_name:
                zlib_name = "zlib%s" % excons.GetArgument("zlib-suffix", "")

        else:
            zlib_name = excons.GetArgument("zlib-name", None)
            if not zlib_name:
                zlib_name = "zdll%s" % excons.GetArgument("zlib-suffix", "")

            env.Append(CPPDEFINES=["ZLIB_DLL"])

    excons.Link(env, zlib_name, static=static, force=True, silent=True)

    excons.AddHelpOptions(zlib=GetOptionsString())

