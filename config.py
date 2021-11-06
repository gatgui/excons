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
import excons
import SCons.Script # pylint: disable=import-error


def GetPath(name):
    return excons.joinpath(excons.out_dir, "%s.status" % name)

def HasChanged(name, opts):
    if not os.path.isfile(GetPath(name)):
        return True
    else:
        with io.open(GetPath(name), "r", newline="\n", encoding="UTF-8") as f:
            for line in f.readlines():
                spl = line.strip().split(" ")
                if spl[0] in opts:
                    if str(opts[spl[0]]) != " ".join(spl[1:]):
                        return True
        return False

def Write(name, opts):
    with io.open(GetPath(name), "w", newline="\n", encoding="UTF-8") as f:
        for k, v in opts.iteritems():
            f.write("%s %s\n" % (k, v))
        f.write("\n")

def GenerateFile(outpath, inpath, opts, pattern=None, optgroup=None, converters=None, replacefuncs=None):
    # Converters must convert opts value to strings
    # When no defined, str() is used
    if pattern is not None:
        if optgroup is None:
            raise Exception("Please specify 'optgroup' when using a custom pattern")
        phexp = re.compile(pattern)
        qualifiergrp = None
    else:
        # @VAR_NAME@
        # @VAR_NAME.defined@
        # @VAR_NAME.undefined@
        # @VAR_NAME.equal(otherval)@
        # @VAR_NAME.not_equal(otherval)@
        # @VAR_NAME.match(expr)@
        # @VAR_NAME.not_match(expr)@
        # @VAR_NAME.greater(numeric)@
        # @VAR_NAME.greater_or_equal(numeric)@
        # @VAR_NAME.lesser(numeric)@
        # @VAR_NAME.lesser_or_equal(numeric)@
        phexp = re.compile(r"@([^@.]+)(?:\.([^@.]+))?@")
        qlexp = re.compile(r"defined|undefined|(?:(equal|greater|lesser|greater_or_equal|lesser_or_equal|match|not_equal|not_match)\(([^)]+)\))")
        optgroup = 1
        qualifiergrp = 2

    if converters is None:
        converters = {}

    # value -> string
    def _convertvalue(v):
        vt = type(v)
        if vt in converters:
            return converters[vt](v)
        elif not isinstance(v, excons.anystring):
            return str(v)
        else:
            return v

    with io.open(outpath, "w", newline="\n", encoding="UTF-8") as outf:
        with io.open(inpath, "r", newline="\n", encoding="UTF-8") as inf:
            for line in inf.readlines():
                if replacefuncs is not None:
                    for replacefunc in replacefuncs:
                        line = replacefunc(line, opts)
                remain = line[:]
                outline = ""
                m = phexp.search(remain)
                while m is not None:
                    outline += remain[:m.start()]
                    matched = m.group()
                    remain = remain[m.end():]

                    key = m.group(optgroup)

                    if not key in opts:
                        val = None
                    else:
                        val = opts[key]

                    if qualifiergrp is not None and m.group(qualifiergrp):
                        qm = qlexp.match(m.group(qualifiergrp))
                        if qm is None:
                            excons.WarnOnce("Invalid qualifier for '%s': %s" % (key, m.group(qualifiergrp)))
                        else:
                            qualifier = qm.group(0)
                            if qualifier == "defined":
                                val = (val is not None)
                            elif qualifier == "undefined":
                                val = (val is None)
                            else:
                                qualifier = qm.group(1)
                                qval = qm.group(2)
                                if qualifier == "equal":
                                    val = (_convertvalue(val) == qval)
                                elif qualifier == "not_equal":
                                    val = (_convertvalue(val) != qval)
                                elif qualifier == "greater":
                                    val = (float(val) > float(qval))
                                elif qualifier == "greater_or_equal":
                                    val = (float(val) >= float(qval))
                                elif qualifier == "lesser":
                                    val = (float(val) < float(qval))
                                elif qualifier == "lesser_or_equal":
                                    val = (float(val) <= float(qval))
                                elif qualifier == "match":
                                    val = (re.match(qval, val) is not None)
                                elif qualifier == "not_match":
                                    val = (re.match(qval, val) is None)
                                else:
                                    excons.WarnOnce("Unexpected qualifier for %s: %s" % (key, qualifier))
                                    val = None

                    if val is None:
                        excons.WarnOnce("No value for placeholder '%s' in %s" % (key, inpath))
                    else:
                        matched = matched.replace(m.group(0), _convertvalue(val))

                    outline += matched
                    m = phexp.search(remain)

                outline += remain
                outf.write(outline)

def AddGenerator(env, name, opts, pattern=None, optgroup=None, converters=None, replacefuncs=None):
    if converters is None:
        converters = {}

    def _ActionFunc(target, source, env): # pylint: disable=unused-argument
        GenerateFile(str(target[0]), str(source[0]), opts, pattern=pattern, optgroup=optgroup, converters=converters, replacefuncs=replacefuncs)
        return None

    funcname = "%sGenerateFile" % name

    env["BUILDERS"][funcname] = SCons.Script.Builder(action=SCons.Script.Action(_ActionFunc, "Generating $TARGET ..."))

    func = getattr(env, funcname)

    def _WrapFunc(target, source):
        if HasChanged(name, opts):
            Write(name, opts)
        return func(target, [source] + [GetPath(name)])

    return _WrapFunc
