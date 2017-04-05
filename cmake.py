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


InstallExp = re.compile(r"^--\s+(Installing|Up-to-date):\s+([^\s].*)$")


def BuildDir(name):
   buildDir = excons.BuildBaseDirectory() + "/" + name
   if sys.platform == "win32":
      buildDir += "/msvc-%s" % excons.GetArgument("mscver", "10.0")
   return buildDir

def ConfigCachePath(name):
   return os.path.abspath(excons.out_dir + "/%s.cmake.config" % name)

def OutputsCachePath(name):
   return os.path.abspath(excons.out_dir + "/%s.cmake.outputs" % name)

def Outputs(name):
   lst = []
   cof = OutputsCachePath(name)
   if os.path.isfile(cof):
      with open(cof, "r") as f:
         lines = filter(lambda y: len(y)>0, map(lambda x: x.strip(), f.readlines()))
         lst = map(lambda x: excons.out_dir + "/" + x, lines)
   return lst

def Configure(name, opts={}):
   if GetOption("clean"):
      return True

   bld = BuildDir(name)
   relpath = os.path.relpath(os.path.abspath("."), bld)

   success = False

   with excons.SafeChdir(bld, tool="cmake"):
      cmd = "cmake "
      if sys.platform == "win32":
         try:
            mscver = float(excons.GetArgument("mscver", "10.0"))
            if mscver == 9.0:
               cmd += "-G \"Visual Studio 9 2008 Win64\" "
            elif mscver == 10.0:
               cmd += "-G \"Visual Studio 10 2010 Win64\" "
            elif mscver == 11.0:
               cmd += "-G \"Visual Studio 11 2012 Win64\" "
            elif mscver == 12.0:
               cmd += "-G \"Visual Studio 12 2013 Win64\" "
            elif mscver == 14.0:
               cmd += "-G \"Visual Studio 14 2015 Win64\" "
            else:
               excons.Print("Unsupported visual studio version %s" % mscver, tool="cmake")
               return False
         except:
            return False
      for k, v in opts.iteritems():
         cmd += "-D%s=%s " % (k, ("\"%s\"" % v if type(v) in (str, unicode) else v))
      cmd += "-DCMAKE_INSTALL_PREFIX=\"%s\" "  % excons.OutputBaseDirectory()
      if sys.platform != "win32":
         cmd += "-DCMAKE_SKIP_BUILD_RPATH=0 "
         cmd += "-DCMAKE_BUILD_WITH_INSTALL_RPATH=0 "
         cmd += "-DCMAKE_INSTALL_RPATH_USE_LINK_PATH=0 "
         if sys.platform == "darwin":
            cmd += "-DCMAKE_MACOSX_RPATH=1 "
      cmd += relpath

      excons.Print("Run Command: %s" % cmd, tool="cmake")
      p = subprocess.Popen(cmd, shell=True)
      p.communicate()

      success = (p.returncode == 0)

   return success

def Build(name, config=None, target=None):
   if GetOption("clean"):
      return True

   ccf = ConfigCachePath(name)
   cof = OutputsCachePath(name)

   if not os.path.isfile(ccf):
      return False

   success = False
   outfiles = []

   with excons.SafeChdir(BuildDir(name), tool="cmake"):
      if config is None:
         config = excons.mode_dir

      if target is None:
         target = "install"

      cmd = "cmake --build . --config %s --target %s" % (config, target)
      njobs = GetOption("num_jobs")
      if njobs > 1:
         if sys.platform == "win32":
            cmd += " -- /m:%d" % njobs
         else:
            cmd += " -- -j %d" % njobs

      excons.Print("Run Command: %s" % cmd, tool="cmake")
      p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

      buf = ""
      while p.poll() is None:
         r = p.stdout.readline(512)
         buf += r
         lines = buf.split("\n")
         if len(lines) > 1:
            for i in xrange(len(lines)-1):
               excons.Print(lines[i], tool="cmake")
               m = InstallExp.match(lines[i].strip())
               if m is not None:
                  outfiles.append(m.group(2))
            buf = lines[-1]
      excons.Print(buf, tool="cmake")

      success = (p.returncode == 0)

   # Write list of outputed files
   with open(cof, "w") as f:
      outfiles.sort()
      f.write("\n".join(excons.NormalizedRelativePaths(outfiles, excons.out_dir)))

   return success

def CleanOne(name):
   if not GetOption("clean"):
      return

   # Remove output files
   for path in Outputs(name):
      path = excons.out_dir + "/" + path
      if os.path.isfile(path):
         os.remove(path)
         excons.Print("Removed: '%s'" % excons.NormalizedRelativePath(path, excons.out_dir), tool="cmake")

   # Remove build temporary files      
   buildDir = BuildDir(name)
   if os.path.isdir(buildDir):
      shutil.rmtree(buildDir)
      excons.Print("Removed: '%s'" % excons.NormalizedRelativePath(buildDir, excons.out_dir), tool="cmake")

   path = ConfigCachePath(name)
   if os.path.isfile(path):
      os.remove(path)
      excons.Print("Removed: '%s'" % excons.NormalizedRelativePath(path, excons.out_dir), tool="cmake")

   path = OutputsCachePath(name)
   if os.path.isfile(path):
      os.remove(path)
      excons.Print("Removed: '%s'" % excons.NormalizedRelativePath(path, excons.out_dir), tool="cmake")

def Clean():
   if not GetOption("clean"):
      return

   allnames = map(lambda x: ".".join(os.path.basename(x).split(".")[:-2]), glob.glob(excons.out_dir + "/*.cmake.outputs"))

   if len(COMMAND_LINE_TARGETS) == 0:
      names = allnames[:]
   else:
      names = COMMAND_LINE_TARGETS

   for name in names:
      CleanOne(name)

