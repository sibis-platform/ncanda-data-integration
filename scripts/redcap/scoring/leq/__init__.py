#!/usr/bin/env python
 
##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##

#
# Variables from surveys needed for leq
#
import numpy as np

input_fields = { 'youthreport2' : [ 'youth_report_2_complete', 'youthreport2_missing', 'youthreport2_leaqa_set1_leaqa3',  			'youthreport2_leaqa_set1_leaqa3','youthreport2_leaq_set1_leaq3','youthreport2_leaq_set1_leaq3',
		'youthreport2_leaq_set1_leaq4','youthreport2_leaq_set1_leaq6','youthreport2_leaq_set1_leaq7',
		'youthreport2_leaq_set1_leaq8','youthreport2_leaq_set2_leaq9','youthreport2_leaq_set2_leaq10',
		'youthreport2_leaq_set2_leaq11','youthreport2_leaq_set2_leaq14','youthreport2_leaq_set2_leaq15',
		'youthreport2_leaq_set3_leaq16','youthreport2_leaq_set5_leaq34','youthreport2_leaq_set5_leaq37',
		'youthreport2_leaq_set6_leaq48','youthreport2_leaq_set8_leaq57','youthreport2_leaq_set8_leaq58',
		'youthreport2_leaqa_set1_leaqa3','youthreport2_leaqa_set1_leaqa4','youthreport2_leaqa_set1_leaqa6',
		'youthreport2_leaqa_set1_leaqa7','youthreport2_leaqa_set1_leaqa8','youthreport2_leaqa_set2_leaqa9',                			'youthreport2_leaqa_set2_leaqa10','youthreport2_leaqa_set2_leaqa11','youthreport2_leaqa_set2_leaqa14',	
		'youthreport2_leaqa_set2_leaqa15','youthreport2_leaqa_set3_leaqa16','youthreport2_leaqa_set5_leaqa34',
		'youthreport2_leaqa_set5_leaqa37','youthreport2_leaqa_set6_leaqa48','youthreport2_leaqa_set8_leaqa57',
		'youthreport2_leaqa_set8_leaqa58','youthreport2_leaqa_set5_leaqa33','youthreport2_leaq_set5_leaq33',
		'youthreport2_leaq_set6_leaq43', 'youthreport2_leaq_set6_leaq44','youthreport2_leaq_set7_leaq50',
		'youthreport2_leaq_set7_leaq52', 'youthreport2_leaq_set7_leaq53','youthreport2_leaqa_set5_leaqa33',
		'youthreport2_leaqa_set6_leaqa43','youthreport2_leaqa_set6_leaqa44', 'youthreport2_leaqa_set7_leaqa50', 
		'youthreport2_leaqa_set7_leaqa52', 'youthreport2_leaqa_set7_leaqa53','youthreport2_leaqa_set1_leaqa1',
		'youthreport2_leaq_set1_leaq1','youthreport2_leaq_set2_leaq12','youthreport2_leaq_set3_leaq17', 
		'youthreport2_leaq_set4_leaq31','youthreport2_leaqa_set4_f_leaqaf31','youthreport2_leaqa_set1_leaqa1', 
		'youthreport2_leaqa_set2_leaqa12','youthreport2_leaqa_set3_leaqa17','youthreport2_leaqa_set4_m_leaqam31',
		'youthreport2_leaqa_set1_leaqa1', 'youthreport2_leaqa_set2_leaqa12','youthreport2_leaqa_set3_leaqa17',
		'youthreport2_leaqa_set4_f_leaqaf31','youthreport2_leaqa_set2_leaqa13','youthreport2_leaq_set2_leaq13',
		'youthreport2_leaq_set4_leaq25', 'youthreport2_leaq_set4_leaq26','youthreport2_leaq_set4_leaq27',
		'youthreport2_leaq_set4_leaq28', 'youthreport2_leaq_set7_leaq55','youthreport2_leaq_set8_leaq56', 
		'youthreport2_leaq_set8_leaq61','youthreport2_leaqa_set4_f_leaqaf25','youthreport2_leaqa_set2_leaqa13', 
		'youthreport2_leaqa_set4_m_leaqam25', 'youthreport2_leaqa_set4_m_leaqam26','youthreport2_leaqa_set4_m_leaqam27', 
		'youthreport2_leaqa_set4_m_leaqam28', 'youthreport2_leaqa_set7_leaqa55','youthreport2_leaqa_set8_leaqa56', 
		'youthreport2_leaqa_set8_leaqa61','youthreport2_leaqa_set2_leaqa13', 'youthreport2_leaqa_set4_f_leaqaf25', 
		'youthreport2_leaqa_set4_f_leaqaf26','youthreport2_leaqa_set4_f_leaqaf27', 'youthreport2_leaqa_set4_f_leaqaf28', 
		'youthreport2_leaqa_set7_leaqa55','youthreport2_leaqa_set8_leaqa56', 'youthreport2_leaqa_set8_leaqa61',
		'youthreport2_leaqa_set5_leaqa39','youthreport2_leaq_set5_leaq39','youthreport2_leaq_set5_leaq40', 
		'youthreport2_leaq_set6_leaq45','youthreport2_leaq_set6_leaq46', 'youthreport2_leaq_set7_leaq51',
		'youthreport2_leaqa_set5_leaqa39','youthreport2_leaqa_set6_leaqa40', 'youthreport2_leaqa_set6_leaqa45',
		'youthreport2_leaqa_set6_leaqa46', 'youthreport2_leaqa_set7_leaqa51','youthreport2_leaqa_set3_leaqa19',
		'youthreport2_leaq_set3_leaq19', 'youthreport2_leaq_set3_leaq21', 'youthreport2_leaq_set3_leaq22',
		'youthreport2_leaq_set4_leaq23', 'youthreport2_leaq_set4_leaq24','youthreport2_leaqa_set3_leaqa19', 
		'youthreport2_leaqa_set3_leaqa21','youthreport2_leaqa_set3_leaqa22','youthreport2_leaqa_set3_leaqa23',
		'youthreport2_leaqa_set3_leaqa24']}
 
