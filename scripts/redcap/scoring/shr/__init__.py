#!/usr/bin/env python
 
##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##

#
# Variables from surveys needed for ssaga_highrisk
#
import numpy as np
import pandas
import string
 

input_fields = { 'ssaga_youth' : ['ssaga_youth_as2b','ssaga_youth_as2a','ssaga_youth_as6b','ssaga_youth_as9','ssaga_youth_as11',
            'ssaga_youth_as14','ssaga_youth_as14b','ssaga_youth_as15','ssaga_youth_as16','ssaga_youth_as17a','ssaga_youth_as18b',
            'ssaga_youth_as19,','ssaga_youth_as20','ssaga_youth_as1_ao15','ssaga_youth_as1_ao16,','ssaga_youth_as1_ao17',
            'ssaga_youth_as1_ao18','ssaga_youth_as1_ao19','ssaga_youth_as1_ao20','ssaga_youth_as2_ao15','ssaga_youth_as2_ao16',
            'ssaga_youth_as2_ao17','ssaga_youth_as2_ao18','ssaga_youth_as2_ao19','ssaga_youth_as2_ao20','ssaga_youth_asa1_ao14',
            'ssaga_youth_asa2_ao14','ssaga_youth_asa_ao2','ssaga_youth_as_ao10','ssaga_youth_as_ao9,','ssaga_youth_asb_ao2,',
            'ssaga_youth_asc1_ao14,','ssaga_youth_asc1_ao6,','ssaga_youth_asc2_ao14',
            'ssaga_youth_asc2_ao6', 'ssaga_youth_as10a','ssaga_youth_asd4asx_cleanordirty',
            'ssaga_youth_asd4csx_cleanordirty','ssaga_youth_complete', 'ssaga_youth_missing'],

            'ssaga_parent' : ['ssaga_parent_as2b','ssaga_parent_as2a','ssaga_parent_as6b,','ssaga_parent_as9',
            'ssaga_parent_as11','ssaga_parent_as14,','ssaga_parent_as14b','ssaga_parent_as15','ssaga_parent_as16',
            'ssaga_parent_as17a,','ssaga_parent_as18b,','ssaga_parent_as19','ssaga_parent_as20','ssaga_parent_as1_ao15',
            'ssaga_parent_as1_ao16','ssaga_parent_as1_ao17','ssaga_parent_as1_ao18','ssaga_parent_as1_ao19',
            'ssaga_parent_as1_ao20','ssaga_parent_as2_ao15','ssaga_parent_as2_ao16','ssaga_parent_as2_ao17',
            'ssaga_parent_as2_ao18','ssaga_parent_as2_ao19','ssaga_parent_as2_ao20','ssaga_parent_asa1_ao14',
            'ssaga_parent_asa2_ao14','ssaga_parent_asa_ao2','ssaga_parent_as_ao10','ssaga_parent_as_ao9','ssaga_parent_asb_ao2',
            'ssaga_parent_asc1_ao14','ssaga_parent_asc1_ao6','ssaga_parent_asc2_ao14','ssaga_parent_asc2_ao6',
            'ssaga_parent_as10a','ssaga_parent_complete', 'ssaga_parent_missing'],

            'lssaga3_youth': ['lssaga3_youth_as2b','lssaga3_youth_as2a','lssaga3_youth_as6b','lssaga3_youth_as9','lssaga3_youth_as11',
            'lssaga3_youth_as14','lssaga3_youth_as14b','lssaga3_youth_as15','lssaga3_youth_as16','lssaga3_youth_as17a',
            'lssaga3_youth_as18b','lssaga3_youth_as19','lssaga3_youth_as20','lssaga3_youth_as1_ao15','lssaga3_youth_as1_ao16',
            'lssaga3_youth_as1_ao17','lssaga3_youth_as1_ao18','lssaga3_youth_as1_ao19','lssaga3_youth_as1_ao20',
            'lssaga3_youth_as2_ao15','lssaga3_youth_as2_ao16','lssaga3_youth_as2_ao17','lssaga3_youth_as2_ao18',
            'lssaga3_youth_as2_ao19','lssaga3_youth_as2_ao20','lssaga3_youth_asa1_ao14','lssaga3_youth_asa2_ao14',
            'lssaga3_youth_asa_ao2','lssaga3_youth_as_ao10','lssaga3_youth_as_ao9','lssaga3_youth_asb_ao2',
            'lssaga3_youth_asc1_ao14','lssaga3_youth_asc1_ao6','lssaga3_youth_asc2_ao14','lssaga3_youth_asc2_ao6',
            'lssaga3_youth_as10a','limesurvey_ssaga_youth_complete', 'lssaga3_youth_missing'],

            'lssaga3_parent' : ['lssaga3_parent_as2b','lssaga3_parent_as2a','lssaga3_parent_as6b','lssaga3_parent_as9',
            'lssaga3_parent_as11','lssaga3_parent_as14','lssaga3_parent_as14b','lssaga3_parent_as15','lssaga3_parent_as16',
            'lssaga3_parent_as17a','lssaga3_parent_as18b','lssaga3_parent_as19','lssaga3_parent_as20','lssaga3_parent_as1_ao15',
            'lssaga3_parent_as1_ao16','lssaga3_parent_as1_ao17','lssaga3_parent_as1_ao18','lssaga3_parent_as1_ao19',
            'lssaga3_parent_as1_ao20','lssaga3_parent_as2_ao15','lssaga3_parent_as2_ao16','lssaga3_parent_as2_ao17',
            'lssaga3_parent_as2_ao18','lssaga3_parent_as2_ao19','lssaga3_parent_as2_ao20','lssaga3_parent_asa1_ao14',
             'lssaga3_parent_asa2_ao14','lssaga3_parent_asa_ao2','lssaga3_parent_as_ao10','lssaga3_parent_as_ao9',
            'lssaga3_parent_asb_ao2','lssaga3_parent_asc1_ao14','lssaga3_parent_asc1_ao6','lssaga3_parent_asc2_ao14',
            'lssaga3_parent_asc2_ao6','lssaga3_parent_as10a','limesurvey_ssaga_parent_complete', 'lssaga3_parent_missing'],

            'youthreport1' : ['youthreport1_cddr16', 'youth_report_1_complete', 'youthreport1_missing']}
 
