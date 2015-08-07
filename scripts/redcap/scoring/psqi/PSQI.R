##
##  Copyright 2015 SRI International
##  License: https://ncanda.sri.com/software-license.txt
##
##  $Revision$
##  $LastChangedBy$
##  $LastChangedDate$
##
###############################
# Pittsburgh Sleep Quality Index
# Related Document: PSQI-scoring,refs.doc
# Author: Shana & Chieko
# Date of Last Revision: 112513
# Reviewed: SEE & JK
# KMC edits Feb 28 2014 (disolved CK's "arrays", removed print calls, removed test/dummy input, ended with a dataframe with 1 row and good var names) )
# Script Name: PSQI_11_25.R
###############################
# setwd("C:/Users/Chieko/Dropbox/SSAGA_Project/InterviewSummaryVars/Data/12471_MRI_part2")

#### Reading the raw data
args <- commandArgs(trailingOnly = TRUE)
case1=read.csv(args[1], sep=",",na.strings=TRUE,header=TRUE)

#### Extracting the correct variable names from inside brackets
vars=names(case1)
vars1=grep("\\.\\.(.*)\\.",as.character(vars),value=TRUE) #Searching the variable names with brackets
vars1=sub(".*\\.\\.(.*)\\..*", "\\1", vars1, perl=TRUE)  #Extracting the strings inside the bracket

#### Creating a new data set with the variable names without brakets 
case1_1=case1[1,grep("\\.\\.(.*)\\.",as.character(vars))] #Select variables with brackets by subsetting the original data
colnames(case1_1)=(vars1)  # Replacing the column names with the variable names inside the blackets
case_1_1=as.data.frame(case1_1)
case1=cbind(case1,case1_1)    
attach(case1)



#### Calculating Duration of Sleep

PSQIDURAT=NA
invisible(  ifelse(psqi4>=7, (PSQIDURAT=0),          
       ifelse(psqi4<7 && psqi4>=6, (PSQIDURAT=1), 
               ifelse(psqi4<6 && psqi4>=5, (PSQIDURAT=2),
                       ifelse(psqi4<5,(PSQIDURAT=3),(PSQIDURAT=NA))))))

#### Calculating Sleep Disturbance: Lime Survey coding (psqi5b-psqi5i) is off by 1
invisible(ifelse(is.na(psqi5j),(psqi5j=0),(psqi5j=1)) ) 
DISTB_TOT=((psqi5b-1)+(psqi5c-1)+(psqi5d-1)+(psqi5e-1)+(psqi5f-1)+(psqi5g-1)+(psqi5h-1)+(psqi5i-1)+(psqi5j))  # Adding items specified 

PSQIDISTB=NA
#ifelse(is.na(DISTB_TOT),(PSQIDISTB=NA),   
invisible(   ifelse(DISTB_TOT==0,(PSQIDISTB=0),
              ifelse(DISTB_TOT>=1 && DISTB_TOT<=9,(PSQIDISTB=1),
                     ifelse(DISTB_TOT>9 && DISTB_TOT<=18,(PSQIDISTB=2),
                            ifelse(DISTB_TOT>18,(PSQIDISTB=3),(PSQIDISTB=NA) )))))

#### Sleep Latency

#### Rescale psqi2
invisible(ifelse(is.na(psqi2),(psqi2.1=NA),
       ifelse(psqi2>=0 && psqi2<=15,(psqi2.1=0),
             ifelse(psqi2>15 && psqi2<=30,(psqi2.1=1),
                    ifelse(psqi2>30 && psqi2<=60,(psqi2.1=2),ifelse (psqi2>60 ,(psqi2.1=3), (psqi2.1=NA)))))))
#### Calculating Sleep Latency: Limesruvey coding for psqi5a is off by 1
LATEN_TOT=psqi5a-1+psqi2.1

invisible( ifelse(is.na(LATEN_TOT),(PSQILATEN=NA),
       ifelse(LATEN_TOT==0,(PSQILATEN=0),
              ifelse(LATEN_TOT>=1 && LATEN_TOT<=2,(PSQILATEN=1),
                     ifelse(LATEN_TOT>=3 && LATEN_TOT<=4,(PSQILATEN=2),ifelse(LATEN_TOT>=5 && LATEN_TOT<=6, (PSQILATEN=3), (PSQILATN=NA))))) ))


#### Calculating Day Disfunction Due To Sleepness: Limesurvey coding from psqi8-9 is off by 1 

DAYDYS_TOT=psqi8-1+psqi9-1
invisible(ifelse(is.na(DAYDYS_TOT),(PSQIDAYDYS=NA),
       ifelse(DAYDYS_TOT==0,(PSQIDAYDYS=0),
             ifelse(DAYDYS_TOT>=1 && DAYDYS_TOT<=2,(PSQIDAYDYS=1),
                   ifelse(DAYDYS_TOT>=3 && DAYDYS_TOT<=4,(PSQIDAYDYS=2),   ifelse(DAYDYS_TOT>=5 && DAYDYS_TOT<=6,(PSQIDAYDYS=3),(PSQIDAYDYS=NA)))))))


#### Calculating Sleep Efficiency
  
 # Hours between GNT(bed time) and GMT(Getting up time)
diffhour=NA
invisible( ifelse( psqi3<psqi1, (diffhour<-((psqi3+2400 -psqi1)/100)), (diffhour<-((psqi3 -psqi1)/100))))
tmphse<-psqi4/diffhour*100

# tmphse
PSQIHSE=NA
invisible(ifelse(tmphse>=85,(PSQIHSE=0),
       ifelse(tmphse<85 && tmphse>=75,(PSQIHSE=1),
              ifelse(tmphse<75 && tmphse>=65,(PSQIHSE=2),ifelse(tmphse<65,(PSQIHSE=3),(PSQIHSE=NA)))) ))


#### Overall Sleep Quality (Lime Survey is off by 1)
PSQISLPQUAL=(psqi6-1)

#### Need Meds To Sleep (Lime Survey is off by 1)
PSQIMEDS=(psqi7-1)

#### Total
PSQI=PSQIDURAT+PSQIDISTB+PSQILATEN+PSQIDAYDYS+PSQIHSE+PSQISLPQUAL+PSQIMEDS

#### Output
PSQI.vars=as.data.frame(cbind(PSQIDURAT,PSQIDISTB,PSQILATEN,PSQIDAYDYS,PSQIHSE,PSQISLPQUAL,PSQIMEDS,PSQI))
write.csv(PSQI.vars, args[2], row.names=FALSE, na="")
