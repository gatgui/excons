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
import sys
import glob
import shutil
import subprocess
import excons
from SCons.Script import *


def CollectFiles(d, pattern, recursive=True, rdirs=None):
   allfiles = None
   rv = []

   if type(pattern) in (str, unicode):
      if pattern.startswith("."):
         rv += glob.glob(d + "/*" + pattern)
      else:
         if os.path.exists(d + "/" + pattern):
            rv.append(d + "/" + pattern)
   else:
      allfiles = glob.glob(d + "/*")
      rv = filter(lambda x: pattern.match(x) is not None, allfiles)

   if recursive:
      if allfiles is None:
         allfiles = glob.glob(d + "/*")
      for sd in filter(os.path.isdir, allfiles):
         if rdirs is None or os.path.basename(sd) in rdirs:
            rv += CollectFiles(sd, pattern, recursive=True, rdirs=None)

   return rv

def NormalizedRelativePath(f, basedir):
   return os.path.relpath(f, basedir).replace("\\", "/")

def NormalizedRelativePaths(files, basedir):
   return map(lambda x: NormalizedRelativePath(x, basedir), files)

def OutputsCachePath(name):
   return os.path.abspath(excons.out_dir + "/%s.automake.outputs" % name)

def Outputs(env, exclude=[]):
   name = env["AUTOMAKE_PROJECT"]
   lst = []
   excl = NormalizedRelativePaths(map(str, exclude), ".")
   cof = OutputsCachePath(name)
   if os.path.isfile(cof):
      with open(cof, "r") as f:
         lst = NormalizedRelativePaths(filter(lambda y: len(y)>0, map(lambda x: x.strip(), f.readlines())), ".")
      lst = filter(lambda x: x not in excl, lst)
   lst.append(NormalizedRelativePath(cof, "."))
   return lst

def InputsCachePath(name):
   return os.path.abspath(excons.out_dir + "/%s.automake.inputs" % name)

def Inputs(env, dirs=[], patterns=[], exclude=[]):
   name = env["AUTOMAKE_PROJECT"]
   lst = []
   excl = NormalizedRelativePaths(map(str, exclude), ".")
   cif = InputsCachePath(name)
   if os.path.isfile(cif):
      with open(cif, "r") as f:
         lst = filter(lambda y: len(y)>0, map(lambda x: x.strip(), f.readlines()))
      lst = filter(lambda x: x not in exclude, lst)
   else:
      rec = (True if not dirs else False)
      if not dirs:
         dirs = ["."]
      for d in dirs:
         lst += CollectFiles(d, ".ac", recursive=rec)
         lst += CollectFiles(d, ".am", recursive=rec)
         for pattern in patterns:
            lst += CollectFiles(d, pattern, recursive=rec)
      lst = filter(lambda x: x not in excl, NormalizedRelativePaths(lst, "."))
      with open(cif, "w") as f:
         lst.sort()
         f.write("\n".join(lst))
   # Configure cache?
   return lst

def Configure(env, name, opts={}, internal=False):
   if sys.platform == "win32":
      return False

   if not internal:
      env["AUTOMAKE_PROJECT"] = name
      env["AUTOMAKE_OPTIONS"] = opts
   
   if GetOption("clean"):
      return True

   if not os.path.isfile("./configure"):
      p = subprocess.Popen("autoreconf -vif", shell=True)
      p.communicate()
      if p.returncode != 0 or not os.path.isfile("./configure"):
         return False

   if os.path.isfile("./Makefile"):
      if not internal and int(ARGUMENTS.get("automake-reconfigure", "0")) != 0:
         # Configure cache?
         cif = InputsCachePath(name)
         if os.path.isfile(cif):
            os.remove(cif)
      else:
         return True

   cmd = "./configure "
   for k, v in opts.iteritems():
      if type(v) == bool:
         if v:
            cmd += "%s " % k
      else:
         cmd += "%s=%s " % (k, ("\"%s\"" % v if type(v) in (str, unicode) else v))
   cmd += "--prefix=\"%s\""  % excons.OutputBaseDirectory()
   excons.Print("Run Command: %s" % cmd, tool="automake")
   p = subprocess.Popen(cmd, shell=True)
   p.communicate()

   return (p.returncode == 0 and os.path.isfile("./Makefile"))

