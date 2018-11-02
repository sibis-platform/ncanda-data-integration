from __future__ import absolute_import

import pandas as pd
import pytest
from datadict.datadict_utils import *

@pytest.fixture
def datadict_df():
    df = pd.DataFrame.from_dict({
        "field_name": ["test1", "test2", "test3"],
        "form_name": ["form1", "form1", "form2"],
    })
    return df.set_index("field_name")

@pytest.fixture
def single_insert_df():
    df = pd.DataFrame.from_dict({
        "field_name": ["test4"],
        "form_name":  ["form1"]
    })
    return df.set_index("field_name")

def test_insert_rows_at(datadict_df, single_insert_df):
    #result = insert_rows_at(datadict_df(), "test1", single_insert_df(), insert_before=True)
    result = insert_rows_at(datadict_df, "test1", single_insert_df)
    assert result.index.tolist() == ["test4", "test1", "test2", "test3"]
