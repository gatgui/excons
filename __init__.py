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
import glob
import platform
import re
import sys
from SCons.Script import *

args_cache_path = os.path.abspath("./excons.cache")
args_cache = None
args_cache_echo = True
args_no_cache = False
bld_dir = os.path.abspath("./.build")
out_dir = os.path.abspath(".")
mode_dir = None
arch_dir = "x64"
mscver = None
no_arch = False
warnl = "all"
issued_warnings = set()


def InitGlobals(output_dir="."):
  global args_cache, args_cache_path, args_no_cache
  global bld_dir, out_dir, mode_dir, arch_dir
  global mscver, no_arch, warnl, issued_warnings
  
  if not output_dir:
    output_dir = "."
  
  cache_path = os.path.abspath("%s/excons.cache" % output_dir)
  
  if cache_path != args_cache_path:
    if args_cache and not args_no_cache:
      args_cache.write()
    
    args_cache_path = cache_path
    args_cache = None
    args_no_cache = False
    
  bld_dir = os.path.abspath("%s/.build" % output_dir)
  out_dir = os.path.abspath(output_dir)
  mode_dir = None
  arch_dir = "x86" if platform.architecture()[0] == '32bit' else "x64"
  mscver = None
  no_arch = False  # Whether or not to create architecture in output directory
  warnl = "all"  # Warning level
  issued_warnings = set()


class Cache(dict):
  def __init__(self, *args, **kwargs):
    super(Cache, self).__init__(*args, **kwargs)
    super(Cache, self).__setitem__(sys.platform, {})
    self.updated = False
  
  def write(self):
    global args_cache_path, args_cache_echo
    
    if self.updated:
      import pprint
      
      print("[excons] Write excons.cache: %s" % args_cache_path)
      f = open(args_cache_path, "w")
      #f.write("%s\n" % str(self))
      pprint.pprint(self, f)
      f.write("\n")
      f.close()
      
      self.updated = False
  
  def __setitem__(self, k, v):
    pd = super(Cache, self).__getitem__(sys.platform)
    if pd.get(k, None) != v:
      print("[excons] Update cache: %s = %s" % (k, v))
      pd[k] = v
      self.updated = True
  
  def __getitem__(self, k):
    return super(Cache, self).__getitem__(sys.platform)[k]
  
  def remove(self, k):
    pd = super(Cache, self).__getitem__(sys.platform)
    if k in pd:
      del(pd[k])
      self.updated = True
  
  def get(self, k, default=None):
    try:
      return self[k]
    except:
      return default
  
  def rawset(self, k, v):
    super(Cache, self).__setitem__(k, v)


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
            if args_cache_echo and k == sys.platform:
              for k2, v2 in v.iteritems():
                print("[excons]  %s = %s" % (k2, v2))
            args_cache.rawset(k, copy.deepcopy(v))
          args_cache_echo = False
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
      for item in glob.glob(os.path.join(path, "*")):
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

def SetRPath(env, settings, relpath=None):
  if sys.platform != "win32":
    osx = (sys.platform == "darwin")
    
    rpath = settings.get("rpath", None)
    rpath_suffix = ("" if osx else ",--enable-new-dtags")
    
    if not rpath or not rpath.startswith("/"):
      if rpath:
        relpath = rpath
      
      if osx:
        rpath = "@loader_path"
        if relpath:
          rpath += "/" + relpath
      
      else:
        rpath = "'$$ORIGIN"
        if relpath:
          rpath += "/" + relpath
        rpath += "'"
    
    env.Append(LINKFLAGS=" -Wl,-rpath,%s%s" % (rpath, rpath_suffix))

def Build32():
  global arch_dir
  return (arch_dir != "x64")

def Build64():
  global arch_dir
  return (arch_dir == "x64")

def WarnOnce(msg):
  global issued_warnings
  
  if not msg in issued_warnings:
    first = True
    for line in msg.split("\n"):
      if first:
        print("[excons] Warning: %s" % line)
        first = False
      else:
        print("[excons]          %s" % line)
    issued_warnings.add(msg)

