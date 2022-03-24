#!/usr/env/bin python
"""
Check the generated mNCANDA data dictionary for correctness.

Raises an AssertionError for the first violation it finds. (Should possibly be rewritten to be a pytest.)

Sample invocation:

    python check_mncanda.py datadict output/mncanda_datadict.csv

TODO: Write data checks. (Possibly in conjunction with datadict? Might not make sense without it.)
"""
import argparse
import pandas as pd
from typing import List, NoReturn
from pathlib import Path


def main():
    args = _args()

    df = pd.read_csv(args.source, dtype=str)
    if args.action == "data":
        check_data(df)
    elif args.action == "datadict":
        check_datadict(df)


def _args(input_args: List[str] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["data", "datadict"])
    p.add_argument("source", type=Path)


def check_data(data: pd.DataFrame) -> NoReturn:
    raise NotImplementedError("Haven't written data checks yet.")


def check_datadict(dd: pd.DataFrame) -> NoReturn:
    assert dd.columns == [
        "Variable / Field Name",
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
        "Field Annotation",
    ], "Wrong datadict header"
    assert ~((dd["Field Type"] == "text") & 
             (dd['Text Validation Type OR Show Slider Number'].isnull())
             .any()), "Unvalidated text fields listed in datadict"
    assert dd['Field Type'].isin([
        "text",
        "dropdown",
        "radio",
        "yesno",
    ]), "Impermissible field type listed in datadict"
    assert dd['Field Label'].notnull().all(), "All variables are described"

if __name__ == "__main__":
    main()
    