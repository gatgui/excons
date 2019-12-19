import os
import re
import excons
from SCons.Script import *


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
               replaced = False
               for keyi in xrange(len(m.groups())):
                  key = m.group(1 + keyi)
                  if key is None:
                     continue
                  elif not key in opts:
                     excons.WarnOnce("No value for placeholder '%s' in %s" % (key, path))
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

   env["BUILDERS"][funcname] = Builder(action=Action(_ActionFunc, "Generating $TARGET ..."))

   func = getattr(env, funcname)

   def _WrapFunc(target, source):
      if HasChanged(name, opts):
         Write(name, opts)
      return func(target, [source] + [GetPath(name)])

   return _WrapFunc