#
# This determines the name of the form in REDCap where the results are posted.
#
output_form = 'clinical'

def sum_nonna(data):
   results = data.sum(axis=1,numeric_only=None)
   return results			


#
# Scoring function - leq really just copies a survey response
#
def compute_scores( data, demographics ):
    # Get rid of all records that don't have YR2
    data.dropna( axis=0, subset=['youth_report_2_complete'] )
    data = data[ data['youth_report_2_complete'] > 0 ]
    data = data[ ~(data['youthreport2_missing'] > 0) ]




#Discrete-Negative-Uncontrollable Life Events
    data['leq_c_dnu'] = sum_nonna(data[['youthreport2_leaq_set1_leaq3','youthreport2_leaq_set1_leaq4',
		'youthreport2_leaq_set1_leaq6','youthreport2_leaq_set1_leaq7','youthreport2_leaq_set1_leaq8',
                'youthreport2_leaq_set2_leaq9','youthreport2_leaq_set2_leaq10','youthreport2_leaq_set2_leaq11',
                'youthreport2_leaq_set2_leaq14','youthreport2_leaq_set2_leaq15','youthreport2_leaq_set3_leaq16',
                 'youthreport2_leaq_set5_leaq34',
		'youthreport2_leaq_set5_leaq37','youthreport2_leaq_set6_leaq48','youthreport2_leaq_set8_leaq57',
		'youthreport2_leaq_set8_leaq58','youthreport2_leaqa_set1_leaqa3','youthreport2_leaqa_set1_leaqa4',
		'youthreport2_leaqa_set1_leaqa6','youthreport2_leaqa_set1_leaqa7','youthreport2_leaqa_set1_leaqa8',
		'youthreport2_leaqa_set2_leaqa9','youthreport2_leaqa_set2_leaqa10','youthreport2_leaqa_set2_leaqa11',
		'youthreport2_leaqa_set2_leaqa14','youthreport2_leaqa_set2_leaqa15','youthreport2_leaqa_set3_leaqa16',
		'youthreport2_leaqa_set5_leaqa34','youthreport2_leaqa_set5_leaqa37','youthreport2_leaqa_set6_leaqa48', 
		'youthreport2_leaqa_set8_leaqa57','youthreport2_leaqa_set8_leaqa58']])/16



#Chronic-Negative-Uncontrollable Life Events scales
    data['leq_c_cnu'] = sum_nonna(data[['youthreport2_leaq_set5_leaq33','youthreport2_leaq_set6_leaq43',
                  'youthreport2_leaq_set6_leaq44' ,'youthreport2_leaq_set7_leaq50','youthreport2_leaq_set7_leaq52',
                  'youthreport2_leaq_set7_leaq53','youthreport2_leaqa_set5_leaqa33','youthreport2_leaqa_set6_leaqa43',
                  'youthreport2_leaqa_set6_leaqa44','youthreport2_leaqa_set7_leaqa50','youthreport2_leaqa_set7_leaqa52' ,
                  'youthreport2_leaqa_set7_leaqa53']])/6

# Discrete-Ambiguous-Uncontrollable Life Events scales
    data['leq_c_dau']= sum_nonna(data[['youthreport2_leaq_set1_leaq1','youthreport2_leaq_set2_leaq12',
                  'youthreport2_leaq_set3_leaq17', 'youthreport2_leaq_set4_leaq31','youthreport2_leaqa_set4_f_leaqaf31',
                  'youthreport2_leaqa_set1_leaqa1', 'youthreport2_leaqa_set2_leaqa12','youthreport2_leaqa_set3_leaqa17',
		  'youthreport2_leaqa_set4_m_leaqam31']])/4

