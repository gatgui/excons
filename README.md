
# excons: EXtension for sCONS

## Basic *SConstruct* structure when using **excons**

```python
# import excons module
import excons
# import other common modules
import glob

# create base build environment
env = excons.MakeBaseEnv()

targets = [
  {"name": "test",
   "type": "program",
   "srcs": glob.glob("src/*.cpp")
  }
]

excons.DeclareTargets(env, targets)
```

## Target dictionary keys
* **name**: The name of the binary to compile. *(required)*
* **alias**: Target alias to use instead of the true name on the build command line.
* **prefix**: Output directory prefix.
* **bldprefix**: Build directory prefix.
* **type**: Output type. One of 'staticlib', 'sharedlib', 'dynamicmodule', 'program' or 'testprograms'. *(required)*
* **defs**: List of compiler defines.
* **incdirs**: List of header files directories.
* **libdirs**: List of library files directories.
* **srcs**: List of source files to compile. *(required)*
* **deps**: List of target dependencies.
* **cppflags**: Preprocessor flags.
* **ccflags**: Compiler C/C++ flags.
* **cxxflags**: Compiler C++ flags.
* **linkflags**: Linker flags.
* **libs**: List of libraries to link (static or shared).
* **staticlibs**: List of static libraries to link.
* **rpaths**: Default library lookup path. *(osx/linux)*
* **symvis**: Symbols visibility ('default' or 'hidden'). *(osx/linux)*
* **custom**: List of functions to customize build environment. Such function should take as single argument the current environment object.
* **post**: List of function to run as post-build steps. (SCons Post Action format)
* **install**: Install additional files.
```
  ...
  "install": {"scripts": glob.glob("scripts/*.py")},
  ...
```

### Type specific keys
1. program/testprograms
  * **console**: Show/hide windows prompt when running resulting program. *(windows)*
  * **stacksize**: Setup stack size in bytes.
2. dynamicmodule
  * **ext**: Dynamic module extension. *(dynamicmodule)*
3. sharedlib
  * **no_import_lib**: Don't generate an import library. *(windows)*
  * **win_separate_dll_and_lib**: Output binary in 'bin' subfolder and import library in 'lib' subfolder rather than everything in 'lib'. *(windows)*
  * **version**: Shared library version. *(osx/linux)*
  * **install_name**: Library name as seen from dependents. *(osx, sharedlib)*
  * **soname**: Library name as seen from dependents. *(linux, sharedlib)*

## Command line flags
libdir-arch=none|subdir|suffix : Modify behaviour of the library folder name use by default
                                   for 'with-<name>=<prefix>' flag    [none]
                                   When set to 'subdir', use '<prefix>/lib/x86' or '<prefix>/lib/x64'
                                   When set to 'suffix', use '<prefix>/lib' or '<prefix>/lib64'

* **no-cache**: Disable excons command line flag caching.
```
scons no-cache=1 ...
```
* **show-cmds**: Show compiler commands.
```
scons show-cmds=1 ...
```
* **stack-size**: Set default stack size in bytes ('k' and 'm' can be used for kilo and mega bytes)
```
scons stacksize=4m ...
```
* **strip**: Strip dead code by default. *(linux/osx only)*
```
scons strip=1 ...
```
* **libdir-arch**: Setup default library subdirectory used in dependency requirements (with-xxx=)
```
scons libdir-arch=none ...   => '/lib')
scons libdir-arch=subdir ... => '/lib/x86' or '/lib/x64'
scons libdir-arch=suffix ... => '/lib' or '/lib64'
```
* **mscver**: Microsoft windows compiler version *(windows only)*
```
scons mscver=9.0 ...
```
* **no-console**: Build programs for windows subsystem by default. *(windows only)*
```
scons no-console=1 ...
```
* **warnings**: One if 'none', 'std' or 'all'. Defaults to 'all'.
```
scons warnings=std ...
```
* **warnings-as-errors**: Treat warnings as errors. Defaults to 0.
```
scons warnings-as-errors=1 ...
```
* **debug**: Debug build. Defaults to 0.
```
scons debug=1 ...
```
* **with-debug-info**: Include debug information in release buikd. Defaults to 0.
```
scons debug=0 with-debug-info=1 ...
```
* **use-c++11**: Use C++11 if compiler supports it. Defaults to 0. *(linux/osx only)*
```
scons use-c++11=1 ...
```
* **use-stdc++**: Use standard C++ library rather than libc++. Defaults to 0. *(linux/osx only)*
