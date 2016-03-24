##
##  Copyright 2015 SRI International
##  License: https://ncanda.sri.com/software-license.txt
##

##############################
# Driving & Riding Behavior & History Questionnaire
# Related Document: N-CANDA SCORING CRITERIA.doc
#                   Driving & Riding Behaivor & History Questionnaire (Shortened)_(DHR).pdf
# Author: Shana
# Date of Last Revision: 2514
# KMC edits Feb 28 2014 (disolved CK's "arrays", removed print calls, removed test/dummy input, ended with a dataframe with 1 row and good var names) )
# Reviewed: SEE
# Script Name: DRHQ_2.5.R
##############################

#### Reading the raw data
args <- commandArgs(trailingOnly = TRUE)
case1=read.csv(args[1], sep=",",na.strings=TRUE,header=TRUE)

#### Extracting the correct variable name from inside brackets
vars=names(case1)
vars1=grep("\\.\\.(.*)\\.",as.character(vars),value=TRUE) # Searching the variable names with brackets
vars1=sub(".*\\.\\.(.*)\\..*", "\\1", vars1, perl=TRUE)   # Extracting the strings inside the brackets
vars1=sub("\\_1", '', vars1)                             #Extracting strings attached at the end of variables 

#### Create a new data set 
case1_1=case1[1,grep("\\.\\.(.*)\\.",as.character(vars))]
colnames(case1_1)=(vars1)  # Replacing the column names with the strings inside the bracket
case1_1=as.data.frame(case1_1)
case1=cbind(case1,case1_1)    
attach(case1)

#### Computations ####

#### Calculating DHR scores
DRHQ.TMV=(dhr7+dhr8+dhr9+dhr10+dhr11)
DRHQ.DSS=(6-dhr14+dhr15-1+dhr16-1+dhr17-1) #this instrument comes with atypical coded responses (never =1, not zero)
DRHQ.DUI=(dhr18+dhr19+dhr20)


#### Output
DRHQ.vars<-as.data.frame(cbind(DRHQ.TMV,DRHQ.DSS,DRHQ.DUI))
write.csv(DRHQ.vars, args[2], row.names=FALSE, na="")