def GetDirs(name, incdirname="include", libdirname="lib", libdirarch=None, noexc=True, silent=False):
  global arch_dir
  
  prefixflag = "with-%s" % name
  incflag = "%s-inc" % prefixflag
  libflag = "%s-lib" % prefixflag
  incvar = name.upper() + "_INCLUDE"
  libvar = name.upper() + "_LIB"
  prefixsrc = None
  incsrc = None
  libsrc = None
  
  prefix = None
  inc = None
  lib = None
  
  prefix = GetArgument(prefixflag)
  if prefix:
    prefixsrc = ("flag" if prefixflag in ARGUMENTS else "cache")
  else:
    prefix = None
  
  prefixinc = None
  prefixlib = None
  
  inc = GetArgument(incflag)
  if inc:
    incsrc = ("flag" if incflag in ARGUMENTS else "cache")
  else:
    inc = None
  
  if (inc is None or incsrc == "cache") and incvar in os.environ:
    val = os.environ[incvar]
    if val:
      #if inc is not None and prefixsrc != "flag":
      if prefixsrc != "flag":
        msg = "Ignore %s include directory read from cache.\nUse environment key %s value." % (name, incvar)
        WarnOnce(msg)
      inc = val
      incsrc = "environment"
  
  lib = GetArgument(libflag)
  if lib:
    libsrc = ("flag" if libflag in ARGUMENTS else "cache")
  else:
    lib = None
  
  if (lib is None or libsrc == "cache") and libvar in os.environ:
    val = os.environ[libvar]
    if val:
      #if lib is not None and prefixsrc != "flag":
      if prefixsrc != "flag":
        msg = "Ignore %s library directory read from cache.\nUse environment key %s value." % (name, libvar)
        WarnOnce(msg)
      lib = val
      libsrc = "environment"
  
  # Priority (highest -> lowest)
  #   inc/lib flag
  #   prefix flag
  #   inc/lib env var
  #   inc/lib cache
  #   prefix cache
  
  if (prefixsrc == "flag" and (incsrc != "flag" or libsrc != "flag")) or inc is None or lib is None:
    if prefix is None:
      msg = "provide %s include and/or library path by using one of:\n  %s=\n  %s=\n  %s=\nflags." % (name, prefixflag, incflag, libflag)
      if noexc:
        if not silent:
          msg = "You may need to %s" % msg
          WarnOnce(msg)
      else:
        raise Exception("Please %s" % msg)
    
    else:
      prefix = os.path.abspath(os.path.expanduser(prefix))
      
      if not os.path.isdir(prefix):
        msg = "Invalid %s prefix directory %s." % (name, prefix)
        if noexc:
          if not silent:
            WarnOnce(msg)
          prefix = None
        else:
          raise Exception(msg)
      else:
        SetArgument(prefixflag, prefix)
      
      prefixinc = "%s/%s" % (prefix, incdirname)
      
      prefixlib = "%s/%s" % (prefix, libdirname)
      mode = (GetArgument("libdir-arch", "none") if libdirarch is None else libdirarch)
      if mode == "subdir":
        prefixlib += "/%s" % arch_dir
      elif mode == "suffix" and Build64():
        prefixlib += "64"
  
  else:
    if prefixsrc == "cache" and incsrc != "environment" and libsrc != "environment":
      RemoveCacheKey(prefixflag)
  
  if inc is None or (prefixsrc == "flag" and incsrc != "flag"):
    if inc is not None:
      msg = "Ignore %s include directory read from %s.\nDerive directory from explicit prefix." % (name, incsrc)
      WarnOnce(msg)
      RemoveCacheKey(incflag)
    inc = prefixinc
  
  if lib is None or (prefixsrc == "flag" and libsrc != "flag"):
    if lib is not None:
      msg = "Ignore %s library directory read from %s.\nDerive directory from explicit prefix." % (name, libsrc)
      WarnOnce(msg)
      RemoveCacheKey(libflag)
    lib = prefixlib
  
  if inc is None:
    print("inc is none")
    msg = "provide %s include and/or library path by using one of:\n  %s=\n  %s=\n  %s=\nflags." % (name, prefixflag, incflag, libflag)
    if noexc:
      if not silent:
        msg = "You may need to %s" % msg
        WarnOnce(msg)
    else:
      raise Exception("Please %s" % msg)
  
  else:
    inc = os.path.abspath(os.path.expanduser(inc))
    if not os.path.isdir(inc):
      msg = "Invalid %s include directory %s." % (name, inc)
      if noexc:
        if not silent:
          WarnOnce(msg)
        inc = None
      else:
        raise Exception(msg)
    elif incsrc is not None:
      SetArgument(incflag, inc)
  
  if lib is None:
    print("lib is none")
    msg = "provide %s include and/or library path by using one of:\n  %s=\n  %s=\n  %s=\nflags." % (name, prefixflag, incflag, libflag)
    if noexc:
      if not silent:
        msg = "You may need to %s" % msg
        WarnOnce(msg)
    else:
      raise Exception("Please %s" % msg)
  
  else:
    lib = os.path.abspath(os.path.expanduser(lib))
    
    if not os.path.isdir(lib):
      msg = "Invalid %s library directory %s." % (name, lib)
      if noexc:
        if not silent:
          WarnOnce(msg)
        lib = None
      else:
        raise Exception(msg)
    elif libsrc is not None:
      SetArgument(libflag, lib)
  
  return (inc, lib)

