# MIT License
#
# Copyright (c) 2015 Gaetan Guidet
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
import excons


def PluginPrefix(pluginname, package=None):
    if package is None:
        package = pluginname

    if sys.platform != "darwin":
        prefix = "unity/%s/Plugins/x86" % package
        if excons.Build64():
            prefix += "_64"

        return prefix

    else:
        return "unity/%s/Plugins/%s.bundle/Contents/MacOS" % (package, pluginname)

def PluginExt():
    if sys.platform == "win32":
        return ".dll"

    elif sys.platform == "darwin":
        return ""

    else:
        return ".so"

def PluginPost(pluginname, package=None):

    def _UnityPostBuild(*args, **kwargs): # pylint: disable=unused-argument
        if sys.platform == "darwin":

            macos_dir = excons.joinpath(excons.OutputBaseDirectory(), PluginPrefix(pluginname, package=package))
            contents_dir = os.path.dirname(macos_dir)

            plist_path = excons.joinpath(contents_dir, "Info.plist")

            if not os.path.isfile(plist_path):
                plist_content = """
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>CFBundleDevelopmentRegion</key>
	<string>English</string>
	<key>CFBundleExecutable</key>
	<string>%s</string>
	<key>CFBundleInfoDictionaryVersion</key>
	<string>6.0</string>
	<key>CFBundlePackageType</key>
	<string>BNDL</string>
	<key>CFBundleSignature</key>
	<string>????</string>
	<key>CFBundleVersion</key>
	<string>1.0</string>
	<key>CSResourcesFileMapped</key>
	<string>yes</string>
</dict>
</plist>
""" % pluginname

                with io.open(plist_path, "w", encoding="UTF-8", newline="\n") as f:
                    f.write(plist_content)

    return _UnityPostBuild


def Plugin(target, libs=None, package=None):
    if libs is None:
        libs = []

    if not isinstance(target, dict):
        return

    if not "name" in target:
        return

    name = target["name"]

    prefix = PluginPrefix(name, package=package)

    post = target.get("post", [])
    post.append(PluginPost(name, package=package))

    install = target.get("install", {})
    if libs:
        libs_dir = excons.joinpath(excons.OutputBaseDirectory(), prefix)
        if sys.platform == "darwin":
            libs_dir = excons.joinpath(os.path.dirname(libs_dir), "Libraries")
        install[libs_dir] = libs

    target["ext"] = PluginExt()
    target["prefix"] = prefix
    target["install"] = install
    target["post"] = post
    # For linux, rpath defaults to $ORIGIN
    if sys.platform == "darwin":
        target["rpath"] = "../Libraries"



