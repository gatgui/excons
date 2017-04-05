import excons
import pprint
import excons.cmake as cmake
from SCons.Script import *


def DummyScanner(node, env, path):
   return []

def ConfigureAction(target, source, env):
   if not cmake.Configure(env["CMAKE_PROJECT"], opts=env["CMAKE_OPTIONS"]):
      if os.path.isfile(env["CMAKE_CONFIG_CACHE"]):
         os.remove(env["CMAKE_CONFIG_CACHE"])
      if os.path.isfile(env["CMAKE_CACHE"]):
         os.remove(env["CMAKE_CACHE"])
   return None

def BuildAction(target, source, env):
   cmake.Build(env["CMAKE_PROJECT"], config=env["CMAKE_CONFIG"], target=env["CMAKE_TARGET"])
   return None

def SetupEnvironment(env, settings):
   name = settings["name"]

   debug = (excons.GetArgument("debug", 0, int) != 0)
   opts = settings.get("cmake-opts", {})
   blddir = cmake.BuildDir(name)
   cmakec = blddir + "/CMakeCache.txt"
   cfgc = cmake.ConfigCachePath(name)
   cexts = [".c", ".h", ".cc", ".hh", ".cpp", ".hpp", ".cxx", ".hxx"]

   # Override default C/C++ file scanner to avoid SCons being too nosy
   env.Prepend(SCANNERS=Scanner(function=DummyScanner, skeys=cexts))
   env["CMAKE_PROJECT"] = name
   env["CMAKE_OPTIONS"] = opts
   env["CMAKE_CONFIG"] = settings.get("cmake-config", ("debug" if debug else "release"))
   env["CMAKE_TARGET"] = settings.get("cmake-target", "install")
   env["CMAKE_CACHE"] = cmakec
   env["CMAKE_CONFIG_CACHE"] = cfgc
   env["BUILDERS"]["CMakeConfigure"] = Builder(action=Action(ConfigureAction, "Configure using CMake ..."))
   env["BUILDERS"]["CMake"] = Builder(action=Action(BuildAction, "Build using CMake ..."))

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
         if os.path.isfile(cmakec):
            os.remove(cmakec)

   cins = settings.get("cmake-cfgs", [])
   cins.append(cfgc)
   cout = [cmakec]

   env.CMakeConfigure(cout, cins)

   bins = settings.get("cmake-srcs", [])
   bins.extend(cout)
   bout = cmake.Outputs(name) + [cmake.OutputsCachePath(name)]

   out = env.CMake(bout, bins)

   # Run clean last
   cmake.CleanOne(name)

   return out
