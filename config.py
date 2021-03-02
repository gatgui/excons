# Copyright (C) 2017~  Gaetan Guidet
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
import re
import excons
import SCons.Script # pylint: disable=import-error


def GetPath(name):
   return excons.joinpath(excons.out_dir, "%s.status" % name)

def HasChanged(name, opts):
   if not os.path.isfile(GetPath(name)):
      return True
   else:
      with open(GetPath(name), "r") as f:
         for line in f.readlines():
            spl = line.strip().split(" ")
            if spl[0] in opts:
               if str(opts[spl[0]]) != " ".join(spl[1:]):
                  return True
      return False

def Write(name, opts):
   with open(GetPath(name), "w") as f:
      for k, v in opts.iteritems():
         f.write("%s %s\n" % (k, v))
      f.write("\n")

def GenerateFile(outpath, inpath, opts, pattern=None):
   if pattern is not None:
      phexp = re.compile(pattern)
   else:
      phexp = re.compile(r"@([^@]+)@")
   with open(outpath, "wb") as outf:
      with open(inpath, "rb") as inf:
         for line in inf.readlines():
            m = phexp.search(line)
            while m is not None:
               for keyi in xrange(len(m.groups())):
                  key = m.group(1 + keyi)
                  if key is None:
                     continue
                  elif not key in opts:
                     excons.WarnOnce("No value for placeholder '%s' in %s" % (key, inpath))
                  else:
                     line = line.replace(m.group(0), opts[key])
                     break
               m = phexp.search(line)
            outf.write(line)

def AddGenerator(env, name, opts, pattern=None):
   def _ActionFunc(target, source, env):
      GenerateFile(str(target[0]), str(source[0]), opts, pattern=pattern)
      return None

   funcname = "%sGenerateFile" % name

   env["BUILDERS"][funcname] = SCons.Script.Builder(action=SCons.Script.Action(_ActionFunc, "Generating $TARGET ..."))

   func = getattr(env, funcname)

   def _WrapFunc(target, source):
      if HasChanged(name, opts):
         Write(name, opts)
      return func(target, [source] + [GetPath(name)])

   return _WrapFunc
