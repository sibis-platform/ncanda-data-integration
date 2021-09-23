#!/bin/bash -l
# Script to programmatically generate All REDCap Forms Dashboards

# Paths for: Dashboard, Save Directory, and Inventory Data
DASHBOARD_FILE="/fs/ncanda-share/beta/chris/ncanda-data-integration/scripts/dashboards/AllRedcapForms.ipynb"
SAVE_DIR="/fs/ncanda-share/log/status_reports/all_redcap_dashboards"
DATA_DIR="/fs/ncanda-share/log/make_all_inventories/inventory_by_site"
TIMESTAMPS_FILE="/fs/ncanda-share/beta/chris/ncanda-data-integration/scripts/reporting/get_all_timestamps.py"

# First, generate Inventory Dates
python3 $TIMESTAMPS_FILE

# Loop through sites
pushd $DATA_DIR > /dev/null
for site in *; do
    mkdir -p $SAVE_DIR/$site
    pushd $site > /dev/null
    # And then through events...
    for event in *; do
      log_file=$SAVE_DIR/$site/$event.log
      papermill --no-progress-bar $DASHBOARD_FILE $SAVE_DIR/$site/$event.ipynb -p site $site -p arm $event --stdout-file "$log_file" --stderr-file "$log_file" > /dev/null
      if egrep -q "Traceback|Exception" "$log_file"; then
          echo "Error occurred while executing $event: See $log_file for details."
      fi
      if [ -f "$SAVE_DIR/$site/$event.ipynb" ]; then
        jupyter nbconvert --log-level ERROR --to html $SAVE_DIR/$site/$event.ipynb --TagRemovePreprocessor.enabled=True --TagRemovePreprocessor.remove_cell_tags remove_cell
      fi
      #echo $SAVE_DIR/$site/$event.ipynb
    done
    popd > /dev/null
done
popd > /dev/null

