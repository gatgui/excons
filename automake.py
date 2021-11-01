# MIT License
#
# Copyright (c) 2017 Gaetan Guidet
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
import re
import sys
import glob
import shutil
import subprocess
import excons
import excons.devtoolset
from excons.cmake import VC_Filter
import SCons.Script # pylint: disable=import-error

# pylint: disable=bad-indentation,global-statement,deprecated-lambda


InstallExp = re.compile(r"^.*?bin/install\s+((-c|-d|(-m\s+\d{3}))\s+)*(.*?)((['\"]?)(%s.*)\6)$" % os.path.abspath(excons.OutputBaseDirectory()))
SymlinkExp = re.compile(r"ln\s+((-s|-f)\s+)*([^|&}{;]*)")
ConfigExtraDeps = {}

def AddConfigureDependencies(name, deps):
   global ConfigExtraDeps

   lst = ConfigExtraDeps.get(name, [])
   lst.extend(deps)
   ConfigExtraDeps[name] = lst

def AdditionalConfigureDependencies(name):
   global ConfigExtraDeps

   return ConfigExtraDeps.get(name, [])

def BuildDir(name):
   return excons.BuildBaseDirectory() + "/" + name

def ConfigCachePath(name):
   return os.path.abspath(excons.out_dir + "/%s.automake.config" % name)

def OutputsCachePath(name):
   return os.path.abspath(excons.out_dir + "/%s.automake.outputs" % name)

def Outputs(name):
   lst = []
   cof = OutputsCachePath(name)
   if os.path.isfile(cof):
      cofd = os.path.dirname(cof)
      with open(cof, "r") as f:
         lines = filter(lambda y: len(y)>0 and os.path.isfile(os.path.join(cofd, y)), map(lambda x: x.strip(), f.readlines()))
         lst = filter(VC_Filter, map(lambda x: excons.out_dir + "/" + x, lines))
   return lst

def Configure(name, topdir=None, opts=None):
   if SCons.Script.GetOption("clean"):
      return True

   if opts is None:
      opts = {}

   if topdir is None:
      topdir = os.path.abspath(".")

   bld = BuildDir(name)
   relpath = os.path.relpath(topdir, bld)

   cmd = "cd \"%s\"; %s/configure " % (bld, relpath)
   for k, v in opts.iteritems():
      if type(v) == bool:
         if v:
            cmd += "%s " % k
      else:
         cmd += "%s=%s " % (k, ("\"%s\"" % v if type(v) in (str, unicode) else v))
   cmd += "--prefix=\"%s\""  % excons.OutputBaseDirectory()

   env = None
   if sys.platform != "win32":
      _env = excons.devtoolset.GetDevtoolsetEnv(excons.GetArgument("devtoolset", ""), merge=True)
      if _env:
         env = os.environ.copy()
         env.update(_env)

   excons.Print("Run Command: %s" % cmd, tool="automake")
   p = subprocess.Popen(cmd, env=env, shell=True)
   p.communicate()

   return (p.returncode == 0)

def ParseOutputsInLines(lines, outfiles, symlinks):
   for line in lines:
      excons.Print(line, tool="automake")
      m = InstallExp.match(line.strip())
      if m is not None:
         f = m.group(7)
         if os.path.isdir(f):
            items = filter(lambda y: len(y) > 0, map(lambda x: x.strip(), m.group(4).split(" ")))
            for item in items:
               o = f + "/" + os.path.basename(item)
               outfiles.add(o)
               #print("ADD - %s" % o)
         else:
            outfiles.add(f)
            #print("ADD - %s" % f)
      else:
         m = SymlinkExp.search(line.strip())
         if m:
            srcdst = filter(lambda y: len(y) > 0, map(lambda x: x.strip(), m.group(3).split(" ")))
            count = len(srcdst)
            if count % 2 == 0:
               mid = count / 2
               src = " ".join(srcdst[:mid])
               dst = " ".join(srcdst[mid:])
               lst = symlinks.get(src, [])
               lst.append(dst)
               symlinks[src] = lst
               #print("SYMLINK - %s -> %s" % (src, dst))

