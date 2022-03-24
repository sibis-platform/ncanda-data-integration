#!/usr/bin/env python
"""
Pares down the mNCANDA data supplied by Kevin to acceptable-to-release columns
based on data dictionary annotations and type/validation presence.

Invoked with:

    python prepare_mncanda.py \
        --in-data input/data.csv --in-datadict input/datadict.xslx \
        --out-data output/data.csv --out-datadict output/datadict.csv

(note that datadict is expected to be an Excel file)
"""
import argparse
import pandas as pd
from typing import List, Union
from pathlib import Path


def main():
    args = _args()

    dd = load_datadict(args.in_datadict)
    varlist = select_variables_from_datadict(dd, verbose=args.verbose)
    dd_out = dd.loc[dd['Variable / Field Name'].isin(varlist)].copy()
    dd_out.iloc[0, 0] = 'subject'

    data = pd.read_csv(args.in_data, dtype=str)
    data_out = data[[x for x in varlist if x in data.columns]].copy()
    data_out.rename(columns={'mri_xnat_sid': 'subject'}, inplace=True)

    dd_out.to_csv(args.out_datadict, index=False)
    data_out.to_csv(args.out_data, index=False)


def _args(input_list: List[str] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="filter_mncanda_data")
    p.add_argument('--in-datadict', type=Path,
                   default=Path("input_Y6/DataDictionary.mNCANDA_2021-04-28kmc.xlsx"))
    p.add_argument('--in-data', type=Path, 
                   default=Path('input_Y6/ncd.ma.2021.mncanda.2021.1_3.csv'))
    p.add_argument('--out-data', type=Path, required=True)
    p.add_argument('--out-datadict', type=Path, required=True)
    p.add_argument('--verbose', '-v', action='store_true')

    return p.parse_args(input_list)


def load_datadict(fname: Union[str, Path]) -> pd.DataFrame:
    # 1. Load
    dd = pd.read_excel(fname)
    # 2. TODO: Protect primary key
    return dd


def select_variables_from_datadict(
    dd: pd.DataFrame,
    skip_annotation: str = "withh?oldfromrelease",
    verbose: bool = False,
) -> List[str]:
    skips = dd['Field Annotation'].str.contains(skip_annotation, na=False, case=False, regex=True)
    unvalidated = (dd['Field Type'] == 'text') & dd['Text Validation Type OR Show Slider Number'].isnull()  # fixed from .notnull()
    index = dd['Variable / Field Name'].iloc[0]
    dropped = dd.loc[skips | unvalidated, 'Variable / Field Name'].tolist()
    selected = dd.loc[~skips & ~unvalidated, 'Variable / Field Name'].tolist()
    selected = [x.strip() for x in selected]

    if verbose:
        print("Dropped: {}".format(", ".join(dropped)))
        print(f"Preserving {index}.")

    if index not in selected:
        selected = [index] + selected

    return selected


if __name__ == "__main__":
    main()
