#!/bin/bash -i
# Script to programmatically run REDCap One Line Per Form Dashboard

# Hard-coded constants -> Dashboard File and save directory
DASHBOARD_FILE='/fs/ncanda-share/beta/chris/ncanda-data-integration/scripts/dashboards/OneLinePerForm.ipynb'
SAVE_DIR="/fs/ncanda-share/log/status_reports/one_line.ipynb"

# Changeable/iterable (future) -> site, arm, form
site="duke"
arm="1y_visit_arm_1"
form="mri_stroop"

# Run Papermill and Jupyter NBConvert to HTML
papermill $DASHBOARD_FILE $SAVE_DIR -p site $site -p arm $arm -p form $form
jupyter nbconvert --to html $SAVE_DIR --TagRemovePreprocessor.remove_cell_tags='{"remove_cell"}'
