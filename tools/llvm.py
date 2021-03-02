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
import excons
import subprocess


def _CleanList(lst):
   return filter(lambda x: len(x) > 0, map(lambda y: y.strip(), lst))

def _FlagsToList(flags):
   spl1 = flags.split(" ")
   spl2 = []
   openc = None
   for i in xrange(len(spl1)):
      li = len(spl1[i])
      if openc is not None:
         spl2[-1] += " "
         if li > 0:
            spl2[-1] += " " + spl1[i]
            if spl1[i][-1] == openc:
               openc = None
      else:
         if li == 0:
            continue
         elif spl1[i][0] == "\"":
            if li < 2 or spl1[i][-1] != "\"":
               openc = "\""
         elif spl1[i][0] == "\'":
            if li < 2 or spl1[i][-1] != "\'":
               openc = "\'"
         spl2.append(spl1[i])
   return _CleanList(spl2)

def _LibName(x):
   return (os.path.splitext(os.path.basename(x))[0] if sys.platform == "win32" else x)

def _IsIncludeFlag(x):
   if x.startswith("-I"):
      return True
   else:
      return (x.startswith("/I") if sys.platform == "win32" else False)

# ===---

llvm_cfg = None

def GetLLVMConfig(components=None):
   global llvm_cfg

   if llvm_cfg is None:
      exesuffix = ("" if sys.platform != "win32" else ".exe")

      llvm_incdir, llvm_libdir = excons.GetDirs("llvm", silent=False)

      llvm_config = None

      if llvm_incdir:
         path = os.path.dirname(llvm_incdir) + "/bin/llvm-config" + exesuffix
         if os.path.isfile(path):
            llvm_config = path

      if llvm_config is None:
         if llvm_libdir:
            path = os.path.dirname(llvm_libdir) + "/bin/llvm-config" + exesuffix
            if os.path.isfile(path):
               llvm_config = path

      if llvm_config is None:
         for d in os.environ["PATH"].split(os.pathsep):
            path = d + "/llvm-config" + exesuffix
            if os.path.isfile(path):
               llvm_config = path
               break

      if llvm_config is None:
         excons.WarnOnce("Could not find 'llvm-config'", tool="llvm")
         sys.exit(1)

      excons.PrintOnce("Use '%s'" % llvm_config, tool="llvm")

      llvm_cfg = {}
      procargs = {"shell": True, "stdout": subprocess.PIPE, "stderr": subprocess.STDOUT}

      if llvm_incdir:
         llvm_cfg["incdir"] = llvm_incdir

      if llvm_libdir:
         llvm_cfg["libdir"] = llvm_libdir

      cmd = "%s --version" % llvm_config
      p = subprocess.Popen(cmd, **procargs)
      out, _ = p.communicate()
      if p.returncode == 0:
         llvm_cfg["version_str"] = out.strip()
         spl = llvm_cfg["version_str"].split(".")
         llvm_cfg["version_major"] = int(spl[0])
         llvm_cfg["version_minor"] = int(spl[1])
      else:
         excons.WarnOnce("'%s' command failed." % cmd, tool="llvm")
         llvm_cfg["verison_str"] = ""
         llvm_cfg["verison_major"] = 0
         llvm_cfg["verison_minor"] = 0

      cmd = "%s --cppflags" % llvm_config
      p = subprocess.Popen(cmd, **procargs)
      out, _ = p.communicate()
      if p.returncode == 0:
         cppflags = out.strip()
         llvm_cfg["cppflags"] = " " + " ".join(filter(lambda x: not _IsIncludeFlag(x), _FlagsToList(cppflags)))
      else:
         excons.WarnOnce("'%s' command failed." % cmd, tool="llvm")
         llvm_cfg["cppflags"] = ""

      cmd = "%s --cxxflags" % llvm_config
      p = subprocess.Popen(cmd, **procargs)
      out, _ = p.communicate()
      if p.returncode == 0:
         cxxflags = _FlagsToList(out.strip())
         if sys.platform != "win32":
            llvm_cfg["rtti"] = (not "-fno-rtti" in cxxflags)
            llvm_cfg["exceptions"] = (not "-fno-exceptions" in cxxflags)
         else:
            llvm_cfg["rtti"] = (not "/GR-" in cxxflags)
            llvm_cfg["exceptions"] = (not "/EHs-c-" in cxxflags)
      else:
         excons.WarnOnce("'%s' command failed." % cmd, tool="llvm")

      cmd = "%s --libs" % llvm_config
      if components:
         if type(components) in (str, unicode):
            cmd += " %s" % components
         elif type(components) in (tuple, list, set):
            cmd += " %s" % " ".join(components)
         else:
            excons.WarnOnce("'components' should either be a string or a list of strings.", tool="llvm")
      p = subprocess.Popen(cmd, **procargs)
      out, _ = p.communicate()
      if p.returncode == 0:      
         libs = []
         for l in out.split("\n"):
            lst = map(_LibName, (_FlagsToList(l) if sys.platform == "win32" else _CleanList(l.split("-l"))))
            libs.extend(lst)
         llvm_cfg["libs"] = libs
      else:
         excons.WarnOnce("'%s' command failed." % cmd, tool="llvm")
         llvm_cfg["libs"] = []

      cmd = "%s --system-libs" % llvm_config
      p = subprocess.Popen(cmd, **procargs)
      out, _ = p.communicate()
      if p.returncode == 0:
         libs = []
         for l in out.split("\n"):
            lst = map(_LibName, (_FlagsToList(l) if sys.platform == "win32" else _CleanList(l.split("-l"))))
            libs.extend(lst)
         llvm_cfg["syslibs"] = libs
      else:
         excons.WarnOnce("'%s' command failed." % cmd, tool="llvm")
         llvm_cfg["syslibs"] = []

   return llvm_cfg