# name list
##var_list=['as2b','as2a','as6b','as9','as11','as14','as14b','as15','as16','as17a','as18b','as19','as20','as1_ao15','as1_ao16',
##          'as1_ao17','as1_ao18','as1_ao19','as1_ao20','as2_ao15','as2_ao16','as2_ao17','as2_ao18','as2_ao19','as2_ao20',
##          'asa1_ao14','asa2_ao14','asa_ao2','as_ao10','as_ao9','asb_ao2','asc1_ao14','asc1_ao6','asc2_ao14','asc2_ao6',
##          'complete','missing']

var_list=['ssaga_youth_as2b','ssaga_youth_as2a','ssaga_youth_as6b',
                  'ssaga_youth_as9','ssaga_youth_as11','ssaga_youth_as14','ssaga_youth_as14b','ssaga_youth_as15',
                   'ssaga_youth_as16',
                  'ssaga_youth_as17a','ssaga_youth_as18b','ssaga_youth_as19','ssaga_youth_as20','lssaga3_youth_as2b',
                  'lssaga3_youth_as2a','lssaga3_youth_as6b','lssaga3_youth_as9','lssaga3_youth_as11','lssaga3_youth_as14',
                  'lssaga3_youth_as14b','lssaga3_youth_as15','lssaga3_youth_as16','lssaga3_youth_as17a','lssaga3_youth_as18b',
                  'lssaga3_youth_as19','lssaga3_youth_as20']

# This determines the name of the form in REDCap where the results are posted.
#
output_form = 'clinical'
outfield_list =['ssaga_highrisk_complete','ssaga_youth_externalizing','ssaga_parent_externalizing','ssaga_youth_assx_minage',
	'ssaga_parent_assx_minage','ssaga_cdsx_onset','highrisk_ssaga_extern_tot','highrisk_blaise_extern']

# this is to sum up all non-na in a row
def sum_nonna(data):    
   results = data.sum(axis=1,numeric_only=None)
   return results

def max_nonna(data):    
   results = data.max(axis=1,numeric_only=True)
   return results

# Safe conversion of string to float
#
def safe_float( strng ):
    if strng == '' or str( strng ) == 'nan':
        return 0
    try:
        return float( strng )
    except:
        return 0


#