def Build(env, name, target=None, opts={}):
   if not Configure(env, name, opts, internal=True):
      return False

   cof = OutputsCachePath(name)

   if target is None:
      target = "install"
   njobs = GetOption("num_jobs")

   cmd = "make"
   if njobs > 1:
      cmd += " -j %d" % njobs
   cmd += " %s" % target

   excons.Print("Run Command: %s" % cmd, tool="automake")
   p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
   e = re.compile(r"^.*?bin/install\s+((-c|-d|(-m\s+\d{3}))\s+)*(.*?)((['\"]?)(%s.*)\6)$" % os.path.abspath(excons.OutputBaseDirectory()))
   le = re.compile(r"ln\s+((-s|-f)\s+)*([^|&}{;]*)")
   buf = ""
   outfiles = set()
   symlinks = {}
   while p.poll() is None:
      r = p.stdout.readline(512)
      buf += r
      lines = buf.split("\n")
      if len(lines) > 1:
         for i in xrange(len(lines)-1):
            excons.Print(lines[i], tool="automake")
            m = e.match(lines[i].strip())
            if m is not None:
               f = m.group(7)
               if os.path.isdir(f):
                  items = filter(lambda y: len(y) > 0, map(lambda x: x.strip(), m.group(4).split(" ")))
                  for item in items:
                     o = f + "/" + os.path.basename(item)
                     outfiles.add(o)
               else:
                  outfiles.add(f)
            else:
               m = le.search(lines[i].strip())
               if m:
                  srcdst = filter(lambda y: len(y) > 0, map(lambda x: x.strip(), m.group(3).split(" ")))
                  count = len(srcdst)
                  if count % 2 == 0:
                     mid = count / 2
                     src = " ".join(srcdst[:mid])
                     dst = " ".join(srcdst[mid:])
                     symlinks[src] = dst
         buf = lines[-1]
   excons.Print(buf, tool="automake")

   with open(cof, "w") as f:
      lst = list(outfiles)
      # Add symlinks
      ll = len(lst)
      for i in xrange(ll):
         bn = os.path.basename(lst[i])
         if bn in symlinks:
            dn = os.path.dirname(lst[i])
            sln = dn + "/" + symlinks[bn]
            if not sln in lst:
               lst.append(sln)
      lst.sort()
      f.write("\n".join(NormalizedRelativePaths(lst, ".")))

   return (p.returncode == 0)

def Clean(env):
   name = env["AUTOMAKE_PROJECT"]
   if not GetOption("clean"):
      return
   if len(COMMAND_LINE_TARGETS) == 0 or name in COMMAND_LINE_TARGETS:
      subprocess.Popen("make distclean", shell=True).communicate()


# === Setup environment ===

def SetupEnvironment(env):
   def GeneratedAction(target, source, env):
      return None

   def BuildAction(target, source, env):
      name = env["AUTOMAKE_PROJECT"]
      opts = (env["AUTOMAKE_OPTIONS"] if "AUTOMAKE_OPTIONS" in env else {})
      target = (env["AUTOMAKE_TARGET"] if "AUTOMAKE_TARGET" in env else None)
      Build(env, name, target=target, opts=opts)
      return None

   # Dummy Scanner
   def DummyScanner(node, env, path):
      return []

   # Required
   #   env["AUTOMAKE_PROJECT"] = <name>
   # Optional
   #   env["AUTOMAKE_OPTIONS"] ( = {} )
   #   env["AUTOMAKE_TARGET"]  ( = "install" )

   env.AddMethod(Inputs, "AutomakeInputs")
   env.AddMethod(Outputs, "AutomakeOutputs")
   env.AddMethod(Configure, "AutomakeConfigure")
   env.AddMethod(Build, "AutomakeBuild")
   env.AddMethod(Clean, "AutomakeClean")

   env["BUILDERS"]["Automake"] = Builder(action=Action(BuildAction, "Build using Automake ..."))
   env["BUILDERS"]["AutomakeGenerated"] = Builder(action=Action(GeneratedAction, "Generate $TARGET using Automake ..."))

   # Override default C/C++ file scanner to avoid SCons begin to nosy
   cexts = [".c", ".h", ".cc", ".hh", ".cpp", ".hpp", ".cxx", ".hxx"]
   env.Prepend(SCANNERS=Scanner(function=DummyScanner, skeys=cexts))

