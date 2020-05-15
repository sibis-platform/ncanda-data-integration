#!/bin/bash -i
# 1. Iterate through per-year inventory locations and create corresponding locations
INVENTORY_DIR=${1:-/fs/ncanda-share/log/make_all_inventories/inventory/}
REPORT_DIR=${2:-/fs/ncanda-share/log/make_all_inventories/report/}
INVENTORY_BY_SITE_DIR=$INVENTORY_DIR/../inventory_by_site
REPORT_BY_SITE_DIR=$REPORT_DIR/../report_by_site

SCRIPT=`realpath $0`
SCRIPTDIR=`dirname $SCRIPT`

pushd $INVENTORY_DIR
for event_dir in *; do
  for filter in empty_marked_present \
                content_marked_missing \
                less_content_than_max \
                empty_unmarked \
                content_unmarked \
                content_not_complete \
                missing_not_complete; do
    for file in ${INVENTORY_DIR}/${event_dir}/*.csv; do
       mkdir -p "${REPORT_DIR}/${event_dir}/${filter}";
       new_name=$(basename "$file");
       python $SCRIPTDIR/filter_inventory.py -i "$file" \
         -o "${REPORT_DIR}/${event_dir}/${filter}/${new_name}" \
         $filter
    done; 
    # mkdir -p ${REPORT_DIR}/${event_dir}
    # python $SCRIPTDIR/filter_inventory.py -i ${INVENTORY_DIR}/${event_dir}/*.csv -o ${REPORT_DIR}/${event_dir}/${filter}.csv $filter
  done
done
popd

pushd $INVENTORY_BY_SITE_DIR
for site in sri duke ohsu upmc ucsd; do
   pushd $INVENTORY_BY_SITE_DIR/$site
   for event_dir in *; do
     for filter in empty_marked_present \
                   content_marked_missing \
                   less_content_than_max \
                   empty_unmarked \
                   content_unmarked \
                   content_not_complete \
                   missing_not_complete; do
       mkdir -p ${REPORT_BY_SITE_DIR}/${site}/${event_dir}
       # Create a filter file that concatenates all forms
       python $SCRIPTDIR/filter_inventory.py -i ${event_dir}/*.csv \
         -o ${REPORT_BY_SITE_DIR}/${site}/${event_dir}/${filter}.csv \
         $filter
     done
   done
   popd
done
popd

pushd $INVENTORY_BY_SITE_DIR
for site in sri duke ohsu upmc ucsd; do 
   pushd $INVENTORY_BY_SITE_DIR/$site
   for event_dir in *; do
     # Only do this for full-year visits
     [[ "$event_dir" =~ ".+month.+" ]] && continue
     mkdir $event_dir/form_groups{,_problem}
     for group in deldisc youth_report np mri deldisc_stroop; do 
        # Filter out only problematic cases first (-x) 
        $SCRIPTDIR/check_form_groups.py -x --form-group $group \
           -o $event_dir/form_groups_problem/${group}.csv \
           $INVENTORY_BY_SITE_DIR/$site/$event_dir/ 

        # Create full classification
        $SCRIPTDIR/check_form_groups.py --form-group $group \
           -o $event_dir/form_groups/${group}.csv \
           $INVENTORY_BY_SITE_DIR/$site/$event_dir/ 
     done
   done
   popd
done
popd

