# Copyright (C) 2009, 2010  Gaetan Guidet
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
import glob as _glob
import platform
import re
import sys
import imp
import atexit
import string
import subprocess
from SCons.Script import *


VCD = set([".git", ".hg", ".svn"])


args_cache_path = None
args_cache = None
args_cache_echo = False
args_no_cache = False
bld_dir = None
out_dir = None
mode_dir = None
arch_dir = "x86" if platform.architecture()[0] == '32bit' else "x64"
mscver = None
no_arch = False
warnl = "all"
issued_warnings = set()
printed_messages = set()
all_targets = {}
all_progress = []
ignore_help = False
help_targets = {}
help_options = {}
ext_types = {}


def abspath(path):
  return os.path.abspath(path).replace("\\", "/")

def joinpath(*parts):
  return os.path.join(*parts).replace("\\", "/")

def glob(pat):
  return map(lambda x: x.replace("\\", "/"), _glob.glob(pat))

def InitGlobals(output_dir=".", force=False):
  global args_cache, args_cache_path, args_no_cache
  global bld_dir, out_dir, mode_dir, arch_dir
  global mscver, no_arch, warnl, issued_warnings
  global all_targets, all_progress
  global ignore_help, help_targets, help_options
  global ext_types

  if bld_dir is None or force:
    bld_dir = abspath("./.build")

  if out_dir is None or force:
    if not output_dir:
      output_dir = "."
  
    if not os.path.isdir(output_dir):
      try:
        os.makedirs(output_dir)
      except:
        sys.exit(1)

    out_dir = abspath(output_dir)

  if args_cache_path is None or force:
    cache_path = abspath("./excons.cache")
  
    if cache_path != args_cache_path:
      if args_cache and not args_no_cache:
        args_cache.write()
    
      args_cache_path = cache_path
      args_cache = None
      args_no_cache = False
  
  if force:
    mode_dir = None
    arch_dir = "x86" if platform.architecture()[0] == '32bit' else "x64"
    mscver = None
    no_arch = False  # Whether or not to create architecture in output directory
    warnl = "all"  # Warning level
    issued_warnings = set()
    printed_messages = set()
    all_targets = {}
    all_progress = []
    ignore_help = False
    help_targets = {}
    help_options = {}
    ext_types = {}


class Cache(dict):
  def __init__(self, *args, **kwargs):
    super(Cache, self).__init__(*args, **kwargs)
    super(Cache, self).__setitem__(sys.platform, {})
    self.updated = False
  
  def write(self):
    global args_cache_path, args_cache_echo
    
    if self.updated:
      import pprint
      
      if args_cache_echo:
        print("[excons] Write excons.cache: %s" % args_cache_path)
      f = open(args_cache_path, "w")
      pprint.pprint(self, f)
      f.write("\n")
      f.close()
      
      self.updated = False
  
  def __setitem__(self, k, v):
    global args_cache_echo

    pd = super(Cache, self).__getitem__(sys.platform)
    if pd.get(k, None) != v:
      if args_cache_echo:
        print("[excons] Update cache: %s = %s" % (k, v))
      pd[k] = v
      self.updated = True
  
  def __getitem__(self, k):
    return super(Cache, self).__getitem__(sys.platform)[k]
  
  def remove(self, k):
    pd = super(Cache, self).__getitem__(sys.platform)
    if k in pd:
      if args_cache_echo:
        print("[excons] Delete cache: %s" % k)
      del(pd[k])
      self.updated = True
  
  def get(self, k, default=None):
    try:
      return self[k]
    except:
      return default
  
  def rawset(self, k, v):
    super(Cache, self).__setitem__(k, v)

  def keys(self):
    return super(Cache, self).__getitem__(sys.platform).keys()



def GetArgument(key, default=None, convert=None):
  global args_cache, args_cache_path, args_no_cache, args_cache_echo
  
  if args_no_cache:
    rv = ARGUMENTS.get(key, default)
  
  else:
    if args_cache is None:
      # First call to GetArgument (as args_no_cache is False by default)
      
      if int(ARGUMENTS.get("no-cache", "0")):
        args_no_cache = True
        return GetArgument(key, default, convert)
      
      args_cache = Cache()
      
      if os.path.exists(args_cache_path):
        print("[excons] Read excons.cache: %s" % args_cache_path)
        import ast
        import copy
        
        f = open(args_cache_path, "r")
        cc = f.read()
        f.close()
        
        try:
          d = ast.literal_eval(cc)
          for k, v in d.iteritems():
            if k == sys.platform:
              for k2, v2 in v.iteritems():
                print("[excons]  %s = %s" % (k2, v2))
            args_cache.rawset(k, copy.deepcopy(v))
        except Exception, e:
          print(e)
          args_cache.clear()
    
    # What if cache was modified in the meantime
    # => happens when using SConscript("path/to/another/SConstruct")
    
    rv = ARGUMENTS.get(key, None)
    
    if rv is None:
      rv = args_cache.get(key, None)
      
      if rv is None:
        return default
    
    else:
      args_cache[key] = rv
  
  if convert:
    try:
      return convert(rv)
    except:
      print("[excons] Failed to convert \"%s\" value" % key)
      return default
  
  else:
    return rv

def SetArgument(key, value, cache=False):
  global args_cache, args_no_cache
  
  ARGUMENTS[key] = str(value)
  
  if not args_no_cache and cache:
    if args_cache is None:
      # force creation
      GetArgument("__dummy__")
    
    args_cache[key] = str(value)

def RemoveCacheKey(key):
  global args_cache, args_no_cache
  
  if not args_no_cache:
    if args_cache is None:
      # force creation
      GetArgument("__dummy__")
    
    args_cache.remove(key)

def Which(target):
  pathsplit = None
  texp = None
  
  if sys.platform == "win32":
    pathsplit = ";"
    if re.search(r"\.(exe|bat)$", target, re.IGNORECASE) is None:
      texp = re.compile(r"%s\.(exe|bat)" % target, re.IGNORECASE)
    else:
      texp = re.compile(target, re.IGNORECASE)
  else:
    pathsplit = ":"
    texp = re.compile(target)
  
  if "PATH" in os.environ:
    paths = filter(lambda x: len(x) > 0, map(lambda x: x.strip(), os.environ["PATH"].split(pathsplit)))
    for path in paths:
      for item in glob(joinpath(path, "*")):
        if os.path.isdir(item):
          continue
        bn = os.path.basename(item)
        if texp.match(bn) is not None:
          return item.replace("\\", "/")
  
  return None

def NoConsole(env):
  if str(Platform()) == "win32":
    env.Append(LINKFLAGS=" /subsystem:windows /entry:mainCRTStartup")

def ParseStackSize(s):
  if not s:
    return None
  m = re.match(r"(\d+)([mk])?", s)
  if m:
    sz = int(m.group(1))
    if m.group(2):
      if m.group(2) == "k":
        sz *= 1024
      else:
        sz *= 1024 * 1024
    return sz
  else:
    return None

def SetStackSize(env, size):
  if size:
    if sys.platform == "win32":
      env.Append(LINKFLAGS=" /stack:0x%x" % size)
    elif sys.platform == "darwin":
      env.Append(LINKFLAGS=" -Wl,-stack_size,0x%x" % size)
    else:
      env.Append(LINKFLAGS=" -Wl,--stack,0x%x" % size)

