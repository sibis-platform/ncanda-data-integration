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
namelist=['1_ysr01','1_ysr02','1_ysr03','1_ysr04','1_ysr05','1_ysr06','1_ysr07','2_ysr08','2_ysr09','2_ysr10','2_ysr11','2_ysr12',
          '2_ysr13','2_ysr14','3_ysr15','3_ysr16','3_ysr17','3_ysr18','3_ysr19','3_ysr20','3_ysr21','4_ysr22','4_ysr23','4_ysr24',
          '4_ysr25','4_ysr26','4_ysr27','4_ysr28','5_ysr29','5_ysr30','5_ysr31','5_ysr32','5_ysr33','5_ysr34','5_ysr35','6_ysr36',
          '6_ysr37','6_ysr38','6_ysr39','6_ysr40','6_ysr41','6_ysr42','7_ysr43','7_ysr44','7_ysr45','7_ysr46','7_ysr47','7_ysr48',
          '7_ysr49','8_ysr50','8_ysr51','8_ysr52','8_ysr53','8_ysr54','8_ysr55','9_ysr56a','9_ysr56b','9_ysr56c','9_ysr56d','9_ysr56e',
          '9_ysr56f','9_ysr56g','9_ysr56h','10_ysr57','10_ysr58','10_ysr59','10_ysr60','10_ysr61','10_ysr62','10_ysr63','11_ysr64',
          '11_ysr65','11_ysr66','11_ysr67','11_ysr68','11_ysr69','11_ysr70','12_ysr71','12_ysr72','12_ysr73','12_ysr74','12_ysr75',
          '12_ysr76','12_ysr77','13_ysr78','13_ysr79','13_ysr80','13_ysr81','13_ysr82','13_ysr83','13_ysr84','14_ysr85','14_ysr86',
          '14_ysr87','14_ysr88','14_ysr89','14_ysr90','14_ysr91','15_ysr92','15_ysr93','15_ysr94','15_ysr95','15_ysr96','15_ysr97',
          '15_ysr98','16_ysr99','16_ysr100','16_ysr101','16_ysr102','16_ysr103','16_ysr104','16_ysr105','17_ysr106','17_ysr107',
          '17_ysr108','17_ysr109','17_ysr110','17_ysr111','17_ysr112']

for i in namelist:
    colnames2score.append('youthreport1_ysr_section'+str(i))
colnames_score=['study_id','redcap_event_name','redcap_data_access_group','dob','sex','age','mri_xnat_sid']+colnames2score
data_entry_raw= DataFrame(project_entry.export_records(fields=colnames_score))
data_entry_raw['age']=data_entry_raw['age'].astype(str)
data2score=data_entry_raw[(data_entry_raw["youthreport1_ysr_section10_ysr57"]!="")]
data2score=data2score[(data2score["age"]!="")]
data2score=data2score.loc[::,]
print data2score.shape
# # of subjects to be scored
subject_count=data2score.shape[0]


today=time.strftime("%m%d%Y")
myfile_name='ysr_reformate_'+today+'.csv'

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
ysr_reformat=DataFrame(columns=header_name)
#ysr_reformat["subjectno"]=range(1,subject_count+1)
ysr_reformat["subjectno"]=range(subject_count)
ysr_reformat["admver"]=9.1
ysr_reformat["datatype"]="raw"
#age=data2score["age"].astype(string)
#aaa=[x.encode('UTF8') for x in age]
##bbb=[x.split('.')[0] for x in aaa]
##ysr_reformat["age"]=ysr_reformat["age"].round(decimals=0)
#data2score["age1"]=data2score["age"].astype(str)
ysr_reformat["age"]=data2score["age"].tolist()
ysr_reformat["firstname"]=data2score["study_id"].values
ysr_reformat["middlename"]=data2score["mri_xnat_sid"].values
ysr_reformat["lastname"]=data2score["redcap_event_name"].values
ysr_reformat["dob"]=data2score["dob"].values
ysr_reformat["dfo"]="//"
ysr_reformat["formver"]="2001"
ysr_reformat["dataver"]="2001"
ysr_reformat["formno"]="13"
ysr_reformat["formid"]="13"
ysr_reformat["type"]="YSR"
ysr_reformat["enterdate"]=time.strftime("%m/%d/%Y")
ysr_reformat["compitems"]="'999999999999999999999999999999999999"
ysr_reformat["bpitems"]="'"

