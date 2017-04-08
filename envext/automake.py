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

import sys
import excons
import pprint
import subprocess
import excons
import excons.automake as automake
from SCons.Script import *


def DummyScanner(node, env, path):
   return []

def AutoconfAction(target, source, env):
   configure = env["AUTOMAKE_CONFIGURE"]
   autogen = env["AUTOMAKE_AUTOGEN"]

   if os.path.isfile(autogen):
      cmd = "sh %s" % autogen

   elif os.path.isfile(configure+".ac"):
      cmd = "autoreconf -vif"

   if cmd is not None:
      cmd = "cd \"%s\"; %s" % (env["AUTOMAKE_TOPDIR"], cmd)
      excons.Print("Run Command: %s" % cmd, tool="automake")
      p = subprocess.Popen(cmd, shell=True)
      p.communicate()
      if p.returncode != 0 or not os.path.isfile(configure):
         raise Exception("Failed to generate Automake 'configure' file")

   return None

def ConfigureAction(target, source, env):
   if not automake.Configure(env["AUTOMAKE_PROJECT"], topdir=env["AUTOMAKE_TOPDIR"], opts=env["AUTOMAKE_OPTIONS"]):
      if os.path.isfile(env["AUTOMAKE_CONFIG_CACHE"]):
         os.remove(env["AUTOMAKE_CONFIG_CACHE"])
      if os.path.isfile(env["AUTOMAKE_MAKEFILE"]):
         os.remove(env["AUTOMAKE_MAKEFILE"])
      raise Exception("Automake Configure Failed")
   return None

def BuildAction(target, source, env):
   if not automake.Build(env["AUTOMAKE_PROJECT"], target=env["AUTOMAKE_TARGET"]):
      raise Exception("Automake Build Failed")
   return None

def SetupEnvironment(env, settings):
   if sys.platform == "win32":
      return None

   name = settings["name"]
   debug = (excons.GetArgument("debug", 0, int) != 0)
   opts = settings.get("automake-opts", {})
   agenf = os.path.abspath("./autogen.sh")
   conff = os.path.abspath("./configure")
   blddir = automake.BuildDir(name)
   makef = blddir + "/Makefile"
   cfgc = automake.ConfigCachePath(name)
   cexts = [".c", ".h", ".cc", ".hh", ".cpp", ".hpp", ".cxx", ".hxx"]

   # Override default C/C++ file scanner to avoid SCons being too nosy
   env.Prepend(SCANNERS=Scanner(function=DummyScanner, skeys=cexts))
   env["AUTOMAKE_PROJECT"] = name
   env["AUTOMAKE_TOPDIR"] = os.path.abspath(".")
   env["AUTOMAKE_OPTIONS"] = opts
   env["AUTOMAKE_TARGET"] = settings.get("automakeg-target", "install")
   env["AUTOMAKE_CONFIGURE"] = conff
   env["AUTOMAKE_AUTOGEN"] = agenf
   env["AUTOMAKE_MAKEFILE"] = makef
   env["AUTOMAKE_CONFIG_CACHE"] = cfgc
   env["BUILDERS"]["Autoconf"] = Builder(action=Action(AutoconfAction, "Running autoconf ..."))
   env["BUILDERS"]["AutomakeConfigure"] = Builder(action=Action(ConfigureAction, "Configure using Automake ..."))
   env["BUILDERS"]["Automake"] = Builder(action=Action(BuildAction, "Build using Automake ..."))

   # Check if we need to reconfigure
   if not GetOption("clean"):
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
      if doconf or int(ARGUMENTS.get("reconfigure", "0")) != 0:
         # Only rewrite cfgc when strictly needed
         if doconf:
            with open(cfgc, "w") as f:
               pprint.pprint(opts, stream=f)
         if os.path.isfile(makef):
            os.remove(makef)

   # Could be a autogen.sh script too
   acins = []
   if os.path.isfile(conff+".ac"):
      acins = [conff+".ac"]
   elif os.path.isfile(agenf):
      acins = [agenf]

   if acins:
      # Don't clean generated configure
      env.NoClean(env.Autoconf([conff], acins))

   cins = settings.get("automake-cfgs", [])
   cins.append(conff)
   cins.append(cfgc)
   cout = [makef]

   env.AutomakeConfigure(cout, cins)

   bins = settings.get("automake-srcs", [])
   bins.extend(cout)
   bout = automake.Outputs(name) + [automake.OutputsCachePath(name)]

   out = env.Automake(bout, bins)

   automake.CleanOne(name)

   return out