def SetRPath(env, settings, relpath=None, rpaths=[""]):
  if sys.platform != "win32":
    osx = (sys.platform == "darwin")
    
    all_rpaths = rpaths[:]
    
    # Keep 'relpath' for backward compatibility
    if relpath:
      all_rpaths.append(relpath)
    
    # Keep 'rpath' for backward compatibility (string expected)
    additional_rpath = settings.get("rpath", None)
    if additional_rpath and not additional_rpath in all_rpaths:
      all_rpaths.append(additional_rpath)
    
    # New 'rpaths' setting (string or collection)
    additional_rpaths = settings.get("rpaths", [])
    if type(additional_rpaths) in (str, unicode):
      additional_rpaths = [additional_rpaths]
    for rpath in additional_rpaths:
      if not rpath in all_rpaths:
        all_rpaths.append(rpath)
    
    for i in xrange(len(all_rpaths)):
      path = all_rpaths[i]
      if path is None:
        continue
      
      if not path.startswith("/"):
        if path:
          all_rpaths[i] = "%s/%s" % (("@loader_path" if osx else "$$ORIGIN"), path)
        else:
          all_rpaths[i] = ("@loader_path" if osx else "$$ORIGIN")
    
    # Remove -Wl,-rpath, not already in flags
    curlinkflags = str(env["LINKFLAGS"])
    linkflags = re.sub(r"\s*-Wl,-rpath,[^\s]*", "", curlinkflags)
    if linkflags != curlinkflags:
      print("Removed -Wl,-rpath from LINKFLAGS ('%s' -> '%s')" % (curlinkflags, linkflags))
      env["LINKFLAGS"] = linkflags
    
    
    if not osx:
      # enquotes because of possible $ sign
      rpath = "'%s'" % ":".join(all_rpaths)
      env.Append(LINKFLAGS=" -Wl,-rpath,%s,--enable-new-dtags" % rpath)
    else:
      rpath = ",".join(map(lambda x: "-rpath,%s" % x, all_rpaths))
      env.Append(LINKFLAGS=" -Wl,%s" % rpath)

def Build32():
  global arch_dir
  return (arch_dir != "x64")

def Build64():
  global arch_dir
  return (arch_dir == "x64")

def WarnOnce(msg, tool=None):
  global issued_warnings
  
  if not msg in issued_warnings:
    if tool is None:
      hdr = ""
    else:
      hdr = "[%s]" % tool
    first = True
    for line in msg.split("\n"):
      if first:
        print("[excons]%s ! %s" % (hdr, line))
        first = False
      else:
        print("[excons]%s   %s" % (hdr, line))
    issued_warnings.add(msg)

def Print(msg, tool=None):
  hdr = ("" if tool is None else "[%s]" % tool)
  for line in msg.split("\n"):
    print("[excons]%s %s" % (hdr, line))

def PrintOnce(msg, tool=None):
  global printed_messages
  
  if not msg in printed_messages:
    if tool is None:
      hdr = ""
    else:
      hdr = "[%s]" % tool
    for line in msg.split("\n"):
      print("[excons]%s %s" % (hdr, line))
    printed_messages.add(msg)

def WarnConfig():
  WarnOnce("Build configuration may be incomplete (use 'scons -h' to list available options)")

def IsBuildOutput(path):
  p0 = OutputBaseDirectory()
  p1 = abspath(path)
  if sys.platform == "win32":
    p0 = p0.replace("\\", "/").lower()
    p1 = p1.replace("\\", "/").lower()
  return p1.startswith(p1)

def GetDirs(name, incdirname="include", libdirname="lib", libdirarch=None, noexc=True, silent=False):
  global arch_dir
  
  prefixflag = "with-%s" % name
  incflag = "%s-inc" % prefixflag
  libflag = "%s-lib" % prefixflag
  incvar = name.upper().replace("-", "_") + "_INCLUDE"
  libvar = name.upper().replace("-", "_") + "_LIB"
  prefixsrc = None
  incsrc = None
  libsrc = None
  
  prefix = None
  prefixinc = None
  prefixlib = None
  inc = None
  lib = None
  
  # Priority (highest -> lowest)
  #   inc/lib flag
  #   prefix flag
  #   inc/lib env var
  #   inc/lib cache
  #   prefix cache
  
  def errorwarn(msg):
    if noexc:
      if not silent:
        WarnOnce(msg)
    else:
        raise Exception(msg)
  
  # Read prefix directory from flag or cache
  prefix = GetArgument(prefixflag)
  if prefix:
    prefix = abspath(os.path.expanduser(prefix))
    if not os.path.isdir(prefix) and not IsBuildOutput(prefix):
      errorwarn("Invalid %s prefix directory %s." % (name, prefix))
      prefix = None
    else:
      # This won't update cache
      prefixsrc = ("flag" if prefixflag in ARGUMENTS else "cache")
      prefixinc = "%s/%s" % (prefix, incdirname)
      prefixlib = "%s/%s" % (prefix, libdirname)
      mode = (GetArgument("libdir-arch", "none") if libdirarch is None else libdirarch)
      if mode == "subdir":
        prefixlib += "/%s" % arch_dir
      elif mode == "suffix" and Build64():
        prefixlib += "64"
      SetArgument(prefixflag, prefix)
  else:
    prefix = None
  
  # Read include directory from flag or cache, fallback to prefixinc
  inc = GetArgument(incflag)
  if inc:
    inc = abspath(os.path.expanduser(inc))
    if not os.path.isdir(inc) and not IsBuildOutput(inc):
      errorwarn("Invalid %s include directory %s." % (name, inc))
      inc = None
    else:
      incsrc = ("flag" if incflag in ARGUMENTS else "cache")
      if incsrc == "cache" and prefixsrc == "flag":
        inc = prefixinc
        incsrc = "flag"
  else:
    inc = prefixinc
    incsrc = prefixsrc
  
  # Warn if value present in environment is to be ignored
  if incvar in os.environ:
    if inc is None or incsrc == "cache":
      val = os.environ[incvar]
      if val:
        val = abspath(os.path.expanduser(val))
        if os.path.isdir(val):
          msg = "Use environment key %s value." % incvar
          WarnOnce(msg)
          inc = val
          incsrc = "environment"
    else:
      msg = "Ignore environment key %s value." % incvar
      WarnOnce(msg)
  
  # Read library directory from flag or cache, fallback to prefixlib
  lib = GetArgument(libflag)
  if lib:
    lib = abspath(os.path.expanduser(lib))
    if not os.path.isdir(lib) and not IsBuildOutput(lib):
      errorwarn("Invalid %s library directory %s." % (name, lib))
      lib = None
    else:
      libsrc = ("flag" if libflag in ARGUMENTS else "cache")
      if libsrc == "cache" and prefixsrc == "flag":
        lib = prefixlib
        libsrc = "flag"
  else:
    lib = prefixlib
    libsrc = prefixsrc
  
  # Warn if value present in environment is to be ignored
  if libvar in os.environ:
    if lib is None or libsrc == "cache":
      val = os.environ[libvar]
      if val:
        val = abspath(os.path.expanduser(val))
        if os.path.isdir(val):
          msg = "Use environment key %s value." % libvar
          WarnOnce(msg)
          lib = val
          libsrc = "environment"
    else:
      msg = "Ignore environment key %s value." % libvar
      WarnOnce(msg)
  
  if inc is None or lib is None:
    if not silent:
      WarnConfig()

  if inc and incsrc != "environment":
    SetArgument(incflag, inc)
  if lib and libsrc != "environment":
    SetArgument(libflag, lib)
  
  return (inc, lib)

def GetDirsWithDefault(name, incdirname="include", libdirname="lib", libdirarch=None, incdirdef=None, libdirdef=None, noexc=True, silent=False):
  inc_dir, lib_dir = GetDirs(name, incdirname=incdirname, libdirname=libdirname, libdirarch=libdirarch, noexc=True, silent=True)
  
  if inc_dir is None:
    inc_dir = incdirdef
  
  if lib_dir is None:
    lib_dir = libdirdef
  
  if inc_dir is None or lib_dir is None:
    if not silent:
      WarnConfig()
    # msg = "%s directories not set.\nUse with-%s=, with-%s-inc=, with-%s-lib= flags." % (name, name, name, name)
    # if noexc:
    #   if not silent:
    #     WarnOnce(msg)
    # else:
    #   raise Exception(msg)
  
  return (inc_dir, lib_dir)

def SharedLibraryLinkExt():
  if sys.platform == "win32":
    return ".lib"
  elif sys.platform == "darwin":
    return ".dylib"
  else:
    return ".so"

