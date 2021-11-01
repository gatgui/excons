# MIT License
#
# Copyright (c) 2017 Gaetan Guidet
#
# This file is part of excons.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


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
