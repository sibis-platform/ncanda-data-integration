#!/bin/bash

##
##  Copyright 2015 SRI International
##  License: https://ncanda.sri.com/software-license.txt
##
##  $Revision: 2114 $
##  $LastChangedBy: dj0330 $
##  $LastChangedDate: 2015-08-07 09:42:11 -0700 (Fri, 07 Aug 2015) $
##

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
        eval "python ${HOME}/scripts/crond/post_github_issues.py --org ncanda --repo ncanda-datacore --title \"${subject}\" --body ${tmpfile}"
    fi

    rm -f ${tmpfile}
}

