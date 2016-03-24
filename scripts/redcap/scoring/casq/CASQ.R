##
##  Copyright 2016 SRI International
##  See COPYING file distributed along with the package for the copyright and license terms.
##
##############################################
# Cleveland Adolescent Sleepiness Questionnaire
# Related Documents: Cleveland Adolescent Sleepiness Questionnaire_scoring.docx
#                    Cleveland Adolescent Sleepiness Questionnaire (CASQ).pdf
# Author: Chieko & Shana
# Date of Last Revision: 111413
# Reviewed: SEE & JK
# Script Name: CASQ_11_14.R
##############################################

#### Reading the raw data
args <- commandArgs(trailingOnly = TRUE)
case1=read.csv(args[1], sep=",",na.strings=TRUE,header=TRUE)

#### Extracting the correct variable name from inside brackets
vars=names(case1)
vars1=grep("\\.\\.(.*)\\.",as.character(vars),value=TRUE) # Searching the variable names with brackets
vars1=sub(".*\\.\\.(.*)\\..*", "\\1", vars1, perl=TRUE)   # Extracting the strings inside the bracket

#### Create a new data set 
case1_1=case1[1,grep("\\.\\.(.*)\\.",as.character(vars))]
colnames(case1_1)=(vars1)  # Replacing the column names with the strings inside the bracket
case1_1=as.data.frame(case1_1)
case1=cbind(case1,case1_1)    
attach(case1)

#### Calculating CASQ score (Lime survey coding is off by 1)
CASQTOT=sum(1+casq1,5-casq2,1+casq3,1+casq4,5-casq5,1+casq6,5-casq7,1+casq8,1+casq9,
            1+casq10,5-casq11,1+casq12,5-casq13,1+casq14,1+casq15,1+casq16)

#### Creating label
CASQ.ary=as.data.frame(matrix(nrow=1,ncol=1))
colnames(CASQ.ary)=c("CASQTOT")
CASQ.ary=t(CASQ.ary)
label_CASQ.ary=as.data.frame(matrix(nrow=1,ncol=1))
colnames(label_CASQ.ary)=c("Label")
label_CASQ.ary[,1]=c("Cleveland Adolescent Sleepiness Score")

###Output
CASQ.ary[,1]=CASQTOT
CASQ.ary=cbind(label_CASQ.ary,CASQ.ary)
write.csv(CASQ.ary, args[2], row.names=FALSE, na="")
