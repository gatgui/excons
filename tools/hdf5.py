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

def GetOptionsString():
  return """HDF5 OPTIONS
  with-hdf5=<path>     : HDF5 prefix                []
  with-hdf5-inc=<path> : HDF5 headers directory     [<prefix>/include]
  with-hdf5-lib=<path> : HDF5 libraries directory   [<prefix>/lib]
  hdf5-name=<str>      : Override HDF5 library name []
                         (default library name is hdf532/hdf564 on windows, hdf5 on linux)
  hdf5-suffix=<str>    : HDF5 library suffix        ['']
                         (ignored when hdf5-name is set)
  hdf5-static=0|1      : Use HDF5 static library    [1]"""

def Require(hl=False, verbose=False):
  global ThreadSafe_exp, Szlib_exp, Zlib_exp, hdf5_confs

  hdf5_inc, hdf5_lib = excons.GetDirs("hdf5")

  hdf5_static = (excons.GetArgument("hdf5-static", 0, int) != 0)

  hdf5_libname = excons.GetArgument("hdf5-name", None)
  if not hdf5_libname:
    hdf5_libsuffix = excons.GetArgument("hdf5-suffix", "")
    hdf5_basename = ("hdf5" if sys.platform != "win32" else "libhdf5")
    hdf5_libname = hdf5_basename + hdf5_libsuffix
    hdf5hl_libname = hdf5_basename + "_hl" + hdf5_libsuffix
  else:
    hdf5hl_libname = hdf5_libname + "_hl"

  def GetConf(env, incdir):
    h5conf = None
    cfg = {"threadsafe": False,
           "zlib": False,
           "szip": False}
    
    quiet = not verbose

    if incdir:
      # Note: On Fedora 14, H5pubconf.h has been renamed to H5pubconf-64.h
      #       -> be slightly more flexible when looking up this file
      lst = filter(lambda x: os.path.basename(x).startswith("H5pubconf"), excons.glob(incdir+"/*.h"))
      if len(lst) > 0:
        h5conf = lst[0].replace("\\", "/")
    
    else:
      # Look in current include paths
      for d in env["CPPPATH"]:
        lst = filter(lambda x: os.path.basename(x).startswith("H5pubconf"), excons.glob(d+"/*.h"))
        if len(lst) > 0:
          h5conf = lst[0].replace("\\", "/")
          break
    
    if h5conf:
      
      if h5conf in hdf5_confs:
        quiet = True
        cfg = hdf5_confs[h5conf]
      
      else:
        if verbose:
          excons.PrintOnce("Reading configuration header '%s'..." % h5conf, tool="hdf5")
        
        f = open(h5conf, "r")
         
        for l in f.readlines():
          l = l.strip()
          
          if ThreadSafe_exp.match(l):
            cfg["threadsafe"] = True
          
          elif Szip_exp.match(l):
            cfg["szip"] = True
          
          elif Zlib_exp.match(l):
            cfg["zlib"] = True
        
        hdf5_confs[h5conf] = cfg
        
        f.close()
      
      if not quiet:
        if cfg["threadsafe"]:
          excons.PrintOnce("Thread safe", tool="hdf5")
        
        if cfg["zlib"]:
          excons.PrintOnce("Using zlib", tool="hdf5")
        
        if cfg["szip"]:
          excons.PrintOnce("Using szip", tool="hdf5")
    
    else:
      excons.WarnOnce("Could not find configuration header", tool="hdf5")

    return (False, cfg)

  def _RealRequire(env):
    quiet, cfg = GetConf(env, hdf5_inc)

    if hdf5_inc:
      env.Append(CPPPATH=[hdf5_inc])
    
    if hdf5_lib:
      env.Append(LIBPATH=[hdf5_lib])
    
    if hl:
      excons.Link(env, hdf5hl_libname, static=hdf5_static, force=True, silent=True)
    
    excons.Link(env, hdf5_libname, static=hdf5_static, force=True, silent=True)
    
    if hdf5_static:
      if not quiet:
        excons.PrintOnce("Static build", tool="hdf5")

      if cfg["threadsafe"]:
        threads.Require(env)
      
      if cfg["zlib"]:
        if excons.GetArgument("zlib-static", None) is None:
          if not quiet:
            excons.PrintOnce("Force static zlib", tool="hdf5")
          excons.SetArgument("zlib-static", 1)
        zlib.Require(env)
      
      if cfg["szip"]:
        if excons.GetArgument("szip-static", None) is None:
          if not quiet:
            excons.PrintOnce("Force static szip", tool="hdf5")
          excons.SetArgument("szip-static", 1)
        szip.Require(env)
      
  return _RealRequire