for i in range(subject_count):
#for i in range(20):    
    ysr_reformat["gender"][i]=ysr_reformat["firstname"][i][8]
    record=[x.encode('UTF8') for x in list(data2score[colnames2score].values[i])]
    ysr_reformat["age"][i]=int(float(ysr_reformat['age'][i]))
    #ysr_reformat["bpitems"]="'"
    for j in range(len(namelist)):
        ysr_reformat["bpitems"][i]=ysr_reformat["bpitems"][i]+record[j][1]
##    print ysr_reformat["bpitems"][i]
##    print ("--------------------------")
    print i    


myfile = open(myfile_name, 'w')
    
###read in all youth report
##data=pandas.io.parsers.read_csv("C:/Users/wchu/Desktop/work/NCANDA ASEBA Scoring Tools/python/ysr2014-11-25.csv",header=0)
##
###select subjects only complete the report
##data_complete=data[data['youth_report_1b_complete']==1]
##data_complete=data_complete[data_complete['age'].round(decimals=1)>0]
##
###colums for asr scoringysr_reformat["i"][i]
##colnames_id=['study_id','age','sex','redcap_data_access_group','redcap_event_name']
##namelist=['1_ysr01','1_ysr02','1_ysr03','1_ysr04','1_ysr05','1_ysr06','1_ysr07','2_ysr08','2_ysr09','2_ysr10','2_ysr11','2_ysr12',
##          '2_ysr13','2_ysr14','3_ysr15','3_ysr16','3_ysr17','3_ysr18','3_ysr19','3_ysr20','3_ysr21','4_ysr22','4_ysr23','4_ysr24',
##          '4_ysr25','4_ysr26','4_ysr27','4_ysr28','5_ysr29','5_ysr30','5_ysr31','5_ysr32','5_ysr33','5_ysr34','5_ysr35','6_ysr36',
##          '6_ysr37','6_ysr38','6_ysr39','6_ysr40','6_ysr41','6_ysr42','7_ysr43','7_ysr44','7_ysr45','7_ysr46','7_ysr47','7_ysr48',
##          '7_ysr49','8_ysr50','8_ysr51','8_ysr52','8_ysr53','8_ysr54','8_ysr55','9_ysr56a','9_ysr56b','9_ysr56c','9_ysr56d','9_ysr56e',
##          '9_ysr56f','9_ysr56g','9_ysr56h','10_ysr57','10_ysr58','10_ysr59','10_ysr60','10_ysr61','10_ysr62','10_ysr63','11_ysr64',
##          '11_ysr65','11_ysr66','11_ysr67','11_ysr68','11_ysr69','11_ysr70','12_ysr71','12_ysr72','12_ysr73','12_ysr74','12_ysr75',
##          '12_ysr76','12_ysr77','13_ysr78','13_ysr79','13_ysr80','13_ysr81','13_ysr82','13_ysr83','13_ysr84','14_ysr85','14_ysr86',
##          '14_ysr87','14_ysr88','14_ysr89','14_ysr90','14_ysr91','15_ysr92','15_ysr93','15_ysr94','15_ysr95','15_ysr96','15_ysr97',
##          '15_ysr98','16_ysr99','16_ysr100','16_ysr101','16_ysr102','16_ysr103','16_ysr104','16_ysr105','17_ysr106','17_ysr107',
##          '17_ysr108','17_ysr109','17_ysr110','17_ysr111','17_ysr112']
##
##for i in namelist:
##    colnames_score.append('youthreport1_ysr_section'+str(i))
## 
###get subjects info as well as item to scores    
##data2subject=data_complete.loc[::,colnames_id]    
##data2score=data_complete.loc[::,colnames_score]
##
##
##
###insert scoring type
##data2subject.insert(0,column="type",value="|YSR", allow_duplicates=True)
##data2subject.insert(1,column="Version",value="|2001", allow_duplicates=True)
##data2subject.insert(7,column="Adaptive",value="99999999999999999999999999999999999   ", allow_duplicates=True)
###data2subject['youthreport1b_age']=data2subject['youthreport1b_age'].round(decimals=0)
###data2subject['youthreport1b_age']=data2subject['youthreport1b_age'].convert_objects(convert_numeric=True)
##data2subject['age']=data2subject['age'].astype('int')
##
###replacing missing value with 9 according to ASR
###data2score.fillna("9")
##
##
###get dimention of the dataframe
##dim=data2score.shape
##total_rows=dim[0]
##
##for i in range(0,total_rows):
###for i in range(0,4):
##    #select ith record
##    subject=data2subject.iloc[[i]]
##    score=data2score.iloc[[i]]
##    subject['study_id']=subject['study_id'] + ' '           #make subject_id to be 12 spaces
##    subject['age']=subject['age'].astype('str') + ' '  #make age to be 3 spaces
##    access_group=subject['redcap_data_access_group'].irow(0)+ '                '
##    subject['redcap_data_access_group'] =access_group[0:15]
##    event=subject['redcap_event_name'].irow(0)+'                     '
##    subject['redcap_event_name']=event[0:20]
##    #120 item need asr scores, convert to array
##    subject=subject.reset_index(drop=True) 
##    score = score.reset_index(drop=True)
##    score_array =score.reset_index().values
##    na_index=score_array.nonzero()
##    #get gender from subject_id which is more accurant and complete
##    if (subject['study_id'].loc[0].find("M"))>0:
##         subject['sex'] = 1
##    if (subject['study_id'].loc[0].find("F"))>0:
##         subject['sex'] = 2     
##    if (len(na_index[1]) < 118):
##        #print(len(na_index[1]))
##        subject_array=subject.reset_index(drop=True).values
##        subject_list=subject_array.tolist()
##        score_list=score_array.tolist()
##        subject_list=subject_list[0]
##        score_list=score_list[0]
##        subject_out=subject_list[0]
##        score_out=""
##        for x in range(1,8) :
##            if str(subject_list[x])=="nan":
##                subject_out=subject_out+"9|"
##            else:
##                subject_out=subject_out+str(subject_list[x])+'|'
##        for x in range(1,(len(score_list))) :
##            if str(score_list[x])=="nan":
##                #print(score_list)
##                score_out=score_out+"9"
##            else:
##                #print str(int(score_list[x]))  
##                score_out=score_out+str(int(score_list[x]))
##        #tobacco=str(int(score_list[x+1]))+'    '
##        #tobacco=tobacco[0:3]
##        #drunk=str(int(score_list[x+2]))+'    '
##        #drunk=tobacco[0:3]
##        #drug=str(int(score_list[x+3]))+'    '
##        #drug=tobacco[0:3]   
##        #score_out=score_out+'   |'
##        #score_out=score_out+tobacco+'|'+drunk+'|'+drug+'|'    
##            #print(x)
##        #subject_out=''.join(subject_array)
##        #score_array=score_array.astype(int)
####        aa.append([item_array[0,x] for x in range(0,dim[1])])
##        #print ', '.join(subject_array)
##        print>>myfile,subject_out+score_out
##        #print>>myfile,score_out

ysr_reformat.to_csv(myfile_name, index=False)
myfile.close()        
elapsed = (time.time() - start)
print elapsed
