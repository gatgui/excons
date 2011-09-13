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

bld_dir  = os.path.abspath("./.build")
out_dir  = os.path.abspath(".")
mode_dir = None
arch_dir = "x86" if platform.architecture()[0] == '32bit' else "x64"
mscver   = None
no_arch  = (int(ARGUMENTS.get("no-arch", "0")) == 1)

arch_over = ARGUMENTS.get("x64", None)
if arch_over != None:
  if int(arch_over) == 1:
    arch_dir = "x64"
  else:
    arch_dir = "x86"
else:
  arch_over = ARGUMENTS.get("x86", None)
  if arch_over != None:
    if int(arch_over) == 1:
      arch_dir = "x86"
    else:
      arch_dir = "x64"

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
    paths = filter(lambda x: len(x)>0, map(lambda x: x.strip(), os.environ["PATH"].split(pathsplit)))
    for path in paths:
      for item in glob.glob(os.path.join(path, "*")):
        if os.path.isdir(item):
          continue
        bn = os.path.basename(item)
        if texp.match(bn) != None:
          return item.replace("\\", "/")

  return None

def NoConsole(env):
  if str(Platform()) == "win32":
    env.Append(LINKFLAGS = " /subsystem:windows /entry:mainCRTStartup")

def MakeBaseEnv(noarch=None):
  global bld_dir, out_dir, mode_dir, arch_dir, mscver, no_arch
  
  if noarch != None:
    no_arch = noarch
  
  def SetupMSVCDebug(env):
    env.Append(CPPFLAGS = " /MDd /Od /Zi")
    env.Append(CPPDEFINES = ["_DEBUG"])
    env.Append(LINKFLAGS = " /debug /opt:noref /opt:noicf /incremental:yes")
  
  def SetupMSVCRelease(env):
    env.Append(CPPFLAGS = " /Gy /MD /O2")
    env.Append(CPPDEFINES = ["NDEBUG"])
    env.Append(LINKFLAGS = " /release /opt:ref /opt:icf /incremental:no")
  
  def SetupMSVCReleaseWithDebug(env):
    env.Append(CPPFLAGS = " /MD /Od /Zi")
    env.Append(CPPDEFINES = ["NDEBUG"])
    env.Append(LINKFLAGS = " /debug /opt:noref /opt:noicf /incremental:yes")
  
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
    env.Append(CPPFLAGS = " -O0 -g -ggdb")
    env.Append(CPPDEFINES = ["_DEBUG"])
  
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
    env.Append(CPPFLAGS = " -O2")
    env.Append(CPPDEFINES = ["NDEBUG"])
    if int(ARGUMENTS.get("strip", 0)) == 1:
      if str(Platform()) == "darwin":
        env.Append(LINKFLAGS = " -Wl,-dead_strip")
      else:
        env.Append(LINKFLAGS = " -s")
  
  
  SetupRelease = None
  SetupDebug   = None
  
  if str(Platform()) == "win32":
    mscver = ARGUMENTS.get("mscver", "8.0")
    msvsarch = "amd64" if arch_dir == "x64" else "x86"
    env = Environment(MSVC_VERSION=mscver, MSVS_VERSION=mscver, MSVS_ARCH=msvsarch, TARGET_ARCH=msvsarch)
    # XP:    _WIN32_WINNT=0x0500
    # Vista: _WIN32_WINNT=0x0600
    winnt = "_WIN32_WINNT=0x0400"
    m = re.match(r"(\d)(\.(\d)(\.(\d+))?)?", platform.version())
    if m:
      winnt = "_WIN32_WINNT=0x0%s00" % m.group(1)
    env.Append(CPPDEFINES = [winnt, "_USE_MATH_DEFINES", "_WIN32", "WIN32", "_WINDOWS"])
    env.Append(CPPFLAGS = " /W4 /GR /EHsc")
    #if "INCLUDE" in os.environ:
    #  env.Append(CPPPATH=os.environ["INCLUDE"].split(";"))
    #if "LIB" in os.environ:
    #  env.Append(LIBPATH=os.environ["LIB"].split(";"))
    mt = Which("mt")
    if mt is None:
      mt = "mt.exe"
    if float(mscver) > 7.1:
      env.Append(CPPDEFINES = ["_CRT_SECURE_NO_DEPRECATE"])
      env['LINKCOM'] = [env['LINKCOM'], '\"%s\" -nologo -manifest ${TARGET}.manifest -outputresource:$TARGET;1' % mt]
      env['SHLINKCOM'] = [env['SHLINKCOM'], '\"%s\" -nologo -manifest ${TARGET}.manifest -outputresource:$TARGET;2' % mt]
    SetupRelease = SetupMSVCRelease
    SetupDebug = SetupMSVCDebug
    if int(ARGUMENTS.get("debugInfo", "0")) == 1:
      SetupRelease = SetupMSVCReleaseWithDebug
  else:
    env = Environment()
    env.Append(CPPFLAGS = " -pipe -W -Wall")
    SetupRelease = SetupGCCRelease
    SetupDebug = SetupGCCDebug
    if str(Platform()) == "darwin":
      if os.path.exists("/opt/local"):
        env.Append(CPPPATH = ["/opt/local/include"])
        env.Append(LIBPATH = ["/opt/local/lib"])
    else:
      env.Append(CCFLAGS = " -fPIC")
  
  if int(ARGUMENTS.get("debug", 0)):
    mode_dir = "debug"
    SetupDebug(env)
  else:
    mode_dir = "release"
    SetupRelease(env)
  
  if no_arch:
    env.Append(CPPPATH = [os.path.join(out_dir, mode_dir, "include")])
    env.Append(LIBPATH = [os.path.join(out_dir, mode_dir, "lib")])
  else:
    env.Append(CPPPATH = [os.path.join(out_dir, mode_dir, arch_dir, "include")])
    env.Append(LIBPATH = [os.path.join(out_dir, mode_dir, arch_dir, "lib")])
  
  env["TARGET_ARCH"] = arch_dir
  env["TARGET_MODE"] = mode_dir
  
  return env

