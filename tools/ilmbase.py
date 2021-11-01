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
import os
import sys

# pylint: disable=bad-indentation


def GetOptionsString():
   return """ILMBASE OPTIONS
  with-ilmbase=<path>     : IlmBase root directory.
  with-ilmbase-inc=<path> : IlmBase headers directory.   [<root>/include]
  with-ilmbase-lib=<path> : IlmBase libraries directory. [<root>/lib]
  ilmbase-static=0|1      : Link static libraries.       [0]
  ilmbase-prefix=<str>    : IlmBase library prefix.      ['']
  ilmbase-suffix=<str>    : IlmBase library suffix.      ['']

  with-ilmbase-python=<path>     : PyIlmBase root directory.      [inherit from ilmbase]
  with-ilmbase-python-inc=<path> : PyIlmBase headers directory.   [inherit from ilmbase]
  with-ilmbase-python-lib=<path> : PyIlmBase libraries directory. [inherit from ilmbase]
  ilmbase-python-static=0|1      : Link static libraries.         [inherit from ilmbase]
  ilmbase-python-prefix=<str>    : PyIlmBase library name prefix. [inherit from ilmbase]
  ilmbase-python-suffix=<str>    : PyIlmBase library name suffix. [inherit from ilmbase]"""

def Require(ilmthread=None, iexmath=None, python=None, halfonly=False):
   
   if not halfonly:
      if ilmthread is None:
         ilmthread = (excons.GetArgument("ilmbase-thread", 1, int) != 0)

      if iexmath is None:
         iexmath = (excons.GetArgument("ilmbase-iexmath", 1, int) != 0)

      if python is None:
         python = (excons.GetArgument("ilmbase-python", 0, int) != 0)
   
   else:
      ilmthread = False
      iexmath = False
      python = False

   ilmbase_libsuffix = excons.GetArgument("ilmbase-suffix", "")
   ilmbase_libprefix = excons.GetArgument("ilmbase-prefix", "")

   pyilmbase_inc, pyilmbase_lib, pyilmbase_libprefix, pyilmbase_libsuffix = "", "", "", ""
   if python:
      pyilmbase_inc, pyilmbase_lib = excons.GetDirs("ilmbase-python")
      if pyilmbase_inc and not pyilmbase_inc.endswith("OpenEXR"):
         pyilmbase_inc += "/OpenEXR"
      pyilmbase_libprefix = excons.GetArgument("ilmbase-python-prefix", ilmbase_libprefix)
      pyilmbase_libsuffix = excons.GetArgument("ilmbase-python-suffix", ilmbase_libsuffix)

   ilmbase_inc, ilmbase_lib = excons.GetDirs("ilmbase")
   if ilmbase_inc and not ilmbase_inc.endswith("OpenEXR"):
      ilmbase_inc += "/OpenEXR"

   static = (excons.GetArgument("ilmbase-static", 0, int) != 0)

   pystatic = static
   if python:
      pystatic = (excons.GetArgument("ilmbase-python-static", (1 if static else 0), int) != 0)

   excons.AddHelpOptions(ilmbase=GetOptionsString())

   def _RealRequire(env):
      # Add python bindings first
      if python:
         if pystatic:
            env.Append(CPPDEFINES=["PLATFORM_BUILD_STATIC"])
         if sys.platform != "win32":
            env.Append(CPPDEFINES=["PLATFORM_VISIBILITY_AVAILABLE"])

         if pyilmbase_inc:
            env.Append(CPPPATH=[pyilmbase_inc, os.path.dirname(pyilmbase_inc)])
         
         if pyilmbase_lib:
            env.Append(LIBPATH=[pyilmbase_lib])
         
         excons.Link(env, "%sPyImath%s" % (pyilmbase_libprefix, pyilmbase_libsuffix), static=pystatic, silent=True)
         excons.Link(env, "%sPyIex%s" % (pyilmbase_libprefix, pyilmbase_libsuffix), static=pystatic, silent=True)

      if ilmbase_inc:
         env.Append(CPPPATH=[ilmbase_inc, os.path.dirname(ilmbase_inc)])
      
      if ilmbase_lib:
         env.Append(LIBPATH=[ilmbase_lib])

      if sys.platform == "win32" and not static:
         env.Append(CPPDEFINES=["OPENEXR_DLL"])
      
      if ilmthread:
         # ilmthread will be False if halfonly is True
         libname = "%sIlmThread%s" % (ilmbase_libprefix, ilmbase_libsuffix)
         excons.Link(env, libname, static=static, force=True, silent=True)
      
      if not halfonly:
         libname = "%sImath%s" % (ilmbase_libprefix, ilmbase_libsuffix)
         excons.Link(env, libname, static=static, force=True, silent=True)
      
      if iexmath:
         # iexmath will be False if halfonly is True
         libname = "%sIexMath%s" % (ilmbase_libprefix, ilmbase_libsuffix)
         excons.Link(env, libname, static=static, force=True, silent=True)
      
      if not halfonly:
         libname = "%sIex%s" % (ilmbase_libprefix, ilmbase_libsuffix)
         excons.Link(env, libname, static=static, force=True, silent=True)
      
      libname = "%sHalf%s" % (ilmbase_libprefix, ilmbase_libsuffix)
      excons.Link(env, libname, static=static, force=True, silent=True)

   return _RealRequire

