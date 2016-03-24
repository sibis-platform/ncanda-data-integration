#!/usr/bin/env python
#!/usr/bin/env python

##
##  Copyright 2016 SRI International
##  See COPYING file distributed along with the package for the copyright and license terms.
####  $Revision: 2110 $
##  $LastChangedBy: nicholsn $
##  $LastChangedDate: 2015-08-07 09:10:29 -0700 (Fri, 07 Aug 2015) $
##
"""
Scan Report Comment Search
======================
This code searches through comments to find those with No MRI. In addition, a list of subjects that were skipped is also generated.

"""

#import needed libraries
import time
start = time.time()
import pandas as pd
import re
import csv

execfile('./visit_years_y1_y2.py')

#import year1 and year2 csv file
today=time.strftime("%m%d%Y")
myfile_name='./yr1_yr2_scannotes_'+today+'.csv'
y1_y2 = pd.read_csv(myfile_name)

#ID for ignored Subjects
year1_ignore = []
year2_ignore = []

i = 0
while i < (len(y1_y2)):
    if y1_y2['Year1_ignore'][i] == 1:
        year1_ignore.append(y1_y2['study_id'][i])
    if y1_y2['Year2_ignore'][i] == 1:
        year2_ignore.append(y1_y2['study_id'][i])
    i += 1

#ID for no MRI subject
year1_noscan = []
year2_noscan = []

i = 0
while i < (len(y1_y2)):
    if type(y1_y2['Year1_notes'][i]) == type('str'):
        if re.match(".*no mri", y1_y2['Year1_notes'][i].lower()) != None:
            year1_noscan.append(y1_y2['study_id'][i])
    if type(y1_y2['Year2_notes'][i]) == type('str'):
        if re.match(".*no mri", y1_y2['Year2_notes'][i].lower()) != None:
            year2_noscan.append(y1_y2['study_id'][i])
    i += 1

#write files to name
f = open("./Year1_ignore.txt", "w")
f.write("\n".join(map(lambda x: str(x), year1_ignore)))

f.close()

f = open("./Year2_ignore.txt", "w")
f.write("\n".join(map(lambda x: str(x), year2_ignore)))
f.close()

f = open("./Year1_NoScan.txt", "w")
f.write("\n".join(map(lambda x: str(x), year1_noscan)))

f.close()

f = open("./Year2_NoScan.txt", "w")
f.write("\n".join(map(lambda x: str(x), year2_noscan)))
f.close()

elapsed = (time.time() - start)
print elapsed