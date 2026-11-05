#!/usr/bin/env bash
script_dir=`dirname $0`

set -e # exit on error
set -x # echo

${script_dir}/backup_mariadb

# REDCap file uploads to AWS
${script_dir}/backup_redcap_files