def LibraryFullpath(env, lib, static=False):
  paths = env["LIBPATH"][:]

  basename = lib

  if sys.platform == "win32":
    # Use import library for dlls
    basename += ".lib"

  else:
    global arch_dir

    basename = "lib%s%s" % (lib, ".a" if static else SharedLibraryLinkExt())

    if arch_dir == "x64":
      if not "/usr/local/lib64" in paths:
        paths.append("/usr/local/lib64")
      if not "/usr/lib64" in paths:
        paths.append("/usr/lib64")
    if not "/usr/local/lib" in paths:
      paths.append("/usr/local/lib")
    if not "/usr/lib" in paths:
      paths.append("/usr/lib")

  for path in paths:
    libpath = "%s/%s" % (path, basename)
    if os.path.isfile(libpath):
      return libpath

  return None

def StaticallyLink(env, lib, silent=False):
  if os.path.isabs(lib):
    fullpath = lib
  else:
    fullpath = LibraryFullpath(env, lib, static=True)
  if fullpath is None:
    if not silent:
      WarnOnce("Could not find static lib for '%s'" % lib)
    return False
  else:
    env.Append(LIBS=[env.File(fullpath)])
    return True

def Link(env, lib, static=False, force=True, silent=False):
  if os.path.isabs(lib):
    fullpath = lib
  else:
    fullpath = LibraryFullpath(env, lib, static=static)
  if fullpath is None:
    if not silent:
      WarnOnce("Could not find %s lib for '%s'" % ("static" if static else "shared", lib))
    if force:
      env.Append(LIBS=[lib])
  else:
    env.Append(LIBS=[env.File(fullpath)])

def CollectFiles(directory, patterns, recursive=True, exclude=[]):
  global VCD

  allfiles = None
  rv = []

  if type(directory) in (list, tuple, set):
    for d in directory:
      rv.extend(CollectFiles(d, patterns, recursive=recursive, exclude=exclude))

  else:
    for pattern in patterns:
      if type(pattern) in (str, unicode):
        items = glob(directory + "/" + pattern)
        for item in items:
          rv.append(item)
      else:
        allfiles = glob(directory + "/*")
        rv.extend(filter(lambda x: pattern.match(x) is not None, allfiles))

    if recursive:
      if allfiles is None:
        allfiles = glob(directory + "/*")
      for subdir in filter(os.path.isdir, allfiles):
        dn = os.path.basename(subdir)
        if dn in VCD or dn in exclude:
          continue
        rv += CollectFiles(subdir, patterns, recursive=True, exclude=exclude)

  return rv

def NormalizedRelativePath(path, baseDirectory):
  return os.path.relpath(path, baseDirectory).replace("\\", "/")

def NormalizedRelativePaths(paths, baseDirectory):
  return map(lambda x: NormalizedRelativePath(x, baseDirectory), paths)