def GetDirsWithDefault(name, incdirname="include", libdirname="lib", libdirarch=None, incdirdef=None, libdirdef=None, noexc=True, silent=False):
  inc_dir, lib_dir = GetDirs(name, incdirname=incdirname, libdirname=libdirname, libdirarch=libdirarch, noexc=True, silent=True)
  
  if inc_dir is None:
    inc_dir = incdirdef
  
  if lib_dir is None:
    lib_dir = libdirdef
  
  if inc_dir is None or lib_dir is None:
    msg = "%s directories not set.\nUse with-%s=, with-%s-inc=, with-%s-lib= flags." % (name, name, name, name)
    if noexc:
      if not silent:
        WarnOnce(msg)
    else:
      raise Exception(msg)
  
  return (inc_dir, lib_dir)

def MakeBaseEnv(noarch=None):
  global bld_dir, out_dir, mode_dir, arch_dir, mscver, no_arch
  
  if int(ARGUMENTS.get("shared-build", "1")) == 0:
    InitGlobals()
  
  no_arch = (GetArgument("no-arch", 0, int) != 0)
  
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
    mscver = GetArgument("mscver", "9.0")
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
    
    if warnl == "none":
      env.Append(CPPFLAGS=" /w")
    elif warnl == "std":
      env.Append(CPPFLAGS=" /W3")
    elif warnl == "all":
      #env.Append(CPPFLAGS=" /Wall")
      env.Append(CPPFLAGS=" /W4")
    
    #if "INCLUDE" in os.environ:
    #  env.Append(CPPPATH=os.environ["INCLUDE"].split(";"))
    #if "LIB" in os.environ:
    #  env.Append(LIBPATH=os.environ["LIB"].split(";"))
    mt = Which("mt")
    if mt is None:
      mt = "mt.exe"
    
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
          env.Append(CPPFLAGS=" -std=c++11")
          
          if warnl == "std":
            # remove some more c++11 specific warnings
            env.Append(CPPFLAGS=" ".join(["-Wno-deprecated-register",
                                          "-Wno-deprecated-declarations",
                                          "-Wno-missing-field-initializers",
                                          "-Wno-unused-private-field"]))
        
        if GetArgument("use-stdc++", 0, int):
          SetArgument("use-stdc++", 1)
          env.Append(CPPFLAGS=" -stdlib=libstdc++")
          env.Append(LINKFLAGS=" -stdlib=libstdc++")
  
  if GetArgument("debug", 0, int):
    mode_dir = "debug"
    SetupDebug(env)
  else:
    mode_dir = "release"
    SetupRelease(env)
  
  if no_arch:
    env.Append(CPPPATH=[os.path.join(out_dir, mode_dir, "include")])
    env.Append(LIBPATH=[os.path.join(out_dir, mode_dir, "lib")])
  else:
    env.Append(CPPPATH=[os.path.join(out_dir, mode_dir, arch_dir, "include")])
    env.Append(LIBPATH=[os.path.join(out_dir, mode_dir, arch_dir, "lib")])
  
  env["TARGET_ARCH"] = arch_dir
  env["TARGET_MODE"] = mode_dir
  
  return env

def OutputBaseDirectory():
  global out_dir, mode_dir, arch_dir, no_arch
  
  if not no_arch:
    return os.path.join(out_dir, mode_dir, arch_dir)
  else:
    return os.path.join(out_dir, mode_dir)

