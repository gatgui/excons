import os
import re
import sys
import subprocess

_VarsCache = {}

def GetDevtoolsetEnv(toolsetver, merge=False):
  if toolsetver and sys.platform.startswith("linux"):
    toolsetname = "devtoolset-%s" % toolsetver
    ret = _VarsCache.get(toolsetname, None)
    if ret is None:
      ret = {}
      p = subprocess.Popen("scl enable %s env" % toolsetname, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
      out, _ = p.communicate()
      if p.returncode == 0:
        lines = filter(lambda y: toolsetname in y, map(lambda x: x.strip(), out.split("\n")))
        matches = filter(lambda y: y is not None, map(lambda x: re.match("^([^=]+)=(.*)$", x), lines))
        ret = dict([(m.group(1), filter(lambda w: toolsetname in w, m.group(2).split(os.pathsep))) for m in matches])
      else:
        print("Invalid devtoolset: %s (%s)" % (toolsetname, toolsetver))
        sys.exit(1)
      _VarsCache[toolsetname] = ret
    if ret:
      env = {}
      for k, v in ret.iteritems():
        if merge:
          _v = os.environ.get(k, None)
          if _v is not None:
            vals = filter(lambda y: len(y) > 0, map(lambda x: x.strip(), _v.split(os.pathsep)))
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
    return out.strip()
  else:
    return None
