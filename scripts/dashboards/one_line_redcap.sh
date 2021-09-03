#!/bin/bash -i
# Script to programmatically run REDCap One Line Per Form Dashboard

# Paths for: Dashboard, Save Directory, and Inventory Data
DASHBOARD_FILE="/fs/ncanda-share/beta/chris/ncanda-data-integration/scripts/dashboards/OneLinePerForm.ipynb"
SAVE_DIR="/fs/ncanda-share/log/status_reports/one_line_dashboards/"
DATA_DIR="/fs/ncanda-share/log/make_all_inventories/inventory_by_site"

# Loop through sites...
pushd $DATA_DIR
for site in *; do
    mkdir $SAVE_DIR$site
    pushd $site
    # And then through events..
    for event in *; do
	mkdir $SAVE_DIR$site/$event
	echo $SAVE_DIR$site/$event
	pushd $event
	# And then for each form...
	for form in *; do
	    if [[ -f $form ]]; then
		# Generate Notebook + HTML
		form_name=${form%.csv}
		papermill $DASHBOARD_FILE $SAVE_DIR$site/$event/$form_name.ipynb -p site $site -p arm $event -p form $form_name
		jupyter nbconvert --to html $SAVE_DIR$site/$event/$form_name.ipynb --TagRemovePreprocessor.remove_cell_tags='{"remove_cell"}'
	    fi
	done
	popd
    done
    popd
done
popd