def MakeBaseEnv(noarch=None, output_dir="."):
  global bld_dir, out_dir, mode_dir, arch_dir, mscver, no_arch, warnl, ext_types
  
  InitGlobals(output_dir, force=(int(ARGUMENTS.get("shared-build", "1")) == 0))

  no_arch = (GetArgument("no-arch", 1, int) == 1)
  
  warnl = GetArgument("warnings", "all")
  if not warnl in ["none", "std", "all"]:
    print("[excons] Warning: Invalid warning level \"%s\". Should be one of: none, std, all. Defaulting to \"all\"" % warnl)
    warnl = "all"
  
  warne = (GetArgument("warnings-as-errors", 0, int) != 0)
  
  arch_over = GetArgument("x64")
  if arch_over is not None:
    if int(arch_over) == 1:
      arch_dir = "x64"
    else:
      arch_dir = "x86"
  else:
    arch_over = GetArgument("x86")
    if arch_over is not None:
      if int(arch_over) == 1:
        arch_dir = "x86"
      else:
        arch_dir = "x64"
  
  if noarch is not None:
    no_arch = noarch
  
  def SetupMSVCDebug(env):
    env.Append(CPPFLAGS=" /MDd /Od /Zi")
    env.Append(CPPDEFINES=["_DEBUG"])
    env.Append(LINKFLAGS=" /debug /opt:noref /opt:noicf /incremental:yes")
  
  def SetupMSVCRelease(env):
    env.Append(CPPFLAGS=" /Gy /MD /O2")
    env.Append(CPPDEFINES=["NDEBUG"])
    env.Append(LINKFLAGS=" /release /opt:ref /opt:icf /incremental:no")
  
  def SetupMSVCReleaseWithDebug(env):
    env.Append(CPPFLAGS=" /MD /Od /Zi")
    env.Append(CPPDEFINES=["NDEBUG"])
    env.Append(LINKFLAGS=" /debug /opt:noref /opt:noicf /incremental:yes")
  
  def SetupGCCDebug(env):
    if arch_dir == "x64":
      if str(Platform()) == "darwin":
        env.Append(CCFLAGS="-arch x86_64")
        env.Append(LINKFLAGS="-arch x86_64")
      else:
        env.Append(CCFLAGS="-m64")
        env.Append(LINKFLAGS="-m64")
    else:
      if str(Platform()) == "darwin":
        env.Append(CCFLAGS="-arch i386")
        env.Append(LINKFLAGS="-arch i386")
      else:
        env.Append(CCFLAGS="-m32")
        env.Append(LINKFLAGS="-m32")
    
    env.Append(CPPFLAGS=" -O0 -g -ggdb")
    env.Append(CPPDEFINES=["_DEBUG"])
  
  def SetupGCCRelease(env):
    if arch_dir == "x64":
      if str(Platform()) == "darwin":
        env.Append(CCFLAGS="-arch x86_64")
        env.Append(LINKFLAGS="-arch x86_64")
      else:
        env.Append(CCFLAGS="-m64")
        env.Append(LINKFLAGS="-m64")
    else:
      if str(Platform()) == "darwin":
        env.Append(CCFLAGS="-arch i386")
        env.Append(LINKFLAGS="-arch i386")
      else:
        env.Append(CCFLAGS="-m32")
        env.Append(LINKFLAGS="-m32")
    
    env.Append(CPPFLAGS=" -O3")
    env.Append(CPPDEFINES=["NDEBUG"])
    
    if GetArgument("strip", 0, int):
      if str(Platform()) == "darwin":
        env.Append(LINKFLAGS=" -Wl,-dead_strip")
      else:
        env.Append(LINKFLAGS=" -s")
  
  def SetupGCCReleaseWithDebug(env):
    if arch_dir == "x64":
      if str(Platform()) == "darwin":
        env.Append(CCFLAGS="-arch x86_64")
        env.Append(LINKFLAGS="-arch x86_64")
      else:
        env.Append(CCFLAGS="-m64")
        env.Append(LINKFLAGS="-m64")
    else:
      if str(Platform()) == "darwin":
        env.Append(CCFLAGS="-arch i386")
        env.Append(LINKFLAGS="-arch i386")
      else:
        env.Append(CCFLAGS="-m32")
        env.Append(LINKFLAGS="-m32")
    
    env.Append(CPPFLAGS=" -O3 -g -ggdb")
    env.Append(CPPDEFINES=["NDEBUG"])
  
  SetupRelease = None
  SetupDebug = None
  
  if str(Platform()) == "win32":
    mscver = GetArgument("mscver", "10.0")
    if GetArgument("use-c++11", 0, int) != 0:
      if float(mscver) < 14.0:
        WarnOnce("Specified compiler version doesn't fully cover C++11. Use mscver=14.0 at least.")
    msvsarch = "amd64" if arch_dir == "x64" else "x86"
    env = Environment(MSVC_VERSION=mscver, MSVS_VERSION=mscver, MSVS_ARCH=msvsarch, TARGET_ARCH=msvsarch)
    # XP:    _WIN32_WINNT=0x0500
    # Vista: _WIN32_WINNT=0x0600
    winnt = "_WIN32_WINNT=0x0400"
    m = re.match(r"(\d)(\.(\d)(\.(\d+))?)?", platform.version())
    if m:
      winnt = "_WIN32_WINNT=0x0%s00" % m.group(1)
    
    env.Append(CPPDEFINES=[winnt, "_USE_MATH_DEFINES", "_WIN32", "WIN32", "_WINDOWS"])
    
    if arch_dir == "x64":
      env.Append(CPPDEFINES=["_WIN64", "WIN64"])
    
    env.Append(CPPFLAGS=" /GR /EHsc")
    
    # Always disable:
    #  4275: non dll-interface class used as base for dll-interface class
    #  4996: POSIX name deprecated ...
    #  4251: template needs to have dll-interface
    if warnl == "none":
      env.Append(CPPFLAGS=" /w")
    elif warnl == "std":
      env.Append(CPPFLAGS=" /W3 /wd4275 /wd4996 /wd4251")
    elif warnl == "all":
      #env.Append(CPPFLAGS=" /Wall")
      env.Append(CPPFLAGS=" /W4 /wd4275 /wd4996 /wd4251")
    
    #if "INCLUDE" in os.environ:
    #  env.Append(CPPPATH=os.environ["INCLUDE"].split(";"))
    #if "LIB" in os.environ:
    #  env.Append(LIBPATH=os.environ["LIB"].split(";"))
    mt = Which("mt")
    if mt is None:
      mt = "mt.exe"
    
    env.Append(CPPEDFINES=["_CRT_SECURE_NO_WARNINGS"])
    if float(mscver) > 7.1 and float(mscver) < 10.0:
      env.Append(CPPDEFINES=["_CRT_SECURE_NO_DEPRECATE"])
      env['LINKCOM'] = [env['LINKCOM'], '\"%s\" -nologo -manifest ${TARGET}.manifest -outputresource:$TARGET;1' % mt]
      env['SHLINKCOM'] = [env['SHLINKCOM'], '\"%s\" -nologo -manifest ${TARGET}.manifest -outputresource:$TARGET;2' % mt]
    
    SetupRelease = SetupMSVCRelease
    SetupDebug = SetupMSVCDebug
    
    if GetArgument("with-debug-info", 0, int):
      SetupRelease = SetupMSVCReleaseWithDebug
    
  else:
    env = Environment()
    cppflags = " -fPIC -pipe -pthread"
    if warnl == "none":
      cppflags += " -w"
    elif warnl == "std":
      cppflags += " -W -Wno-unused-parameter"
    else:
      cppflags += " -W -Wall"
    if warne:
      cppflags += " -Werror"
    env.Append(CPPFLAGS=cppflags)
    
    SetupRelease = SetupGCCRelease
    SetupDebug = SetupGCCDebug
    if GetArgument("with-debug-info", 0, int):
      SetupRelease = SetupGCCReleaseWithDebug
    
    if str(Platform()) == "darwin":
      env.Append(CCFLAGS=" -fno-common -DPIC")
      if os.path.exists("/opt/local"):
        env.Append(CPPPATH=["/opt/local/include"])
        env.Append(LIBPATH=["/opt/local/lib"])
      
      vers = map(int, platform.mac_ver()[0].split("."))
      # starting OSX 10.9, default compiler is clang
      if vers[0] > 10 or vers[1] >= 9:
        if GetArgument("use-c++11", 0, int):
          SetArgument("use-c++11", 1)
          env.Append(CXXFLAGS=" -std=c++11")
          
          if warnl == "std":
            # remove some more c++11 specific warnings
            env.Append(CPPFLAGS=" ".join(["-Wno-deprecated-register",
                                          "-Wno-deprecated-declarations",
                                          "-Wno-missing-field-initializers",
                                          "-Wno-unused-private-field"]))
        
        if GetArgument("use-stdc++", 0, int):
          SetArgument("use-stdc++", 1)
          env.Append(CXXFLAGS=" -stdlib=libstdc++")
          env.Append(LINKFLAGS=" -stdlib=libstdc++")
    
    else:
      if GetArgument("use-c++11", 0, int):
        SetArgument("use-c++11", 1)
        env.Append(CXXFLAGS=" -std=c++11")
    
    def symlink(source, target, env):
      srcpath = str(source[0])
      tgtpath = str(target[0])
      tgtdir = os.path.dirname(tgtpath)
      relsrcpath = os.path.relpath(srcpath, tgtdir)
      cmd = "cd %s; ln -s %s %s" % (tgtdir, relsrcpath, os.path.basename(tgtpath))
      p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      out, err = p.communicate()
      if p.returncode != 0:
        print("symlink failed: %s" % err)
    builder = Builder(action=symlink)
    env.Append(BUILDERS={"Symlink" : builder})
  
  if GetArgument("debug", 0, int):
    mode_dir = "debug"
    SetupDebug(env)
  else:
    mode_dir = "release"
    SetupRelease(env)
  
  if no_arch:
    env.Append(CPPPATH=[joinpath(out_dir, mode_dir, "include")])
    env.Append(LIBPATH=[joinpath(out_dir, mode_dir, "lib")])
  else:
    env.Append(CPPPATH=[joinpath(out_dir, mode_dir, arch_dir, "include")])
    env.Append(LIBPATH=[joinpath(out_dir, mode_dir, arch_dir, "lib")])
  
  env["TARGET_ARCH"] = arch_dir
  env["TARGET_MODE"] = mode_dir
  
  # Progress
  env["PROGRESS"] = ""
  
  def BuildProgress(node):
    global all_progress
    
    e = node.env
    if e is None:
      return
    
    n = abspath(str(node))
    
    for i in xrange(len(all_progress)):
      name, nodes, cnt = all_progress[i]
      if n in nodes:
        cnt += 1
        progress = "%d" % int(100 * (float(cnt) / len(nodes)))
        e["PROGRESS"] = "[ %s / %s%% ]" % (name, progress)
        
        all_progress[i] = (name, nodes, cnt)
        
        break
  
  Progress(BuildProgress)
  
  # Build output
  try:
    from colorama import init
    init()
    from colorama import Fore, Back, Style
    CComp = Fore.GREEN # + Style.BRIGHT
    CLink = Fore.MAGENTA # + Style.BRIGHT
    CReset = Fore.RESET + Back.RESET + Style.RESET_ALL
  except Exception, e:
    PrintOnce("Install 'colorama' python module for colored output ('pip install colorama').")
    CComp = ""
    CLink = ""
    CReset = ""
  newstrs = {}
  newstrs["CCCOMSTR"] = CComp + "$PROGRESS Compiling (static) $SOURCE ..." + CReset
  newstrs["SHCCCOMSTR"] = CComp + "$PROGRESS Compiling (shared) $SOURCE ..." + CReset
  newstrs["CXXCOMSTR"] = CComp + "$PROGRESS Compiling (static) $SOURCE ..." + CReset
  newstrs["SHCXXCOMSTR"] = CComp + "$PROGRESS Compiling (shared) $SOURCE ..." + CReset
  newstrs["LINKCOMSTR"] = CLink + "$PROGRESS Linking $TARGET ..." + CReset
  newstrs["SHLINKCOMSTR"] = CLink + "$PROGRESS Linking $TARGET ..." + CReset
  newstrs["LDMODULECOMSTR"] = CLink + "$PROGRESS Linking $TARGET ..." + CReset
  newstrs["ARCOMSTR"] = CLink + "$PROGRESS Archiving $TARGET ..." + CReset
  newstrs["RANLIBCOMSTR"] = CLink + "$PROGRESS Indexing $TARGET ..." + CReset
  show_cmds = (int(ARGUMENTS.get("show-cmds", "0")) != 0)
  
  def PrintCmd(s, target, source, env):
    sys.stdout.write("%s\n" % env.subst(s))
  env["PRINT_CMD_LINE_FUNC"] = PrintCmd

  for k, v in newstrs.iteritems():
    if not show_cmds:
      env[k] = v
    else:
      if env.get(k[:-3], None) is None:
        env[k] = v
      else:
        env[k] = "%s\n$%s" % (v, k[:-3])

  for item in glob(os.path.dirname(__file__) + "/envext/*.py"):
    bn = os.path.basename(item)
    if bn == "__init__.py":
      continue
    try:
      extname = os.path.splitext(os.path.basename(item))[0]
      mod = imp.load_source(extname, item)
      if not hasattr(mod, "SetupEnvironment"):
        print("Missing 'SetupEnvironment' function in '%s'" % item)
      else:
        #mod.SetupEnvironment(env)
        ext_types[extname] = mod.SetupEnvironment
    except Exception, e:
      print("Failed to load '%s': %s" % (item, e))

  return env

