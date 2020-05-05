#!/usr/bin/env python
"""
Given datadict(s), output a list of variables whose field type or validation
allow/prevent the use in an NCANDA release.
"""
import argparse
from typing import List
import sys
import pandas as pd

from datadict_utils import load_datadict


def parse_args(input_args: List = None) -> argparse.Namespace:
    """
    Parse CLI arguments. (Note that -v is has non-standard use here.)
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--invert', '-v',
                        help='Get variables that are *not* releasable',
                        action='store_true')
    parser.add_argument('--format',
                        choices=['text', 'df'],
                        default='text',
                        help="Output format")
    parser.add_argument('datadict', nargs='+', help="Path to datadict file(s)")
    return parser.parse_args(input_args)


def get_variables(datadict: pd.DataFrame, invert: bool = False) -> List:
    """
    Given a datadict DataFrame, find all allowable indices and output index
    names at either those locations, or all other locations if invert=True
    """
    allowable_validation = ['number', 'integer']
    allowable_validation_idx = (
        datadict['Text Validation Type OR Show Slider Number']
        .str.strip()
        .isin(allowable_validation))

    allowable_types = ['dropdown', 'checkbox', 'yesno', 'calc', 'radio']
    allowable_types_idx = (datadict['Field Type'].isin(allowable_types))

    allowable_idx = allowable_validation_idx | allowable_types_idx
    if invert:
        allowable_idx = ~allowable_idx

    # TODO: Actually expand the checkboxes
    return datadict.loc[allowable_idx].index.tolist()


if __name__ == '__main__':
    args = parse_args()

    all_vars: List[str] = []
    all_dds: List[pd.DataFrame] = []
    for fpath in args.datadict:
        dd = load_datadict(fpath, force_names=True)
        datadict_vars = get_variables(dd, invert=args.invert)
        all_vars.extend(datadict_vars)
        if args.format in ['csv', 'df']:
            all_dds.append(dd.loc[datadict_vars])

    if args.format == 'text':
        print("\n".join(all_vars))
    elif args.format in ['csv', 'df']:
        pd.concat(all_dds, sort=False).to_csv(sys.stdout)

    sys.exit(0)
