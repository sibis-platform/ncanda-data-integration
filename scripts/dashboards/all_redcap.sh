#!/bin/bash -i
# Script to programmatically generate All REDCap Forms Dashboards

# Paths for: Dashboard, Save Directory, and Inventory Data
DASHBOARD_FILE="/fs/ncanda-share/beta/chris/ncanda-data-integration/scripts/dashboards/AllRedcapForms.ipynb"
SAVE_DIR="/fs/ncanda-share/log/status_reports/all_redcap_dashboards"
DATA_DIR="/fs/ncanda-share/log/make_all_inventories/inventory_by_site"
TIMESTAMPS_FILE="/fs/ncanda-share/beta/chris/ncanda-data-integration/scripts/reporting/get_all_timestamps.py"

# First, generate Inventory Dates
python3 $TIMESTAMPS_FILE

# Loop through sites
pushd $DATA_DIR
for site in *; do
    mkdir $SAVE_DIR/$site
    pushd $site
    # And then through events...
    for event in *; do
	papermill $DASHBOARD_FILE $SAVE_DIR/$site/$event.ipynb -p site $site -p arm $event
	jupyter nbconvert --to html $SAVE_DIR/$site/$event.ipynb --TagRemovePreprocessor.remove_cell_tags='{"remove_cell"}'
	#echo $SAVE_DIR/$site/$event.ipynb
    done
    popd
done
popd

