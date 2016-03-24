##
##  Copyright 2015 SRI International
##  See COPYING file distributed along with the package for the copyright and license terms.
##
#############################
# Center for Epidemiologic Studies Depression Scale
# Related Document: N-CANDA Scoring Criteria.docx
#                   CES-D (for depressed mood state).pdf
# Author: Chieko & Shana
# Date of Last Revision: 111813
# Reviewed: SEE & JK
# Script Name: CES_D_11_18.R
##############################

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

#### Caluculating CES-D scores (Limesurvey coding is off by 1)
CES.SUM=(cesd1-1+cesd2-1+cesd3-1+4-cesd4+cesd5-1+cesd6-1+cesd7-1+4-cesd8+cesd9-1+
           ces10-1+ces11-1+4-ces12+ces13-1+ces14-1+ces15-1+4-ces16+ces17-1+ces18-1+ces19-1+ces20-1)

#### Creating Label
CES.ary=as.data.frame(matrix(nrow=1,ncol=1))
colnames(CES.ary)=c("CES")
CES.ary=t(CES.ary)                       
label_CES.ary=as.data.frame(matrix(nrow=1,ncol=1))
colnames(label_CES.ary)=c("Label")
label_CES.ary[,1]=c("CES Symptomatology Score")
                    
#### Output
CES.ary[,1]=CES.SUM
CES.ary=cbind(label_CES.ary,CES.ary)
write.csv(CES.ary, args[2], row.names=FALSE, na="")