# average of 8 items common to both the adolescent (leaqa) and young adult (leaq)
#Discrete-Negative-Controllable Life Events scales
    data['leq_c_dnc'] = sum_nonna(data[['youthreport2_leaq_set2_leaq13', 'youthreport2_leaq_set4_leaq25',
                  'youthreport2_leaq_set4_leaq26','youthreport2_leaq_set4_leaq27','youthreport2_leaq_set4_leaq28',
                  'youthreport2_leaq_set7_leaq55','youthreport2_leaq_set8_leaq56', 'youthreport2_leaq_set8_leaq61',
                  'youthreport2_leaqa_set2_leaqa13', 'youthreport2_leaqa_set4_m_leaqam25', 'youthreport2_leaqa_set4_m_leaqam26', 
                  'youthreport2_leaqa_set4_m_leaqam27', 'youthreport2_leaqa_set4_m_leaqam28', 'youthreport2_leaqa_set7_leaqa55', 
                  'youthreport2_leaqa_set8_leaqa56', 'youthreport2_leaqa_set8_leaqa61',
                  'youthreport2_leaqa_set4_f_leaqaf25', 'youthreport2_leaqa_set4_f_leaqaf26', 
                  'youthreport2_leaqa_set4_f_leaqaf27', 'youthreport2_leaqa_set4_f_leaqaf28']])/8

# average of 5 items common to both the adolescent (leaqa) and young adult (leaq)
# Chronic-Negative-Controllable Life Events scales
    data['leq_c_cnc']= sum_nonna(data[['youthreport2_leaq_set5_leaq39','youthreport2_leaq_set5_leaq40',
		 'youthreport2_leaq_set6_leaq45', 'youthreport2_leaq_set6_leaq46',  'youthreport2_leaq_set7_leaq51',
                 'youthreport2_leaqa_set5_leaqa39','youthreport2_leaqa_set6_leaqa40','youthreport2_leaqa_set6_leaqa45', 
                 'youthreport2_leaqa_set6_leaqa46', 'youthreport2_leaqa_set7_leaqa51']])/5
                    

# average of 5 items common to both the adolescent (leaqa) and young adult (leaq)
# Discrete-Positive-Controllable Life Events scales
    data['leq_c_dpc'] = sum_nonna(data[['youthreport2_leaq_set3_leaq19', 'youthreport2_leaq_set3_leaq21',
                  'youthreport2_leaq_set3_leaq22','youthreport2_leaq_set4_leaq23','youthreport2_leaq_set4_leaq24',
                  'youthreport2_leaqa_set3_leaqa19', 'youthreport2_leaqa_set3_leaqa21', 'youthreport2_leaqa_set3_leaqa22', 
                  'youthreport2_leaqa_set3_leaqa23', 'youthreport2_leaqa_set3_leaqa24']])/5


# average of 22 items common to both adolescent (leaqa) and young adult (leaq) for
#  Negative Uncontrollable Life Events
    data['leq_c_nu'] = (16*data['leq_c_dnu'] + 6*data['leq_c_cnu'])/22

# average of 20 items common to both adolescent (leaqa) and young adult (leaq) for
#Discrete Negative and Ambiguous Uncontrollable Life Events
    data['leq_c_dcu'] = (16*data['leq_c_dnu'] + 4*data['leq_c_dau'])/20

# average of 26 items common to both adolescent (leaqa) and young adult (leaq)  for
#Negative and Ambiguous Uncontrollable Life Events
    data['leq_c_u'] = (16*data['leq_c_dnu']+ 4*data['leq_c_dau'] + 6*data['leq_c_cnu'])/26

# average of 13 items common to both adolescent (leaqa) and young adult (leaq)  for
# Negative Controllable Life Events
    data['leq_c_nc']= (8*data['leq_c_dnc'] + 5* data['leq_c_cnc'])/ 13
                             
# average of 39 items common to both adolescent (leaqa) and young adult (leaq)  for
#Negative and Ambiguous Life Events
    data['leq_c_c'] = (16*data['leq_c_dnu'] + 6*data['leq_c_cnu'] + 4*data['leq_c_dau']
                      + 8*data['leq_c_dnc'] + 5* data['leq_c_cnc'])/ 39

# average of 35 items common to both adolescent (leaqa) and young adult (leaq)  for Negative Life Events
    data['leq_c_sn'] = (16*data['leq_c_dnu'] + 6*data['leq_c_cnu'] 
                      + 8*data['leq_c_dnc'] + 5* data['leq_c_cnc'])/ 35
                                                      


    data['leq_complete'] = data['youth_report_2_complete'].map( int )

    # Return the computed scores - this is what will be imported back into REDCap
    outfield_list = [ 'leq_complete','leq_c_dnu','leq_c_cnu','leq_c_dau','leq_c_dnc','leq_c_cnc','leq_c_dpc','leq_c_nu',
		'leq_c_dcu','leq_c_u','leq_c_nc','leq_c_c','leq_c_sn']


    return data[ outfield_list ]

