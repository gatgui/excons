import excons
import excons.cmake as cmake
from SCons.Script import *


def SetupEnvironment(env, settings):
   name = settings["name"]

   debug = (excons.GetArgument("debug", 0, int) != 0)

   env["CMAKE_PROJECT"] = name
   env["CMAKE_CONFIG"] = settings.get("cmake-config", ("debug" if debug else "release"))
   env["CMAKE_TARGET"] = settings.get("cmake-target", "install")

   # Override default C/C++ file scanner to avoid SCons being too nosy
   def DummyScanner(node, env, path):
      return []
   
   cexts = [".c", ".h", ".cc", ".hh", ".cpp", ".hpp", ".cxx", ".hxx"]
   env.Prepend(SCANNERS=Scanner(function=DummyScanner, skeys=cexts))

   def BuildAction(target, source, env):
      print("Calling 'CMake'")
      cmake.Build(env["CMAKE_PROJECT"], config=env["CMAKE_CONFIG"], target=env["CMAKE_TARGET"])
      return None

   env["BUILDERS"]["CMake"] = Builder(action=Action(BuildAction, "Build using CMake ..."))

   srcs = settings.get("cmake-srcs", [])
   srcs.extend(excons.CollectFiles(".", patterns=["CMakeLists.txt"], recursive=True))
   srcs.append(cmake.ConfigCachePath(name))

   outputs = cmake.Outputs(name) + [cmake.OutputsCachePath(name)]

   cmake.Configure(name, opts=settings.get("cmake-opts", {}))

   cmake.Clean()

   return env.CMake(outputs, srcs)

