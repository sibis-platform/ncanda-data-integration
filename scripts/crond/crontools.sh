#!/bin/bash

##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##

# Run a command, and send its output (stdout and stderr) to a given email address, but only if there is output
if [ "${SIBIS_CONFIG}" == "" ]; then
  export SIBIS_CONFIG="~/.sibis-general-config.yml"
fi 

export SIBIS_ADMIN_EMAIL=`grep email: ${SIBIS_CONFIG} | cut -d ' ' -f2`
export SIBIS_PROJECT_NAME=`grep project_name: ${SIBIS_CONFIG} | cut -d ' ' -f2`
#/fs/ncanda-share
export SIBIS_ANALYSIS_DIR=`grep analysis_dir: ${SIBIS_CONFIG} | cut -d ' ' -f2`
#/fs/storage/laptops
export SIBIS_LAPTOP_DIR="`grep import_dir: ${SIBIS_CONFIG} | cut -d ' ' -f2`/laptops"

catch_output_email()
{
    local mailto=${SIBIS_ADMIN_EMAIL}
    local subject="{SIBIS_PROJECT_NAME}: $1"

    shift 1
    local cmd="$*"

    local tmpfile=$(mktemp)

    eval ${cmd} &> ${tmpfile}
    if [ -s ${tmpfile} ]; then
	
        eval "mailx -r ${SIBIS_ADMIN_EMAIL} -s \"${subject}\" ${mailto} < ${tmpfile}"
        eval "python ${PYTHONPATH}/sibispy/post_issues_to_github.py --title \"${subject}\" --body ${tmpfile}"
    fi

    rm -f ${tmpfile}
}
