# Copyright (C) 2010  Gaetan Guidet
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

from SCons.Script import *

import os
import sys
import shutil
#import platform as pyplat

def MakeBundle(target=None, source=None, env=None):
  binaryPath = str(target[0])
  print("openfx.MakeBundle for \"%s\"" % binaryPath)
  print(os.getcwd())
  outPath = os.path.join(os.path.dirname(binaryPath), "openfx")
  ofxName = os.path.basename(binaryPath)
  BundleDir = os.path.join(outPath, ofxName+".bundle")
  ContentsDir = os.path.join(BundleDir, "Contents")
  try:
    os.makedirs(ContentsDir)
  except:
    pass
  BinaryDir = None
  if sys.platform == "darwin":
    plistPath = os.path.join(ContentsDir, "Info.plist")
    plist = """
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
<key>CFBundleVersion</key>
<string>1.0</string>
</dict>
</plist>
""" % ofxName
    f = open(plistPath, "w")
    f.write(plist)
    f.close()
    if env["TARGET_ARCH"] == "x64" and "OFX_NEW_PACKAGE" in env and env["OFX_NEW_PACKAGE"]:
      BinaryDir = os.path.join(ContentsDir, "MacOS-x86-64")
    else:
      BinaryDir = os.path.join(ContentsDir, "MacOS")
  elif sys.platform in ["win32", "cygwin"]:
    #if pyplat.architecture()[0] == '64bit':
    if env["TARGET_ARCH"] == "x64":
      BinaryDir = os.path.join(ContentsDir, "Win64")
    else:
      BinaryDir = os.path.join(ContentsDir, "Win32")
  else:
    #if pyplat.architecture()[0] == '64bit':
    if env["TARGET_ARCH"] == "x64":
      BinaryDir = os.path.join(ContentsDir, "Linux-x86-64")
    else:
      BinaryDir = os.path.join(ContentsDir, "Linux-x86")
  try:
    os.mkdir(BinaryDir)
  except:
    pass
  shutil.copy(binaryPath, BinaryDir)
  # Doesn't seem to work
  env.Clean(target, BundleDir)

