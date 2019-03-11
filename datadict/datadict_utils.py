import pandas as pd

def load_datadict(filepath, trim_index=True, trim_all=False):
    df = pd.read_csv(filepath, index_col=0, dtype=object)
    if trim_index:
        df.index = df.index.to_series().str.strip()
    if trim_all:
        df = df.applymap(lambda x: x.strip() if type(x) is str else x)
    return df

def insert_rows_at(main_df, index_name, inserted_df, insert_before=False):
    # Not checking if index exists because that will be apparent from error
    # NOTE: This will not work with duplicate indices
    pre_df = main_df.loc[:index_name]
    post_df = main_df.loc[index_name:]
    # Both pre_ and post_ contain the value at index_name, so one needs to
    # drop it
    if not insert_before:
        pre_df = pre_df.drop(index_name)
    else:
        post_df = post_df.drop(index_name)
    return pd.concat([pre_df, inserted_df, post_df],
                     axis=0)
