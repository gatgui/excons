# Copyright (C) 2009  Gaetan Guidet
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
from SCons.Script import *
from string import Template

def Require(e):
  rb_conf = Template("ruby -e \"require 'rbconfig'; print Config::CONFIG['$flag']\"")
  e.Append(CPPPATH=[os.popen(rb_conf.substitute(flag='archdir')).read()])
  e.Append(LIBPATH=[os.popen(rb_conf.substitute(flag='libdir')).read()])
  e.Append(LIBS=[os.popen(rb_conf.substitute(flag='RUBY_SO_NAME')).read()])

def ModulePrefix():
  return "lib/ruby/"

def ModuleExtension():
  rb_conf = Template("ruby -e \"require 'rbconfig'; print Config::CONFIG['$flag']\"")
  return ('.' + os.popen(rb_conf.substitute(flag='DLEXT')).read())
