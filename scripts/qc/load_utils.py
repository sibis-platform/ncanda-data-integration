import pandas as pd
import redcap as rc

# Taken from http://pycap.readthedocs.io/en/latest/deep.html#dealing-with-large-exports
# and adapted to scope down to forms
def chunked_export(project, form, chunk_size=100, verbose=True, **kwargs):
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
            chunked_response = project.export_records(
                records=record_chunk,
                fields=[project.def_field],
                forms=[form],
                format='df',
                df_kwargs={'low_memory': False}.update(kwargs))
            if response is not None:
                response = pd.concat([response, chunked_response], axis=0)
            else:
                response = chunked_response
    except rc.RedcapError:
        msg = "Chunked export failed for chunk_size={:d}".format(chunk_size)
        raise ValueError(msg)
    else:
        return response


def load_all_forms(api, arm='1'):
    fem = api.export_fem(format='df', arms=arm)
    forms = fem['form'].unique().tolist()
    form_n = len(forms)
    dfs = []
    for i, form in enumerate(forms):
        print(i, form_n, form)
        dfs.append(chunked_export(api, form))
    return pd.concat(dfs, axis=1)


def all_forms_exist_in_redcap(form_names, api):
    meta = api.export_metadata(format='df')
    available_forms = meta['form_name'].unique().tolist()
    for form in form_names:
        if form not in available_forms:
            return False
    return True


def load_form(api, form_name, verbose=True):
    if verbose:
        print(form_name)
    
    try:
        if verbose:
            print("Trying chunked export, 5000 records at a time")
        return chunked_export(api, form_name, 5000)
    except (ValueError, rc.RedcapError, pd.io.common.EmptyDataError):
        pass
    
    # 2. Chunked load with chunk size of 1000
    try:
        if verbose:
            print("Trying chunked export, 1000 records at a time")
        return chunked_export(api, form_name, 1000)
    except (ValueError, rc.RedcapError, pd.io.common.EmptyDataError):
        pass
    
    # 2. Chunked load with default chunk size
    try:
        if verbose:
            print("Trying chunked export, default chunk size (100)")
        return chunked_export(api, form_name, 100)
    except (ValueError, rc.RedcapError, pd.io.common.EmptyDataError):
        pass
    
    # 3. Chunked load with tiny chunk
    try:
        if verbose:
            print("Trying chunked export with tiny chunks (10)")
        return chunked_export(api, form_name, 10)
    except (ValueError, rc.RedcapError, pd.io.common.EmptyDataError):
        print("Giving up")
        return None


def load_form_with_primary_key(api, form_name, verbose=True):
    df = load_form(api, form_name, verbose)
    if df is not None:
        if api.def_field in df.index.names:
            return df
        if api.is_longitudinal():
            return df.set_index([api.def_field, "redcap_event_name"])
        else:
            return df.set_index([api.def_field])