def OutputBaseDirectory():
  global out_dir, mode_dir, arch_dir, no_arch
  
  if not no_arch:
    return joinpath(out_dir, mode_dir, arch_dir)
  else:
    return joinpath(out_dir, mode_dir)

def BuildBaseDirectory():
  global bld_dir, mode_dir, arch_dir

  return joinpath(bld_dir, mode_dir, sys.platform, arch_dir)

def Call(path, targets=None, overrides={}, imp=[]):
  global ignore_help, args_no_cache, args_cache

  cur_ignore_help = ignore_help
  ignore_help = True

  s = path + "/SConstruct"
  if not os.path.isfile(s):
    s = path + "/SConscript"
    if not os.path.isfile(s):
      # path may be a sub-repository
      if len(glob(path+"/*")) == 0:
        d, n = os.path.split(path)
        cwd = os.getcwd()
        if d:
          os.chdir(d)
        cmd = "git submodule update --init %s" % n
        p = subprocess.Popen(cmd, shell=True)
        p.communicate()
        if d:
          os.chdir(cwd)
        if p.returncode == 0:
          s = path + "/SConstruct"
          if not os.path.isfile(s):
            s = path + "/SConscript"
            if not os.path.isfile(s):
              return
        else:
          return
      else:
        return

  old_vals = {}
  old_cached_vals = {}
  old_keys = set()
  check_cache = (not args_no_cache and args_cache is not None)

  # Store current arguments cache state
  if args_cache:
    old_keys = set(args_cache.keys())
  for k, v in overrides.iteritems():
    old_vals[k] = ARGUMENTS.get(k, None)
    ARGUMENTS[k] = str(v)
    if check_cache:
      old_cached_vals[k] = args_cache.get(k, None)

  if targets is not None:
    if type(targets) in (str, unicode):
      for target in filter(lambda x: len(x)>0, map(lambda y: y.strip(), targets.split(" "))):
        BUILD_TARGETS.append(target)
    else:
      for target in targets:
        BUILD_TARGETS.append(target)

  SConscript(s)

  # Restore old values
  for k, v in old_vals.iteritems():
    if v is None:
      del(ARGUMENTS[k])
    else:
      ARGUMENTS[k] = v
  for k, v in old_cached_vals.iteritems():
    if v is None:
      args_cache.remove(k)
    else:
      args_cache[k] = v
  # Remove newly introduced keys
  if check_cache:
    for k in args_cache.keys():
      if not k in old_keys:
        args_cache.remove(k)
        if k in ARGUMENTS:
          del(ARGUMENTS[k])

  for name in imp:
    Import(name)

  ignore_help = cur_ignore_help

def GetOptionsString():
  return """GENERIC OPTIONS
  no-cache=0|1                   : Ignore excons flag cache    [0]
  debug=0|1                      : Build in debug mode         [0]
  with-debug-info=0|1            : Build with debug info       [0]
  stack-size=<str>               : Setup stack size in bytes   [system default]
                                   Letters 'k', and 'm' can be used
                                   to specify kilobytes and megabytes
  warnings=none|std|all          : Warning level               [all]
  warnings-as-errors=0|1         : Treat warnings as errors    [0]
  libdir-arch=none|subdir|suffix : Modify behaviour of the library folder name use by default
                                   for 'with-<name>=<prefix>' flag    [none]
                                   When set to 'subdir', use '<prefix>/lib/x86' or '<prefix>/lib/x64'
                                   When set to 'suffix', use '<prefix>/lib' or '<prefix>/lib64'
  show-cmds=0|1                  : Show build commands         [0]
  mscver=<float>                 : Visual C runtime version    [10.0] (windows)
  no-console=0|1                 : Use window subsystem        [0]    (windows)
  strip=0|1                      : Strip dead code             [0]    (osx/linux)
  use-c++11=0|1                  : Compile code as C++ 11      [0]    (osx/linux)
  use-stdc++=0|1                 : Use libstdc++ for C++ 11    [0]    (osx)

DEPRECATED OPTIONS
  no-arch=0|1                    : Don't create arch directory [1]
                                   When enabled, a 'x86' or 'x64' sub-directory
                                   will be added to build output structure
  x64=0|1                        : Build 64bits binaries       [1]
  x86=0|1                        : Build 32bits binaries       [0]"""

def IgnoreHelp():
  global ignore_help
  ignore_help = True

def AddHelpTargets(tgts={}, **kwargs):
  global help_targets

  for name, desc in tgts.iteritems():
    help_targets[name] = desc

  for name, desc in kwargs.iteritems():
    help_targets[name] = desc

def AddHelpOptions(opts={}, **kwargs):
  global help_options

  for name, desc in opts.iteritems():
    help_options[name] = desc

  for name, desc in kwargs.iteritems():
    help_options[name] = desc

def GetHelpString():
  global help_targets, help_options

  help = """USAGE
  scons [OPTIONS] TARGET

AVAILABLE TARGETS\n"""

  maxlen = 0
  for name, _ in help_targets.iteritems():
    if len(name) > maxlen:
      maxlen = len(name)

  names = help_targets.keys()
  names.sort()
  for name in names:
    desc = help_targets[name]
    padding = "" if len(name) >= maxlen else " " * (maxlen - len(name))
    help += "  %s%s : %s\n" % (name, padding, desc)

  names = help_options.keys()
  names.sort()
  for name in names:
    desc = help_options[name]
    help += "\n%s\n" % desc

  help += "\n%s\n" % GetOptionsString()

  return help

def SetHelp(help):
  global ignore_help
  if not ignore_help:
    Help(help)

@atexit.register
def SyncCache():
  global args_no_cache, args_cache

  if not args_no_cache and args_cache:
    args_cache.write()

def ExternalLibHelp(name):
  return string.Template("""EXTERNAL ${uc_name} OPTIONS
  with-${name}=<path>     : ${name} prefix.
  with-${name}-inc=<path> : ${name} headers directory.           [<prefix>/include]
  with-${name}-lib=<path> : ${name} libraries directory.         [<prefix>/lib]
  ${name}-static=0|1      : Link ${name} statically.             [0]
  ${name}-name=<str>      : Override ${name} library name.       []
  ${name}-suffix=<str>    : Default ${name} library name suffix. [] (ignored when ${name}-name is set)""").substitute(uc_name=name.upper(), name=name)

