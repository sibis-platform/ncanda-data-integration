#!/bin/bash

##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##

# Run a command, and send its output (stdout and stderr) to a given email address, but only if there is output

#
# Functions
#
catch_output_email()
{
    local mailto=${SIBIS_ADMIN_EMAIL}
    local subject="${SIBIS_PROJECT_NAME}: $1"

    shift 1
    local cmd="$*"

    local tmpfile=$(mktemp)

    eval ${cmd} &> ${tmpfile}
    if [ -s ${tmpfile} ]; then
        cat <<End-Of-Content >> ${tmpfile}

Command:
${cmd}

Environment:
$(set)

$(python --version)
End-Of-Content
    # echo "mailx parameters: -r ${SIBIS_ADMIN_EMAIL} -s ${subject}"
    eval "mailx -r ${SIBIS_ADMIN_EMAIL} -s \"${subject}\" ${mailto} < ${tmpfile}"
	# Issues are now directly posted to github by program - os if their is an issue with github do not post it again as it gets confusing 
        # eval "python ${SIBIS_PYTHON_PATH}/sibispy/post_issues_to_github.py --title \"${subject}\" --body ${tmpfile}"
    fi

    rm -f ${tmpfile}
}

get_sibis_variable()
{
    python3 $SIBIS_PYTHON_PATH/sibispy/session.py get_${1}
}

#
# Check that this is run in the right container
# avoided by sourcing with option force
# 

if [ "$1" != "force" ]; then 
    VALID_CONTAINER_LOG=$(dirname $0)/valid_container_${SCRIPT_LABEL}.log

    if [ ! -e ${VALID_CONTAINER_LOG} ]; then 
	echo "crontools.sh:Error: ${VALID_CONTAINER_LOG} is not defined!"
	exit 1 
    fi

    VALID_CONTAINER=`cat ${VALID_CONTAINER_LOG}`
    if [ "$VALID_CONTAINER" != "${DOCKER_CONTAINER_NAME}" ]; then  
	echo "crontools.sh:Error: Trying to run '${SCRIPT_LABEL}' from container '${DOCKER_CONTAINER_NAME}' but only allowed from container '${VALID_CONTAINER}' !"
	exit 1
    fi 
fi 
    
#
# Set Variables
#
if [ "${SIBIS_CONFIG}" == "" ]; then
  export SIBIS_CONFIG=/fs/storage/share/operations/secrets/.sibis/.sibis-general-config.yml
fi 

export SIBIS_ADMIN_EMAIL=`get_sibis_variable email`
if [ "$SIBIS_ADMIN_EMAIL" == "" ]; then
    echo "ERROR:crontools.sh:Failed to retrieve email!"
    exit 1
fi
    
export SIBIS_PROJECT_NAME=`get_sibis_variable project_name`
export SIBIS_LOG_DIR=`get_sibis_variable log_dir`
export SIBIS_CASES_DIR=`get_sibis_variable cases_dir`
export SIBIS_SUMMARIES_DIR=`get_sibis_variable summaries_dir`
export SIBIS_DVD_DIR=`get_sibis_variable dvd_dir`
export SIBIS_DATADICT_DIR=`get_sibis_variable datadict_dir`

# Still there for front-hourly 
export SIBIS_ANALYSIS_DIR=`grep analysis_dir: ${SIBIS_CONFIG} | cut -d ' ' -f2`
#make sure the following directory is accessible on the cluster !
export SIBIS_IMAGE_SCRIPTS_DIR=${SIBIS_ANALYSIS_DIR}/scripts/image_processing

# catch_output_email blubber echo blubber
