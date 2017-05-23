#!/bin/bash

##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##

# Run a command, and send its output (stdout and stderr) to a given email address, but only if there is output
export SIBIS_ADMIN_EMAIL=`grep email: ~/.sibis-general-config.yml | cut -d ' ' -f2`

catch_output_email()
{
    local mailto="$1"
    local subject="$2"

    shift 2
    local cmd="$*"

    local tmpfile=$(mktemp)

    eval ${cmd} &> ${tmpfile}
    if [ -s ${tmpfile} ]; then
	
        eval "mailx -r ${SIBIS_ADMIN_EMAIL} -s \"${subject}\" ${mailto} < ${tmpfile}"
        eval "python ${PYTHONPATH}/sibisBeta/post_issues_to_github.py --org sibis-platform --repo ncanda-operations --title \"${subject}\" --body ${tmpfile}"
    fi

    rm -f ${tmpfile}
}
