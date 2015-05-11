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
import glob
import excons
from excons.tools import zlib
from excons.tools import szip
from excons.tools import threads

ThreadSafe_exp = re.compile(r"^\s*#define\s+H5_HAVE_THREADSAFE\s+1")
Szip_exp = re.compile(r"^\s*#define\s+H5_HAVE_SZLIB_H\s+1")
Zlib_exp = re.compile(r"^\s*#define\s+H5_HAVE_ZLIB_H\s+1")
hdf5_confs = {}

def Require(hl=False, verbose=False):
  
  def _RealRequire(env):
    global ThreadSafe_exp, Szlib_exp, Zlib_exp, hdf5_confs
    
    hdf5_inc, hdf5_lib = excons.GetDirs("hdf5")
    
    if hdf5_inc:
      env.Append(CPPPATH=[hdf5_inc])
    
    if hdf5_lib:
      env.Append(LIBPATH=[hdf5_lib])
    
    hdf5_libname = excons.GetArgument("hdf5-libname", None)
    if not hdf5_libname:
      hdf5_libsuffix = excons.GetArgument("hdf5-libsuffix", "")
      hdf5_basename = ("hdf5" if sys.platform != "win32" else "libhdf5")
      hdf5_libname = hdf5_basename + hdf5_libsuffix
      hdf5hl_libname = hdf5_basename + "_hl" + hdf5_libsuffix
    else:
      hdf5hl_libname = hdf5_libname + "_hl"
    
    if hl:
      env.Append(LIBS=[hdf5_libname, hdf5hl_libname])
    else:
      env.Append(LIBS=[hdf5_libname])
    
    hdf5_static = (excons.GetArgument("hdf5-static", 0, int) != 0)
    hdf5_threadsafe = False
    hdf5_szip = False
    hdf5_zlib = False
    
    if hdf5_inc:
      # Note: On Fedora 14, H5pubconf.h has been renamed to H5pubconf-64.h
      #       -> be slightly more flexible when looking up this file
      lst = filter(lambda x: os.path.basename(x).startswith("H5pubconf"), glob.glob(hdf5_inc+"/*.h"))
      if len(lst) > 0:
        h5conf = lst[0].replace("\\", "/")
        
        if h5conf in hdf5_confs:
          if verbose:
            print("[HDF5] Use cached configuration for '%s'..." % h5conf)
          hdf5_threadsafe = hdf5_confs[h5conf]["threadsafe"]
          hdf5_zlib = hdf5_confs[h5conf]["zlib"]
          hdf5_szip = hdf5_confs[h5conf]["szip"]
        
        else:
          if verbose:
            print("[HDF5] Reading configuration header '%s'..." % h5conf)
          
          f = open(h5conf, "r")
           
          for l in f.readlines():
            l = l.strip()
            
            if ThreadSafe_exp.match(l):
              hdf5_threadsafe = True
            
            elif Szip_exp.match(l):
              hdf5_szip = True
            
            elif Zlib_exp.match(l):
              hdf5_zlib = True
          
          hdf5_confs[h5conf] = {"threadsafe": hdf5_threadsafe,
                                "zlib": hdf5_zlib,
                                "szip": hdf5_szip}
          
          f.close()
        
        if verbose:
          if hdf5_threadsafe:
            print("[HDF5] Thread safe")
          
          if hdf5_zlib:
            print("[HDF5] Using zlib")
          
          if hdf5_szip:
            print("[HDF5] Using szip")
    
    if hdf5_static:
      if verbose:
        print("[HDF5] Static build")
      
      if hdf5_threadsafe:
        threads.Require(env)
      
      if hdf5_zlib:
        if excons.GetArgument("zlib-static", None) is None:
          if verbose:
            print("[HDF5] force static zlib")
          excons.SetArgument("zlib-static", 1)
        zlib.Require(env)
      
      if hdf5_szip:
        szip_static = excons.GetArgument("szip-static", None)
        if szip_static is None:
          if verbose:
            print("[HDF5] force static szip")
          excons.SetArgument("szip-static", 1)
        szip.Require(env)
      
  return _RealRequire
