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


import excons

# pylint: disable=bad-indentation


def GetOptionsString():
  return """TBB OPTIONS
  with-tbb=<path>     : TBB root directory.
  with-tbb-inc=<path> : TBB headers directory.     [<root>/include]
  with-tbb-lib=<path> : TBB libraries directory.   [<root>/lib]
  tbb-static=0|1      : Link static library.       [0]
  tbb-name=<str>      : Override TBB library name. []
  tbb-prefix=<str>    : TBB library name prefix.   ['']
                        (ignored when tbb-name is set)
  tbb-suffix=<str>    : TBB library name suffix.   ['']
                        (ignored when tbb-name is set)"""

def Require(env):
  tbbinc, tbblib = excons.GetDirs("tbb")
  
  if tbbinc:
    env.Append(CPPPATH=[tbbinc])
  
  if tbblib:
    env.Append(LIBPATH=[tbblib])
  
  static = (excons.GetArgument("tbb-static", 0, int) != 0)
  # Any specific defines?
  #env.Append(CPPDEFINES=[])
  
  tbblibname = excons.GetArgument("tbb-name", None)
  if not tbblibname:
    tbblibname = "%stbb%s" % (excons.GetArgument("tbb-prefix", ""), excons.GetArgument("tbb-suffix", ""))

  excons.Link(env, tbblibname, static=static, force=True, silent=True)

  excons.AddHelpOptions(tbb=GetOptionsString())