def Build(name, target=None):
   if SCons.Script.GetOption("clean"):
      return True

   ccf = ConfigCachePath(name)
   cof = OutputsCachePath(name)

   if not os.path.isfile(ccf):
      return False

   outfiles = set()
   symlinks = {}

   if target is None:
      target = "install"
   njobs = SCons.Script.GetOption("num_jobs")

   cmd = "cd \"%s\"; make" % BuildDir(name)
   if njobs > 1:
      cmd += " -j %d" % njobs
   if excons.GetArgument("show-cmds", 0, int):
      cmd += " V=1"
   cmd += " %s" % target

   env = None
   if sys.platform != "win32":
      _env = excons.devtoolset.GetDevtoolsetEnv(excons.GetArgument("devtoolset", ""), merge=True)
      if _env:
         env = os.environ.copy()
         env.update(_env)

   excons.Print("Run Command: %s" % cmd, tool="automake")
   p = subprocess.Popen(cmd, shell=True, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

   buf = ""
   while p.poll() is None:
      r = p.stdout.readline(512)
      buf += r
      lines = buf.split("\n")
      if len(lines) > 1:
         buf = lines[-1]
         ParseOutputsInLines(lines[:-1], outfiles, symlinks)
   ParseOutputsInLines(buf.split("\n"), outfiles, symlinks)
   excons.Print(buf, tool="automake")

   if p.returncode == 0:
      with open(cof, "w") as f:
         lst = filter(VC_Filter, outfiles)
         # Add symlinks
         ll = len(lst)
         for i in xrange(ll):
            bn = os.path.basename(lst[i])
            if bn in symlinks:
               dn = os.path.dirname(lst[i])
               for l in symlinks[bn]:
                  sln = dn + "/" + l
                  if not sln in lst:
                     lst.append(sln)
                     #print("ADD - %s" % sln)
         lst.sort()
         f.write("\n".join(excons.NormalizedRelativePaths(lst, excons.out_dir)))
      return True
   else:
      if os.path.isfile(cof):
         os.remove(cof)
      return False


def CleanOne(name):
   if not SCons.Script.GetOption("clean"):
      return

   # Remove output files
   for path in Outputs(name):
      path = excons.out_dir + "/" + path
      if os.path.isfile(path):
         os.remove(path)
         excons.Print("Removed: '%s'" % excons.NormalizedRelativePath(path, excons.out_dir), tool="automake")

   # Remove build temporary files      
   buildDir = BuildDir(name)
   if os.path.isdir(buildDir):
      env = None
      if sys.platform != "win32":
         _env = excons.devtoolset.GetDevtoolsetEnv(excons.GetArgument("devtoolset", ""), merge=True)
         if _env:
            env = os.environ.copy()
            env.update(_env)
      subprocess.Popen("cd \"%s\"; make distclean" % buildDir, shell=True, env=env).communicate()
      shutil.rmtree(buildDir)
      excons.Print("Removed: '%s'" % excons.NormalizedRelativePath(buildDir, excons.out_dir), tool="automake")

   path = ConfigCachePath(name)
   if os.path.isfile(path):
      os.remove(path)
      excons.Print("Removed: '%s'" % excons.NormalizedRelativePath(path, excons.out_dir), tool="automake")

   path = OutputsCachePath(name)
   if os.path.isfile(path):
      os.remove(path)
      excons.Print("Removed: '%s'" % excons.NormalizedRelativePath(path, excons.out_dir), tool="automake")

def Clean():
   if not SCons.Script.GetOption("clean"):
      return

   allnames = map(lambda x: ".".join(os.path.basename(x).split(".")[:-2]), glob.glob(excons.out_dir + "/*.automake.outputs"))

   if len(SCons.Script.COMMAND_LINE_TARGETS) == 0:
      names = allnames[:]
   else:
      names = SCons.Script.COMMAND_LINE_TARGETS

   for name in names:
      CleanOne(name)

def ExternalLibRequire(configOpts, name, libnameFunc=None, definesFunc=None, extraEnvFunc=None, flagName=None):
   rv = excons.ExternalLibRequire(name, libnameFunc=libnameFunc, definesFunc=definesFunc, extraEnvFunc=extraEnvFunc)

   req = rv["require"]

   if req is not None:
      defines = ("" if definesFunc is None else definesFunc(rv["static"]))
      if defines:
         extraflags = " ".join(map(lambda x: "-D%s" % x, defines))
         configOpts["CPPFLAGS"] = "%s %s" % (os.environ.get("CPPFLAGS", ""), extraflags)

      if flagName is None:
         flagName = name
         excons.PrintOnce("Use Automake flag '%s' for external dependency '%s'" % (flagName, name))

      configOpts["--with-%s" % flagName] = "%s,%s" % (rv["incdir"], rv["libdir"])

   return rv
