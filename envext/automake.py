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
import sys
import pprint
import subprocess
import excons
import excons.automake as automake
import SCons.Script # pylint: disable=import-error

# pylint: disable=unused-argument


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
    # debug = (excons.GetArgument("debug", 0, int) != 0)
    opts = settings.get("automake-opts", {})
    agenf = excons.abspath("./autogen.sh")
    conff = excons.abspath("./configure")
    blddir = automake.BuildDir(name)
    makef = blddir + "/Makefile"
    cfgc = automake.ConfigCachePath(name)
    cexts = [".c", ".h", ".cc", ".hh", ".cpp", ".hpp", ".cxx", ".hxx"]

    # Override default C/C++ file scanner to avoid SCons being too nosy
    env.Prepend(SCANNERS=SCons.Script.Scanner(function=DummyScanner, skeys=cexts))
    env["AUTOMAKE_PROJECT"] = name
    env["AUTOMAKE_TOPDIR"] = excons.abspath(".")
    env["AUTOMAKE_OPTIONS"] = opts
    env["AUTOMAKE_TARGET"] = settings.get("automake-target", "install")
    env["AUTOMAKE_CONFIGURE"] = conff
    env["AUTOMAKE_AUTOGEN"] = agenf
    env["AUTOMAKE_MAKEFILE"] = makef
    env["AUTOMAKE_CONFIG_CACHE"] = cfgc
    env["BUILDERS"]["Autoconf"] = SCons.Script.Builder(action=SCons.Script.Action(AutoconfAction, "Running autoconf ..."))
    env["BUILDERS"]["AutomakeConfigure"] = SCons.Script.Builder(action=SCons.Script.Action(ConfigureAction, "Configure using Automake ..."))
    env["BUILDERS"]["Automake"] = SCons.Script.Builder(action=SCons.Script.Action(BuildAction, "Build using Automake ..."))

    # Check if we need to reconfigure
    if not SCons.Script.GetOption("clean"):
        if not os.path.isdir(blddir):
            try:
                os.makedirs(blddir)
            except Exception as e: # pylint: disable=broad-except
                print("[automake] Couldn't create directory: %s (%s)" % (blddir, e))
                return None

        doconf = True
        if os.path.isfile(cfgc):
            doconf = False
            with io.open(cfgc, "r", encoding="UTF-8", newline="\n") as f: 
                try:
                    d = eval(f.read()) # pylint: disable=eval-used
                    for k, v in d.iteritems():
                        if not k in opts or opts[k] != v:
                            doconf = True
                            break
                    if not doconf:
                        for k, v in opts.iteritems():
                            if not k in d:
                                doconf = True
                                break
                except Exception as e: # pylint: disable=broad-except
                    print("[automake] Couldn't read configuration file '%s' (%s)" % (cfgc, e))
                    doconf = True
        if doconf or int(SCons.Script.ARGUMENTS.get("reconfigure", "0")) != 0:
            # Only rewrite cfgc when strictly needed
            if doconf:
                with io.open(cfgc, "w", encoding="UTF-8", newline="\n") as f:
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
    cins.extend(automake.AdditionalConfigureDependencies(name))
    cout = [makef]

    env.AutomakeConfigure(cout, cins)

    bins = settings.get("automake-srcs", [])
    bins.extend(cout)

    expected_outputs = settings.get("automake-outputs", [])
    expected_outputs = map(lambda x: (x if os.path.isabs(x) else (excons.OutputBaseDirectory() + "/" + x)), expected_outputs)
    actual_outputs = automake.Outputs(name)
    bout = list(set(actual_outputs).union(set(expected_outputs))) + [automake.OutputsCachePath(name)]

    out = env.Automake(bout, bins)

    automake.CleanOne(name)

    return out
