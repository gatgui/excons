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


import SCons.Script # pylint: disable=import-error
import excons
import sys
import re
import os

# pylint: disable=bad-indentation


def FindFileIn(filename, directory):
  for item in excons.glob(directory+"/*"):
    if os.path.isdir(item):
      rv = FindFileIn(filename, item)
      if rv is not None:
        return rv
    else:
      basename = os.path.basename(item)
      if basename.lower() == filename:
        return directory
  return None

def PluginExt():
  if str(SCons.Script.Platform()) == "win32":
    return ".dll"
  else:
    return ".so"

def Version(asString=True, nice=False):
  vrayinc, _ = excons.GetDirs("vray")

  vraybase = excons.joinpath(vrayinc, "vraybase.h")
  
  if os.path.isfile(vraybase):
    defexp = re.compile(r"^\s*#define\s+VRAY_DLL_VERSION\s+(0x[a-fA-F0-9]+)")
    f = open(vraybase, "r")
    for line in f.readlines():
      m = defexp.match(line)
      if m:
        #rv = (int(m.group(1), 16) if not asString else m.group(1)[2:])
        rv = m.group(1)[2:]
        if nice:
          iv = int(rv)
          major = iv / 10000
          minor = (iv % 10000) / 100
          patch = iv % 100
          rv = (major, minor, patch)
          if asString:
            rv = "%d.%d.%d" % rv
        else:
          if not asString:
            rv = int(rv)
        return rv
    f.close()

  return ("" if asString else (0 if not nice else (0, 0, 0)))

def Require(env):
  vrayinc, vraylib = excons.GetDirs("vray")
  
  if vrayinc:
    env.Append(CPPPATH=[vrayinc])
  
  if vraylib:
    if sys.platform == "win32":
      lookfor = "plugman_s.lib"
    else:
      lookfor = "libplugman_s.a"
    vraylib = FindFileIn(lookfor, vraylib)
    if vraylib:
      env.Append(LIBPATH=[vraylib])
  
  env.Append(LIBS=["vray", "plugman_s", "vutils_s"])

  if sys.platform == "win32":
    env.Append(CPPDEFINES=["SENSELESS_DEFINE_FOR_WIN32",
                           "_CRT_SECURE_NO_DEPRECATE",
                           "_CRT_NONSTDC_NO_DEPRECATE"])
    env.Append(LIBS=["user32", "advapi32", "shell32"])

