# MIT License
#
# Copyright (c) 2010 Gaetan Guidet
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


import excons

# pylint: disable=bad-indentation


def GetOptionsString():
  return """FREEIMAGE OPTIONS
  with-freeimage=<path>     : FreeImage root directory.
  with-freeimage-inc=<path> : FreeImage headers directory.     [<root>/include]
  with-freeimage-lib=<path> : FreeImage libraries directory.   [<root>/lib]
  freeimage-static=0|1      : Link FreeImage static lib.       [0]
  freeimage-name=<str>      : Override FreeImage library name. []
  freeimage-prefix=<str>    : FreeImage library name prefix.   ['']
                              (ignored when freeimage-name is set)
  freeimage-suffix=<str>    : FreeImage library name suffix.   ['']
                              (ignored when freeimage-name is set)"""

def Require(env):
  fiinc, filib = excons.GetDirs("freeimage")
  
  if fiinc:
    env.Append(CPPPATH=[fiinc])
  
  if filib:
    env.Append(LIBPATH=[filib])
  
  static = (excons.GetArgument("freeimage-static", 0, int) != 0)
  if static:
    env.Append(CPPDEFINES=["FREEIMAGE_LIB"])
  
  filibname = excons.GetArgument("freeimage-name", None)
  if not filibname:
    filibprefix = excons.GetArgument("freeimage-prefix", "")
    filibsuffix = excons.GetArgument("freeimage-suffix", "")
    filibname = "%sfreeimage%s" % (filibprefix, filibsuffix)
  
  excons.Link(env, filibname, static=static, force=True, silent=True)
  
  excons.AddHelpOptions(freeimage=GetOptionsString())
