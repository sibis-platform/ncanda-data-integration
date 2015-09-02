##
##  Copyright 2015 SRI International
##  License: https://ncanda.sri.com/software-license.txt
##
##  $Revision: 2121 $
##  $LastChangedBy: nicholsn $
##  $LastChangedDate: 2015-08-07 14:27:43 -0700 (Fri, 07 Aug 2015) $
##
#############################
# Hangover Symptom Survey
# Related Document: N-CANDA scoring criteria.doc
#                   HSS_11_18.pdf
# Author: Chieko & Shana
# Date of Last Revision: 111813
# Reviewed: SEE,JK
# Script Name: HSS_11_18.R
#############################

#### Reading the raw data
args <- commandArgs(trailingOnly = TRUE)
case1=read.csv(args[1], sep=",",na.strings=TRUE,header=TRUE)

#### Extracting the correct variable names from inside brackets
vars=names(case1)
vars1=grep("\\.\\.(.*)\\.",as.character(vars),value=TRUE)#Searching the variable names with brackets
vars1=sub(".*\\.\\.(.*)\\..*", "\\1", vars1, perl=TRUE)#Extracting the strings inside the bracket

#### Creating a new data set with the variable names without brackets 
case1_1=case1[1,grep("\\.\\.(.*)\\.",as.character(vars))]
colnames(case1_1)=(vars1)  # Replacing the column names with the strings inside the blacket
case_1_1=as.data.frame(case1_1)
case1=cbind(case1,case1_1)    
attach(case1)

#### Creating Label
HSS.ary<-as.data.frame(matrix(nrow=1,ncol=2))
colnames(HSS.ary)<-c("HSS.PASTWEEK","HSS.PASTYEAR")
HSS.ary=t(HSS.ary)                       

label_HSS.ary<-as.data.frame(matrix(nrow=2,ncol=1))
colnames(label_HSS.ary)<-c("Label")
label_HSS.ary[,1]<-c("HSS Past Week Score","HSS Past Year Score")

#### Creating HSS Week sum variables
HSSW.SUM=0
#### Calculating HSS Week scores (Limesurvey coding is off by 1)
dummy<-ifelse(is.na(hssweek2),(HSSW.SUM<-NA), HSSW.SUM<-(hssweek2-1+hssweek3-1+hssweek4-1+hssweek5-1+hssweek6-1+hssweek7-1+hssweek8-1+hssweek9-1+
                                            hssweek10-1+hssweek11-1+hssweek12-1+hssweek13-1+hssweek14-1))

#### Creating HSS Year sum varibales 
HSSY.SUM=0

#### Calculating HSS Year scores (Limesurvey coding is off by 1)
dummy<-ifelse(is.na(hssyear2),(HSSY.SUM<-NA),HSSY.SUM<-(hssyear2-1+hssyear3-1+hssyear4-1+hssyear5-1+hssyear6-1+hssyear7-1+hssyear8-1+hssyear9-1+
                                         hssyea10-1+hssyea11-1+hssyea12-1+hssyea13-1+hssyea14-1))

#### Output
HSS.ary[,1]=c(HSSW.SUM, HSSY.SUM)
HSS.ary=cbind(label_HSS.ary,HSS.ary)
write.csv(HSS.ary, args[2], row.names=FALSE, na="")
