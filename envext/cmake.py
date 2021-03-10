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
import excons
import pprint
import excons.cmake as cmake
import SCons.Script # pylint: disable=import-error


def DummyScanner(node, env, path):
   return []

def ConfigureAction(target, source, env):
   if not cmake.Configure(env["CMAKE_PROJECT"], topdir=env["CMAKE_TOPDIR"], opts=env["CMAKE_OPTIONS"], flags=env["CMAKE_FLAGS"], min_mscver=env["CMAKE_MIN_MSCVER"]):
      if os.path.isfile(env["CMAKE_CONFIG_CACHE"]):
         os.remove(env["CMAKE_CONFIG_CACHE"])
      if os.path.isfile(env["CMAKE_CACHE"]):
         os.remove(env["CMAKE_CACHE"])
      raise Exception("CMake Configure Failed")
   return None

def BuildAction(target, source, env):
   if not cmake.Build(env["CMAKE_PROJECT"], config=env["CMAKE_CONFIG"], target=env["CMAKE_TARGET"]):
      raise Exception("CMake Build Failed")
   return None

def SetupEnvironment(env, settings):
   name = settings["name"]

   debug = (excons.GetArgument("debug", 0, int) != 0)
   opts = settings.get("cmake-opts", {})
   flags = settings.get("cmake-flags", "")
   blddir = cmake.BuildDir(name)
   cmakec = blddir + "/CMakeCache.txt"
   cfgc = cmake.ConfigCachePath(name)
   cexts = [".c", ".h", ".cc", ".hh", ".cpp", ".hpp", ".cxx", ".hxx"]

   # Override default C/C++ file scanner to avoid SCons being too nosy
   env.Prepend(SCANNERS=SCons.Script.Scanner(function=DummyScanner, skeys=cexts))
   env["CMAKE_PROJECT"] = name
   env["CMAKE_TOPDIR"] = excons.abspath(settings.get("cmake-root", "."))
   env["CMAKE_OPTIONS"] = opts
   env["CMAKE_FLAGS"] = flags
   env["CMAKE_MIN_MSCVER"] = settings.get("cmake-min-mscver", None)
   env["CMAKE_CONFIG"] = settings.get("cmake-config", ("debug" if debug else "release"))
   env["CMAKE_TARGET"] = settings.get("cmake-target", "install")
   env["CMAKE_CACHE"] = cmakec
   env["CMAKE_CONFIG_CACHE"] = cfgc
   env["BUILDERS"]["CMakeConfigure"] = SCons.Script.Builder(action=SCons.Script.Action(ConfigureAction, "Configure using CMake ..."))
   env["BUILDERS"]["CMake"] = SCons.Script.Builder(action=SCons.Script.Action(BuildAction, "Build using CMake ..."))

   # Check if we need to reconfigure
   if not SCons.Script.GetOption("clean"):
      if not os.path.isdir(blddir):
         try:
            os.makedirs(blddir)
         except:
            return None

      doconf = True
      if os.path.isfile(cfgc):
         doconf = False
         with open(cfgc, "r") as f:
            try:
               d = eval(f.read())
               for k, v in d.iteritems():
                  if not k in opts or opts[k] != v:
                     doconf = True
                     break
               if not doconf:
                  for k, v in opts.iteritems():
                     if not k in d:
                        doconf = True
                        break
            except:
               doconf = True
      if doconf or int(SCons.Script.ARGUMENTS.get("reconfigure", "0")) != 0:
         # Only rewrite cfgc when strictly needed
         if doconf:
            with open(cfgc, "w") as f:
               pprint.pprint(opts, stream=f)
         if os.path.isfile(cmakec):
            os.remove(cmakec)

   cins = settings.get("cmake-cfgs", [])
   cins.append(cfgc)
   cins.extend(cmake.AdditionalConfigureDependencies(name))
   cout = [cmakec]

   env.CMakeConfigure(cout, cins)

   bins = settings.get("cmake-srcs", [])
   bins.extend(cout)

   expected_outputs = settings.get("cmake-outputs", [])
   expected_outputs = map(lambda x: (x if os.path.isabs(x) else (excons.OutputBaseDirectory() + "/" + x)), expected_outputs)
   actual_outputs = cmake.Outputs(name)
   bout = list(set(actual_outputs).union(set(expected_outputs))) + [cmake.OutputsCachePath(name)]

   out = env.CMake(bout, bins)

   # Run clean last
   cmake.CleanOne(name)

   return out