def DeclareTargets(env, prjs):
  global bld_dir, out_dir, mode_dir, arch_dir, mscver, no_arch
  
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
      penv.Append(LIBPATH = settings["libdirs"])
    
    if "incdirs" in settings:
      penv.Append(CPPPATH = settings["incdirs"])
    
    if "defs" in settings:
      penv.Append(CPPDEFINES = settings["defs"])
    
    if "libs" in settings:
      penv.Append(LIBS = settings["libs"])
    
    if "custom" in settings:
      for customcall in settings["custom"]:
        customcall(penv)
    
    if no_arch:
      odir = os.path.join(bld_dir, mode_dir, prj)
    else:
      odir = os.path.join(bld_dir, mode_dir, arch_dir, prj)
    
    shared = True
    if settings["type"] == "program" or\
       settings["type"] == "testprograms" or\
       settings["type"] == "staticlib":
     shared = False
    
    objs = []
    for src in settings["srcs"]:
      bn = os.path.splitext(os.path.basename(src))[0]
      if shared:
        objs.append(penv.SharedObject(os.path.join(odir, bn), src))
      else:
        objs.append(penv.StaticObject(os.path.join(odir, bn), src))
    
    if settings["type"] == "sharedlib":
      if str(Platform()) == "win32":
        if no_arch:
          outbn = os.path.join(out_dir, mode_dir, "bin", prj)
          impbn = os.path.join(out_dir, mode_dir, "lib", prj)
        else:
          outbn = os.path.join(out_dir, mode_dir, arch_dir, "bin", prj)
          impbn = os.path.join(out_dir, mode_dir, arch_dir, "lib", prj)
        try:
          os.makedirs(os.path.dirname(impbn))
        except:
          pass
        penv['no_import_lib'] = 1
        penv.Append(SHLINKFLAGS = " /implib:%s.lib" % impbn)
        pout = penv.SharedLibrary(outbn, objs)
        # Cleanup
        penv.Clean(pout, impbn+".lib")
        penv.Clean(pout, impbn+".exp")
        if float(mscver) > 7.1:
          penv.Clean(pout, outbn+".dll.manifest")
        if int(ARGUMENTS.get("debug", 0)):
          penv.Clean(pout, outbn+".ilk")
          penv.Clean(pout, outbn+".pdb")
      else:
        if no_arch:
          pout = penv.SharedLibrary(os.path.join(out_dir, mode_dir, "lib", prj), objs)
        else:
          pout = penv.SharedLibrary(os.path.join(out_dir, mode_dir, arch_dir, "lib", prj), objs)
      add_deps(pout)
    
    elif settings["type"] == "program":
      if no_arch:
        outbn = os.path.join(out_dir, mode_dir, "bin", prj)
      else:
        outbn = os.path.join(out_dir, mode_dir, arch_dir, "bin", prj)
      if int(ARGUMENTS.get("no-console", 0)) or ("console" in settings and settings["console"] is False):
        NoConsole(penv)
      pout = penv.Program(outbn, objs)
      add_deps(pout)
      # Cleanup
      if str(Platform()) == "win32":
        if float(mscver) > 7.1:
          penv.Clean(pout, outbn+".exe.manifest")
        if int(ARGUMENTS.get("debug", 0)):
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
      if int(ARGUMENTS.get("no-console", 0)) or ("console" in settings and settings["console"] is False):
        NoConsole(penv)
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
          if float(mscver) > 7.1:
            penv.Clean(prg, outbn+".exe.manifest")
          if int(ARGUMENTS.get("debug", 0)):
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
        impbn = os.path.join(odir, os.path.basename(prj)) #prj)
        penv['no_import_lib'] = 1
        penv.Append(SHLINKFLAGS = " /implib:%s.lib" % impbn)
        pout = penv.SharedLibrary(outbn, objs)
        # Cleanup
        penv.Clean(pout, impbn+".lib")
        penv.Clean(pout, impbn+".exp")
        if float(mscver) > 7.1:
          penv.Clean(pout, outbn+penv["SHLIBSUFFIX"]+".manifest")
        if int(ARGUMENTS.get("debug", 0)):
          penv.Clean(pout, outbn+".ilk")
          penv.Clean(pout, outbn+".pdb")
      else:
        penv["LDMODULEPREFIX"] = ""
        if "ext" in settings:
          penv["LDMODULESUFFIX"] = settings["ext"]
        else:
          if str(Platform()) == "darwin":
            penv["LDMODULESUFFIX"] = ".bundle"
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
    


