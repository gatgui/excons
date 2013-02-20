# Copyright (C) 2013  Gaetan Guidet
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

from SCons.Script import *
import excons
import sys
import re
import os

def PluginExt():
  if str(Platform()) == "darwin":
    return ".dylib"
  elif str(Platform()) == "win32":
    return ".dll"
  else:
    return ".so"

def Plugin(env):
  env.Append(CPPDEFINES = ["MAKING_DSO"])

def GetVersionAndDirectory(noexc=False):
  verexp = re.compile(r"\d+\.\d+\.\d+(\.\d+)?")
  hfs = ARGUMENTS.get("with-houdini", None)
  
  if not hfs:
    ver = ARGUMENTS.get("houdini-ver", None)
    if not ver:
      if not noexc:
        raise Exception("Please set Houdini version using houdini-ver=")
      else:
        return (None, None)
    if not verexp.match(ver):
      if not noexc:
        raise Exception("Invalid version format: \"%s\"" % ver)
      else:
        return (None, None)
    if sys.platform == "win32":
      if excons.arch_dir == "x64":
        hfs = "C:/Program Files/Side Effects Software/Houdini %s" % ver
      else:
        hfs = "C:/Program Files (x86)/Side Effects Software/Houdini %s" % ver
    elif sys.platform == "darwin":
      hfs = "/Library/Frameworks/Houdini.framework/Versions/%s" % ver
    else:
      hfs = "/opt/hfs%s" % ver
  else:
    # retrive version from hfs
    m = verexp.search(hfs)
    if not m:
      ver = ARGUMENTS.get("houdini-ver", None)
      if not ver:
        if not noexc:
          raise Exception("Could not figure out houdini version from path \"%s\". Please provide it using houdini-ver=" % hfs)
        else:
          return (None, None)
    else:
      ver = m.group(0)
  
  if not os.path.isdir(hfs):
    if not noexc:
      raise Exception("Invalid Houdini directory: %s" % hfs)
    else:
      return (None, None)
  
  return (ver, hfs)

def Require(env):
  ver, hfs = GetVersionAndDirectory()
  
  majver = int(ver.split(".")[0])
  
  env.Append(CPPDEFINES = ["VERSION=\"%s\"" % ver])
  
  if sys.platform == "win32":
    env.Append(CPPDEFINES = ['DLLEXPORT="__declspec(dllexport)"', 'I386', 'SESI_LITTLE_ENDIAN', 'SWAP_BITFIELDS'])
    if majver >= 11: # == 11?
      env.Append(CPPDEFINES = ["NEED_SPECIALIZATION_STORAGE"])
    #env.Append(CPPPATH = [hfs+"/toolkit/include"])
    env.Append(CPPPATH = [hfs+"/toolkit/include", hfs+"/toolkit/include/OpenEXR"])
    
    libpath = hfs+"/custom/houdini/dsolib"
    env.Append(LIBS = ['libGB', 'libGEO', 'libGU', 'libUT', 'libCH', 'libOP', 'libSOP', 'libSOPz', 'libPRM'])
    env.Append(LINKFLAGS = [libpath+"/*.a", libpath+"/*.lib"])
    
  elif sys.platform == "darwin":
    env.Append(CPPDEFINES = ['DLLEXPORT=', '_GNU_SOURCE', 'MBSD', 'MBSD_COCOA', 'MBSD_INTEL', 'SESI_LITTLE_ENDIAN', 'ENABLE_THREADS', 'USE_PTHREADS', '_REENTRANT', 'GCC4', 'GCC3'])
    if excons.arch_dir == "x64":
      env.Append(CPPDEFINES = ["AMD64", "SIZEOF_VOID_P=8", "_FILE_OFFSET_BITS=64"])
    if majver >= 11: # == 11?
      env.Append(CPPDEFINES = ["NEED_SPECIALIZATION_STORAGE"])
    #env.Append(CPPPATH = [hfs+"/Resources/toolkit/include"])
    env.Append(CPPPATH = [hfs+"/Resources/toolkit/include", hfs+"/Resources/toolkit/include/OpenEXR"])
    env.Append(CCFLAGS = ['-Wno-deprecated'])
    
    env.Append(LIBPATH = [hfs+"/Libraries"])
    env.Append(LIBS = ['HoudiniUI', 'HoudiniOPZ', 'HoudiniOP3', 'HoudiniOP2', 'HoudiniOP1', 'HoudiniSIM', 'HoudiniGEO', 'HoudiniPRM', 'HoudiniUT'])
    env.Append(LINKFLAGS = " -Wl,-rpath,%s/Libraries" % hfs)
  
  else:
    env.Append(CPPDEFINES = ['DLLEXPORT=', '_GNU_SOURCE', 'LINUX', 'SESI_LITTLE_ENDIAN', 'ENABLE_THREADS', 'USE_PTHREADS', '_REENTRANT', 'GCC4', 'GCC3'])
    if excons.arch_dir == "x64":
      env.Append(CPPDEFINES = ["AMD64", "SIZEOF_VOID_P=8", "_FILE_OFFSET_BITS=64"])
    else:
      env.Append(CPPDEFINES = ["SIZEOF_VOID_P=4", "_FILE_OFFSET_BITS=32"])
    #env.Append(CPPPATH = [hfs+"/toolkit/include"])
    env.Append(CPPPATH = [hfs+"/toolkit/include", hfs+"/toolkit/include/OpenEXR"])
    env.Append(CCFLAGS = ['-Wno-deprecated'])
    
    env.Append(LIBPATH = [hfs+"/dsolib"])
    env.Append(LIBS = ['HoudiniUI', 'HoudiniOPZ', 'HoudiniOP3', 'HoudiniOP2', 'HoudiniOP1', 'HoudiniSIM', 'HoudiniGEO', 'HoudiniPRM', 'HoudiniUT'])
  
