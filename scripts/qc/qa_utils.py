import pandas as pd

def get_items_matching_regex(regex, haystack):
    import re
    return filter(lambda x: re.search(regex, x), haystack)


def get_notnull_entries(row, ignore_always_notna=True):
    # FIXME: should accept columns to ignore as an argument
    try:
        columns = row.columns.tolist()
    except:
        columns = row.index.tolist()
    if ignore_always_notna:
        cols_complete = get_items_matching_regex("complete$", columns)
        cols_ignore = get_items_matching_regex("^visit_ignore", columns)
        cols_missing = get_items_matching_regex("missing(_why(_other)?)?$", 
                                                columns)
        cols_clinical = get_items_matching_regex("^fh_|^ssq_", columns)
        # cols_missing_rationale = get_items_matching_regex("missing_why(_other)?$",
        #                                                   columns)
        cols_checklist = get_items_matching_regex("___", columns)

        non_nan_items = row.drop(cols_complete + cols_ignore + cols_missing +
                                 cols_clinical +  # cols_missing_rationale +
                                 cols_checklist).notnull()
    else:
        non_nan_items = row.notnull()

    return non_nan_items


def count_notnull_entries(row):
    return get_notnull_entries(row).sum(axis=1)


def has_notnull_entries(row):
    return get_notnull_entries(row).any()

