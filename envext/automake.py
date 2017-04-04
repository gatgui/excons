import excons
import excons.automake as automake
from SCons.Script import *


def SetupEnvironment(env, settings):
   name = settings["name"]

   debug = (excons.GetArgument("debug", 0, int) != 0)

   env["AUTOMAKE_PROJECT"] = name
   env["AUTOMAKE_TARGET"] = settings.get("automakeg-target", "install")

   # Override default C/C++ file scanner to avoid SCons being too nosy
   def DummyScanner(node, env, path):
      return []
   
   cexts = [".c", ".h", ".cc", ".hh", ".cpp", ".hpp", ".cxx", ".hxx"]
   env.Prepend(SCANNERS=Scanner(function=DummyScanner, skeys=cexts))

   def BuildAction(target, source, env):
      automake.Build(env["AUTOMAKE_PROJECT"], target=env["AUTOMAKE_TARGET"])
      return None

   env["BUILDERS"]["Automake"] = Builder(action=Action(BuildAction, "Build using Automake ..."))

   srcs = settings.get("automake-srcs", [])
   srcs.append(automake.ConfigCachePath(name))

   outputs = automake.Outputs(name) + [automake.OutputsCachePath(name)]

   automake.Configure(name, opts=settings.get("automake-opts", {}))

   automake.Clean()

   return env.Automake(outputs, srcs)

