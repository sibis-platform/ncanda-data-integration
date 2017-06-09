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
    local server="$3"

    shift 2
    local cmd="$*"

    local tmpfile=$(mktemp)

    eval ${cmd} &> ${tmpfile}
    if [ -s ${tmpfile} ]; then
	
        eval "mailx -r admin -s \"${subject}\" ${server} ${mailto} < ${tmpfile}"
        eval "python ${PYTHONPATH}/sibispy/post_issues_to_github.py --title \"${subject}\" --body ${tmpfile}"
    fi

    rm -f ${tmpfile}
}
