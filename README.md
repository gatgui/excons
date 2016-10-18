
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
* **libs**: List of libraries to link.
* **rpaths**: Default library lookup path. *(osx/linux)*
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
  * **no-console**: Don't popup windows prompt when running resulting program. *(windows)*
  * **stacksize**: Setup stack size.
2. dynamicmodule
  * **ext**: Dynamic module extension. *(dynamicmodule)*
3. sharedlib
  * **no_import_lib**: Don't generate an import library. *(windows)*
  * **win_separate_dll_and_lib**: Output binary in 'bin' subfolder and import library in 'lib' subfolder rather than everything in 'lib'. *(windows)*
  * **version**: Shared library version. *(osx/linux)*
  * **install_name**: Library name as seen from dependents. *(osx, sharedlib)*
  * **soname**: Library name as seen from dependents. *(linux, sharedlib)*

## Command line flags
* **mscver**: Microsoft windows compiler version *(windows only)*
```
scons mscver=9.0 ...
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
* **use-c++11**: Use C++11 if compiler supports it. Defaults to 0. *(osx only)*
```
scons use-c++11=1 ...
```
* **use-stdc++**: Use standard C++ library rather than libc++. Defaults to 0. *(osx only)*
