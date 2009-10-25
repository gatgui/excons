# Copyright (C) 2009  Gaetan Guidet
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
from SCons.Script import *

bin_sfx = ""
bld_dir = ".build"
out_dir = "."
obj_dir = ""

def SetupMSVCDebug(env):
  env.Append(CPPFLAGS = " /MDd /Od")
  env.Append(CPPDEFINES = ["_DEBUG"])
  env.Append(LINKFLAGS = " /debug /opt:noref /opt:noicf")

def SetupMSVCRelease(env):
  env.Append(CPPFLAGS = " /Gy /MD /O2")
  env.Append(CPPDEFINES = ["NDEBUG"])
  env.Append(LINKFLAGS = " /release /opt:ref /opt:noicf")

def SetupGCCDebug(env):
  env.Append(CPPFLAGS = " -O0 -g -ggdb")
  env.Append(CPPDEFINES = ["_DEBUG"])

def SetupGCCRelease(env):
  env.Append(CPPFLAGS = " -O2")
  env.Append(CPPDEFINES = ["NDEBUG"])
  if int(ARGUMENTS.get("strip", 0)) == 1:
    if str(Platform()) == "darwin":
      env.Append(LINKFLAGS = " -Wl,-dead_strip")
    else:
      env.Append(LINKFLAGS = " -s")

def NoConsole(env):
  if str(Platform()) == "win32":
    env.Append(LINKFLAGS = " /subsystem:windows /entry:mainCRTStartup")

def MakeBaseEnv():
  global bld_dir, out_dir, bin_sfx, obj_dir
  
  SetupRelease = None
  SetupDebug   = None
  
  if str(Platform()) == "win32":
    mscver = ARGUMENTS.get("mscver", "8.0")
    env = Environment(MSVS_VERSION=mscver)
    # XP:    _WIN32_WINNT=0x0500
    # Vista: _WIN32_WINNT=0x0600
    winnt = "_WIN32_WINNT=0x0400"
    m = re.match(r"(\d)(\.(\d)(\.(\d+))?)?", platform.version())
    if m:
      winnt = "_WIN32_WINNT=0x0%s00" % m.group(1)
    env.Append(CPPDEFINES = [winnt, "_USE_MATH_DEFINES", "_WIN32", "WIN32", "_WINDOWS"])
    env.Append(CPPFLAGS = " /W4 /Wp64 /GR /EHsc")
    #env.Append(CPPPATH = ["etc/win32/include"])
    #env.Append(LIBPATH = ["etc/win32/lib"])
    if float(mscver) > 7.1:
      env.Append(CPPDEFINES = ["_CRT_SECURE_NO_DEPRECATE"])
      env['LINKCOM'] = [env['LINKCOM'], 'mt.exe -nologo -manifest ${TARGET}.manifest -outputresource:$TARGET;1']
      env['SHLINKCOM'] = [env['SHLINKCOM'], 'mt.exe -nologo -manifest ${TARGET}.manifest -outputresource:$TARGET;2']
    SetupRelease = SetupMSVCRelease
    SetupDebug = SetupMSVCDebug
  else:
    env = Environment()
    # Base GCC setup
    env.Append(CPPFLAGS = " -pipe -W -Wall")
    SetupRelease = SetupGCCRelease
    SetupDebug = SetupGCCDebug
    #if str(Platform()) == "darwin":
    #  env.Append(CPPPATH = ["/opt/local/include"])
    #  env.Append(LIBPATH = ["/opt/local/lib"])
  
  env.Append(CPPPATH = ["include"])
  env.Append(LIBPATH = ["lib"])
  
  ext = ARGUMENTS.get("extra-dir", None)
  if ext:
    env.Append(CPPPATH = [os.path.join(ext, "include")])
    env.Append(LIBPATH = [os.path.join(ext, "lib")])
  
  ext = ARGUMENTS.get("extra-include-dir", None)
  if ext:
    env.Append(CPPPATH = [ext])
  
  ext = ARGUMENTS.get("extra-lib-dir", None)
  if ext:
    env.Append(LIBPATH = [ext])
  
  if int(ARGUMENTS.get("debug", 0)):
    obj_dir = "debug"
    SetupDebug(env)
  else:
    obj_dir = "release"
    SetupRelease(env)
  
  return env

def DeclareTargets(env, prjs):
  global bld_dir, out_dir, bin_sfx, obj_dir
  
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
    
    odir = os.path.join(bld_dir, obj_dir, prj)
    
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
        outbn = os.path.join(out_dir, prj)
        impbn = os.path.join(out_dir, "lib", prj)
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
        pout = penv.SharedLibrary(os.path.join(out_dir, "lib", prj), objs)
      add_deps(pout)
    
    elif settings["type"] == "program":
      outbn = os.path.join(out_dir, prj)
      if int(ARGUMENTS.get("no-console", 0)):
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
      pout = penv.StaticLibrary(os.path.join(out_dir, "lib", prj), objs)
      add_deps(pout)
    
    elif settings["type"] == "testprograms":
      pout = []
      if int(ARGUMENTS.get("no-console", 0)):
        NoConsole(penv)
      for obj in objs:
        name = os.path.splitext(os.path.basename(str(obj)))[0]
        outbn = os.path.join(out_dir, name)
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
      prefix = out_dir
      if "prefix" in settings:
        prefix = os.path.join(prefix, settings["prefix"])
      if str(Platform()) == "win32":
        outbn = os.path.join(prefix, prj)
        penv["SHLIBPREFIX"] = ""
        if "ext" in settings:
          penv["SHLIBSUFFIX"] = settings["ext"]
        # set import lib in build folder
        impbn = os.path.join(odir, prj)
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
      Alias(prj, pout)
    
    all_projs[prj] = pout


