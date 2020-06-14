"""
Print out a hierarchical list of changes between two folders' CSV files.
Intended to be used for comparisons of release folders.

Only compares files that are found in both folders.

Sample call when comparing same-year releases:

```
RELEASE_DIR=/fs/ncanda-share/releases/internal/followup_5y
python compare_releases.py --cutoff 10 \
    ${RELEASE_DIR}/NCANDA_SNAPS_5Y_REDCAP_V01/summaries/redcap/ \
    ${RELEASE_DIR}/NCANDA_SNAPS_5Y_REDCAP_V02/summaries/redcap/
```

Sample call when comparing between-year releases:

```
RELEASE_DIR=/fs/ncanda-share/releases/internal
python compare_releases.py --cutoff 10 --exclude-visit followup_5y \
    ${RELEASE_DIR}/followup_4y/NCANDA_SNAPS_4Y_REDCAP_V02/summaries/redcap/ \
    ${RELEASE_DIR}/followup_5y/NCANDA_SNAPS_5Y_REDCAP_V02/summaries/redcap
```

(Note the `--exclude-visit followup_5y`, which makes the script omit any
differences on the provided year.)
"""
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Union


def _parse_args(input_args: List = None):
    """
    Handle CLI arguments
    """
    parser = argparse.ArgumentParser(
        description="Compare CSV contents of NCANDA releases")
    parser.add_argument('first_folder', type=Path,
                        help="Older folder or file to compare")
    parser.add_argument('second_folder', type=Path,
                        help="Newer folder or file to compare")
    parser.add_argument('--index-keys', default=['subject', 'arm', 'visit'],
                        help="Foreign keys to compare the files on")
    parser.add_argument('--exclude-visit', '-V',
                        help="Visits to exclude from the listing of results")
    parser.add_argument('--exclude-files', '-F',
                        nargs='*', default=["locked_forms.csv"],
                        help="Any files in the folders to avoid processing")
    parser.add_argument('--enumeration-cutoff', '--cutoff', '-c',
                        dest='cutoff', type=int,
                        help="Truncate results after this many values")
    return parser.parse_args(input_args)


def collect_file_pairs(folder1, folder2, exclusions: List = []) -> List[Tuple]:
    """
    Normalize path inputs into a list of path tuples
    """
    if folder1.is_file():
        assert folder2.is_file()
        assert folder1.name == folder2.name
        return [(folder1, folder2)]
    else:
        assert folder1.is_dir() and folder2.is_dir()

    pairs: List[Tuple[str]] = []

    for file in folder1.glob('*.csv'):
        if file.name in exclusions or not file.is_file():
            continue

        file2 = folder2 / file.name
        if file2.exists():
            pairs.append((file, file2))

    return sorted(pairs)


def prepare_index(df: pd.DataFrame, index_keys: List) -> pd.DataFrame:
    """
    Ensure that df has a (Multi)Index consisting of index_keys
    """
    if df.index.names == index_keys:
        return df
    elif len(df.index.names) == 1 and df.index.name is None:
        return df.set_index(index_keys)
    else:
        return df.reset_index().set_index(index_keys)


def get_dataframe_differences(df1: pd.DataFrame, df2: pd.DataFrame,
                              index_keys: List) -> pd.DataFrame:
    """
    Create a list of all variable differences between two dataframes.

    Returns a DataFrame with a MultiIndex consisting of index_keys and
    'colname', and two columns with changed values from each DataFrame.
    """
    df1 = prepare_index(df1, index_keys)
    df2 = prepare_index(df2, index_keys)

    diff_columns = compare_columns(df1.columns, df2.columns)
    shared_columns = df1.columns[~df1.columns.isin(diff_columns['removed'])]

    df1_long = df1[shared_columns].stack().to_frame('df1')
    df2_long = df2[shared_columns].stack().to_frame('df2')

    comparison = df1_long.join(df2_long, how="outer")
    comparison.index.rename('colname', level=-1, inplace=True)

    differences = comparison.loc[comparison['df1'] != comparison['df2']]
    return differences


def summarize_differences(difference_df: pd.DataFrame,
                          index_keys: List) -> Dict:
    counts_by_index = difference_df.reset_index().groupby(index_keys).count()

    summarized_changes = counts_by_index.apply(
        lambda x: F"{x['df1']} changed, {x['df2']} new values", axis=1)

    return _reshape_differences(summarized_changes)


def _reshape_differences(difference_series: pd.Series) -> Dict:
    output_dict: Dict = {}
    difference_dict = difference_series.to_dict()
    for (subject, arm, visit), statement in difference_dict.items():
        if visit not in output_dict:
            output_dict[visit] = []
        output_dict[visit].append(F"{subject}: {statement}")

    return output_dict


def dict_to_string(d: Dict[str, Union[Dict, str]], prefix: str = '',
                   enumeration_cutoff: int = None) -> str:
    """
    Intended sample output:

    Visit 1:
        Subject (X added, Y removed)
    Visit 2:
        300 subjects with changes or additions
    """
    output: str = ''
    for key in sorted(d.keys()):
        value = d[key]
        output += f"\n{prefix}{key}: "
        if type(value) == dict:
            output += dict_to_string(value, prefix=prefix + '\t')
        elif type(value) == list:
            sub_prefix = F"\n{prefix}\t"
            if enumeration_cutoff and len(value) > enumeration_cutoff:
                output += sub_prefix + F"{len(value)} subjects with changes or additions"
            else:
                output += sub_prefix + sub_prefix.join(value)
        else:
            output += value
    return output


def compare_columns(columns1: pd.Index, columns2: pd.Index) -> Dict[str, List]:
    added = columns2.difference(columns1).tolist()
    removed = columns1.difference(columns2).tolist()

    return {'removed': removed, 'added': added}


def compared_columns_to_str(comparison_dict: Dict[str, List],
                            enumeration_cutoff: int = None) -> str:
    outputs: List[str] = []
    for action, variables in comparison_dict.items():
        count = len(variables)
        if enumeration_cutoff and count > enumeration_cutoff:
            outputs.append(f"{count} {action}")
        elif count > 0:
            outputs.append(f"{action}: " + ", ".join(variables))

    if len(outputs) > 0:
        return " (Variable changes - {})".format("; ".join(outputs))
    else:
        return ""


def test_compare_columns():
    df1 = pd.DataFrame({'a': [1, 2], 'b': [np.nan, 3]})
    df2 = pd.DataFrame({'a': [np.nan, 3], 'c': ['x', 'y']})

    assert compare_columns(df1.columns, df2.columns) == {'removed': ['b'],
                                                         'added': ['c']}


if __name__ == '__main__':
    args = _parse_args()

    release1 = args.first_folder
    release2 = args.second_folder

    enumeration_cutoff = args.cutoff

    pairs = collect_file_pairs(release1, release2)

    for pair in pairs:
        df1 = pd.read_csv(pair[0], dtype=str)
        df2 = pd.read_csv(pair[1], dtype=str)
        if df1.empty or df2.empty:
            continue

        differences = get_dataframe_differences(df1, df2, args.index_keys)
        if differences.empty:
            continue

        col_diffs = compare_columns(df1.columns, df2.columns)
        col_diffs_str = compared_columns_to_str(col_diffs, enumeration_cutoff)
        print(F"{pair[0].name}{col_diffs_str}:", end='')
        try:
            summary = summarize_differences(differences, args.index_keys)
            if args.exclude_visit and args.exclude_visit in summary:
                del summary[args.exclude_visit]
            print(dict_to_string(summary, "\t", enumeration_cutoff))
        except Exception:  # we don't care what failed
            print()
            continue
