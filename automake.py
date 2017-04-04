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
import pprint
import subprocess
import excons
from SCons.Script import *


InstallExp = re.compile(r"^.*?bin/install\s+((-c|-d|(-m\s+\d{3}))\s+)*(.*?)((['\"]?)(%s.*)\6)$" % os.path.abspath(excons.OutputBaseDirectory()))
SymlinkExp = re.compile(r"ln\s+((-s|-f)\s+)*([^|&}{;]*)")


def BuildDir(name):
   buildDir = excons.BuildBaseDirectory() + "/" + name
   if sys.platform == "win32":
      buildDir += "/msvc-%s" % excons.GetArgument("mscver", "10.0")
   return buildDir

def ConfigCachePath(name):
   return os.path.abspath(excons.out_dir + "/%s.automake.config" % name)

def OutputsCachePath(name):
   return os.path.abspath(excons.out_dir + "/%s.automake.outputs" % name)

def Outputs(name):
   lst = []
   cof = OutputsCachePath(name)
   if os.path.isfile(cof):
      with open(cof, "r") as f:
         lines = filter(lambda y: len(y)>0, map(lambda x: x.strip(), f.readlines()))
         lst = map(lambda x: excons.out_dir + "/" + x, lines)
   return lst

def Configure(name, opts={}):
   if sys.platform == "win32":
      return False

   if GetOption("clean"):
      return True

   doconf = False
   ccf = ConfigCachePath(name)
   if os.path.isfile(ccf):
      with open(ccf, "r") as f:
         try:
            d = eval(f.read())
            for k, v in d.iteritems():
               if not k in opts or opts[k] != v:
                  doconf = True
                  break
            if not doconf:
               for k, v in opts.iteritems():
                  if not k in d:
                     doconf = True
                     break
         except:
            doconf = True
   else:
      doconf = True

   cwd = os.path.abspath(".")
   bld = BuildDir(name)
   relpath = os.path.relpath(cwd, bld)
   if not os.path.isdir(bld):
      doconf = True
      try:
         os.makedirs(bld)
      except:
         if os.path.isfile(ccf):
            os.remove(ccf)
         return False

   configure = "%s/configure" % cwd
   Makefile = "%s/Makefile" % bld

   if not os.path.isfile(configure):
      p = subprocess.Popen("autoreconf -vif", shell=True)
      p.communicate()
      if p.returncode != 0 or not os.path.isfile(configure):
         return False

   if os.path.isfile(Makefile):
      if int(ARGUMENTS.get("reconfigure", "0")) != 0:
         # Configure cache to remove?
         os.remove(Makefile)
         doconf = True
      else:
         return True
   else:
      doconf = True

   if not doconf:
      return True

   success = False

   with excons.SafeChdir(bld, cur=cwd, tool="automake"):
      cmd = "%s/configure " % relpath
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

      success = (p.returncode == 0)

   if success and os.path.isfile(Makefile):
      # Write out configuration cache
      with open(ccf, "w") as f:
         pprint.pprint(opts, stream=f)
      return True
   else:
      if os.path.isfile(ccf):
         os.remove(ccf)
      return False

def Build(name, target=None):
   if GetOption("clean"):
      return True

   ccf = ConfigCachePath(name)
   cof = OutputsCachePath(name)

   if not os.path.isfile(ccf):
      return False

   outfiles = set()
   symlinks = {}
   success = False

   with excons.SafeChdir(BuildDir(name), tool="automake"):
      if target is None:
         target = "install"
      njobs = GetOption("num_jobs")

      cmd = "make"
      if njobs > 1:
         cmd += " -j %d" % njobs
      cmd += " %s" % target

      excons.Print("Run Command: %s" % cmd, tool="automake")
      p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

      buf = ""
      while p.poll() is None:
         r = p.stdout.readline(512)
         buf += r
         lines = buf.split("\n")
         if len(lines) > 1:
            for i in xrange(len(lines)-1):
               excons.Print(lines[i], tool="automake")
               m = InstallExp.match(lines[i].strip())
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
                  m = SymlinkExp.search(lines[i].strip())
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
            buf = lines[-1]
      excons.Print(buf, tool="automake")

      success = (p.returncode == 0)

   with open(cof, "w") as f:
      lst = list(outfiles)
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

   return success


def CleanOne(name):
   if not GetOption("clean"):
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
      with excons.SafeChdir(buildDir, tool="automake"):
         subprocess.Popen("make distclean", shell=True).communicate()
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
   if not GetOption("clean"):
      return

   allnames = map(lambda x: ".".join(os.path.basename(x).split(".")[:-2]), glob.glob(excons.out_dir + "/*.automake.outputs"))

   if len(COMMAND_LINE_TARGETS) == 0:
      names = allnames[:]
   else:
      names = COMMAND_LINE_TARGETS

   for name in names:
      CleanOne(name)

