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
import subprocess
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
printed_messages = set()
all_targets = {}


def InitGlobals(output_dir="."):
  global args_cache, args_cache_path, args_no_cache
  global bld_dir, out_dir, mode_dir, arch_dir
  global mscver, no_arch, warnl, issued_warnings
  global all_targets
  
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
  all_targets = {}


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
        print("[excons]%s Warning! %s" % (hdr, line))
        first = False
      else:
        print("[excons]%s          %s" % (hdr, line))
    issued_warnings.add(msg)

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
    prefix = os.path.abspath(os.path.expanduser(prefix))
    if not os.path.isdir(prefix):
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
    inc = os.path.abspath(os.path.expanduser(inc))
    if not os.path.isdir(inc):
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
        val = os.path.abspath(os.path.expanduser(val))
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
    lib = os.path.abspath(os.path.expanduser(lib))
    if not os.path.isdir(lib):
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
        val = os.path.abspath(os.path.expanduser(val))
        if os.path.isdir(val):
          msg = "Use environment key %s value." % libvar
          WarnOnce(msg)
          lib = val
          libsrc = "environment"
    else:
      msg = "Ignore environment key %s value." % libvar
      WarnOnce(msg)
  
  if inc is None or lib is None:
    msg = "provide %s include and/or library path by using one of:\n  %s=\n  %s=\n  %s=\nflags, or set %s and/or %s environment variables." % (name, prefixflag, incflag, libflag, incvar, libvar)
    if noexc:
      if not silent:
        msg = "You may need to %s" % msg
        WarnOnce(msg)
    else:
      raise Exception("Please %s" % msg)
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
  global bld_dir, out_dir, mode_dir, arch_dir, mscver, no_arch, args_no_cache, args_cache, all_targets
  
  all_projs = {}
  
  for settings in prjs:
    
    # recusively add deps if one of the lib or deps is a project
    
    if not "name" in settings:
      print("[excons] Project missing \"name\"")
      continue
    
    prj = settings["name"]
    prefix = settings.get("prefix", None)
    
    if not "srcs" in settings:
      print("[excons] Project \"%s\" missing \"src\"" % prj)
      continue
    
    if not "type" in settings:
      print("[excons] Project \"%s\" missing \"type\"" % prj)
      continue
    
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
    
    alias = settings.get("alias", prj)
    
    penv = env.Clone()
    
    def add_deps(tgt):
      if "deps" in settings:
        for dep in settings["deps"]:
          if dep in all_projs:
            penv.Depends(tgt, all_projs[dep])
            # but should not clean all_projs[dep]
          elif dep in all_targets:
            penv.Depends(tgt, all_targets[dep])
      # also check libs
      if "libs" in settings:
        for lib in settings["libs"]:
          if lib in all_projs:
            penv.Depends(tgt, all_projs[lib])
            # but should not clean all_projs[lib]
          elif lib in all_targets:
            penv.Depends(tgt, all_targets[lib])
    
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
      sout = []
      
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
        relpath = None
        if prefix:
          relpath = "/".join([".."] * (1 + prefix.count("/")))
        
        symlinks = set()
        
        penv["SHLIBPREFIX"] = ""
        penv["SHLIBSUFFIX"] = ""
        
        outlibdir = os.path.join(out_dir, mode_dir).replace("\\", "/")
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
      
      add_deps(pout)
      
      if sout:
        sout.extend(pout)
        pout = sout
    
    elif settings["type"] == "program":
      outbindir = os.path.join(out_dir, mode_dir).replace("\\", "/")
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
      
      add_deps(pout)
      
      # Cleanup
      if str(Platform()) == "win32":
        if float(mscver) > 7.1 and float(mscver) < 10.0:
          penv.Clean(pout, outbn+".exe.manifest")
        if GetArgument("debug", 0, int):
          penv.Clean(pout, outbn+".ilk")
          penv.Clean(pout, outbn+".pdb")
    
    elif settings["type"] == "staticlib":
      outlibdir = os.path.join(out_dir, mode_dir).replace("\\", "/")
      if not no_arch:
        outlibdir += "/" + arch_dir
      outlibdir += "/lib"
      if prefix:
        outlibdir += "/" + prefix
      
      pout = penv.StaticLibrary(outlibdir + "/" + prj, objs)
      
      add_deps(pout)
    
    elif settings["type"] == "testprograms":
      pout = []
      
      outbindir = os.path.join(out_dir, mode_dir).replace("\\", "/")
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
      outmoddir = os.path.join(out_dir, mode_dir)
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
        
        pout = penv.LoadableModule(outmoddir + "/" + prj, objs)
      
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
            for item in glob.glob(filepath + "/*"):
              install_file(dn, item)
        else:
          penv.Depends(pout, penv.Install(dstdir, filepath))
      
      if "install" in settings:
        for prefix, files in settings["install"].iteritems():
          if no_arch:
            dst = os.path.join(out_dir, mode_dir, prefix)
          else:
            dst = os.path.join(out_dir, mode_dir, arch_dir, prefix)
          for f in files:
            install_file(dst, f)
      
      aliased = all_projs.get(alias, [])
      aliased.extend(pout)
      all_projs[alias] = aliased
      
      # Also keep target name alias
      if alias != prj:
        Alias(prj, pout)
  
  if not args_no_cache and args_cache:
    args_cache.write()
  
  for alias, targets in all_projs.iteritems():
    Alias(alias, targets)
    if alias in all_targets:
      PrintOnce("Target '%s' already declared in another SCons script.")
    else:
      all_targets[alias] = targets
  
  env["EXCONS_TARGETS"] = all_projs

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

def EcosystemDist(env, ecofile, targetdirs, name=None, version=None, targets=None, defaultdir="eco", dirflag="eco-dir"):
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

  distenv = env.Clone()

  distdir = GetArgument(dirflag, defaultdir)
  verdir = "%s/%s/%s" % (distdir, name, version)

  if updenv:
    with open(ecofile+".tmp", "w") as f:
      import pprint
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
