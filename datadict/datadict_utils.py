import pandas as pd
from six import string_types


def load_datadict(filepath, trim_index=True, trim_all=False, force_names=False):
    # TODO: Verify headers / set column names, if necessary
    headers = ["Variable / Field Name",
               "Form Name",
               "Section Header",
               "Field Type",
               "Field Label",
               "Choices, Calculations, OR Slider Labels",
               "Field Note",
               "Text Validation Type OR Show Slider Number",
               "Text Validation Min",
               "Text Validation Max",
               "Identifier?",
               "Branching Logic (Show field only if...)",
               "Required Field?",
               "Custom Alignment",
               "Question Number (surveys only)",
               "Matrix Group Name",
               "Matrix Ranking?",
               "Field Annotation"]
    index_name = headers[0]
    headers = headers[1:]
    df = pd.read_csv(filepath, index_col=0, dtype=object, engine="python")

    try:
        assert df.index.name == index_name, F"Index must be named {index_name}"
        assert df.columns.isin(headers).all(), "Nonstandard headers!"
    except AssertionError:
        if force_names:
            df.index.name = index_name
            df.columns = headers
        else:
            raise

    if trim_index:
        df.index = df.index.to_series().str.strip()
    if trim_all:
        df = df.applymap(lambda x: x.strip() if isinstance(x, string_types) else x)
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
                     sort=False,
                     axis=0)
