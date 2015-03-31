# Copyright (C) 2015~  Gaetan Guidet
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
import os
import re
import sys
import excons
from excons.tools import zlib
from excons.tools import threads

ThreadSafe_exp = re.compile(r"^\s*#define\s+H5_HAVE_THREADSAFE\s+1")
Szip_exp = re.compile(r"^\s*#define\s+H5_HAVE_SZLIB_H\s+1")
Zlib_exp = re.compile(r"^\s*#define\s+H5_HAVE_ZLIB_H\s+1")

def Require(hl=False, verbose=False):
  
  def _RealRequire(env):
    global ThreadSafe_exp, Szlib_exp, Zlib_exp
    
    hdf5_inc, hdf5_lib = excons.GetDirs("hdf5")
    hdf5_libname = excons.GetArgument("hdf5-libname", ("hdf5" if sys.platform != "win32" else "libhdf5"))
    
    hdf5_static = excons.GetArgument("hdf5-static", None)
    if hdf5_static is None:
      hdf5_static = (excons.GetArgument("static", 0, int) != 0)
    else:
      try:
        hdf5_static = (int(hdf5_static) != 0)
      except:
        hdf5_static = True
    
    hdf5_threadsafe = False
    hdf5_szip = False
    hdf5_zlib = False
    
    incdirs = []
    libdirs = []
    libs = []
    
    if hdf5_inc:
      h5conf = os.path.join(hdf5_inc, "H5pubconf.h")
      if os.path.isfile(h5conf):
        if verbose:
          print("[HDF5] Reading configuration header...")
        
        f = open(h5conf, "r")
         
        for l in f.readlines():
          l = l.strip()
          
          if ThreadSafe_exp.match(l):
            if verbose:
              print("[HDF5] Thread safe")
            hdf5_threadsafe = True
          
          elif Szip_exp.match(l):
            if verbose:
              print("[HDF5] Using szip")
            hdf5_szip = True
          
          elif Zlib_exp.match(l):
            if verbose:
              print("[HDF5] Using zlib")
            hdf5_zlib = True
        
        f.close()
    
    if hdf5_static:
      if verbose:
        print("[HDF5] Static build")
      
      if hdf5_threadsafe:
        threads.Require(env)
      
      if hdf5_zlib:
        if not excons.GetArgument("with-zlib") and \
           not excons.GetArgument("with-zlib-inc") and \
           not excons.GetArgument("with-zlib-lib"):
          if hdf5_inc:
            excons.SetArgument("with-zlib-inc", hdf5_inc)
          if hdf5_lib:
            excons.SetArgument("with-zlib-lib", hdf5_inc)
           
        zlib.Require(env)
      
      if hdf5_szip:
        szip_inc, szip_lib = excons.GetDirsWithDefault("szip", incdirdef=hdf5_inc, libdirdef=hdf5_lib)
        if szip_inc and szip_inc != hdf5_inc:
          incdirs.append(szip_inc)
        if szip_lib and szip_lib != hdf5_lib:
          libdirs.append(szip_lib)
        szip_libname = excons.GetArgument("szip-libname", ("sz" if sys.platform != "win32" else "libszip"))
        libs.append(szip_libname)
    
    if hdf5_inc:
      incdirs.append(hdf5_inc)
    if hdf5_lib:
      incdirs.append(hdf5_lib)
    
    libs.append(hdf5_libname)
    if hl:
      libs.append(hdf5_libname+"_hl")
    
    env.Append(CPPPATH=incdirs)
    env.Append(LIBPATH=libdirs)
    env.Append(LIBS=libs)
      
  return _RealRequire
