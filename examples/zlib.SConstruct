import sys
import re
import excons
import excons.cmake as cmake


env = excons.MakeBaseEnv()

prjs = [
   {  "name": "zlib",
      "type": "cmake",
      "cmake-opts": {"AMD64": excons.GetArgument("AMD64", 0, int)},
      "cmake-cfgs": excons.CollectFiles(".", patterns=["CMakeLists.txt", "*.cmakein"], recursive=True),
      "cmake-srcs": excons.CollectFiles(".", patterns=["*.c", "*.S"], recursive=True)
   }
]

excons.AddHelpOptions(zlib="""CMAKE ZLIB OPTIONS
  AMD64=0|1 : Enable building amd64 assembly implementation""")

excons.DeclareTargets(env, prjs)
