# Wine related functions 

import collections 
import json
import os
import subprocess
import shutil
import re

def log(uid, message, **kwargs):
    # Turn message into a ordered dictionary
    log = collections.OrderedDict()
    log.update(experiment_site_id=uid,error=message)
    log.update(kwargs)
    jlog = json.dumps(log)
    log.clear()
    print jlog


def call_shell_program(cmd):
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (out, err) = process.communicate()
    return (process.returncode, out, err)

def sas(sas_script) :
    sas_path = os.path.join( os.path.expanduser("~"), '.wine', 'drive_c', 'Program Files', 'SAS', 'SAS 9.1', 'sas.exe' )
    sas_script_path = 'S:\\%s' % sas_script
    return call_shell_program(['wine',sas_path,'-SYSIN', sas_script_path,'-NOSPLASH','-NOLOGO','-NOTERMINAL'])

def manipula(exedir,bdb_file) :
    manipulaPath = os.path.join(os.path.dirname(os.path.realpath(__file__)),'manipula')
    manipulaExe =  os.path.join(manipulaPath, 'Manipula.exe' )

    for suffix in ['bdb', 'bdm', 'bfi', 'bjk', 'bla', 'bmi', 'bpk', 'bxi']:
        shutil.copy( re.sub( 'bdb$', suffix,bdb_file), exedir )

    for suffix in ['man', 'msu', 'msx']:
        if not os.path.exists(os.path.join(exedir,'crtNSSAGA_v3.%s' % suffix)) :
            shutil.copy( os.path.join(manipulaPath, 'crtNSSAGA_v3.%s' % suffix ), exedir )

    olddir = os.getcwd()
    os.chdir( exedir )
    result =  call_shell_program(['wine', manipulaExe, 'crtNSSAGA_v3.man'])
    os.chdir( olddir )
    return result 
    




