from __future__ import absolute_import, print_function
import os, pytest, subprocess


__script_dir = os.path.dirname(os.path.abspath(__file__))
CRONTOOLS_PATH=os.path.realpath(os.path.join(__script_dir, '../../../scripts/crond/crontools.sh'))

def _get_exported_var(script_file, env_var, env=None):
    script_dir = os.path.dirname(script_file)
    script_name = os.path.basename(script_file)
    # subcmd = "cd {0} && source {1} && echo -n ${{{2}}}".format(script_dir, script_name, env_var)
    subcmd = "source {1} && echo -n ${{{2}}}".format(script_dir, script_file, env_var)
    # subcmd = ["echo", "$(pwd)"]
    cmd = ["bash", "-c", subcmd]
    err = None
    out = None
    try:
      print("ECHO: {0}".format(subprocess.check_output(["/bin/bash", "-c", "echo -n $(pwd)"], env=env, cwd=script_dir, shell=False)))
      out = subprocess.check_output(cmd, env=env, cwd=script_dir, shell=False)
      print("OUT: {0}".format(out))
    except subprocess.CalledProcessError as e:
      print("ERROR: {0}".format(e.output))
      err = e.output
    return (out, err)

@pytest.fixture
def get_exported_var():
  return _get_exported_var

@pytest.fixture
def boilerplate_env(config_file):
  cur_env = os.environ
  return cur_env.update({
    "SIBIS_PYTHON_PATH": os.environ.get("SIBIS_PYTHON_PATH") if "SIBIS_PYTHON_PATH" in os.environ else os.path.realpath(os.path.join(__script_dir, '../../../../')),
    "SIBIS_CONFIG": config_file,
    "DOCKER_CONTAINER_NAME": "jim_pipeline-back_1",
    "SCRIPT_LABEL": "back-nightly"
  })

VALUE_VARS=[
  "SIBIS_ADMIN_EMAIL",
  "SIBIS_PROJECT_NAME"
]

FILE_VARS=[
  "SIBIS_CONFIG"
]

DIR_VARS=[
  ("SIBIS_LOG_DIR", False),
  ("SIBIS_CASES_DIR", False),
  ("SIBIS_SUMMARIES_DIR", False),
  ("SIBIS_DVD_DIR", False),
  ("SIBIS_DATADICT_DIR", False),
  ("SIBIS_ANALYSIS_DIR", False),
  ("SIBIS_IMAGE_SCRIPTS_DIR", True)
]

# def test_script_runs(config_file):
#   env = 

@pytest.mark.parametrize("env_var", VALUE_VARS)
def test_environment_var_value_exists(get_exported_var, env_var, boilerplate_env):
  out, err =  get_exported_var(CRONTOOLS_PATH, env_var, boilerplate_env)
  assert err is None, "expected no error, got: `{0}`".format(err)
  assert out not in [None, ''], "expected env var `{0}` to have a value, got: `{1}`".format(env_var, out)


@pytest.mark.parametrize("file_var", FILE_VARS)
def test_environment_var_file_exists(get_exported_var, file_var, boilerplate_env):
  out, err = get_exported_var(CRONTOOLS_PATH, file_var, boilerplate_env)
  assert err is None, "expected no error, got: `{0}`".format(err)
  print("FILES: {0} = {1}".format(file_var, out))
  assert out not in [None, ''], "expected env var `{0}` to have a value, got: `{1}`".format(file_var, out)
  assert os.path.exists(out) and os.path.isfile(out), "expected file `{0}` to exist, not found.".format(out)
  

@pytest.mark.parametrize("dir_var,cluster_only", DIR_VARS)
def test_environment_var_dir_exists(get_exported_var, dir_var, cluster_only, cluster_job, boilerplate_env):
  if not cluster_job and cluster_only:
    return
  out, err = get_exported_var(CRONTOOLS_PATH, dir_var, boilerplate_env)
  assert err is None, "expected no error, got: `{0}`".format(err)
  print("DIRS: {0} = {1}".format(dir_var, out))
  assert out not in [None, ''], "expected env var `{0}` to have a value, got: `{1}`".format(dir_var, out)
  assert os.path.exists(out) and os.path.isdir(out), "expected dir `{0}` to exist, not found.".format(out)