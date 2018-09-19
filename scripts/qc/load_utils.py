import pandas as pd
import redcap as rc

# Taken from http://pycap.readthedocs.io/en/latest/deep.html#dealing-with-large-exports
# and adapted to scope down to forms
def chunked_export(project, form, chunk_size=100, verbose=True, **kwargs):
    def chunks(l, n):
        """Yield successive n-sized chunks from list l"""
        for i in xrange(0, len(l), n):
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
        print i, form_n, form
        dfs.append(chunked_export(api, form))
    return pd.concat(dfs, axis=1)