# parameters
#   libnameFunc: f(static) -> str
#   definesFunc: f(static) -> []
#   extraEnvFunc f(env, static) -> None
def ExternalLibRequire(name, libnameFunc=None, definesFunc=None, extraEnvFunc=None):
  global arch_dir

  rv = {"require": None,
        "incdir": None,
        "libdir": None,
        "libname": None,
        "libpath": None,
        "static": None}

  incdir, libdir = GetDirs(name)
  if incdir and libdir:
    libname = GetArgument("%s-name" % name, None)
    staticlink = (GetArgument("%s-static" % name, 0, int) != 0)

    if libname is None:
      libname = (name if libnameFunc is None else libnameFunc(staticlink))
      libname += GetArgument("%s-suffix" % name, "")

    if sys.platform == "win32":
      libpath = libdir + "/" + libname + ".lib"

    else:
      #not os.path.isfile(libpath)
      libext = (".a" if staticlink else SharedLibraryLinkExt())
      libpath = None
      if arch_dir == "x64" and not libdir.endswith("64"):
        libpath = libdir + "64/lib" + libname + libext
        if not os.path.isfile(libpath):
          libpath = None
        else:
          libdir = libdir + "64"
      if libpath is None:
        libpath = libdir + "/lib" + libname + libext

    if os.path.isfile(libpath) or IsBuildOutput(libpath):
      def RequireFunc(env):
        if definesFunc:
          env.Append(CPPDEFINES=definesFunc(staticlink))
        env.Append(CPPPATH=[incdir])
        Link(env, libpath, static=staticlink, force=True, silent=True)
        if extraEnvFunc:
          extraEnvFunc(env, staticlink)

      rv["require"] = RequireFunc
      rv["incdir"] = incdir
      rv["libdir"] = libdir
      rv["libname"] = libname
      rv["libpath"] = libpath
      rv["static"] = staticlink

  AddHelpOptions({"ext_%s" % name: ExternalLibHelp(name)})

  return rv

