# MIT License
#
# Copyright (c) 2021 Gaetan Guidet
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
import sys
import subprocess
import excons


_VarsCache = {}

# Note: GCC>=5 on linux breaks stdc++ library ABI
#       the "_GLIBCXX_USE_CXX11_ABI" can be set to revert it to the old ABI
#       -> "-D_GLIBCXX_USE_CXX11_ABI=0"

def GetToolsetName(toolsetver):
    toolstr = "^(dev|gcc-)?toolset-%s$" % toolsetver
    toolexp = re.compile(toolstr)

    if toolsetver and sys.platform.startswith("linux"):
        p = subprocess.Popen("scl list-collections", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out, _ = p.communicate()
        if p.returncode != 0:
            p = subprocess.Popen("scl -l", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            out, _ = p.communicate()
        if p.returncode == 0:
            for toolset in out.split("\n"):
                if toolexp.match(toolset):
                    return toolset
        else:
            return ""

def GetDevtoolsetEnv(toolsetver, merge=False):
    if toolsetver and sys.platform.startswith("linux"):
        toolsetname = GetToolsetName(toolsetver)
        if not toolsetname:
            raise Exception("Failed to get toolsetname")

        ret = _VarsCache.get(toolsetname, None)
        if ret is None:
            ret = {}
            p = subprocess.Popen("scl enable %s env" % toolsetname, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            out, _ = p.communicate()
            if p.returncode == 0:
                out_dcd = out.decode("ascii").split("\n") if sys.version_info.major > 2 else out.split("\n")
                lines = [x.strip() for x in out_dcd if toolsetname in x]
                matches = [re.match("^([^=]+)=(.*)$", x) for x in lines if x is not None]
                ret = dict([(m.group(1), [x for x in m.group(2).split(os.pathsep) if toolsetname in x]) for m in matches])
            else:
                print("Invalid devtoolset: %s (%s)" % (toolsetname, toolsetver))
                sys.exit(1)
            _VarsCache[toolsetname] = ret
        if ret:
            env = {}
            for k, v in excons.iteritems(ret):
                if merge:
                    _v = os.environ.get(k, None)
                    if _v is not None:
                        vals = [x.strip() for x in _v.split(os.pathsep) if len(x) > 0]
                        v.extend(vals)
                env[k] = os.pathsep.join(v)
            return env
    return {}

def GetGCCFullVer(toolsetver):
    _env = None
    _vars = GetDevtoolsetEnv(toolsetver, merge=True)
    if _vars:
        _env = os.environ.copy()
        _env.update(_vars)
    p = subprocess.Popen(["gcc", "-dumpversion"], env=_env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out, _ = p.communicate()
    if p.returncode == 0:
        return out.decode("ascii").strip() if sys.version_info.major > 2 else out.strip()
    else:
        return None