def compute( record ):    
#ssaga_youth_externalizing##
   ssaga_youth_externalizing  = 0
   
   if (((record['ssaga_youth_complete'] > 0) and ( record['ssaga_youth_missing'] != '1'))
 	 or ((record['limesurvey_ssaga_youth_complete'] > 0) and ( record['lssaga3_youth_missing'] != '1'))):
      #record['ssaga_highrisk_complete']= int(record['ssaga_youth_complete'])
      #if (record['limesurvey_ssaga_youth_complete'] >0): 
	#record['ssaga_highrisk_complete']= int(record['limesurvey_ssaga_youth_complete']) 
      for f in ['ssaga_youth_as2b','ssaga_youth_as2a','ssaga_youth_as6b','ssaga_youth_as9','ssaga_youth_as11',
		'ssaga_youth_as14','ssaga_youth_as14b','ssaga_youth_as15','ssaga_youth_as16','ssaga_youth_as17a','ssaga_youth_as18b',
                'ssaga_youth_as19','ssaga_youth_as20','lssaga3_youth_as2b','lssaga3_youth_as2a','lssaga3_youth_as6b',
		'lssaga3_youth_as9','lssaga3_youth_as11','lssaga3_youth_as14','lssaga3_youth_as14b','lssaga3_youth_as15',
                'lssaga3_youth_as16','lssaga3_youth_as17a','lssaga3_youth_as18b','lssaga3_youth_as19','lssaga3_youth_as20']:
         if record[f] == 5:
            ssaga_youth_externalizing += 1
      if safe_float(record['ssaga_youth_as10a']) > 0 or safe_float(record['lssaga3_youth_as10a']) > 0:
         ssaga_youth_externalizing += 1
   if ssaga_youth_externalizing ==0:
      ssaga_youth_externalizing = None
   record['ssaga_youth_externalizing'] = ssaga_youth_externalizing

###ssaga_parent_externalizing##
   ssaga_parent_externalizing  = 0
   
   if (((record['ssaga_parent_complete'] > 0) and ( record['ssaga_parent_missing'] != '1'))
 	 or ((record['limesurvey_ssaga_parent_complete'] > 0) and ( record['lssaga3_parent_missing'] != '1'))):
      #if safe_float(record['ssaga_highrisk_complete']) < record['ssaga_parent_complete']:
	#record['ssaga_highrisk_complete']= int(record['ssaga_parent_complete'])
      #if safe_float(record['ssaga_highrisk_complete']) < record['limesurvey_ssaga_parent_complete']:
	#record['ssaga_highrisk_complete']= int(record['limesurvey_ssaga_parent_complete'])
      for f in ['ssaga_parent_as2b','ssaga_parent_as2a','ssaga_parent_as6b','ssaga_parent_as9','ssaga_parent_as11',
		'ssaga_parent_as14','ssaga_parent_as14b','ssaga_parent_as15','ssaga_parent_as16','ssaga_parent_as17a','ssaga_parent_as18b',
               'ssaga_parent_as19','ssaga_parent_as20','lssaga3_parent_as2b','lssaga3_parent_as2a','lssaga3_parent_as6b',
		'lssaga3_parent_as9','lssaga3_parent_as11','lssaga3_parent_as14','lssaga3_parent_as14b','lssaga3_parent_as15',
               'lssaga3_parent_as16','lssaga3_parent_as17a','lssaga3_parent_as18b','lssaga3_parent_as19','lssaga3_parent_as20']:
         if record[f] == 5:
            ssaga_parent_externalizing += 1
      if safe_float(record['ssaga_parent_as10a']) > 0 or safe_float(record['lssaga3_parent_as10a']) > 0:
         ssaga_parent_externalizing += 1
   if ssaga_parent_externalizing ==0:
        ssaga_parent_externalizing = None
   record['ssaga_parent_externalizing'] = ssaga_parent_externalizing
