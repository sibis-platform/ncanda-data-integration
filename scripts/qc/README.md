# NCANDA QC scripts

## Notebook reports

Each of the notebooks in the directory is optimized for use with Papermill. This means that initial variables can be specified in a CLI `papermill` call. It then outputs a generated Jupyter notebook file populated with any outputted results, as well as the computational state.

An example for `check_form_groups.ipynb`:

```bash
for form_group in deldisc mri deldisc_stroop youth_report; do 
    for site in ucsd sri upmc ohsu duke; do
        OUTPUT_DIR=/fs/ncanda-share/beta/warehouse/redcap/reports/ntb/
        papermill check_form_groups.ipynb ${OUTPUT_DIR}/check_${site}_${form_group}.ipynb \
            -p output_dir "${OUTPUT_DIR}" \
            -p form_group $form_group \
            -p event 4y_visit_arm_1 \
            -p site $site; 
    done;
done
```

## Inventories

Almost all QC scripts in this directory check three form characteristics: missingness (if available), completion status, and number of non-NA responses. Then, they filter through such an inventory to find problematic cases.

### Create inventory

`make_redcap_inventory.py` has the required functionality.

```bash
for form in visit_date \
            youth_report_1 youth_report_1b youth_report_2 parent_report \
            np_wrat4_word_reading_and_math_computation \
            np_grooved_pegboard np_reyosterrieth_complex_figure_files \
            np_reyosterrieth_complex_figure \
            np_modified_greglygraybiel_test_of_ataxia np_waisiv_coding \
            biological_np biological_mr biological_bp \
            saliva_samples saliva_hormone_survey \
            delayed_discounting_1000 delayed_discounting_100 \
            paced_auditory_serial_addition_test_pasat \
            cnp_summary \
            stroop \
            mr_session_report mri_report mri_stroop \
            brief \
            limesurvey_ssaga_youth limesurvey_ssaga_parent \
            participant_last_use_summary; do 
    echo $form; 
    ./make_redcap_inventory.py -v -e 4y_visit_arm_1 -f $form > /fs/ncanda-share/beta/warehouse/redcap/${form}.csv; 
done
```

### Filter inventory

`filter_inventory.py` defines the issue filters to apply. Given an inventory file, it will output the subset that matches the filter.

```bash
INVENTORY_DIR=/fs/ncanda-share/beta/warehouse/redcap/inventory/
REPORT_DIR=/fs/ncanda-share/beta/warehouse/redcap/reports/
EVENT=4y_visit_arm_1
for filter in probably_not_missing_but_unmarked \
              probably_missing_but_marked_present \
              probably_missing_but_unmarked \
              content_not_marked_complete \
              missing_not_marked_complete \
							has_content_but_marked_missing \
							empty_and_not_complete \
              less_content_than_max; do
   for file in ${INVENTORY_DIR}/${EVENT}/*.csv; do
        mkdir -p "${REPORT_DIR}/${EVENT}/${filter}";
        new_name=$(basename "$file");
        python filter_inventory.py -i "$file" -o "${REPORT_DIR}/${EVENT}/${filter}/${new_name}" $filter;
   done; 
done
```

## Utility scripts

`load_utils.py` and `qa_utils.py` offer re-usable services across QC. (Sometimes, the services overlap; that should, at some point, be fixed.)
