#!/bin/bash -i
# Script to programmatically execute all of the SVN Reports using Bash!

# Directories for: SVN script, directory for dashboards, and directory for csvs
DASHBOARDS_DIR=/fs/ncanda-share/beta/chris/ncanda-data-integration/scripts/dashboards
SVN_FILE='SVN Reports.ipynb'
SCRIPT_DIR=/fs/ncanda-share/beta/chris/ncanda-data-integration/scripts/reporting
SAVE_DIR=/fs/ncanda-share/log/status_reports/sla_dashboards
STATUS_DIR=/fs/ncanda-share/log/status_reports/sla_files
sites=()

# First, execute python script
pushd "$SCRIPT_DIR"
LC_ALL=C python3 svn_report.py
popd

# Next, head into the directory with all statuses and grab an array of all sites 
pushd "$STATUS_DIR"
for file in *; do
    site=${file%.csv}
    sites+=($site)
done
popd

# For each site -- generate papermill notebook, then convert to HTML
for site in ${sites[@]}; do
    papermill '/fs/ncanda-share/beta/chris/ncanda-data-integration/scripts/dashboards/SVN Reports.ipynb' $SAVE_DIR/$site.ipynb -p site $site
    jupyter nbconvert --to html $SAVE_DIR/$site.ipynb --TagRemovePreprocessor.remove_cell_tags='{"remove_cell"}'
done
