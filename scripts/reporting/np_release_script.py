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
Generates a CSV file for all subjects included in NP analysis for Dolf
"""
import os
import sys
import datetime

import pandas as pd

directory = "/fs/ncanda-share/releases/NCANDA_DATA_00010/summaries"

csv_dir = "/fs/u00/alfonso/Desktop/"

today =  datetime.date.today()

nps_file = ["ataxia.csv", "cddr.csv", "clinical.csv", "cnp.csv", "dd100.csv",
            "dd1000.csv", "grooved_pegboard.csv", "ishihara.csv",
            "landoltc.csv", "rey-o.csv", "wais4.csv", "wrat4.csv",
            "mri_report.csv", "parentreport.csv"]

fields = ['site', 'sex', 'visit_age','exceed_or_mrianomaly',
          'exceeds_bl_drinking', 'cddr_past_month_binge','cddr_past_year_binge',
          'binge_groups_1', 'binge_groups_month', 'hispanic', 'race',
          'race_label', 'mri_analysisanomalies', 'hi_ed',
          'african_american_black', 'asian','caucasian_white',
          'native_american_american_indian', 'pacific_islander',
          'cddrheight_inches', 'cddrweight_pounds', 'ses_parent_yoe',
          'fh_alc_density','fh_drug_density', 'bmi_value', 'bmi_zscore',
          'bmi_percentile', 'pds_score','np_atax_sht_sum', 'np_atax_steps_sum',
          'np_atax_standr_sum','np_atax_standl_sum', 'cnp_mpract_mp2rtcr',
          'cnp_cpf_ifac_tot','cnp_cpf_ifac_rtc', 'cnp_cpw_iwrd_tot',
          'cnp_cpw_iwrd_rtc','cnp_spcptnl_scpl_tprt', 'cnp_spcptnl_scpt_tp',
          'cnp_spcptnl_scpt_tprt','cnp_sfnb2_sfnb_rtc', 'cnp_sfnb2_sfnb_rtc0',
          'cnp_sfnb2_sfnb_rtc1','cnp_sfnb2_sfnb_rtc2', 'cnp_sfnb2_sfnb_mcr',
          'cnp_sfnb2_sfnb_mrtc','cnp_pmat24a_pmat24_a_cr',
          'cnp_pmat24a_pmat24_a_rtcr', 'cnp_cpfd_cpfdtp','cnp_cpfd_cpfdtprt',
          'cnp_cpwd_dwrd_tot', 'cnp_cpwd_dwrd_rtc','cnp_shortvolt_svt',
          'cnp_shortvolt_svtcrt', 'cnp_shortvolt_svt_eff','cnp_er40d_er40_cr',
          'cnp_er40d_er40_crt', 'cnp_er40d_er40angrt','cnp_er40d_er40fearrt',
          'cnp_er40d_er40haprt', 'cnp_er40d_er40noert','cnp_er40d_er40sadrt',
          'cnp_pcet_pcetcr', 'cnp_pcet_pcetrtcr','cnp_pcet_pcet_eff',
          'cnp_pcet_pcet_acc', 'cnp_pcet_pcet_acc2',
          'cnp_medf36_medf36_hap_rtcr', 'cnp_medf36_medf36_sad_rtcr',
          'cnp_medf36_medf36_ang_rtcr', 'cnp_medf36_medf36_fear_rtcr',
          'cnp_medf36_medf36_a', 'cnp_medf36_medf36_t', 'cnp_pvoc_pvoccr',
          'cnp_pvoc_pvocrtcr', 'cnp_pvrt_pvrtcr', 'cnp_pvrt_pvrtrtcr',
          'cnp_pvrt_pvrt_eff', 'cnp_svdelay_svt_ld', 'cnp_svdelay_svtldrtc',
          'cnp_svdelay_svtldrter', 'cnp_svdelay_svt_effd', 'cnp_sfnb2_sfnb_mrt',
          'cnp_sfnb2_sfnb_meff', 'np_gpeg_dh_time', 'np_gpeg_ndh_time',
          'np_wais4_rawscore', 'np_wrat4_wr_raw', 'np_wrat4_mc_raw',
          'cnp_spcptnl_scpn_tp', 'cnp_spcptnl_scpn_tprt', 'cnp_spcptnl_scpl_tp',
          'cnp_cpfd_dfac_tot', 'cnp_cpfd_dfac_rtc']

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

def main(args=None):
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

    final_df['binge_groups_1'] = final_df['cddr_past_year_binge'].apply(replace_binge_groups_1)
    final_df['binge_groups_month'] = final_df['cddr_past_month_binge'].apply(replace_binge_groups_month)

    final_df['exceed_or_mrianomaly'] = pd.np.NaN
    final_df['hi_ed'] = pd.np.NaN
    final_df['mri_analysisanomalies'] = pd.np.NaN

    final_df = final_df[fields]

    final_df.to_csv('{}np_release_{}.csv'.format(csv_dir,today))

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    argv = parser.parse_args()
    sys.exit(main(args=argv))
