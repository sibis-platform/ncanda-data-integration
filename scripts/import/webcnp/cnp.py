#!/usr/bin/env python

##
##  Copyright 2013 SRI International
##
##  http://nitrc.org/projects/ncanda-datacore/
##
##  This file is part of the N-CANDA Data Component Software Suite, developed
##  and distributed by the Data Integration Component of the National
##  Consortium on Alcohol and NeuroDevelopment in Adolescence, supported by
##  the U.S. National Institute on Alcohol Abuse and Alcoholism (NIAAA) under
##  Grant No. 1U01 AA021697
##
##  The N-CANDA Data Component Software Suite is free software: you can
##  redistribute it and/or modify it under the terms of the GNU General Public
##  License as published by the Free Software Foundation, either version 3 of
##  the License, or (at your option) any later version.
##
##  The N-CANDA Data Component Software Suite is distributed in the hope that it
##  will be useful, but WITHOUT ANY WARRANTY; without even the implied
##  warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU General Public License for more details.
##
##  You should have received a copy of the GNU General Public License along
##  with the N-CANDA Data Component Software Suite.  If not, see
##  <http://www.gnu.org/licenses/>.
##
##  $Revision$
##
##  $LastChangedDate$
##
##  $LastChangedBy$
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
    for form in instruments.values():
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


