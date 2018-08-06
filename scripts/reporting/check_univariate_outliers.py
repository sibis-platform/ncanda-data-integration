#!/usr/bin/env python
"""
Get values outside of `n` standard deviations of the given variable(s).

Sample use:

    ./check_univariate_outliers.py \
      --last-event 3 \
      --subject-list ./subjects-include.txt \
      --columns measure_brainsegvol measure_rhcortexvol measure_lhcortexvol \
                measure_rhcorticalwhitemattervol measure_lhcorticalwhitemattervol \
                measure_subcortgrayvol measure_totalgrayvol \
                measure_supratentorialvol measure_etiv \
      -- $SOURCE_FILE > $RESULT_FILE 

    ./check_univariate_outliers.py \
      --last-event 3 \
      --subject-list ./subjects-include.txt \
      --column-regex "_grayvol$" \
      -- $SOURCE_FILE1 $SOURCE_FILE2 > $RESULT_FILE 
"""
# TODO: Actually use longitudinal outlier check
# TODO: Test normalization by column from a different file

import pandas as pd


def number_to_event_name(number):
    """
    Convert an integer to an NCANDA event name (Arm 1 + full-year visits only)
    """
    if number == 0:
        return "baseline"
    elif number >= 1:
        return "followup_%dy" % number
    else:
        raise KeyError("Number %d is not eligible for conversion" % number)


def event_name_to_number(event_name):
    """
    Convert an NCANDA event name to an integer (Arm 1 + full-year visits only)
    """
    import re
    if event_name == "baseline":
        return 0
    else:
        match_obj = re.match(r'^followup_(\d+)y$', event_name)
        if match_obj:
            return int(match_obj.groups()[0])


def prepare_subject_list(subject_list):
    pass


def prepare_file(filename, primary_keys, columns=None, column_regex=None,
                 all_arms=False, subject_list=None, last_event=None,
                 normalize_file=None, normalize_column=None):
    # Call:
    # selected_args = ['columns', 'column_regex', 'all_arms', 'subject_list',
    #                  'last_event', 'normalize_file', 'normalize_column']
    # prepare_file(filename, primary_keys=PRIMARY_KEYS,
    #              **dict(zip(selected_args,
    #                         attrgetter(*selected_args)(args))))
    # prepare_file(filename, primary_keys=PRIMARY_KEYS,
    #              *attrgetter(*selected_args)(args))
    pass


def get_univariate_outliers_in_file(filename, sd_count=3, reference="baseline",
                                    verbose=False):

    if args.columns:
        df = pd.read_csv(filename,
                         index_col=PRIMARY_KEYS,
                         usecols=PRIMARY_KEYS + args.columns)
    else:
        df = pd.read_csv(filename,
                         index_col=PRIMARY_KEYS)

    if args.column_regex:
        df = df.filter(regex=args.column_regex)

    if not args.all_arms:
        df = df.xs('standard', level='arm')

    if args.subject_list:
        with open(args.subject_list, 'r') as subject_file:
            subjects = [x.strip() for x in subject_file.readlines()]
        df = df[df.index.get_level_values(level='subject').isin(subjects)]

    if args.last_event:
        all_events = [number_to_event_name(x) for x
                      in xrange(0, args.last_event + 1)]
        df = df[df.index.get_level_values(level='visit').isin(all_events)]

    if args.normalize_file:
        if not args.normalize_column:
            raise NotImplementedError(("Cannot provide --normalize-file"
                                       " without --normalize-column!"))
        else:
            df = normalize_by_column_from_file(df,
                                               args.normalize_file,
                                               args.normalize_column,
                                               keep_normalizer=False)
    elif args.normalize_column:
        df = normalize_by_column_in_df(df, args.normalize_column)

    baseline_only = (reference == "baseline")
    outliers = df.apply(pick_univariate_outliers, sd_count=sd_count,
                        verbose=verbose, baseline_only=baseline_only)
    outlier_values = df.mask(~outliers).stack().to_frame('outlier_value')
    outlier_values.index.set_names('variable', -1, inplace=True)

    outlier_values['file'] = filename
    outlier_values.set_index(['file'], append=True, inplace=True)
    # outlier_values.reorder_levels
    return outlier_values


def normalize_by_column_in_df(df, colname):
    # Process:
    # 1. Create a df copy
    # 2. Copy df[colname] to df_divisor[other_col] for all other colnames
    # 3. df_divisor[other_col] = 1
    # 4. Return df.div(df_divisor)
    df2 = pd.DataFrame().reindex_like(df)
    df2 = df2.assign(**{col: df[colname] for col in df2.columns})
    # Alternative for older pandas: iterate through df2.columns and assign
    # df[colname]
    df2[colname] = 1.0  # To preserve the value of the normalizing column
    return df.divide(df2)


