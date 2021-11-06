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


import os
import re
import io
import sys
import glob
import shutil
import subprocess
import excons
import excons.devtoolset
import SCons.Script # pylint: disable=import-error


InstallExp = re.compile(r"^--\s+(Installing|Up-to-date):\s+([^\s].*)$")
CmdSep = ("&&" if sys.platform == "win32" else ";")
ConfigExtraDeps = {}

# Avoid listing microsoft runtime dlls:
#  - concrtXXX.dll
#  - msvcpXXX.dll
#  - vcruntimeXXX.dll
_VC_ignores_by_ext = {"dll": set(["concrt", "msvcp", "msvcr", "vcruntime"])}

def VC_Filter(path):
    bn = os.path.basename(path)
    key = os.path.splitext(bn)[-1][1:].lower()
    prefices = _VC_ignores_by_ext.get(key, [])

    for prefix in prefices:
        if bn.startswith(prefix):
            return False

    return True

def AddConfigureDependencies(name, deps):
    lst = ConfigExtraDeps.get(name, [])
    lst.extend(deps)
    ConfigExtraDeps[name] = lst

def AdditionalConfigureDependencies(name):
    return ConfigExtraDeps.get(name, [])

def BuildDir(name):
    return excons.BuildBaseDirectory() + "/" + name

def ConfigCachePath(name):
    return os.path.abspath(excons.out_dir + "/%s.cmake.config" % name)

def OutputsCachePath(name):
    return os.path.abspath(excons.out_dir + "/%s.cmake.outputs" % name)

def Outputs(name):
    lst = []
    cof = OutputsCachePath(name)
    if os.path.isfile(cof):
        cofd = os.path.dirname(cof)
        with io.open(cof, "r", newline="\n", encoding="UTF-8") as f:
            _lines = [x.strip() for x in f.readlines()]
            lines = [x for x in _lines if len(x) > 0 and os.path.isfile(os.path.join(cofd, x))]
            lst = [excons.out_dir + "/" + x for x in lines if VC_Filter(x)]
    return lst

def Configure(name, topdir=None, opts=None, min_mscver=None, flags=None):
    if SCons.Script.GetOption("clean"):
        return True

    if opts is None:
        opts = {}

    if topdir is None:
        topdir = os.path.abspath(".")

    bld = BuildDir(name)
    relpath = os.path.relpath(topdir, bld)

    cmd = "cd \"%s\" %s %s " % (bld, CmdSep, excons.GetArgument("with-cmake", "cmake"))
    env = None
    if sys.platform == "win32":
        try:
            mscver = float(excons.GetArgument("mscver", "10.0"))
            if min_mscver is not None and mscver < min_mscver:
                mscver = min_mscver
            if mscver == 9.0:
                cmd += "-G \"Visual Studio 9 2008 Win64\" "
            elif mscver == 10.0:
                cmd += "-G \"Visual Studio 10 2010 Win64\" "
            elif mscver == 11.0:
                cmd += "-G \"Visual Studio 11 2012 Win64\" "
            elif mscver == 12.0:
                cmd += "-G \"Visual Studio 12 2013 Win64\" "
            elif mscver == 14.0:
                cmd += "-G \"Visual Studio 14 2015 Win64\" "
            elif mscver == 14.1:
                cmd += "-G \"Visual Studio 15 2017 Win64\" "
            elif mscver == 14.2:
                cmd += "-G \"Visual Studio 16 2019 Win64\" "
            else:
                excons.Print("Unsupported visual studio version %s" % mscver, tool="cmake")
                return False
        except: # pylint: disable=bare-except
            return False
    else:
        _env = excons.devtoolset.GetDevtoolsetEnv(excons.GetArgument("devtoolset", ""), merge=True)
        if _env:
            env = os.environ.copy()
            env.update(_env)
    if flags:
        if not cmd.endswith(" "):
            cmd += " "
        cmd += flags
        if not flags.endswith(" "):
            cmd += " "
    for k, v in opts.iteritems():
        cmd += "-D%s=%s " % (k, ("\"%s\"" % v if isinstance(v, excons.anystring) else v))
    cmd += "-DCMAKE_INSTALL_PREFIX=\"%s\" "  % excons.OutputBaseDirectory()
    if sys.platform != "win32":
        cmd += "-DCMAKE_SKIP_BUILD_RPATH=0 "
        cmd += "-DCMAKE_BUILD_WITH_INSTALL_RPATH=0 "
        cmd += "-DCMAKE_INSTALL_RPATH_USE_LINK_PATH=0 "
        if sys.platform == "darwin":
            cmd += "-DCMAKE_MACOSX_RPATH=1 "
    cmd += relpath

    excons.Print("Run Command: %s" % cmd, tool="cmake")
    p = subprocess.Popen(cmd, env=env, shell=True)
    p.communicate()

    return (p.returncode == 0)

def ParseOutputsInLines(lines, outfiles):
    for line in lines:
        excons.Print(line, tool="cmake")
        m = InstallExp.match(line.strip())
        if m is not None:
            f = m.group(2)
            if not os.path.isdir(f):
                outfiles.add(f)

