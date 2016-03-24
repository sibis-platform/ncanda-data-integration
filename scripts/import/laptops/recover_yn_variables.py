#!/usr/bin/env python

##
##  Copyright 2015 SRI International
##  License: https://ncanda.sri.com/software-license.txt
##


import pandas

#
# Dictionary for FULL recovery (Y and N responses).
#
# Each dict entry is a dict of fields for a specific survey type (key is survey prefix).
#
# For each survey, the dict keys are the Y/N fields to be recovered. The dict values are vectors 
# of dependent fields. A missing Y/N field is set to "Y" if ANY of the dependent fields is set,
# and to "N" if none of them are set.
#
recovery_full_dict = dict()
recovery_full_dict['youthreport1'] = { "youthreport1_cddr1" : [ "youthreport1_cddr2" ],
                                       "youthreport1_cddr7a" : [ "youthreport1_cddr7" ],
                                       "youthreport1_cddr15a" : [ "youthreport1_cddr15" ],
                                       "youthreport1_cddr16a" : [ "youthreport1_cddr16" ],
                                       "youthreport1_cddr27" : [ "youthreport1_cddr28" ],
                                       "youthreport1_cddr32" : [ "youthreport1_cddr33" ],
                                       "youthreport1_cddr40" : [ "youthreport1_cddr40a" ],
                                       "youthreport1_cddr41" : [ "youthreport1_cddr41b" ],
                                       "youthreport1_cddr42" : [ "youthreport1_cddr42b" ],
                                       "youthreport1_cddr43" : [ "youthreport1_cddr43b" ],
                                       "youthreport1_cddr44" : [ "youthreport1_cddr44b" ],
                                       "youthreport1_cddr45" : [ "youthreport1_cddr45b" ],
                                       "youthreport1_cddr46" : [ "youthreport1_cddr46b" ],
                                       "youthreport1_cddr47" : [ "youthreport1_cddr47b" ],
                                       "youthreport1_cddr48" : [ "youthreport1_cddr48b" ],
                                       "youthreport1_cddr49" : [ "youthreport1_cddr49b" ],
                                       "youthreport1_cddr50" : [ "youthreport1_cddr50b" ],
                                       "youthreport1_cddr51" : [ "youthreport1_cddr51b" ],
                                       "youthreport1_cddr52a" : [ "youthreport1_cddr52" ],
                                       "youthreport1_cddr53a" : [ "youthreport1_cddr53" ],
                                       "youthreport1_cddr58a" : [ "youthreport1_cddr58" ],
                                       "youthreport1_cddr59a" : [ "youthreport1_cddr59" ],
                                       "youthreport1_cddr64a" : [ "youthreport1_cddr64" ],
                                       "youthreport1_cddr65a" : [ "youthreport1_cddr65" ],
                                       "youthreport1_cddr70a" : [ "youthreport1_cddr71" ],
                                       "youthreport1_cddr72a" : [ "youthreport1_cddr72" ],
                                       "youthreport1_cddr77a" : [ "youthreport1_cddr77" ],
                                       "youthreport1_cddr78a" : [ "youthreport1_cddr78" ],
                                       "youthreport1_cddr83a" : [ "youthreport1_cddr83" ],
                                       "youthreport1_cddr84a" : [ "youthreport1_cddr84" ],
                                       "youthreport1_cddr89a" : [ "youthreport1_cddr89" ],
                                       "youthreport1_cddr90a" : [ "youthreport1_cddr90" ],
                                       "youthreport1_cddr95a" : [ "youthreport1_cddr95" ],
                                       "youthreport1_cddr96a" : [ "youthreport1_cddr96" ],
                                       "youthreport1_cddr101a" : [ "youthreport1_cddr101" ],
                                       "youthreport1_cddr102a" : [ "youthreport1_cddr102" ],
                                       "youthreport1_cddr107a" : [ "youthreport1_cddr107" ],
                                       "youthreport1_cddr108a" : [ "youthreport1_cddr108" ],
                                       "youthreport1_cddr113a" : [ "youthreport1_cddr113" ],
                                       "youthreport1_cddr114a" : [ "youthreport1_cddr114" ],
                                       "youthreport1_cddr119a" : [ "youthreport1_cddr119" ],
                                       "youthreport1_cddr120a" : [ "youthreport1_cddr120" ],
                                       "youthreport1_cddr125a" : [ "youthreport1_cddr125" ],
                                       "youthreport1_cddr126a" : [ "youthreport1_cddr126" ],
                                       "youthreport1_cddr131a" : [ "youthreport1_cddr132" ],
                                       "youthreport1_cddr131" : [ "youthreport1_cddr132" ],
                                       "youthreport1_cddr133" : [ "youthreport1_cddr134a" ],
                                       "youthreport1_cddr145a" : [ "youthreport1_cddr145" ],
                                       "youthreport1_cddr147a" : [ "youthreport1_cddr147" ],
                                       "youthreport1_cddr149a" : [ "youthreport1_cddr149" ],
                                       "youthreport1_cddr150" : [ "youthreport1_cddr150b" ],
                                       "youthreport1_cddr151" : [ "youthreport1_cddr151b" ],
                                       "youthreport1_cddr152" : [ "youthreport1_cddr152b" ],
                                       "youthreport1_cddr153" : [ "youthreport1_cddr153b" ],
                                       "youthreport1_cddr154" : [ "youthreport1_cddr154b" ],
                                       "youthreport1_cddr155" : [ "youthreport1_cddr155b" ],
                                       "youthreport1_cddr156" : [ "youthreport1_cddr156b" ],
                                       "youthreport1_cddr157" : [ "youthreport1_cddr157b" ],
                                       "youthreport1_cddr158" : [ "youthreport1_cddr158b" ],
                                       "youthreport1_cddr159" : [ "youthreport1_cddr159b" ],
                                       "youthreport1_cddr160" : [ "youthreport1_cddr160b" ],
                                       "youthreport1_cddr161" : [ "youthreport1_cddr161b" ],
                                       "youthreport1_cddr162" : [ "youthreport1_cddr162b" ],
                                       "youthreport1_cddr163" : [ "youthreport1_cddr163b" ],
                                       "youthreport1_cddr164" : [ "youthreport1_cddr164b" ],
                                       "youthreport1_cddr165" : [ "youthreport1_cddr165b" ],
                                       "youthreport1_cddr166" : [ "youthreport1_cddr166b" ],
                                       "youthreport1_cddr167" : [ "youthreport1_cddr167b" ],
                                       "youthreport1_cddr168" : [ "youthreport1_cddr168b" ],
                                       "youthreport1_cddr169" : [ "youthreport1_cddr169b" ],
                                       "youthreport1_cddr170" : [ "youthreport1_cddr170b" ],
                                       "youthreport1_cddr171" : [ "youthreport1_cddr171b" ],
                                       "youthreport1_cddr172" : [ "youthreport1_cddr172b" ],
                                       "youthreport1_cddr173" : [ "youthreport1_cddr173b" ],
                                       "youthreport1_cddr174" : [ "youthreport1_cddr174b" ],
                                       "youthreport1_cddr175" : [ "youthreport1_cddr175b" ],
                                       "youthreport1_cddr176" : [ "youthreport1_cddr176b" ],
                                       "youthreport1_cddr177" : [ "youthreport1_cddr177b" ],
                                       "youthreport1_tbiloc1" : [ "youthreport1_tbiloctime1" ],
                                       "youthreport1_tbiloc2" : [ "youthreport1_tbiloctime2" ],
                                       "youthreport1_tbiloc3" : [ "youthreport1_tbiloctime3" ],
                                       "youthreport1_tbiloc4" : [ "youthreport1_tbiloctime4" ],
                                       "youthreport1_tbiloc5" : [ "youthreport1_tbiloctime5" ],
                                       "youthreport1_tbiloc6" : [ "youthreport1_tbiloctime6" ],
                                       "youthreport1_tbiloc7" : [ "youthreport1_tbiloctime7" ],
                                       "youthreport1_tbiloc8" : [ "youthreport1_tbiloctime8" ],
                                       "youthreport1_tbiloc9" : [ "youthreport1_tbiloctime9" ],
                                       "youthreport1_yfhi3" : [ "youthreport1_yfhi3a_yfhi3a" ],
                                       "youthreport1_yfhi4" : [ "youthreport1_yfhi4a_yfhi4a" ] }

