import time
start = time.time()
import redcap
import array
import string
import csv
import numpy
import sys
import glob
from datetime import datetime
import numpy
from numpy import genfromtxt
import numpy as np
import pandas
from pandas import DataFrame


api_url='https://ncanda.sri.com/redcap/api/'
api_key_entry='Token'
project_entry = redcap.Project(api_url, api_key_entry)

colnames2score=list()
namelist=['1_asr01','1_asr02','1_asr03','1_asr04','1_asr05','1_asr06','1_asr07','2_asr08','2_asr09','2_asr10','2_asr11','2_asr12','2_asr13',
          '2_asr14','3_asr15','3_asr16','3_asr17','3_asr18','3_asr19','3_asr20','3_asr21','4_asr22','4_asr23','4_asr24','4_asr25','4_asr26',
          '4_asr27','4_asr28','5_asr29','5_asr30','5_asr31','5_asr32','5_asr33','5_asr34','5_asr35','6_asr36','6_asr37','6_asr38','6_asr39',
          '6_asr40','6_asr41','6_asr42','7_asr43','7_asr44','7_asr45','7_asr46','7_asr47','7_asr48','7_asr49','8_asr50','8_asr51','8_asr52',
          '8_asr53','8_asr54','8_asr55','9_asr56a','9_asr56b','9_asr56c','9_asr56d','9_asr56e','9_asr56f','9_asr56g','9_asr56h','9_asr56i',
          '10_asr57','10_asr58','10_asr59','10_asr60','10_asr61','10_asr62','10_asr63','11_asr64','11_asr65','11_asr66','11_asr67','11_asr68',
          '11_asr69','11_asr70','12_asr71','12_asr72','12_asr73','12_asr74','12_asr75','12_asr76','12_asr77','13_asr78','13_asr79','13_asr80',
          '13_asr81','13_asr82','13_asr83','13_asr84','14_asr85','14_asr86','14_asr87','14_asr88','14_asr89','14_asr90','14_asr91','15_asr92',
          '15_asr93','15_asr94','15_asr95','15_asr96','15_asr97','15_asr98','16_asr99','16_as100','16_as101','16_as102','16_as103','16_as104',
          '16_as105','17_asr106','17_asr107','17_asr108','17_asr109','17_asr110','17_asr111','17_asr112','18_asr113','18_asr114','18_asr115',
          '18_asr116','18_asr117','18_asr118','18_asr119','19_asr120','19_asr121','19_asr122','19_asr123']



for i in namelist:
    colnames2score.append('youthreport1_asr_section'+str(i))
colnames_score=['study_id','redcap_event_name','redcap_data_access_group','dob','sex','age','mri_xnat_sid']+colnames2score
data_entry_raw= DataFrame(project_entry.export_records(fields=colnames_score))
data_entry_raw['age']=data_entry_raw['age'].astype(str)
data2score=data_entry_raw[(data_entry_raw["youthreport1_asr_section19_asr123"]!="")]
data2score=data2score[(data2score["age"]!="")]
data2score=data2score.loc[::,]
print data2score.shape
# # of subjects to be scored
subject_count=data2score.shape[0]


today=time.strftime("%m%d%Y")
myfile_name='asr_reformate_'+today+'.csv'

header_name=["admver","datatype","subjectno","id","firstname","middlename","lastname","othername","gender","dob",
             "ethniccode","formver","dataver","formno","formid","type","enterdate","dfo","age","agemonths",
             "educcode","fobcode","fobgender","fparentses","fsubjses","fspouseses","agencycode","clincode",
             "bpitems","compitems","afitems","otheritems","experience","scafitems","facilityco","numchild",
             "hours","months","schoolname","schoolcode","tobacco","drunk","drugs","drinks","ctimecode","ctypecode",
             "early","weeksearly","weight","lb_gram","ounces","infections","nonenglish","slowtalk","worried",
             "spontan","combines","mlp","words162","words310","otherwords","totwords","origin","fudefcode1",
             "fudefcode2","sudefcode1","interviewr","rater","fstatus","usertext","sparentses","ssubjses","cas",
             "casfsscr","das","dasgcascr","kabc","kabcmpcscr","sb5","sb5fsiqscr","wj3cog","wj3cogscr","wais3",
             "wais3scr","wisc4","wisc4scr","wppsi3","wppsi3scr","other1test","othtst1scr","other2test","othtst2scr",
             "other3test","othtst3scr","other1name","other2name","other3name","obstime","rptgrd","medic","medicdesc",
             "dsmcrit","dsmcode1","dsmdiag1","dsmcode2","dsmdiag2","dsmcode3","dsmdiag3","dsmcode4","dsmdiag4",
             "dsmcode5","dsmdiag5","dsmcode6","dsmdiag6","illness","illdesc","speced","sped1","sped2","sped3",
             "sped4","sped5","sped6","sped7","sped8","sped9","sped10","sped10a","sped10b","sped10c","admcatlg",
             "society","cethnic","ceduc","cfob","cagency","cclin","cintervr","crater","cfacilit","ctime","ctype",
             "cschool","cfudef1","cfudef2","csudef1"]


print "Please to remember to fill in the cut off date"
cut_off_date=datetime.strptime('2014-11-20 12:57:42', "%Y-%m-%d %H:%M:%S")
asr_reformat=DataFrame(columns=header_name)
#ysr_reformat["subjectno"]=range(1,subject_count+1)
asr_reformat["subjectno"]=range(subject_count)
asr_reformat["admver"]=9.1
asr_reformat["datatype"]="raw"
asr_reformat["age"]=data2score["age"].tolist()
asr_reformat["firstname"]=data2score["study_id"].values
asr_reformat["middlename"]=data2score["mri_xnat_sid"].values
asr_reformat["lastname"]=data2score["redcap_event_name"].values
asr_reformat["dob"]=data2score["dob"].values
asr_reformat["dfo"]="//"
asr_reformat["formver"]="2003"
asr_reformat["dataver"]="2003"
asr_reformat["formno"]="9"
asr_reformat["formid"]="9"
asr_reformat["type"]="ASR"
asr_reformat["enterdate"]=time.strftime("%m/%d/%Y")
asr_reformat["compitems"]="'999999999999999999999999999999999999"
asr_reformat["bpitems"]="'"

for i in range(subject_count):
#for i in range(20):    
    asr_reformat["gender"][i]=asr_reformat["firstname"][i][8]
    record=[x.encode('UTF8') for x in list(data2score[colnames2score].values[i])]
    asr_reformat["age"][i]=int(float(asr_reformat['age'][i]))
    for j in range(len(namelist)):
        asr_reformat["bpitems"][i]=asr_reformat["bpitems"][i]+record[j][1]
##    print asr_reformat["bpitems"][i]
##    print ("--------------------------")
    print i


myfile = open(myfile_name, 'w')
    


asr_reformat.to_csv(myfile_name, index=False)
myfile.close()        
elapsed = (time.time() - start)
print elapsed
