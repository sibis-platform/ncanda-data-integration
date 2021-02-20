import pandas as pd
import redcap as rc


"""
## FIXME

- There's multiple functions doing mostly the same thing, but not quite. I need to go through it.
"""

def get_items_matching_regex(regex, haystack):
    import re
    return list(filter(lambda x: re.search(regex, x), haystack))


def get_notnull_entries(row, ignore_always_notna=True):
    # FIXME: should accept columns to ignore as an argument
    try:
        columns = row.columns.tolist()
    except:
        columns = row.index.tolist()
    if ignore_always_notna:
        cols_complete = get_items_matching_regex("_complete$", columns)
        cols_ignore = get_items_matching_regex("^visit_ignore", columns)
        cols_missing = get_items_matching_regex("_missing(_why(_other)?)?$", 
                                                columns)
        #cols_clinical = get_items_matching_regex("^fh_|^ssq_", columns)
        # cols_missing_rationale = get_items_matching_regex("missing_why(_other)?$",
        #                                                   columns)
        cols_checklist = get_items_matching_regex("___", columns)

        non_nan_items = row.drop(cols_complete + cols_ignore + cols_missing +
                                 #cols_clinical +  # cols_missing_rationale +
                                 cols_checklist).notnull()
    else:
        non_nan_items = row.notnull()

    return non_nan_items


def count_non_nan_rowwise(df, form_name=None, drop_column=None):
    """ A more efficient method of checking non-NaN values """
    # 1. check complete
    if form_name:
        complete_field = form_name + '_complete'
        if drop_columns:
            drop_columns.append(complete_field)
        else:
            drop_columns = [complete_field]
    if drop_columns is None:
        drop_columns = []
    
    # 2. count up NaNs
    return df.drop(drop_columns, axis=1).notnull().sum(axis=1)


def count_notnull_entries(row):
    try:
        return get_notnull_entries(row).sum(axis=1)
    except ValueError:
        return get_notnull_entries(row).sum()


def has_notnull_entries(row):
    return get_notnull_entries(row).any()


def form_has_content(row):
    """ If the form is knowledgeably not empty (e.g. marked missing or 
    marked complete) or it has content in it, it is considered to have content. """
    try:
        columns = row.columns.tolist()
    except:
        columns = row.index.tolist()
    cols_complete = get_items_matching_regex("complete$", columns)
    cols_missing  = get_items_matching_regex("missing$", columns)
    cols_checklist = get_items_matching_regex("___", columns)
    
    if cols_missing:
        missing = (row[cols_missing] == 1).any()
    else:
        missing = None
    
    if cols_complete:
        complete = (row[cols_complete].isin([2])).any()
    else:
        complete = False
    
    non_nan_items = row.drop(cols_complete + cols_missing + cols_checklist).notnull().any()
    
    return missing | complete | non_nan_items


def form_has_content_and_is_not_missing(row):
    """ If the form is *not* marked missing *and* has any non-empty non-meta 
    fields (which count_notnull_entries gets), then it's considered to have content.
    """
    try:
        columns = row.columns.tolist()
    except:
        columns = row.index.tolist()

    cols_missing  = get_items_matching_regex("missing$", columns)
    if cols_missing:
        missing = (row[cols_missing] == 1).any()
    else:
        missing = None
       
    notnull_count = count_notnull_entries(row)
    
    return (not missing) and (notnull_count > 0)

# Taken from http://pycap.readthedocs.io/en/latest/deep.html#dealing-with-large-exports
# and adapted to scope down to forms

# FIXME: Possibly duplicates chunk edges? Need to check it out
def chunked_form_export(project, forms, events=None, include_dag=False, chunk_size=100, fields=[]):
    if isinstance(forms, str):
        forms = [forms]
    if isinstance(events, str):
        events = [events]
        
    def chunks(l, n):
        """Yield successive n-sized chunks from list l"""
        for i in range(0, len(l), n):
            yield l[i:i+n]
    record_list = project.export_records(fields=[project.def_field])
    records = [r[project.def_field] for r in record_list]
    try:
        response = None
        record_count = 0
        for record_chunk in chunks(records, chunk_size):
            record_count = record_count + chunk_size
            #print record_count
            try:
                chunked_response = project.export_records(records=record_chunk,
                                                          fields=[project.def_field] + fields,
                                                          forms=forms,
                                                          events=events,
                                                          export_data_access_groups=include_dag,
                                                          format='df',
                                                          df_kwargs={'low_memory': False})
            except pd.errors.EmptyDataError:
                print("Empty DataFrame error for event {}, fields {}, forms {}"
                        .format(events, fields, forms))
                continue

            if response is not None:
                response = pd.concat([response, chunked_response], axis=0)
            else:
                response = chunked_response
    except rc.RedcapError:
        msg = "Chunked export failed for chunk_size={:d}".format(chunk_size)
        raise ValueError(msg)
    else:
        if project.is_longitudinal:
            response.set_index([project.def_field, 'redcap_event_name'], inplace=True)
        else:
            response.set_index([project.def_field], inplace=True)
            
        return response
