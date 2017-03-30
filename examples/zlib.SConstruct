import sys
import re
import excons


env = excons.MakeBaseEnv()

#env.CMakeConfigure("zlib", opts={"AMD64": 1})
env.CMakeConfigure("zlib")

out_incdir = excons.OutputBaseDirectory() + "/include"
out_libdir = excons.OutputBaseDirectory() + "/lib"

zconf_in = ["zconf.h.in"]
zconf_out = env.CMakeGenerated(out_incdir + "/zconf.h", zconf_in)

cmake_in = env.CMakeInputs(dirs=["."], patterns=[re.compile(r"^.*\.(cmakein|h|c|S)$")], exclude=zconf_in)
cmake_out = env.CMakeOutputs(exclude=zconf_out)

target = env.CMake(cmake_out, cmake_in)

env.CMakeClean()
env.Alias("zlib", target)

