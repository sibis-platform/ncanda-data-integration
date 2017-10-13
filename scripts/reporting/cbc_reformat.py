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
namelist=['1_cbcl01','1_cbcl02','1_cbcl03','1_cbcl04','1_cbcl05','1_cbcl06','1_cbcl07','2_cbcl08','2_cbcl09','2_cbcl10',
          '2_cbcl11','2_cbcl12','2_cbcl13','2_cbcl14','3_cbcl15','3_cbcl16','3_cbcl17','3_cbcl18','3_cbcl19','3_cbcl20',
          '3_cbcl21','4_cbcl22','4_cbcl23','4_cbcl24','4_cbcl25','4_cbcl26','4_cbcl27','4_cbcl28','5_cbcl29','5_cbcl30',
          '5_cbcl31','5_cbcl32','5_cbcl33','5_cbcl34','5_cbcl35','6_cbcl36','6_cbcl37','6_cbcl38','6_cbcl39','6_cbcl40',
          '6_cbcl41','6_cbcl42','7_cbcl43','7_cbcl44','7_cbcl45','7_cbcl46','7_cbcl47','7_cbcl48','7_cbcl49','8_cbcl50',
          '8_cbcl51','8_cbcl52','8_cbcl53','8_cbcl54','8_cbcl55','9_cbcl56a','9_cbcl56b','9_cbcl56c','9_cbcl56d','9_cbcl56e',
          '9_cbcl56f','9_cbcl56g','9_cbcl56h','10_cbcl57','10_cbcl58','10_cbcl59','10_cbcl60','10_cbcl61','10_cbcl62',
          '10_cbcl63','11_cbcl64','11_cbcl65','11_cbcl66','11_cbcl67','11_cbcl68','11_cbcl69','11_cbcl70','12_cbcl71','12_cbcl72',
          '12_cbcl73','12_cbcl74','12_cbcl75','12_cbcl76','12_cbcl77','13_cbcl78','13_cbcl79','13_cbcl80','13_cbcl81','13_cbcl82',
          '13_cbcl83','13_cbcl84','14_cbcl85','14_cbcl86','14_cbcl87','14_cbcl88','14_cbcl89','14_cbcl90','14_cbcl91','15_cbcl92',
          '15_cbcl93','15_cbcl94','15_cbcl95','15_cbcl96','15_cbcl97','15_cbcl98','16_cbcl99','16_cbc100','16_cbc101','16_cbc102',
          '16_cbc103','16_cbc104','16_cbc105','17_cbcl106','17_cbcl107','17_cbcl108','17_cbcl109','17_cbcl110','17_cbcl111','17_cbcl112']



for i in namelist:
    colnames2score.append('parentreport_cbcl_section'+str(i))
colnames_score=['study_id','redcap_event_name','redcap_data_access_group','dob','sex','age','mri_xnat_sid']+colnames2score
data_entry_raw= DataFrame(project_entry.export_records(fields=colnames_score))
data_entry_raw['age']=data_entry_raw['age'].astype(str)
data2score=data_entry_raw[(data_entry_raw["parentreport_cbcl_section17_cbcl112"]!="")]
data2score=data2score[(data2score["age"]!="")]
data2score=data2score.loc[::,]
print data2score.shape
# # of subjects to be scored
subject_count=data2score.shape[0]


today=time.strftime("%m%d%Y")
myfile_name='cbc_reformate_'+today+'.csv'

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
cbc_reformat=DataFrame(columns=header_name)
#cbc_reformat["subjectno"]=range(1,subject_count+1)
cbc_reformat["subjectno"]=range(subject_count)
cbc_reformat["admver"]=9.1
cbc_reformat["datatype"]="raw"
cbc_reformat["age"]=data2score["age"].tolist()
cbc_reformat["firstname"]=data2score["study_id"].values
cbc_reformat["middlename"]=data2score["mri_xnat_sid"].values
cbc_reformat["lastname"]=data2score["redcap_event_name"].values
cbc_reformat["dob"]=data2score["dob"].values
cbc_reformat["dfo"]="//"
cbc_reformat["formver"]="2001"
cbc_reformat["dataver"]="2001"
cbc_reformat["formno"]="9"
cbc_reformat["formid"]="9"
cbc_reformat["type"]="CBC"
cbc_reformat["enterdate"]=time.strftime("%m/%d/%Y")
cbc_reformat["compitems"]="'9999999999999999999999999999999999999999"
cbc_reformat["bpitems"]="'"

for i in range(subject_count):
#for i in range(20):    
    cbc_reformat["gender"][i]=cbc_reformat["firstname"][i][8]
    record=[x.encode('UTF8') for x in list(data2score[colnames2score].values[i])]
    cbc_reformat["age"][i]=int(float(cbc_reformat['age'][i]))
    for j in range(len(namelist)):
        cbc_reformat["bpitems"][i]=cbc_reformat["bpitems"][i]+record[j]
##    print cbc_reformat["bpitems"][i]
##    print ("--------------------------")


myfile = open(myfile_name, 'w')
    


cbc_reformat.to_csv(myfile_name, index=False)
myfile.close()        
elapsed = (time.time() - start)
print elapsed
