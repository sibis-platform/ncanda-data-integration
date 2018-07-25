import pytest
import pandas as pd
import numpy as np
from check_univariate_outliers import pick_univariate_outliers

s = np.random.seed(54920)


def make_df_with_outliers(mean, std, size, colname, values_to_insert=None, **kwargs):
    data = np.random.normal(loc=mean, scale=std, size=size)
    if values_to_insert:
        data = np.append(np.array(values_to_insert), data)
    df_args = kwargs
    df_args[colname] = data
    return pd.DataFrame(df_args)

# make_df_with_outliers(2000, 100, 10, colname="brain_volume", 
#                       values_to_insert=[1600, 2400], arm="standard", visit="baseline")


@pytest.fixture
def df_within_limits(mean=1000, sd=100, size=1000):
    df = make_df_with_outliers(mean, sd, size, colname="brain_volume",
                               arm="standard", visit="baseline")
    df.index.names = ['subject']
    df.set_index(['visit', 'arm'], append=True, inplace=True)
    return df


@pytest.fixture
def df_baseline(mean=2000, sd=100, size=1000):
    df = make_df_with_outliers(mean, sd, size, colname="brain_volume",
                               values_to_insert=[mean - 4*sd, mean + 4*sd],
                               arm="standard", visit="baseline")
    df.index.names = ['subject']
    df.set_index(['visit', 'arm'], append=True, inplace=True)
    return df


@pytest.fixture
def df_year1(mean=2000, sd=50, size=1000):
    df = make_df_with_outliers(mean, sd, size, colname="brain_volume",
                               values_to_insert=[mean - 4*sd, mean + 4*sd],
                               arm="standard", visit="followup_1y")
    df.index.names = ['subject']
    df.set_index(['visit', 'arm'], append=True, inplace=True)
    return df


@pytest.fixture
def df_nice():
    data = [0] * 5 + [10] * 90 + [1000] * 4 + [10000]  # mean: 149, sd = 1008.9
    df = make_df_with_outliers(0, 1, 0, colname="brain_volume",
                               values_to_insert=data,
                               arm="standard", visit="baseline")
    df.index.names = ['subject']
    df.set_index(['visit', 'arm'], append=True, inplace=True)
    return df


def test_catches_outlier(df_nice):
    result = df_nice.mask(~df_nice.apply(pick_univariate_outliers,
                                         sd_count=3)).stack()
    assert result.shape[0] == 1
    assert result.values == [10000]

# 0. Sanity checks:
#   a. Should return a series
#   b. Should return no outliers if everything is within limits
def test_returns_series(df_within_limits):
    result = df_within_limits.mask(
        ~df_within_limits.apply(pick_univariate_outliers,
                                sd_count=3.5)).stack()
    assert type(result) == pd.core.series.Series
    assert result.shape[0] == 0

# Others:
# - It should throw an error if the data frame is not indexed / indexes are not
#   named correctly
# - Should error out if there is now baseline visit

# Tests:
# 1. Testing df_baseline should find the two outliers
def test_baseline_finds(df_baseline):
    result = df_baseline.mask(~df_baseline.apply(pick_univariate_outliers)).stack()
    assert result.shape[0] >= 2
    assert result.shape[0] <= 2 + int(np.round(0.002 * df_baseline.shape[0]))

# 2. Testing df_baseline + df_year1 should find two outliers if baseline-only
#   is enabled, four if not
def test_year1_ok_if_baseline_only(df_baseline, df_year1):
    df = pd.concat([df_baseline, df_year1], axis=0)
    result = df.mask(~df.apply(pick_univariate_outliers, baseline_only=True)).stack()
    assert (result.reset_index(['visit'])['visit'] != "followup_1y").all()

def test_year1_outliers_if_per_year(df_baseline, df_year1):
    df = pd.concat([df_baseline, df_year1], axis=0)
    result = df.mask(~df.apply(pick_univariate_outliers, baseline_only=False)).stack()
    assert (result.reset_index(['visit'])['visit'] == "followup_1y").any()