def Build(name, config=None, target=None):
    if SCons.Script.GetOption("clean"):
        return True

    ccf = ConfigCachePath(name)
    cof = OutputsCachePath(name)

    if not os.path.isfile(ccf):
        return False

    outfiles = set()

    if config is None:
        config = excons.mode_dir

    if target is None:
        target = "install"

    cmd = "cd \"%s\" %s %s --build . --config %s --target %s" % (BuildDir(name), CmdSep, excons.GetArgument("with-cmake", "cmake"), config, target)
    env = None

    extraargs = ""
    njobs = SCons.Script.GetOption("num_jobs")
    if njobs > 1:
        if sys.platform == "win32":
            extraargs += " /m:%d" % njobs
        else:
            extraargs += " -j %d" % njobs
    if excons.GetArgument("show-cmds", 0, int):
        if sys.platform == "win32":
            extraargs += " /v:n" # normal verbosity
        else:
            extraargs += " V=1"
    else:
        if sys.platform == "win32":
            extraargs += " /v:m" # minimal verbosity
    if extraargs and (sys.platform != "win32" or float(excons.GetArgument("mscver", "10.0")) >= 10.0):
        cmd += " --" + extraargs

    if sys.platform != "win32":
        _env = excons.devtoolset.GetDevtoolsetEnv(excons.GetArgument("devtoolset", ""), merge=True)
        if _env:
            env = os.environ.copy()
            env.update(_env)

    excons.Print("Run Command: %s" % cmd, tool="cmake")
    p = subprocess.Popen(cmd, shell=True, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    buf = ""
    while p.poll() is None:
        r = p.stdout.readline(512)
        buf += r
        lines = buf.split("\n")
        if len(lines) > 1:
            buf = lines[-1]
            ParseOutputsInLines(lines[:-1], outfiles)
    ParseOutputsInLines(buf.split("\n"), outfiles)
    excons.Print(buf, tool="cmake")

    # Write list of outputed files
    if p.returncode == 0:
        with io.open(cof, "w", newline="\n", encoding="UTF-8") as f:
            lst = sorted(filter(VC_Filter, outfiles))
            f.write("\n".join(excons.NormalizedRelativePaths(lst, excons.out_dir)))
        return True
    else:
        if os.path.isfile(cof):
            os.remove(cof)
        return False

def CleanOne(name):
    if not SCons.Script.GetOption("clean"):
        return

    # Remove output files
    for path in Outputs(name):
        path = excons.out_dir + "/" + path
        if os.path.isfile(path):
            os.remove(path)
            excons.Print("Removed: '%s'" % excons.NormalizedRelativePath(path, excons.out_dir), tool="cmake")

    # Remove build temporary files
    buildDir = BuildDir(name)
    if os.path.isdir(buildDir):
        shutil.rmtree(buildDir)
        excons.Print("Removed: '%s'" % excons.NormalizedRelativePath(buildDir, excons.out_dir), tool="cmake")

    path = ConfigCachePath(name)
    if os.path.isfile(path):
        os.remove(path)
        excons.Print("Removed: '%s'" % excons.NormalizedRelativePath(path, excons.out_dir), tool="cmake")

    path = OutputsCachePath(name)
    if os.path.isfile(path):
        os.remove(path)
        excons.Print("Removed: '%s'" % excons.NormalizedRelativePath(path, excons.out_dir), tool="cmake")

def Clean():
    if not SCons.Script.GetOption("clean"):
        return

    allnames = [".".join(os.path.basename(x).split(".")[:-2]) for x in glob.glob(excons.out_dir + "/*.cmake.outputs")]

    if len(SCons.Script.COMMAND_LINE_TARGETS) == 0:
        names = allnames[:]
    else:
        names = SCons.Script.COMMAND_LINE_TARGETS

    for name in names:
        CleanOne(name)

def ExternalLibRequire(configOpts, name, libnameFunc=None, definesFunc=None, extraEnvFunc=None, varPrefix=None):
    rv = excons.ExternalLibRequire(name, libnameFunc=libnameFunc, definesFunc=definesFunc, extraEnvFunc=extraEnvFunc)

    req = rv["require"]

    if req is not None:
        defines = ("" if definesFunc is None else definesFunc(rv["static"]))
        if defines:
            extraflags = " ".join(map(lambda x: "-D%s" % x, defines))
            configOpts["CMAKE_CPP_FLAGS"] = "%s %s" % (configOpts.get("CMAKE_CPP_FLAGS", ""), extraflags)

        if varPrefix is None:
            varPrefix = name.upper() + "_"
            excons.PrintOnce("Use CMake variable prefix '%s' for external dependency '%s'" % (varPrefix, name))

        configOpts["%sINCLUDE_DIR" % varPrefix] = rv["incdir"]
        configOpts["%sLIBRARY" % varPrefix] = rv["libpath"]
        # sometimes LIBRARY is used, sometines LIBRARY_RELEASE / LIBRARY_DEBUG...
        configOpts["%sLIBRARY_DEBUG" % varPrefix] = rv["libpath"]
        configOpts["%sLIBRARY_RELEASE" % varPrefix] = rv["libpath"]

    return rv
