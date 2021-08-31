'''
Quickly subset Redcap inventories.

Note: Filter functions taken from: https://github.com/sibis-platform/ncanda-data-integration/blob/master/scripts/qc/filter_inventory.py
'''

# Reports

## 1. Reports that indicate mistakes (site check required)

# empty_marked_present
def empty_marked_present(inventory):
    # -> Site should investigate why the form was marked "not missing"
    return ((inventory['non_nan_count'] == 0)
            & (inventory['missing'] == 0)
            & (inventory['exclude'] != 1)
            & (inventory['form_name'] != 'biological_mr'))  # false positives

# content_marked_missing
def content_marked_missing(inventory):
    # -> Missingness likely applied by mistake, should be switched to present
    return ((inventory['missing'] == 1) 
            & (inventory['non_nan_count'] > 0)
            & (inventory['exclude'] != 1))

## 2. Reports that contain possible omissions (site check recommended)

def less_content_than_max(inventory):
    # -> Site should ensure that no content was omitted
    # (only makes sense on some forms)
    return ((inventory['non_nan_count'] > 0) &
            (inventory['non_nan_count'] < inventory['non_nan_count'].max()))

def empty_unmarked(inventory):
    # -> Site should double-check that these cases are actually absent, and
    #    mark missingness where appropriate
    # (potentially better handled in check_form_groups)
    # (hits "grey" circles, but not just them)
    return ((inventory['non_nan_count'] == 0)
            & inventory['missing'].isnull()
            & (inventory['exclude'] != 1))


## 3. Reports that indicate undermarking, and can be auto-marked (site consent requested)
### 3a. Undermarking of non-missingness

def content_unmarked(inventory):
    # -> Site should confirm that hits can be automatically marked "not missing"
    return (inventory['non_nan_count'] > 0) & (inventory['missing'].isnull())

### 3b. Undermarking of completion
def content_not_complete(inventory):
    # -> Site should confirm that hits can be automatically marked "complete"
    return ((inventory['non_nan_count'] > 0)
            & (inventory['complete'] < 2)
            # Computed forms that will be marked Complete once other forms are
            & (~inventory['form_name'].isin(['clinical', 'brief']))
            )

def missing_not_complete(inventory):
    # -> Site should confirm that hits can be automatically marked "complete"
    return (inventory['missing'] == 1) & (inventory['complete'] < 2)

### 4. Excluded forms with content on them
def excluded_with_content(inventory):
    # -> Site should either unmark exclusion, or have the content deleted
    return ((inventory['exclude'] == 1)
            & (inventory['non_nan_count'] > 0)
            & (~inventory['form_name'].isin(['visit_date', 'clinical'])))

# Reports -- end
