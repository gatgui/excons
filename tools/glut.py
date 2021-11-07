# MIT License
#
# Copyright (c) 2009 Gaetan Guidet
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
import excons


def GetOptionsString():
    return """GLUT OPTIONS
  with-glut=<path>     : GLUT root directory.        []
  with-glut-inc=<path> : GLUT headers directory.     [<root>/include]
  with-glut-lib=<path> : GLUT libraries directory.   [<root>/lib]
  glut-name=<str>      : Override GLUT library name. []
                         (default library name is glut32/glut64 on windows, glut on linux)
  glut-prefix=<str>    : GLUT library name prefix.   ['']
                         (ignored when glut-name is set)
  glut-suffix=<str>    : GLUT library name suffix.   ['']
                         (ignored when glut-name is set)
  glut-static=0|1      : Use GLUT static library.    [1]

  On OSX, library related options are ignored as the GLUT framework is used"""

def Require(env):
    glutinc, glutlib = excons.GetDirs("glut")

    if glutinc:
        env.Append(CPPPATH=[glutinc])

    if glutlib:
        env.Append(LIBPATH=[glutlib])

    static = (excons.GetArgument("glut-static", 0, int) != 0)

    libname = excons.GetArgument("glut-name", "")
    if not libname:
        libprefix = excons.GetArgument("glut-prefix", "")
        libsuffix = excons.GetArgument("glut-suffix", "")
        if sys.platform == "win32":
            libname = ("glut64" if excons.Build64() else "glut32") + libsuffix
        else:
            libname = "%sglut%s" % (libprefix, libsuffix)

    if sys.platform == "win32":
        env.Append(CPPDEFINES=["GLUT_NO_LIB_PRAGMA"])
        env.Append(LIBS=[libname])

    elif sys.platform == "darwin":
        env.Append(LINKFLAGS=" -framework GLUT")

    else:
        excons.Link(env, libname, static=static, force=True, silent=True)

    excons.AddHelpOptions(glut=GetOptionsString())