def DeclareTargets(env, prjs):
  global bld_dir, out_dir, mode_dir, arch_dir, mscver, no_arch, args_no_cache, args_cache, all_targets, all_progress, ext_types, help_targets

  all_projs = {}
  
  for settings in prjs:
    
    # recusively add deps if one of the lib or deps is a project
    
    if not "name" in settings:
      print("[excons] Project missing \"name\"")
      continue
    
    prj = settings["name"]
    alias = settings.get("alias", prj)
    desc = settings.get("desc", "")
    prefix = settings.get("prefix", None)
    progress_nodes = set()

    if not "type" in settings:
      print("[excons] Project \"%s\" missing \"type\"" % prj)
      continue
    elif settings["type"] not in ext_types and not "srcs" in settings:
      print("[excons] Project \"%s\" missing \"srcs\"" % prj)
      continue

    penv = env.Clone()

    def add_deps(tgt):
      for k in ("deps", "libs", "staticlibs"):
        if k in settings:
          for dep in settings[k]:
            if dep in all_projs:
              penv.Depends(tgt, all_projs[dep])
              # but should not clean all_projs[dep]
            elif dep in all_targets:
              penv.Depends(tgt, all_targets[dep])
            else:
              if k == "deps":
                # WarnOnce("Can't find dependent target '%s'. Depend on file." % dep)
                penv.Depends(tgt, dep)

    if settings["type"] in ext_types:
      pout = ext_types[settings["type"]](penv, settings)
      if pout:
        if not prj in help_targets:
          AddHelpTargets({prj: ("Build %s project" % settings["type"]) if not desc else desc})
        add_deps(pout)

    else:
      if "/" in prj.replace("\\", "/"):
        print("[excons] Invalid target name '%s'. Please use 'prefix' instead." % prj)
        spl = prj.split("/")
        spl = prj.split("/")
        prj = spl[-1]
        subdir = "/".join(spl[:-1])
        prefix = ("%s/%s" % (prefix, subdir) if prefix else subdir)
        settings["name"] = prj
        settings["prefix"] = prefix
        print("[excons] => Update: name='%s', prefix='%s'" % (prj, prefix))
      
      if prefix:
        if prefix.startswith("/"):
          prefix = prefix[1:]
        if prefix.endswith("/"):
          prefix = prefix[:-1]
        settings["prefix"] = prefix
      
      if "libdirs" in settings:
        penv.Append(LIBPATH=settings["libdirs"])
      
      if "incdirs" in settings:
        penv.Append(CPPPATH=settings["incdirs"])
      
      if "defs" in settings:
        penv.Append(CPPDEFINES=settings["defs"])
      
      if "cppflags" in settings:
        penv.Append(CPPFLAGS=settings["cppflags"])

      if "ccflags" in settings:
        penv.Append(CCFLAGS=settings["ccflags"])

      if "cxxflags" in settings:
        penv.Append(CXXFLAGS=settings["cxxflags"])

      if "libs" in settings:
        penv.Append(LIBS=settings["libs"])
      
      if "staticlibs" in settings:
        missing = False
        for item in settings["staticlibs"]:
          if not StaticallyLink(penv, item, silent=True):
            # Could be another project
            if not item in all_projs and not item in all_targets:
              print("[excons] No static library for \"%s\". Project \"%s\" ignored." % (item, prj))
              missing = True
              break
            else:
              tgts = filter(lambda x: os.path.splitext(str(x))[1].lower() not in (".so", ".dll", ".dylib"), all_projs.get(item, all_targets.get(item)))
              penv.Append(LIBS=tgts)
        if missing:
          continue

      if "linkflags" in settings:
        penv.Append(LINKFLAGS=settings["linkflags"])

      if "custom" in settings:
        for customcall in settings["custom"]:
          customcall(penv)
      
      odir = joinpath(bld_dir, mode_dir, sys.platform, arch_dir, prj)
      
      # On windows, also msvc-9.0
      if str(Platform()) == "win32":
        msvcver = env.get("MSVC_VERSION", None)
        if msvcver:
          odir = joinpath(odir, "msvc-%s" % msvcver)
      if "bldprefix" in settings:
        odir = joinpath(odir, settings["bldprefix"])
      
      shared = True
      if settings["type"] in ["program", "testprograms", "staticlib"]:
        shared = False
      
      if str(Platform()) != "win32":
        symvis = settings.get("symvis", None)
        if symvis is None:
          symvis = ("hidden" if settings["type"] != "sharedlib" else "default")
        if symvis == "hidden":
          penv.Append(CCFLAGS=["-fvisibility=hidden"])
      
      objs = []
      # Source level dependencies
      srcdeps = settings.get("srcdeps", {})
      prereqs = srcdeps.get("*", [])
      for src in settings["srcs"]:
        bn = os.path.basename(str(src))
        bnnoext = os.path.splitext(bn)[0]
        if shared:
          obj = penv.SharedObject(joinpath(odir, bnnoext), src)
        else:
          obj = penv.StaticObject(joinpath(odir, bnnoext), src)
        #objs.append(obj)
        objs.extend(obj)
        key = str(src)
        deps = srcdeps.get(key, [])
        if not deps:
          key = key.replace("\\", "/")
          deps = srcdeps.get(key, [])
          if not deps:
            deps = srcdeps.get(bn, [])
        if deps:
          #Print("Add dependencies for '%s': %s" % (str(obj[0]).replace("\\", "/"), map(lambda x: str(x).replace("\\", "/"), deps)))
          penv.Depends(obj, deps)
        # target prerequisites
        if prereqs:
          penv.Depends(obj, prereqs)
      
      #progress_nodes = set(map(lambda x: abspath(str(x[0])), objs))
      progress_nodes = set(map(lambda x: abspath(str(x)), objs))
      
      if alias != prj:
        if not alias in help_targets:
          val = help_targets.get(alias, "")
          if val:
            val += ", "
          val += prj
          help_targets[alias] = val
      
      if settings["type"] == "sharedlib":
        if not prj in help_targets:
          AddHelpTargets({prj: "Shared library" if not desc else desc})
        
        sout = []
        
        if str(Platform()) == "win32":
          if settings.get("win_separate_dll_and_lib", True):
            if no_arch:
              outbn = joinpath(out_dir, mode_dir, "bin", prj)
              impbn = joinpath(out_dir, mode_dir, "lib", prj)
            else:
              outbn = joinpath(out_dir, mode_dir, arch_dir, "bin", prj)
              impbn = joinpath(out_dir, mode_dir, arch_dir, "lib", prj)
          else:
            if no_arch:
              impbn = joinpath(out_dir, mode_dir, "lib", prj)
            else:
              impbn = joinpath(out_dir, mode_dir, arch_dir, "lib", prj)
            outbn = impbn
              
          try:
            os.makedirs(os.path.dirname(impbn))
          except:
            pass
          
          penv['no_import_lib'] = 1
          penv.Append(SHLINKFLAGS=" /implib:%s.lib" % impbn)
          pout = penv.SharedLibrary(outbn, objs)
          implib = File(mode_dir + ("/" if no_arch else "/%s" % arch_dir) + "/lib/" + prj + ".lib")
          # Create a fake target for implib
          penv.Depends(implib, pout[0])
          pout.append(implib)
          
          # Cleanup
          penv.Clean(pout, impbn+".lib")
          penv.Clean(pout, impbn+".exp")
          if float(mscver) > 7.1 and float(mscver) < 10.0:
            penv.Clean(pout, outbn+".dll.manifest")
          if GetArgument("debug", 0, int):
            penv.Clean(pout, outbn+".ilk")
            penv.Clean(pout, outbn+".pdb")
        
        else:
          relpath = None
          if prefix:
            relpath = "/".join([".."] * (1 + prefix.count("/")))
          
          symlinks = set()
          
          penv["SHLIBPREFIX"] = ""
          penv["SHLIBSUFFIX"] = ""
          
          outlibdir = joinpath(out_dir, mode_dir).replace("\\", "/")
          if not no_arch:
            outlibdir += "/" + arch_dir
          outlibdir += "/lib"
          if prefix:
            outlibdir += "/" + prefix
          
          outlibname = "lib%s" % prj
          
          version = settings.get("version", None)
          if version:
            if sys.platform == "darwin":
              outlibname += ".%s.dylib" % version
              symlinks.add("%s/lib%s.dylib" % (outlibdir, prj))
            else:
              outlibname += ".so.%s" % version
              symlinks.add("%s/lib%s.so" % (outlibdir, prj))
          else:
            outlibname += (".dylib" if sys.platform == "darwin" else ".so")
          
          # Setup rpath
          SetRPath(penv, settings, relpath=relpath)
          
          # Setup library name
          if sys.platform == "darwin":
            libname = settings.get("install_name", "lib%s.dylib" % prj)
            if not ".dylib" in libname:
              libname += ".dylib"
            if libname != outlibname:
              symlinks.add("%s/%s" % (outlibdir, libname))
            if not libname.startswith("@rpath"):
              libname = "@rpath/%s" % libname
            penv.Append(LINKFLAGS=" -Wl,-install_name,%s" % libname)
          
          else:
            libname = settings.get("soname", "lib%s.so" % prj)
            if not ".so" in libname:
              libname += ".so"
            if libname != outlibname:
              symlinks.add("%s/%s" % (outlibdir, libname))
            penv.Append(LINKFLAGS=" -Wl,-soname,%s" % libname)
          
          # Declare library target
          pout = penv.SharedLibrary(outlibdir + "/" + outlibname, objs)
          
          # create symlinks
          for symlink in symlinks:
            sout.extend(penv.Symlink(symlink, pout))
        
        progress_nodes.add(abspath(str(pout[0])))
        
        add_deps(pout)
        
        if sout:
          sout.extend(pout)
          pout = sout
      
      elif settings["type"] == "program":
        if not prj in help_targets:
          AddHelpTargets({prj: "Program" if not desc else desc})
        
        outbindir = joinpath(out_dir, mode_dir).replace("\\", "/")
        if not no_arch:
          outbindir += "/" + arch_dir
        outbindir += "/bin"
        if prefix:
          outbindir += "/" + prefix
        
        outbn = outbindir + "/" + prj
        
        if GetArgument("no-console", 0, int) or ("console" in settings and settings["console"] is False):
          NoConsole(penv)
        
        SetStackSize(penv, size=settings.get("stacksize", ParseStackSize(GetArgument("stack-size", None))))
        
        if prefix:
          relpath = "/".join([".."] * (1 + prefix.count("/"))) + "/../lib"
        else:
          relpath = "../lib"
        
        SetRPath(penv, settings, relpath=relpath)
        
        pout = penv.Program(outbn, objs)
        
        progress_nodes.add(abspath(str(pout[0])))
        
        add_deps(pout)
        
        # Cleanup
        if str(Platform()) == "win32":
          if float(mscver) > 7.1 and float(mscver) < 10.0:
            penv.Clean(pout, outbn+".exe.manifest")
          if GetArgument("debug", 0, int):
            penv.Clean(pout, outbn+".ilk")
            penv.Clean(pout, outbn+".pdb")
      
      elif settings["type"] == "staticlib":
        if not prj in help_targets:
          AddHelpTargets({prj: "Static library" if not desc else desc})
        
        outlibdir = joinpath(out_dir, mode_dir).replace("\\", "/")
        if not no_arch:
          outlibdir += "/" + arch_dir
        outlibdir += "/lib"
        if prefix:
          outlibdir += "/" + prefix
        
        # It seems that is there's a '.' in prj, SCons fails to add extension
        # Let's force it
        pout = penv.StaticLibrary(outlibdir + "/" + prj + penv["LIBSUFFIX"], objs)
        
        progress_nodes.add(abspath(str(pout[0])))
        
        add_deps(pout)
      
      elif settings["type"] == "testprograms":
        if not prj in help_targets:
          AddHelpTargets({prj: "Programs" if not desc else desc})
        
        pout = []
        
        outbindir = joinpath(out_dir, mode_dir).replace("\\", "/")
        if not no_arch:
          outbindir += "/" + arch_dir
        outbindir += "/bin"
        if prefix:
          outbindir += "/" + prefix
        
        if GetArgument("no-console", 0, int) or ("console" in settings and settings["console"] is False):
          NoConsole(penv)
        
        SetStackSize(penv, size=settings.get("stacksize", ParseStackSize(GetArgument("stack-size", None))))
        
        if prefix:
          relpath = "/".join([".."] * (1 + prefix.count("/"))) + "/../lib"
        else:
          relpath = "../lib"
        SetRPath(penv, settings, relpath=relpath)
        
        for obj in objs:
          name = os.path.splitext(os.path.basename(str(obj)))[0]
          
          outbn = outbindir + "/" + name
          
          prg = penv.Program(outbn, obj)
          
          progress_nodes.add(abspath(str(prg[0])))
          
          add_deps(prg)
          
          pout.append(prg)
          
          # Cleanup
          if str(Platform()) == "win32":
            if float(mscver) > 7.1 and float(mscver) < 10.0:
              penv.Clean(prg, outbn+".exe.manifest")
            if GetArgument("debug", 0, int):
              penv.Clean(prg, outbn+".ilk")
              penv.Clean(prg, outbn+".pdb")
      
      elif settings["type"] == "dynamicmodule":
        if not prj in help_targets:
          AddHelpTargets({prj: "Dynamic module" if not desc else desc})
        
        outmoddir = joinpath(out_dir, mode_dir)
        if not no_arch:
          outmoddir += "/" + arch_dir
        if prefix:
          outmoddir += "/" + prefix
        
        if str(Platform()) == "win32":
          outbn = outmoddir + "/" + prj
          penv["SHLIBPREFIX"] = ""
          if "ext" in settings:
            penv["SHLIBSUFFIX"] = settings["ext"]
         
          # set import lib in build folder
          impbn = joinpath(odir, os.path.basename(prj))
          penv['no_import_lib'] = 1
          penv.Append(SHLINKFLAGS=" /implib:%s.lib" % impbn)
          pout = penv.SharedLibrary(outbn, objs)
          
          # Cleanup
          penv.Clean(pout, impbn+".lib")
          penv.Clean(pout, impbn+".exp")
          if float(mscver) > 7.1 and float(mscver) < 10.0:
            penv.Clean(pout, outbn+penv["SHLIBSUFFIX"]+".manifest")
          
          if GetArgument("debug", 0, int):
            penv.Clean(pout, outbn+".ilk")
            penv.Clean(pout, outbn+".pdb")
        
        else:
          penv["LDMODULEPREFIX"] = ""
          if "ext" in settings:
            penv["LDMODULESUFFIX"] = settings["ext"]
          else:
            if str(Platform()) == "darwin":
              penv["LDMODULESUFFIX"] = ".bundle"
          
          SetRPath(penv, settings)
          
          pout = penv.LoadableModule(outmoddir + "/" + prj, objs)
        
        progress_nodes.add(abspath(str(pout[0])))
        
        add_deps(pout)
      
      else:
        pout = None
    
    if pout:
      if "post" in settings:
        penv.AddPostAction(pout, settings["post"])
      
      def install_file(dstdir, filepath):
        if type(filepath) in (str, unicode):
          if os.path.isfile(filepath):
            penv.Depends(pout, penv.Install(dstdir, filepath))
          else:
            dn = dstdir + "/" + os.path.basename(filepath)
            for item in glob(filepath + "/*"):
              install_file(dn, item)
        else:
          penv.Depends(pout, penv.Install(dstdir, filepath))
      
      if "install" in settings:
        for prefix, files in settings["install"].iteritems():
          if no_arch:
            dst = joinpath(out_dir, mode_dir, prefix)
          else:
            dst = joinpath(out_dir, mode_dir, arch_dir, prefix)
          for f in files:
            install_file(dst, f)
      
      all_progress.append((prj, progress_nodes, 0))
      
      aliased = all_projs.get(alias, [])
      aliased.extend(pout)
      all_projs[alias] = aliased

      # Also keep target name alias
      if alias != prj:
        Alias(prj, pout)

        tgts = all_projs.get(prj, [])
        tgts.extend(pout)
        all_projs[prj] = tgts
  
  #SyncCache()
  
  for alias, targets in all_projs.iteritems():
    Alias(alias, targets)
    if alias in all_targets:
      PrintOnce("Target '%s' already declared in another SCons script. Merging." % alias)
      all_targets[alias].extend(targets)
    else:
      all_targets[alias] = targets
  
  env["EXCONS_TARGETS"] = all_projs

  SetHelp(GetHelpString())

  return all_projs

