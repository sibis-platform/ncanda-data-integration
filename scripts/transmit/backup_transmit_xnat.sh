#!/usr/bin/env bash
script_dir=`dirname $0`

set -e # exit on error
set -x # echo

# PostgreSQL backup for XNAT
${script_dir}/backup_pgsql

# copy to AWS
${script_dir}/transmit_xnat2


