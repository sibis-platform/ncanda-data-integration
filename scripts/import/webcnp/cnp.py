#!/usr/bin/env python

##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##

import os.path
import pandas

# Dictionary mapping instruments to their internal REDCap names (for "*_complete" fields)
instruments = { 'test_sessions' : 'test_sessions', 
                'cpf' : 'penn_facial_memory_test', 
                'cpfd' : 'penn_facial_memory_test_delayed_version', 
                'cpw' : 'penn_word_memory_test',
                'cpwd'  : 'penn_word_memory_test_delayed_version',
                'medf36' : 'measured_emotion_differentiation_task_36_items',
                'er40d' : 'emotion_recognition_task_form_d_40_items',                
                'mpract' : 'motor_praxis_test', 
                'pcet' : 'penn_conditional_exclusion_test_form_a',
                'pmat24a' : 'penn_matrix_analysis_test_form_a_24_items', 
                'pvoc' : 'penn_vocabulary_test', 
                'pvrt' : 'penn_logical_reasoning_test_short_version',
                'sfnb2' : 'short_fractalnback_2_back_version',
                'shortvolt' : 'visual_object_learning_test_short_version', 
                'spcptnl' : 'short_penn_continuous_performance_task_number_letter_version',
                'svdelay' : 'visual_object_learning_test_delayed_short_version' }

# Get a list of variables to copy as the intersections of source and target project field names
def get_copy_variables( project_src, project_dst ):
    copy_vars = []
    form_dst_vars = [ field['field_name'][4:] for field in project_dst.metadata if (field['form_name'] == 'cnp_summary' ) ] ## get fields from 'cnp_summary' form and remove 'cnp_prefix'
    for form in list(instruments.values()):
        form_src_vars = [ field['field_name'] for field in project_src.metadata if (field['form_name'] == form) ]
        copy_vars += list( set( form_src_vars ) & set( form_dst_vars ) )
    return copy_vars

# Lookup tables for age-specific z-score
module_dir = os.path.dirname(os.path.abspath(__file__))
mean_sdev_byage_table = pandas.io.parsers.read_csv( os.path.join( module_dir, 'norm_means_stdev_byage.csv' ), header=0, index_col=[0] )

# This table maps fields in the summary form (keys) that need z-scores to fields in the imported lookup table that contain mean and standard deviation by age.
mean_sdev_by_field_dict = { 'cpf_ifac_tot'          : 'cpf-a_cr',
                            'cpf_ifac_rtc'          : 'cpf-a_rtcr',
                            'er40d_er40_cr'         : 'k-er40-d_cr',
                            'er40d_er40_crt'        : 'k-er40-d_rtcr',
                            'cpw_iwrd_tot'          : 'k-cpw_cr',
                            'cpw_iwrd_rtc'          : 'k-cpw_rtcr',
                            'medf36_medf36_a'       : 'medf36-a_cr',
                            'medf36_medf36_t'       : 'medf36-a_rtcr',
                            'mpract_mp2rtcr'        : 'mpraxis_mp2rtcr',
                            'pmat24a_pmat24_a_cr'   : 'pmat24-a_cr',
                            'pmat24a_pmat24_a_rtcr' : 'pmat24-a_rtcr',
                            'shortvolt_svt'         : 'svolt_cr',
                            'shortvolt_svtcrt'      : 'svolt_rtcr',
                            'pcet_pcetrtcr'         : 'pcet_rtcr',
                            'pcet_pcet_acc2'        : 'pcet_acc2',
                            'spcptnl_scpt_tp'       : 'spcptnl_t_tp',
                            'spcptnl_scpt_tprt'     : 'spcptnl_t_tprt' }


