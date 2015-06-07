# Copyright (C) 2015  Gaetan Guidet
#
# This file is part of excons.
#
# excons is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation; either version 2.1 of the License, or (at
# your option) any later version.
#
# excons is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301,
# USA.

import os
import sys
import excons

def PluginPrefix(pluginName):
  if sys.platform == "win32":
    prefix = "unity/%s/Plugins/x86" % pluginName
    if excons.Build64():
      prefix += "_64"
    
    return prefix
  
  elif sys.platform == "darwin":
    return "unity/%s/Plugins/%s.bundle/Contents/MacOS" % (pluginName, pluginName)
  
  else:
    return "unity/%s/Plugins" % pluginName

def PluginExt():
  if sys.platform == "win32":
    return ".dll"
  
  elif sys.platform == "darwin":
    return ""
  
  else:
    return ".so"

def PluginSetup(env):
  if sys.platform == "darwin":
    # Note: linked libraries must have their install_name set to @rpath/libXXX.dylib
    env.Append(LINKFLAGS=" -Wl,-rpath,@loader_path/../Libraries")

def PluginPost(pluginName):
  
  def _UnityPostBuild(*args, **kwargs):
    if sys.platform == "darwin":
      
      macos_dir = os.path.join(excons.OutputBaseDirectory(), PluginPrefix(pluginName))
      contents_dir = os.path.dirname(macos_dir)
      
      plist_path = os.path.join(contents_dir, "Info.plist")
      
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
""" % pluginName
        
        f = open(plist_path, "w")
        f.write(plist_content)
        f.close()
  
  return _UnityPostBuild


def AsPlugin(target, libs=[]):
  if not isinstance(target, dict):
    return
  
  if not "name" in target:
    return
  
  name = target["name"]
  
  post = target.get("post", [])
  post.append(PluginPost(name))
  
  custom = target.get("custom", [])
  custom.append(PluginSetup)
  
  install = target.get("install", {})
  if libs:
    libs_dir = os.path.join(excons.OutputBaseDirectory(), PluginPrefix(name))
    if sys.platform == "darwin":
      libs_dir = os.path.join(os.path.dirname(libs_dir), "Libraries")
    install[libs_dir] = libs
  
  target["ext"] = PluginExt()
  target["prefix"] = PluginPrefix(name)
  target["custom"] = custom
  target["install"] = install
  target["post"] = post



