# MIT License
#
# Copyright (c) 2009 Gaetan Guidet
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

# pylint: disable=bad-indentation


def Require(env):
  linc, llib = excons.GetDirs("lua")
  if linc:
    env.Append(CPPPATH=[linc])
  if llib:
    env.Append(LIBPATH=[llib])

  if sys.platform == "win32":
    env.Append(CPPDEFINES=["LUA_BUILD_AS_DLL"])
    env.Append(LIBS=["lua51"])
  
  else:
    env.Append(LIBS=["lua"])
  
  #elif sys.platform == "darwin":
  #  # Do not link lua static lib [would duplicate core]
  #  # But add linkflags so OSX doesn't complain about unresolved symbols
  #  env.Append(LINKFLAGS = " -undefined dynamic_lookup")
  #else:
  #  # Do not link lua static lib [would duplicate core]
  #  # Only do it for final executable [using LinkLUA]
  #  pass

def ModulePrefix():
  return "lib/lua/"

def ModuleExtension():
  return ".so"
