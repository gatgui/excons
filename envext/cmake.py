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
import io
import excons
import pprint
import excons.cmake as cmake
import SCons.Script # pylint: disable=import-error

# pylint: disable=unused-argument


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
            except Exception as e: # pylint: disable=broad-except
                excons.WarnOnce("[cmake] Couldn't create directory: %s (%s)" % (blddir, e))
                return None

        doconf = True
        if os.path.isfile(cfgc):
            doconf = False
            with io.open(cfgc, "r", encoding="UTF-8", newline="\n") as f:
                try:
                    d = eval(f.read()) # pylint: disable=eval-used
                    for k, v in excons.iteritems(d):
                        if not k in opts or opts[k] != v:
                            doconf = True
                            break
                    if not doconf:
                        for k, v in excons.iteritems(opts):
                            if not k in d:
                                doconf = True
                                break
                except Exception as e: # pylint: disable=broad-except
                    excons.WarnOnce("[cmake] Failed to read configuration file: %s (%s)" % (cfgc, e))
                    doconf = True
        if doconf or int(SCons.Script.ARGUMENTS.get("reconfigure", "0")) != 0:
            # Only rewrite cfgc when strictly needed
            if doconf:
                with io.open(cfgc, "w", encoding="UTF-8", newline="\n") as f:
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
    expected_outputs = [(x if os.path.isabs(x) else (excons.OutputBaseDirectory() + "/" + x)) for x in expected_outputs]
    actual_outputs = cmake.Outputs(name)
    bout = list(set(actual_outputs).union(set(expected_outputs))) + [cmake.OutputsCachePath(name)]

    out = env.CMake(bout, bins)

    # Run clean last
    cmake.CleanOne(name)

    return out
