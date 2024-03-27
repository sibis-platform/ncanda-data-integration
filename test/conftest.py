from __future__ import absolute_import, print_function

import os, yaml

def pytest_addoption(parser):
  parser.addoption("--general-config-file", dest="config_file", action="store",
                   default=os.path.join(*"/fs/storage/share/operations/secrets/.sibis/.sibis-general-config.yml".split('/')),
                   help="Path to SIBIS General Configuration File")
  parser.addoption("--cluster-job", action="store_true", default=False, help="Running as cluster job")

def pytest_generate_tests(metafunc):
  option_value = metafunc.config.option.config_file
  print("opt_val: >{0}<".format(option_value))
  general_cfg = yaml.safe_load(option_value)
  if 'config' in metafunc.fixturenames and general_cfg is not None:
    metafunc.parametrize("config", [general_cfg])
  if 'config_file' in metafunc.fixturenames and general_cfg is not None:
    metafunc.parametrize("config_file", [option_value])

  option_value = metafunc.config.option.cluster_job
  if 'cluster_job' in metafunc.fixturenames and option_value is not None:
    metafunc.parametrize("cluster_job", [option_value])