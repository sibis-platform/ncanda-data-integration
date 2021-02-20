"""
Quickly subset Redcap inventories.
"""

import argparse
import pandas as pd
import sys
# import sibispy

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


# Reports -- end


def get_filter_results(inventorized_data, filter_function, verbose=False):
    """
    Apply pd.Index-returning function to data and return it filtered.
    """
    try:
        index = filter_function(inventorized_data)
    except KeyError as e:
        if verbose:
            print("Error in {}:".format(filter_function.__name__), str(e))
        return None
    else:
        return inventorized_data.loc[index]


def parse_args(filter_choices, input_args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="Verbose operation",
                        action="store_true")
    parser.add_argument("-p", "--post-to-github",
                        help="Post all issues to GitHub instead of stdout.",
                        action="store_true")
    parser.add_argument("-i", "--input",
                        help="Inventory file to operate on",
                        nargs='+',
                        required=True)
    parser.add_argument('-o', '--output',
                        help="File to save filtered inventory to",
                        default=sys.stdout)
    # Reference to `choices` in `help` courtesy of https://stackoverflow.com/a/20335589
    parser.add_argument('filter', metavar='FILTER', choices=filter_choices,
            help="Filter function to apply, one of following: {%(choices)s}")
    args = parser.parse_args(input_args)
    return args


if __name__ == '__main__':
    # TODO: There should be some way to auto-generate this - maybe embed the
    # filters in a file, import it, then get the names of all callables?
    FILTER_LIST = [
        empty_marked_present,
        content_marked_missing,
        less_content_than_max,
        empty_unmarked,
        content_unmarked,
        content_not_complete,
        missing_not_complete,
    ]
    FILTERS = {x.__name__: x for x in FILTER_LIST}

    args = parse_args(FILTERS.keys())

    # TODO: Should explicitly assume + read in columns?
    all_out = []
    for filename in args.input:
        data = pd.read_csv(filename)
        filter_function = FILTERS[args.filter]
        result = get_filter_results(data, filter_function, verbose=args.verbose)
        if result is None:
            if args.verbose:
                print("Filter {} failed on file {}; skipping".format(args.filter, filename))
        elif not result.empty:
            all_out.append(result)

            if args.verbose:
                if args.output == sys.stdout:
                    output_display_name = "stdout"
                else:
                    output_display_name = args.output

                print("Filter {} used on {} => {}".format(args.filter, filename, output_display_name))
        else:
            if args.verbose:
                print("Filter {} used on {} => no matches, skipping.".format(args.filter, filename))
        
    if len(all_out) > 0:
        (pd.concat(all_out, sort=False)
         .to_csv(args.output, index=False, float_format="%.0f"))
    sys.exit(0)
