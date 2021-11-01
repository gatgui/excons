# MIT License
#
# Copyright (c) 2010 Gaetan Guidet
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
import sys
import shutil
import excons

# pylint: disable=bad-indentation,unused-argument,bare-except


def MakeBundle(target=None, source=None, env=None):
  binaryPath = str(target[0])
  
  excons.PrintOnce("MakeBundle for \"%s\"" % binaryPath, tool="openfx")
  
  outPath = excons.joinpath(os.path.dirname(binaryPath), "openfx")
  ofxName = os.path.basename(binaryPath)
  BundleDir = excons.joinpath(outPath, ofxName+".bundle")
  ContentsDir = excons.joinpath(BundleDir, "Contents")
  
  try:
    os.makedirs(ContentsDir)
  except:
    pass
  
  BinaryDir = None
  
  if sys.platform == "darwin":
    plistPath = excons.joinpath(ContentsDir, "Info.plist")
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
      BinaryDir = excons.joinpath(ContentsDir, "MacOS-x86-64")
      
    else:
      BinaryDir = excons.joinpath(ContentsDir, "MacOS")
  
  elif sys.platform in ["win32", "cygwin"]:
    #if pyplat.architecture()[0] == '64bit':
    if env["TARGET_ARCH"] == "x64":
      BinaryDir = excons.joinpath(ContentsDir, "Win64")
      
    else:
      BinaryDir = excons.joinpath(ContentsDir, "Win32")
  
  else:
    #if pyplat.architecture()[0] == '64bit':
    if env["TARGET_ARCH"] == "x64":
      BinaryDir = excons.joinpath(ContentsDir, "Linux-x86-64")
      
    else:
      BinaryDir = excons.joinpath(ContentsDir, "Linux-x86")
  
  try:
    os.mkdir(BinaryDir)
  except:
    pass
  
  shutil.copy(binaryPath, BinaryDir)
  
  # Doesn't seem to work
  env.Clean(target, BundleDir)
