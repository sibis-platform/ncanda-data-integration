#!/bin/bash -l
# Script to programmatically execute all of the SVN Reports using Bash!

# Directories for: SVN script, directory for dashboards, and directory for csvs
DASHBOARD_FILE=${1:-/sibis-software/ncanda-data-integration/scripts/dashboards/SVNReports.ipynb}
SCRIPT_DIR=${2:-/fs/ncanda-share/beta/chris/ncanda-data-integration/scripts/reporting}
SAVE_DIR=${3:-/fs/ncanda-share/log/status_reports/sla_dashboards}
STATUS_DIR=${4:-/fs/ncanda-share/log/status_reports/sla_files}
sites=()

# First, execute python script
pushd "$SCRIPT_DIR" > /dev/null
LC_ALL=C python3 svn_report.py
popd > /dev/null

# Next, head into the directory with all statuses and grab an array of all sites 
pushd "$STATUS_DIR" > /dev/null
for file in *; do
    site=${file%.csv}
    sites+=($site)
done
popd > /dev/null

# For each site -- generate papermill notebook, then convert to HTML
for site in ${sites[@]}; do
    log_file=$SAVE_DIR/$site.log
    papermill --log-level ERROR --no-progress-bar $DASHBOARD_FILE $SAVE_DIR/$site.ipynb -p site $site --stdout-file $log_file --stderr-file $log_file &> /dev/null
    if egrep -q "Traceback|Exception" "$log_file"; then
        echo "Error occurred while executing $site: See $log_file for details."
    fi
    jupyter nbconvert --log-level ERROR --to html $SAVE_DIR/$site.ipynb --TagRemovePreprocessor.enabled=True --TagRemovePreprocessor.remove_cell_tags remove_cell
done