##
##
### ssaga_youth_assx_minage
###Compute minimum age of onset for endorsement of conduct disorder symptoms
   ssaga_youth_assx_minage  = 999
   
   if (((record['ssaga_youth_complete'] > 0) and ( record['ssaga_youth_missing'] != '1'))
 	 or ((record['limesurvey_ssaga_youth_complete'] > 0) and ( record['lssaga3_youth_missing'] != '1'))):      
      for f in ["ssaga_youth_as1_ao15", "ssaga_youth_as1_ao16", "ssaga_youth_as1_ao17",
             "ssaga_youth_as1_ao18", "ssaga_youth_as1_ao19", "ssaga_youth_as1_ao20",
             "ssaga_youth_as2_ao15", "ssaga_youth_as2_ao16", "ssaga_youth_as2_ao17",
            "ssaga_youth_as2_ao18", "ssaga_youth_as2_ao19", "ssaga_youth_as2_ao20",
             "ssaga_youth_asa1_ao14", "ssaga_youth_asa2_ao14", "ssaga_youth_asa_ao2",
             "ssaga_youth_as_ao10", "ssaga_youth_as_ao9", "ssaga_youth_asb_ao2",
             "ssaga_youth_asc1_ao14", "ssaga_youth_asc1_ao6",
             "ssaga_youth_asc2_ao14", "ssaga_youth_asc2_ao6","lssaga3_youth_as1_ao15", "lssaga3_youth_as1_ao16", 			"lssaga3_youth_as1_ao17",
             "lssaga3_youth_as1_ao18", "lssaga3_youth_as1_ao19", "lssaga3_youth_as1_ao20",
             "lssaga3_youth_as2_ao15", "lssaga3_youth_as2_ao16", "lssaga3_youth_as2_ao17",
             "lssaga3_youth_as2_ao18", "lssaga3_youth_as2_ao19", "lssaga3_youth_as2_ao20",
             "lssaga3_youth_asa1_ao14", "lssaga3_youth_asa2_ao14", "lssaga3_youth_asa_ao2",
             "lssaga3_youth_as_ao10", "lssaga3_youth_as_ao9", "lssaga3_youth_asb_ao2",
             "lssaga3_youth_asc1_ao14", "lssaga3_youth_asc1_ao6",
             "lssaga3_youth_asc2_ao14", "lssaga3_youth_asc2_ao6"]:
         if record[f] < ssaga_youth_assx_minage:
            ssaga_youth_assx_minage = record[f]
   if ssaga_youth_assx_minage == 999:
      ssaga_youth_assx_minage = None
   record['ssaga_youth_assx_minage'] = ssaga_youth_assx_minage
##
##
### ssaga_parent_assx_minage
###Compute minimum age of onset for endorsement of conduct disorder symptoms
   ssaga_parent_assx_minage  = 999
  
   if (((record['ssaga_parent_complete'] > 0) and ( record['ssaga_parent_missing'] != '1'))
 	 or ((record['limesurvey_ssaga_parent_complete'] > 0) and ( record['lssaga3_parent_missing'] != '1'))):      
       for f in ["ssaga_parent_as1_ao15", "ssaga_parent_as1_ao16", "ssaga_parent_as1_ao17",
             "ssaga_parent_as1_ao18", "ssaga_parent_as1_ao19", "ssaga_parent_as1_ao20",
             "ssaga_parent_as2_ao15", "ssaga_parent_as2_ao16", "ssaga_parent_as2_ao17",
             "ssaga_parent_as2_ao18", "ssaga_parent_as2_ao19", "ssaga_parent_as2_ao20",
             "ssaga_parent_asa1_ao14", "ssaga_parent_asa2_ao14", "ssaga_parent_asa_ao2",
             "ssaga_parent_as_ao10", "ssaga_parent_as_ao9", "ssaga_parent_asb_ao2",
             "ssaga_parent_asc1_ao14", "ssaga_parent_asc1_ao6",
             "ssaga_parent_asc2_ao14", "ssaga_parent_asc2_ao6","lssaga3_parent_as1_ao15", "lssaga3_parent_as1_ao16", 		 			"lssaga3_parent_as1_ao17",
             "lssaga3_parent_as1_ao18", "lssaga3_parent_as1_ao19", "lssaga3_parent_as1_ao20",
             "lssaga3_parent_as2_ao15", "lssaga3_parent_as2_ao16", "lssaga3_parent_as2_ao17",
             "lssaga3_parent_as2_ao18", "lssaga3_parent_as2_ao19", "lssaga3_parent_as2_ao20",
             "lssaga3_parent_asa1_ao14", "lssaga3_parent_asa2_ao14", "lssaga3_parent_asa_ao2",
             "lssaga3_parent_as_ao10", "lssaga3_parent_as_ao9", "lssaga3_parent_asb_ao2",
             "lssaga3_parent_asc1_ao14", "lssaga3_parent_asc1_ao6",
             "lssaga3_parent_asc2_ao14", "lssaga3_parent_asc2_ao6"]:
         if record[f] < ssaga_parent_assx_minage:
            ssaga_parent_assx_minage = record[f]
   if ssaga_parent_assx_minage == 999:
       ssaga_parent_assx_minage = None
   record['ssaga_parent_assx_minage'] = ssaga_parent_assx_minage


  
