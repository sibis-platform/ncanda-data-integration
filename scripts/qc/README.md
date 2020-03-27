# NCANDA QC scripts

## Inventories

Almost all QC scripts in this directory check three form characteristics: missingness (if available), completion status, and number of non-NA responses. Then, they filter through such an inventory to find problematic cases.

### Create inventory

Use `make_all_inventories.py` to create inventory files, both complete and split by Data Access Group. It will take care of any directory creation and, if you don't provide limiting forms and events, will make inventory for all forms and events available:

```bash
./make_all_inventories.py -v --output-dir /tmp/inventories/all --split-by-dag-to /tmp/inventories/by_site
```

The plan is to make inventories nightly in `/fs/ncanda-share/log/make_all_inventories`.


(Under the hood, `make_all_inventories.py` is using the machinery in `make_redcap_inventory.py`, which can also be called via CLI if needed.)

### Filter inventory

`filter_inventory.py` defines the issue filters to apply. Given an inventory file, it will output the subset that matches the filter.

```bash
INVENTORY_DIR=/fs/ncanda-share/log/make_all_inventories/inventory/
REPORT_DIR=/fs/ncanda-share/log/make_all_inventories/reports/
EVENT=5y_visit_arm_1
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

The inventories can be consumed by any scripts. This is advantageous in many ways; for example, you can keep whatever filter/check you're running separated by DAG if you so desire.

### Checking form groups

Some forms should co-occur. `check_form_groups.py` can be run on previously made inventories and classify each form as `PRESENT`, `MISSING`, `EXCLUDE` or `EMPTY`. The theory is that if one form within the group is present, then all of the other forms should be accounted for in some way, and - most importantly - none of them should be empty.

You get a full classification of forms by default. If you supply `-x` / `--failures-only`, you'll receive only files with the problematic cases.

```bash
INVENTORY_ROOTDIR=/fs/ncanda-share/log/make_all_inventories/
EVENT=5y_visit_arm_1
for site in sri duke ohsu upmc ucsd; do 
   for group in deldisc youth_report mri deldisc_stroop; do 
      ./check_form_groups.py -x --form-group $group \
         -o $INVENTORY_ROOTDIR/report_by_site/$site/$EVENT/form_groups/${site}_${group}.csv \
         $INVENTORY_ROOTDIR/inventory_by_site/$site/$EVENT/ 
   done
done
```

## Notebook reports

Each of the notebooks in the directory is optimized for use with Papermill. This means that initial variables can be specified in a CLI `papermill` call. It then outputs a generated Jupyter notebook file populated with any outputted results, as well as the computational state.

An example for `check_unuploaded_files.ipynb`:

```bash
OUTPUT_DIR=/fs/ncanda-share/log/make_all_inventories/file_check
cd /sibis-software/ncanda-data-integration/scripts/qc
papermill scripts/qc/check_unuploaded_files.ipynb ${OUTPUT_DIR}/check_unuploaded_files.ipynb \
   -p output_dir "${OUTPUT_DIR}"
```

## Utility scripts

`load_utils.py` and `qa_utils.py` offer re-usable services across QC. (Sometimes, the services overlap; that should, at some point, be fixed.)
