#!/bin/bash

##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##

# Set the SIBIS environment variable to the data integration repo
export SIBIS=${HOME}/ncanda-data-integration

# Run a command, and send its output (stdout and stderr) to a given email address, but only if there is output
catch_output_email()
{
    local mailto="$1"
    local subject="$2"

    shift 2
    local cmd="$*"

    local tmpfile=$(mktemp)

    eval ${cmd} &> ${tmpfile}
    if [ -s ${tmpfile} ]; then
        eval "mailx -r crond@ncanda.sri.com -s \"${subject}\" ${mailto} < ${tmpfile}"
        eval "python ${SIBIS}/scripts/crond/post_github_issues.py --org sibis-platform --repo ncanda-operations --title \"${subject}\" --body ${tmpfile}"
    fi

    rm -f ${tmpfile}
}
