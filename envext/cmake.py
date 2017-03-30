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

def BuildDir(name):
   buildDir = excons.BuildBaseDirectory() + "/" + name
   if sys.platform == "win32":
      buildDir += "/msvc-%s" % excons.GetArgument("mscver", "10.0")
   return buildDir

def OutputsCachePath(name):
   return os.path.abspath("./%s.cmake.outputs" % name)

def Outputs(env, exclude=[]):
   name = env["CMAKE_PROJECT"]
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
   return os.path.abspath("./%s.cmake.inputs" % name)

def Inputs(env, dirs=[], patterns=[], exclude=[]):
   name = env["CMAKE_PROJECT"]
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
         lst += CollectFiles(d, "CMakeLists.txt", recursive=rec)
         for pattern in patterns:
            lst += CollectFiles(".", pattern, recursive=rec)
      lst = filter(lambda x: x not in excl, NormalizedRelativePaths(lst, "."))
      with open(cif, "w") as f:
         f.write("\n".join(lst))
   lst.append(NormalizedRelativePath(BuildDir(name) + "/CMakeCache.txt", "."))
   return lst

def Configure(env, name, opts={}, internal=False):
   if not internal:
      env["CMAKE_PROJECT"] = name
      env["CMAKE_OPTIONS"] = opts
   
   if GetOption("clean"):
      return

   buildDir = BuildDir(name)

   relpath = os.path.relpath(".", buildDir)
   if not os.path.isdir(buildDir):
      try:
         os.makedirs(buildDir)
      except:
         return False
   else:
      CMakeCache = buildDir + "/CMakeCache.txt"
      if os.path.isfile(CMakeCache):
         if not internal and excons.GetArgument("cmake-reconfigure", 0, int) != 0:
            os.remove(CMakeCache)
            cif = InputsCachePath(name)
            if os.path.isfile(cif):
               os.remove(cif)
         else:
            return True
   
   os.chdir(buildDir)

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
            print("Unsupported visual studio version %s" % mscver)
            return False
      except:
         return False
   for k, v in opts.iteritems():
      cmd += "-D%s=%s " % (k, ("\"%s\"" % v if type(v) in (str, unicode) else v))
   cmd += "-DCMAKE_INSTALL_PREFIX=\"%s\" "  % excons.OutputBaseDirectory()
   cmd += relpath
   print("Run Command: %s" % cmd)
   p = subprocess.Popen(cmd, shell=True)
   p.communicate()

   os.chdir(relpath)

   return (p.returncode == 0)

def Build(env, name, config=None, target=None, opts={}):
   buildDir = BuildDir(name)

   if not Configure(env, name, opts, internal=True):
      return False

   cof = OutputsCachePath(name)
   cwd = os.path.abspath(".")

   os.chdir(buildDir)

   if config is None:
      config = excons.mode_dir
   if target is None:
      target = "install"
   cmd = "cmake --build . --config %s --target %s" % (config, target)
   print("Run Command: %s" % cmd)
   p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
   e = re.compile(r"^--\s+(Installing|Up-to-date):\s+([^\s].*)$")
   buf = ""
   outfiles = []
   while p.poll() is None:
      r = p.stdout.readline(512)
      buf += r
      lines = buf.split("\n")
      if len(lines) > 1:
         for i in xrange(len(lines)-1):
            print(lines[i])
            m = e.match(lines[i])
            if m is not None:
               outfiles.append(m.group(2))
         buf = lines[-1]
   print(buf)

   with open(cof, "w") as f:
      f.write("\n".join(NormalizedRelativePaths(outfiles, cwd)))

   os.chdir(cwd)

   return (p.returncode == 0)

def Clean(env):
   name = env["CMAKE_PROJECT"]
   if not GetOption("clean"):
      return
   if len(COMMAND_LINE_TARGETS) == 0 or name in COMMAND_LINE_TARGETS:
      buildDir = BuildDir(name)
      if os.path.isdir(buildDir):
         shutil.rmtree(buildDir)
         print("Removed %s" % NormalizedRelativePath(buildDir, "."))


# === Setup environment ===

def SetupEnvironment(env):
   def GeneratedAction(target, source, env):
      return None

   def BuildAction(target, source, env):
      name = env["CMAKE_PROJECT"]
      opts = (env["CMAKE_OPTIONS"] if "CMAKE_OPTIONS" in env else {})
      config = (env["CMAKE_CONFIG"] if "CMAKE_CONFIG" in env else None)
      target = (env["CMAKE_TARGET"] if "CMAKE_TARGET" in env else None)
      Build(env, name, config=config, target=target, opts=opts)
      return None

   # Required
   #   env["CMAKE_PROJECT"] = <name>
   # Optional
   #   env["CMAKE_OPTIONS"] ( = {} )
   #   env["CMAKE_CONFIG"]  ( = "release" | "debug" )
   #   env["CMAKE_TARGET"]  ( = "install" )

   env.AddMethod(Inputs, "CMakeInputs")
   env.AddMethod(Outputs, "CMakeOutputs")
   env.AddMethod(Configure, "CMakeConfigure")
   env.AddMethod(Build, "CMakeBuild")
   env.AddMethod(Clean, "CMakeClean")

   env["BUILDERS"]["CMake"] = Builder(action=Action(BuildAction, "Build using CMake ..."))
   env["BUILDERS"]["CMakeGenerated"] = Builder(action=Action(GeneratedAction, "Generate $TARGET using CMake ..."))