def DeclareTargets(env, prjs):
  global bld_dir, out_dir, mode_dir, arch_dir, mscver, no_arch, args_no_cache, args_cache
  
  all_projs = {}
  
  for settings in prjs:
    
    # recusively add deps if one of the lib or deps is a project
    
    if not "name" in settings:
      print("Project missing \"name\"")
      continue
    
    prj = settings["name"]
    
    if not "srcs" in settings:
      print("Project \"%s\" missing \"src\"" % prj)
      continue
    
    if not "type" in settings:
      print("Project \"%s\" missing \"type\"" % prj)
      continue
    
    penv = env.Clone()
    
    def add_deps(tgt):
      if "deps" in settings:
        for dep in settings["deps"]:
          if dep in all_projs:
            penv.Depends(tgt, all_projs[dep])
            # but should not clean all_projs[dep]
      # also check in libs (because of windows way to handle shared lib)
      if "libs" in settings:
        for lib in settings["libs"]:
          if lib in all_projs:
            penv.Depends(tgt, all_projs[lib])
            # but should not clean all_projs[lib]
    
    
    if "libdirs" in settings:
      penv.Append(LIBPATH=settings["libdirs"])
    
    if "incdirs" in settings:
      penv.Append(CPPPATH=settings["incdirs"])
    
    if "defs" in settings:
      penv.Append(CPPDEFINES=settings["defs"])
    
    if "libs" in settings:
      penv.Append(LIBS=settings["libs"])
    
    if "custom" in settings:
      for customcall in settings["custom"]:
        customcall(penv)
    
    if "alias" in settings:
      odir = os.path.join(bld_dir, mode_dir, sys.platform, arch_dir, settings["alias"])
    else:
      odir = os.path.join(bld_dir, mode_dir, sys.platform, arch_dir, prj)
    # On windows, also msvc-9.0
    if str(Platform()) == "win32":
      msvcver = env.get("MSVC_VERSION", None)
      if msvcver:
        odir = os.path.join(odir, "msvc-%s" % msvcver)
    if "bldprefix" in settings:
      odir = os.path.join(odir, settings["bldprefix"])
    
    shared = True
    if settings["type"] in ["program", "testprograms", "staticlib"]:
      shared = False
    
    if str(Platform()) != "win32" and settings["type"] != "sharedlib":
      penv.Append(CCFLAGS=["-fvisibility=hidden"])
    
    objs = []
    for src in settings["srcs"]:
      bn = os.path.splitext(os.path.basename(src))[0]
      if shared:
        objs.append(penv.SharedObject(os.path.join(odir, bn), src))
      else:
        objs.append(penv.StaticObject(os.path.join(odir, bn), src))
    
    if settings["type"] == "sharedlib":
      if str(Platform()) == "win32":
        if settings.get("win_separate_dll_and_lib", True):
          if no_arch:
            outbn = os.path.join(out_dir, mode_dir, "bin", prj)
            impbn = os.path.join(out_dir, mode_dir, "lib", prj)
          else:
            outbn = os.path.join(out_dir, mode_dir, arch_dir, "bin", prj)
            impbn = os.path.join(out_dir, mode_dir, arch_dir, "lib", prj)
        else:
          if no_arch:
            impbn = os.path.join(out_dir, mode_dir, "lib", prj)
          else:
            impbn = os.path.join(out_dir, mode_dir, arch_dir, "lib", prj)
          outbn = impbn
            
        try:
          os.makedirs(os.path.dirname(impbn))
        except:
          pass
        penv['no_import_lib'] = 1
        penv.Append(SHLINKFLAGS=" /implib:%s.lib" % impbn)
        pout = penv.SharedLibrary(outbn, objs)
        # Cleanup
        penv.Clean(pout, impbn+".lib")
        penv.Clean(pout, impbn+".exp")
        if float(mscver) > 7.1 and float(mscver) < 10.0:
          penv.Clean(pout, outbn+".dll.manifest")
        if GetArgument("debug", 0, int):
          penv.Clean(pout, outbn+".ilk")
          penv.Clean(pout, outbn+".pdb")
      else:
        dn, bn = os.path.split(prj)
        if dn:
          dn += "/"
          relpath = "/".join([".."] * dn.count("/"))
        else:
          relpath = None
        
        SetRPath(penv, settings, relpath=relpath)
        
        if no_arch:
          pout = penv.SharedLibrary(os.path.join(out_dir, mode_dir, "lib", prj), objs)
        else:
          pout = penv.SharedLibrary(os.path.join(out_dir, mode_dir, arch_dir, "lib", prj), objs)
        
        if sys.platform == "darwin":
          penv.Append(LINKFLAGS=" -Wl,-install_name,@rpath/%slib%s.dylib" % (dn, bn))
          #penv.AddPostAction(pout, "install_name_tool -id @rpath/lib%s.dylib $TARGETS" % os.path.basename(prj))
        else:
          penv.Append(LINKFLAGS=" -Wl,-soname,lib%s.so" % bn)
      add_deps(pout)
    
    elif settings["type"] == "program":
      if no_arch:
        outbn = os.path.join(out_dir, mode_dir, "bin", prj)
      else:
        outbn = os.path.join(out_dir, mode_dir, arch_dir, "bin", prj)
      if GetArgument("no-console", 0, int) or ("console" in settings and settings["console"] is False):
        NoConsole(penv)
      SetStackSize(penv, size=settings.get("stacksize", ParseStackSize(GetArgument("stack-size", None))))
      
      dn, _ = os.path.split(prj)
      if dn:
        relpath = "/".join([".."] * (1 + dn.count("/"))) + "/../lib"
      else:
        relpath = "../lib"
      
      SetRPath(penv, settings, relpath=relpath)
      
      pout = penv.Program(outbn, objs)
      add_deps(pout)
      # Cleanup
      if str(Platform()) == "win32":
        if float(mscver) > 7.1 and float(mscver) < 10.0:
          penv.Clean(pout, outbn+".exe.manifest")
        if GetArgument("debug", 0, int):
          penv.Clean(pout, outbn+".ilk")
          penv.Clean(pout, outbn+".pdb")
    
    elif settings["type"] == "staticlib":
      if no_arch:
        pout = penv.StaticLibrary(os.path.join(out_dir, mode_dir, "lib", prj), objs)
      else:
        pout = penv.StaticLibrary(os.path.join(out_dir, mode_dir, arch_dir, "lib", prj), objs)
      add_deps(pout)
    
    elif settings["type"] == "testprograms":
      pout = []
      if GetArgument("no-console", 0, int) or ("console" in settings and settings["console"] is False):
        NoConsole(penv)
      SetStackSize(penv, size=settings.get("stacksize", ParseStackSize(GetArgument("stack-size", None))))
      SetRPath(penv, settings, relpath="../lib")
      for obj in objs:
        name = os.path.splitext(os.path.basename(str(obj)))[0]
        if no_arch:
          outbn = os.path.join(out_dir, mode_dir, "bin", name)
        else:
          outbn = os.path.join(out_dir, mode_dir, arch_dir, "bin", name)
        prg = penv.Program(outbn, obj)
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
      if no_arch:
        prefix = os.path.join(out_dir, mode_dir)
      else:
        prefix = os.path.join(out_dir, mode_dir, arch_dir)
      if "prefix" in settings:
        prefix = os.path.join(prefix, settings["prefix"])
      if str(Platform()) == "win32":
        outbn = os.path.join(prefix, prj)
        penv["SHLIBPREFIX"] = ""
        if "ext" in settings:
          penv["SHLIBSUFFIX"] = settings["ext"]
        # set import lib in build folder
        impbn = os.path.join(odir, os.path.basename(prj))
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
        pout = penv.LoadableModule(os.path.join(prefix, prj), objs)
      add_deps(pout)
    
    else:
      pout = None
    
    if pout:
      if "post" in settings:
        penv.AddPostAction(pout, settings["post"])
      
      if "install" in settings:
        for prefix, files in settings["install"].iteritems():
          if no_arch:
            dst = os.path.join(out_dir, mode_dir, prefix)
          else:
            dst = os.path.join(out_dir, mode_dir, arch_dir, prefix)
          inst = penv.Install(dst, files)
          penv.Depends(pout, inst)
      
      if "alias" in settings:
        Alias(settings["alias"], pout)
        all_projs[settings["alias"]] = pout
      else:
        Alias(prj, pout)
        all_projs[prj] = pout
  
  if not args_no_cache and args_cache:
    args_cache.write()
  
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
