#!/bin/bash -l
# Script to programmatically run REDCap One Line Per Form Dashboard

# Paths for: Dashboard, Save Directory, and Inventory Data
DASHBOARD_FILE="/fs/ncanda-share/beta/chris/ncanda-data-integration/scripts/dashboards/OneLinePerForm.ipynb"
SAVE_DIR="/fs/ncanda-share/log/status_reports/one_line_dashboards/"
DATA_DIR="/fs/ncanda-share/log/make_all_inventories/inventory_by_site"

# Loop through sites...
pushd $DATA_DIR > /dev/null
for site in *; do
    mkdir -p $SAVE_DIR/$site
    pushd $site > /dev/null
    # And then through events..
    for event in *; do
        mkdir -p $SAVE_DIR/$site/$event
        # echo $SAVE_DIR/$site/$event
        pushd $event > /dev/null
        # And then for each form...
        for form in *; do
            if [[ -f $form ]]; then
                # Generate Notebook + HTML
                form_name=${form%.csv}
                log_file=$SAVE_DIR/$site/$event/$form_name.log
                papermill --log-level ERROR --no-progress-bar $DASHBOARD_FILE $SAVE_DIR/$site/$event/$form_name.ipynb -p site $site -p arm $event -p form $form_name --stdout-file $log_file --stderr-file $log_file
                if egrep -q "Traceback|Exception" "$log_file"; then
                    echo "Error occurred while executing $site/$form: See $log_file for details."
                fi
                jupyter nbconvert --log-level ERROR --to html $SAVE_DIR$site/$event/$form_name.ipynb --TagRemovePreprocessor.enabled=True --TagRemovePreprocessor.remove_cell_tags remove_cell
            fi
        done
        popd > /dev/null
    done
    popd > /dev/null
done
popd