## #ssaga_cdsx_onset
###Create a variable that indicated whether onset of Conduct Disorder symptoms occurred BEFORE onset of regular drinking
###0 - NEGATIVE; 1- POSITIVE
##   
   ssaga_cdsx_onset = None
   if safe_float(record['youthreport1_cddr16']) >0 :
	if (safe_float(record['ssaga_parent_assx_minage']) < safe_float(record['youthreport1_cddr16']) or 
	safe_float(record['ssaga_youth_assx_minage']) < safe_float(record['youthreport1_cddr16'])):
      		ssaga_cdsx_onset = 1
        else:
                ssaga_cdsx_onset = 0
        if (safe_float(record['ssaga_parent_assx_minage']) > safe_float(record['youthreport1_cddr16']) and 
	safe_float(record['ssaga_youth_assx_minage']) ==0) :
                ssaga_cdsx_onset = 0
        if (safe_float(record['ssaga_youth_assx_minage']) > safe_float(record['youthreport1_cddr16']) and 
	safe_float(record['ssaga_parent_assx_minage']) ==0) :
                ssaga_cdsx_onset = 0
   else:
       if (safe_float(record['ssaga_parent_assx_minage']) > 0 or safe_float(record['ssaga_youth_assx_minage'])) >0:
      		ssaga_cdsx_onset = 1
       else:
                ssaga_cdsx_onset = 0

  # if safe_float(record['youthreport1_cddr16']) ==0 and record['ssaga_youth_assx_minage'] >0:
  #    ssaga_cdsx_onset = 1
  # if safe_float(record['youthreport1_cddr16']) ==0 and record['ssaga_parent_assx_minage'] >0:
  #    ssaga_cdsx_onset = 1
   if safe_float(record['ssaga_parent_assx_minage']) ==0 and safe_float(record['ssaga_youth_assx_minage']) ==0:
      ssaga_cdsx_onset = None
 
   record['ssaga_cdsx_onset'] = ssaga_cdsx_onset
##
###Create 'highrisk_ssaga_extern_tot', 'One or more externalizing symptoms endorsed on parent or teen SSAGA'
###0='No'; 1='Yes'
   highrisk_ssaga_extern_tot = None
   if record['ssaga_youth_externalizing'] >= 1 or record['ssaga_parent_externalizing'] >=1 :
      highrisk_ssaga_extern_tot = 1
   if record['ssaga_youth_externalizing'] == 0 and record['ssaga_parent_externalizing'] ==0 :
      highrisk_ssaga_extern_tot = 0
   record['highrisk_ssaga_extern_tot']= highrisk_ssaga_extern_tot
##
##############################################
###Create 'highrisk_blaise_extern' - 'Age of >endorsement of Externalizing Symptoms on SSAGA prior to regular drinking using Blaise Count variables'
###Compute a High Risk variable if onset of CD symptoms were prior to onset of regular drinking and participant endorsed 1 or more symptoms**.
###This will be more conservative than the 'ssaga_cdsx_onset' because it required endorsement of more severe symptoms**.
###But this variable uses only the youth report SSAGA, NOT the parent SSAGA
   highrisk_blaise_extern = None
   #if record['ssaga_cdsx_onset'] ==1 and safe_float(record['ssaga_youth_asd4asx_cleanordirty']) >0 :
   #   highrisk_blaise_extern = 1
   #else:
   #   highrisk_blaise_extern = 0	
   #if record['ssaga_cdsx_onset'] ==1 and safe_float(record['ssaga_youth_asd4csx_cleanordirty']) >0 :   
   #  highrisk_blaise_extern = 1
   #else:
   #   highrisk_blaise_extern = 0
   if safe_float(record['ssaga_cdsx_onset']) ==0:
      highrisk_blaise_extern = 0
      if record['ssaga_cdsx_onset'] == None or str(record['ssaga_cdsx_onset'])  == 'nan':
         highrisk_blaise_extern = None
   else:
      highrisk_blaise_extern = 0
      if (safe_float(record['ssaga_youth_asd4asx_cleanordirty']) >=1 or safe_float(record['ssaga_youth_asd4csx_cleanordirty']) >=1):
         highrisk_blaise_extern = 1

   record['highrisk_blaise_extern']= highrisk_blaise_extern


   #print record['youthreport1_cddr16']
   #record['aaa']=record['youthreport1_cddr16']
   record['ssaga_highrisk_complete'] = '1'
   return record[ outfield_list ]

   


def compute_scores( data, demographics ):
    for f in outfield_list:
        data[f] = ''

    # Do computations, return result
    results = data.apply( compute, axis=1 )
    results.index = pandas.MultiIndex.from_tuples( results.index )
    return results