#
# Dictionary for PARTIAL recovery (Y responses only).
#
# Each dict entry is a dict of fields for a specific survey type (key is survey prefix).
#
# For each survey, the dict keys are the Y/N fields to be recovered. The dict values are vectors 
# of dependent fields. A missing Y/N field is set to "Y" if ANY of the dependent fields is set.
# If all dependent fields are missing, the missing Y/N field is kept missing, because the dependent
# items were not mandatory.
#
recovery_yesonly_dict = dict()
recovery_yesonly_dict['youthreport1'] = { "youthreport1_tbimore" : [ "youthreport1_tbimorenum" ],
                                          "youthreport1_tbi7" : [ "youthreport1_tbi7ab_tbi7a", "youthreport1_tbi7ab_tbi7a" ],
                                          "youthreport1_1yei13" : [ "youthreport1_1yei13b" ],
                                          "youthreport1_ydi5" : [ "youthreport1_ydi5b" ],
                                          "youthreport1_yfhi5" : [ "youthreport1_yfhi5a" ],
                                          "youthreport1_ses3a" : [ "youthreport1_ses3b" ] }
# Apply yes-only recovery
def recover_full( row, recovery_dict ):
    for field in row.index:
        if field in recovery_dict.keys():
            for dep in recovery_dict[field]:
                if str(row[dep]) != 'nan':
                    row[field] = 'Y'
    return row

# Apply full recovery
def recover_full( row, recovery_dict ):
    for field in row.index:
        if field in recovery_dict.keys():
            row[field] = 'N' # This is the only difference to yes-only recovery: if non of the dependent fields are set, this gets a 'N'
            for dep in recovery_dict[field]:
                if str(row[dep]) != 'nan':
                    row[field] = 'Y'
    return row


# Recover Y/N responses
def recover( row, form_prefix ):
    if form_prefix in recovery_full_dict.keys():
        row = recover_full( row, recovery_full_dict[form_prefix] )
    if form_prefix in recovery_yesonly_dict.keys():
        row = recover_full( row, recovery_yesonly_dict[form_prefix] )
    return row