def GetTargetOutputFiles(env, target, builders=None, verbose=False):
  def GetTargetOuptutFilesIter(env, node):
    if node.has_builder():
      builder_name = node.get_builder().get_name(env)
      if builders is None or builder_name in builders:
        yield node
      elif verbose:
        print("Ignore builder '%s' output: %s" % (builder_name, node))
    
    for kid in node.all_children():
      for kid in GetTargetOuptutFilesIter(env, kid):
        yield kid
  
  node = env.arg2nodes(target, env.fs.Entry)[0]
  return list(GetTargetOuptutFilesIter(env, node))

# 'targets' is a dictionary like the one returned by DeclareTargets function
#           key=target name, value=list of SCons targets
def ConservativeClean(env, targetname, targets=None):
  if GetOption("clean"):
    if targets is None and "EXCONS_TARGETS" in env:
      print("Get targets from environment.")
      targets = env["EXCONS_TARGETS"]
    if targetname in COMMAND_LINE_TARGETS:
      targetnames = filter(lambda x: x != targetname, COMMAND_LINE_TARGETS)
      if len(targetnames) == 0:
        # if not other target specified keep all of them
        targetnames = targets.keys()
      for tn in targetnames:
        if tn == targetname or not tn in targets:
          continue
        for target in targets[tn]:
          for item in GetTargetOutputFiles(env, target):
            env.NoClean(item)

def EcosystemPlatform():
  if sys.platform == "darwin":
    return "darwin"
  elif sys.platform == "win32":
    return "windows"
  else:
    return "linux"

class EcoUtils(object):
  KeyOrder = ["tool", "version", "platforms", "requires", "environment", "optional"]

  class OKey(object):
    def __init__(self, name, position):
      self.name = name
      self.position = position
    def __cmp__(self, b):
      assert isinstance(b, EcoUtils.OKey)
      return cmp(self.position, b.position)
    def __repr__(self):
      return repr(self.name)

  @staticmethod
  def IsSameValue(v0, v1):
    v0t = type(v0)
    if v0t == tuple:
      v0t = list
      v0 = v0t(v0)

    v1t = type(v1)
    if v1t == tuple:
      v1t = list
      v1 = v1t(v1)

    if v1t != v0t:
      return False

    if v0t == list:
      if len(v0) != len(v1):
        return False
      else:
        for i in xrange(len(v0)):
          if not EcoUtils.IsSameValue(v0[i], v1[i]):
            return False
        return True

    elif v0t == dict:
      if len(v0) != len(v1):
        return False
      else:
        for key, val0 in v0.iteritems():
          if not key in v1:
            return False
          val1 = v1[key]
          if not EcoUtils.IsSameValue(val0, val1):
            return False
        for key, _ in v1.iteritems():
          if not key in v0:
            return False
        return True

    elif v0t in (str, unicode):
      return (v0 == v1)

    else:
      return False

  @staticmethod
  def SortKeys(item):
    try:
      return EcoUtils.KeyOrder.index(item[0])
    except:
      return len(korder)

  @staticmethod
  def SortedDict(d):
    try:
      import collections
      collections.OrderedDict.__repr__ = dict.__repr__
      items = d.items()
      items.sort(key=EcoUtils.SortKeys)
      items = [(EcoUtils.OKey(k, i), v) for i, (k, v) in enumerate(items)]
      return collections.OrderedDict(items)
    except:
      return d

def EcosystemDist(env, ecofile, targetdirs, name=None, version=None, targets=None, defaultdir="eco", dirflag="eco-dir", ecoenv={}):
  if targets is None and "EXCONS_TARGETS" in env:
    targets = env["EXCONS_TARGETS"]

  ecod = {}

  try:
    with open(ecofile, "r") as f:
      ecod = eval(f.read())
  except Exception, e:
    print("Invalid ecosystem env (%s)" % e)
    return

  updenv = False

  if name is None:
    try:
      name = ecod["tool"]
    except:
      print("No tool name for ecosystem distribution.")
      return
  else:
    if not "tool" in ecod or ecod["tool"] != name:
      ecod["tool"] = name
      updenv = True

  if version is None:
    try:
      version = ecod["version"]
    except:
      print("No tool version for ecosystem distribution.")
      return
  else:
    if not "version" in ecod or ecod["version"] != version:
      ecod["version"] = version
      updenv = True

  for k, v in ecoenv.iteritems():
    cv = ecod.get(k, None)
    if cv is None:
      updenv = True
      ecod[k] = v
    else:
      if not EcoUtils.IsSameValue(v, cv):
        updenv = True
        ecod[k] = v

  distenv = env.Clone()

  #distdir = GetArgument(dirflag, defaultdir)
  distdir = ARGUMENTS.get(dirflag, defaultdir)
  verdir = "%s/%s/%s" % (distdir, name, version)

  if updenv:
    with open(ecofile+".tmp", "w") as f:
      import pprint
      try:
        ecod = EcoUtils.SortedDict(ecod)
      except:
        pass
      pprint.pprint(ecod, stream=f, indent=1, width=1)
      f.write("\n")
    Alias("eco", distenv.InstallAs(distdir + "/%s_%s.env" % (name, version.replace(".", "_")), ecofile + ".tmp"))
  else:
    Alias("eco", distenv.InstallAs(distdir + "/%s_%s.env" % (name, version.replace(".", "_")), ecofile))

  for targetname, subdir in targetdirs.iteritems():
    dstdir = verdir + subdir
    for target in targets[targetname]:
      path = str(target)
      if os.path.islink(path):
        lnksrc = os.readlink(path)
        if not os.path.isabs(lnksrc):
          lnksrc = dstdir + "/" + lnksrc
          lnkdst = dstdir + "/" + os.path.basename(path)
          Alias("eco", distenv.Symlink(lnkdst, lnksrc))
          continue
      Alias("eco", distenv.Install(dstdir, target))

  # Also add version directory to 'eco' alias for additional install targets
  Alias("eco", verdir)

  distenv.Clean("eco", verdir)

  ConservativeClean(env, "eco", targets=targets)

  return (distenv, verdir)
