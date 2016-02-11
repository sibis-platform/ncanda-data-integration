#!/usr/bin/env python
##
##  Copyright 2015 SRI International
##  License: https://ncanda.sri.com/software-license.txt
##
##  $Revision: 2110 $
##  $LastChangedBy: nicholsn $
##  $LastChangedDate: 2015-08-07 09:10:29 -0700 (Fri, 07 Aug 2015) $
##
"""
NP Release Script
======================
Generates a CSV file for all subjects included in NP analysis
"""
import os

import pandas as pd

directory = "/fs/ncanda-share/releases/NCANDA_DATA_00019/summaries"

nps_file = ["ataxia.csv", "cddr.csv", "clinical.csv", "cnp.csv", "dd100.csv",
            "dd1000.csv", "grooved_pegboard.csv", "ishihara.csv",
            "landoltc.csv", "rey-o.csv", "wais4.csv", "wrat4.csv"]

final_df = pd.read_csv(os.path.join(directory, "demographics.csv"),
                       index_col=['subject','arm','visit'])

race_map = dict(native_american_american_indian=1,
                asian=2,
                pacific_islander=3,
                african_american_black=4,
                caucasian_white=5);

# Create a series for each race where there is a 1 or 0 indicating if the
# participant belongs to the race or not and append to the final_df
for k, v in race_map.iteritems():
    race_filter = final_df.race == v
    final_df[k] = race_filter.apply(lambda x: 1 if x == True else 0)

for i in nps_file:
    df = pd.read_csv(os.path.join(directory, i),
                     index_col=['subject','arm','visit'])
    final_df = pd.concat([final_df, df], axis=1)

final_df = final_df.rename(columns={'cddr31':'cddr_past_month_binge',
                                    'cddr30':'cddr_past_year_binge'})

def replace_binge_groups_1(x):
	"""
	 A binary variable from CDDR_PastYr_Binge (i.e., 0 or blank, 
	 but not missing = 0, and 1 or more = 1)
	"""
	if x > 0:
		result = 1
	elif x == 0:
		result = 0
	else:
		result = pd.np.NaN
	return result

def replace_binge_groups_month(x):
	"""
	 #3groups based on past month binge drinking (0 - is o or blank, but not missing)
	"""
	if x == 0:
		result = 'None'
	elif x == 1:
		result = '1'
	elif x > 1:
		result = '2+'
	else:
		result = ''
	return result


final_df['binge_groups_1'] = final_df['cddr_past_year_binge'].apply(replace_binge_groups_1)
final_df['binge_groups_month'] = final_df['cddr_past_month_binge'].apply(replace_binge_groups_month)

final_df.to_csv('np_release.csv')