def GetOptionsString():
  return """LLVM OPTIONS
  with-llvm=<path>     : LLVM prefix                []
  with-llvm-inc=<path> : LLVM headers directory     [<prefix>/include]
  with-llvm-lib=<path> : LLVM libraries directory   [<prefix>/lib]"""

def Require(min_version=None, require_rtti=False, require_exceptions=False, components=None):
   cfg = GetLLVMConfig(components)

   if min_version is not None:
      rmaj, rmin = None, None
      if type(min_version) in (str, unicode):
         try:
            rmaj, rmin = map(int, min_version.split("."))
         except Exception, e:
            excons.WarnOnce("Invalid version requirement '%s' (%s). Skip version check." % (min_version, e), tool="llvm")
      elif type(min_version) in (list, tuple):
         try:
            rmaj, rmin = int(min_version[0]), int(min_version[1])
         except Exception, e:
            excons.WarnOnce("Invalid version requirement %s (%s). Skip version check." % (min_version, e), tool="llvm")
      if rmaj is not None and rmin is not None:
         if cfg["version_major"] != rmaj:
            excons.WarnOnce("Unsupported LLVM version %d.%d." % (cfg["version_major"], cfg["version_minor"]))            
            sys.exit(1)
         if cfg["version_minor"] < rmin:
            excons.WarnOnce("Unsupported LLVM version %d.%d." % (cfg["version_major"], cfg["version_minor"]))            
            sys.exit(1)

   if require_rtti and not cfg["rtti"]:
      excons.WarnOnce("Require LLVM with RTTI enabled.", tool="llvm")
      sys.exit(1)

   if require_exceptions and not cfg["exceptions"]:
      excons.WarnOnce("Require LLVM with exceptions enabled.", tool="llvm")
      sys.exit(1)

   def _RequireLLVM(env):
      env.Append(CPPFLAGS=cfg["cppflags"])
      if "incdir" in cfg:
         env.Append(CPPPATH=[cfg["incdir"]])
      if "libdir" in cfg:
         env.Append(LIBPATH=[cfg["libdir"]])
      for lib in cfg["libs"]:
         excons.Link(env, lib, static=True, force=True, silent=False)
      env.Append(LIBS=cfg["syslibs"])

      excons.AddHelpOptions(llvm=GetOptionsString())

   return _RequireLLVM

