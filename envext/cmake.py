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
   return os.path.abspath(excons.out_dir + "/%s.cmake.outputs" % name)

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
   return os.path.abspath(excons.out_dir + "/%s.cmake.inputs" % name)

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
            lst += CollectFiles(d, pattern, recursive=rec)
      lst = filter(lambda x: x not in excl, NormalizedRelativePaths(lst, "."))
      with open(cif, "w") as f:
         lst.sort()
         f.write("\n".join(lst))
   lst.append(NormalizedRelativePath(BuildDir(name) + "/CMakeCache.txt", "."))
   return lst

def Configure(env, name, opts={}, internal=False):
   if not internal:
      env["CMAKE_PROJECT"] = name
      env["CMAKE_OPTIONS"] = opts
   
   if GetOption("clean"):
      return True

   cwd = os.path.abspath(".")
   buildDir = BuildDir(name)

   relpath = os.path.relpath(cwd, buildDir)
   if not os.path.isdir(buildDir):
      try:
         os.makedirs(buildDir)
      except:
         return False
   else:
      CMakeCache = buildDir + "/CMakeCache.txt"
      if os.path.isfile(CMakeCache):
         if not internal and int(ARGUMENTS.get("cmake-reconfigure", "0")) != 0:
            os.remove(CMakeCache)
            cif = InputsCachePath(name)
            if os.path.isfile(cif):
               os.remove(cif)
         else:
            return True

   excons.Print("Change Directory: '%s'" % buildDir, tool="cmake")
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
            excons.Print("Unsupported visual studio version %s" % mscver, tool="cmake")
            return False
      except:
         return False
   for k, v in opts.iteritems():
      cmd += "-D%s=%s " % (k, ("\"%s\"" % v if type(v) in (str, unicode) else v))
   cmd += "-DCMAKE_INSTALL_PREFIX=\"%s\" "  % excons.OutputBaseDirectory()
   cmd += "-DCMAKE_SKIP_BUILD_RPATH=0 "
   cmd += "-DCMAKE_BUILD_WITH_INSTALL_RPATH=0 "
   cmd += "-DCMAKE_INSTALL_RPATH_USE_LINK_PATH=0 "
   if sys.platform == "darwin":
      cmd += "-DCMAKE_MACOSX_RPATH=1 "
   cmd += relpath
   excons.Print("Run Command: %s" % cmd, tool="cmake")
   p = subprocess.Popen(cmd, shell=True)
   p.communicate()

   excons.Print("Change Directory: '%s'" % cwd, tool="cmake")
   os.chdir(cwd)

   return (p.returncode == 0)

def Build(env, name, config=None, target=None, opts={}):
   buildDir = BuildDir(name)

   if not Configure(env, name, opts, internal=True):
      return False

   cof = OutputsCachePath(name)
   cwd = os.path.abspath(".")

   excons.Print("Change Directory: '%s'" % buildDir, tool="cmake")
   os.chdir(buildDir)

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
   e = re.compile(r"^--\s+(Installing|Up-to-date):\s+([^\s].*)$")
   buf = ""
   outfiles = []
   while p.poll() is None:
      r = p.stdout.readline(512)
      buf += r
      lines = buf.split("\n")
      if len(lines) > 1:
         for i in xrange(len(lines)-1):
            excons.Print(lines[i], tool="cmake")
            m = e.match(lines[i].strip())
            if m is not None:
               outfiles.append(m.group(2))
         buf = lines[-1]
   excons.Print(buf, tool="cmake")

   with open(cof, "w") as f:
      outfiles.sort()
      f.write("\n".join(NormalizedRelativePaths(outfiles, cwd)))

   excons.Print("Change Directory: '%s'" % cwd, tool="cmake")
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
         excons.Print("Removed: '%s'" % NormalizedRelativePath(buildDir, "."), tool="cmake")


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

   IncludeCommentPattern = re.compile(r"(//.*$|/\*|\*/)|(^\s*#\s*include\s+([\"<])([^\"<>]+)[>\"])", re.MULTILINE)

   # Custom C/C++ file scanner
   def CScanner(node, env, path):
      searchpath = map(str, path)
      rv = []
      try:
         cmtlvl = 0
         cmtlin = 0
         posoff = 0
         linoff = 0
         nd = os.path.dirname(str(node))
         with open(str(node), "r") as f:
            content = f.read()
            m = IncludeCommentPattern.search(content)
            while m is not None:
               if m.group(1):
                  cmt = m.group(1)
                  if not cmt.startswith("//"):
                     if cmt == "/*":
                        cmtlvl += 1
                     else:
                        cmtlvl -= 1
                        if cmtlvl < 0:
                           raise Exception("Comment Block Mismatch")
               else:
                  if cmtlvl == 0:
                     f = m.group(4)
                     ignore = False
                     if m.group(3) == "\"":
                        ignore = os.path.isfile(nd + "/" + f)
                     if not ignore:
                        for p in searchpath:
                           if os.path.isfile(p + "/" + f):
                              ignore = True
                              break
                     if not ignore:
                        rv.append(f)
               content = content[m.end():]
               m = IncludeCommentPattern.search(content)
         return rv
      except Exception, e:
         print("CScanner Failed on '%s': %s" % (str(node), e))
         return []

   # Dummy Scanner
   def DummyScanner(node, env, path):
      return []

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

   # Override default C/C++ file scanner to avoid SCons begin to nosy
   cexts = [".c", ".h", ".cc", ".hh", ".cpp", ".hpp", ".cxx", ".hxx"]
   env.Prepend(SCANNERS=Scanner(function=DummyScanner, skeys=cexts))