def normalize_by_column_from_file(df, filename, colname,
                                  keep_normalizer=False):
    """
    Wrapper over `normalize_by_column_in_df` that loads another CSV file with
    normalizing value in `colname`  into a pandas.DataFrame, which it joins
    onto `df`.

    - Deletes the normalizing column from `df` afterwards unless
        `keep_normalizer` is `True`.
    - Assumes the existence of the same primary keys in `filename`.
    """
    # TODO: Take primary keys from df instead of the PRIMARY_KEYS const, e.g.:
    #   usecols = df.index.names + [colname]
    df_norm = pd.read_csv(filename, index_cols=PRIMARY_KEYS,
                          usecols=PRIMARY_KEYS + [colname])
    df_join = normalize_by_column_in_df(df.join(df_norm), colname)
    if not keep_normalizer:
        df_join.drop(columns=[colname], inplace=True)
    return df_join


def pick_univariate_outliers(df_col, sd_count=3, baseline_only=False,
                             verbose=False):
    colname = df_col.name
    year_min, year_max = ((df_col.groupby(['visit']).mean() -
                           sd_count * df_col.groupby(['visit']).std())
                          .to_frame('col_min'),
                          (df_col.groupby(['visit']).mean() +
                           sd_count * df_col.groupby(['visit']).std())
                          .to_frame('col_max'))
    if baseline_only:
        # TODO: Also implement for reference = "all"
        year_min = year_min.loc['baseline'].squeeze()
        year_max = year_max.loc['baseline'].squeeze()

        return (df_col < year_min) | (df_col > year_max)
    else:
        df_col = df_col.to_frame().join(year_min).join(year_max)
        return ((df_col[colname] < df_col['col_min']) |
                (df_col[colname] > df_col['col_max']))


def pick_longitudinal_outliers(df, fn):
    # Approach:
    #   1. From indexed df, get df.columns
    #   2. Group df by ['subject', 'arm']
    #   3. Accumulate a dict of data frames with residuals / other linreg stats
    #      for each column
    #   4. Concatenate horizontally
    cols = df.columns.tolist()
    df_grouped = df.reset_index().groupby(['subject', 'arm'])
    return pd.concat([df_grouped.apply(fn, colname=x) for x in cols],
                     axis=1)


def get_aic(df_grp, colname, longit_col="visit"):
    # Or any other per-subject linreg stat
    import statsmodels.formula.api as smf
    result = smf.ols(colname + ' ~ ' + longit_col, df_grp).fit()
    return pd.Series({colname: result.aic})
    # Should be generalized with pd.Series{colname: attrgetter(stat)(result)}


def get_residuals(df_grp, colname, longit_col="visit"):
    # Or any other per-timepoint linreg stat
    import statsmodels.formula.api as smf
    result = smf.ols(colname + ' ~ ' + longit_col, df_grp).fit()
    # Assignment is important because it sets up the index
    df_grp[colname] = result.resid
    # Should be generalized with df_grp[colname] = attrgetter(stat)(result)
    return df_grp[colname]

PRIMARY_KEYS = ["visit", "subject", "arm"]
if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        prog='check_univariate_outliers',
        description=('For all variables in passed files, print out the ones'
                     'that are beyond 3 SDs of their mean.'))
    parser.add_argument("-v", "--verbose",
                        help="Verbose operation",
                        action="store_true")
    parser.add_argument("--sd-count",
                        help="Flag beyond how many SDs?",
                        default=3, action="store")
    parser.add_argument("--all-arms",
                        help="Prevent removal of non-standard arms",
                        default=False, action="store")
    parser.add_argument('--reference',
                        default='baseline',
                        choices=['baseline', 'year', 'all'],
                        help=('Which means/SDs to compare to? "year" keeps the'
                              'comparison within each event; "baseline" relies'
                              'only on the baseline reference; and "all" mixes'
                              'all together.'))
    parser.add_argument('-e', '--last-event', type=int,
                        help="Last event to include as int (baseline=0)")
    parser.add_argument('-s', '--subject-list',
                        help="File with newline-separated IDs to include")
    parser.add_argument('-c', '--columns', nargs='*', default=None,
                        help="Column(s) to check")
    parser.add_argument('--column-regex', default=None,
                        help="Regex for columns to preserve")
    # TODO: Implement this bit of logic
    parser.add_argument('--normalize-file', default=None,
                        help=("File that contains the normalizing column"
                              "specified in --normalize-column, as well as"
                              "primary keys equivalent to the file under"
                              "analysis"))
    parser.add_argument('--normalize-column', default=None,
                        help=("Column to normalize by. If --normalize-file is"
                              "not provided, this column is assumed to be in"
                              "the file(s) to be analyzed."))
    parser.add_argument('-o', '--outfile', default=sys.stdout)
    parser.add_argument('files', nargs='+',
                        help="Paths to CSV files to analyze")
    args = parser.parse_args()

    # make_header = True
    file_dfs = []
    for f in args.files:
        if args.verbose:
            print "Now processing %s..." % f
        # TODO: Join with get_longitudinal_outliers, when that's written
        file_dfs.append(
            get_univariate_outliers_in_file(f, sd_count=args.sd_count,
                                            reference=args.reference,
                                            verbose=args.verbose))
    (pd.concat(file_dfs, axis=0)
     .reorder_levels(order=["subject", "visit", "file", "variable"])
     .sort_index(level=["subject", "visit"])
     .to_csv(args.outfile))
