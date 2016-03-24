##
##  Copyright 2015 SRI International
##  See COPYING file distributed along with the package for the copyright and license terms.
##
####################################################
# Alcohol Expectancy Questionnaire-Adolescent version
# Related Documents: AEQ scoring.docx
#                    Alcohol Expectancy Questionnaire-Adolescent Form (AEQ).pdf
# Author: Chieko & Shana
# Date of Last Revision: 2272014
# KMC edits Feb 28 2014 (disolved CK's "arrays", removed print calls, removed test/dummy input, ended with a dataframe with 1 row and good var names) )
# Reviewed: SEE
# Script Name: AEQ_2_25.R
#####################################################

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


###### Computations ######

#### Creating new variables 
ifelse(is.na(aeq3)|is.na(aeq4)|is.na(aeq18),(AEQ.GPC=NA),(AEQ.GPC=aeq3+aeq4+aeq18))         # Calculating AEQ.GPC
ifelse(is.na(aeq2)|is.na(aeq6)|is.na(aeq15),(AEQ.CSB=NA),(AEQ.CSB=aeq2+aeq6+aeq15))         # Calculating AEQ.CSB
ifelse(is.na(aeq5)|is.na(aeq9)|is.na(aeq14),(AEQ.ICMA=NA),(AEQ.ICMA=aeq5+aeq9+aeq14))       # Calculating AEQ.ICMAv
ifelse(is.na(aeq1)|is.na(aeq10)|is.na(aeq21),(AEQ.SE=NA),(AEQ.SE=aeq1+aeq10+aeq21))         # Calculating AEQ.SE
ifelse(is.na(aeq11)|is.na(aeq13)|is.na(aeq16),(AEQ.CMI=NA),(AEQ.CMI=aeq11+aeq13+aeq16))     # Calculating AEQ.CMI
ifelse(is.na(aeq7)|is.na(aeq8)|is.na(aeq20),(AEQ.IA=NA),(AEQ.IA=aeq7+aeq8+aeq20))           # Calculating AEQ.IA
ifelse(is.na(aeq12)|is.na(aeq17)|is.na(aeq19),(AEQ.RTR=NA),(AEQ.RTR=aeq12+aeq17+aeq19))     # Calculating AEQ.RTR
ifelse(is.na(AEQ.GPC)|is.na(AEQ.CSB)|is.na(AEQ.ICMA)|is.na(AEQ.SE)|is.na(AEQ.CMI)|is.na(AEQ.IA)|is.na(AEQ.RTR),
       (AEQ.MEAN=NA),((AEQ.MEAN=(AEQ.GPC+AEQ.CSB+AEQ.ICMA+AEQ.SE+AEQ.CMI+AEQ.IA+AEQ.RTR)/21))) # Calculating AEQ.MEAN
       
#### Calculating Positive and Negative Non-Drinking Expectancies 
AEQ.NEG=0
AEQ.POS=0
for (i in 1:21) {
  ifelse (get(paste0('aeq',i),envir=as.environment(-1))==1 | get(paste0('aeq',i),envir=as.environment(-1))==2, (AEQ.NEG<-AEQ.NEG+1),(AEQ.NEG<-AEQ.NEG))
  ifelse (get(paste0('aeq',i),envir=as.environment(-1))==4 | get(paste0('aeq',i),envir=as.environment(-1))==5, (AEQ.POS<-AEQ.POS+1),(AEQ.POS<-AEQ.POS))
}

#### Output
AEQ.vars=as.data.frame(cbind(AEQ.GPC,AEQ.CSB,AEQ.ICMA,AEQ.SE,AEQ.CMI,AEQ.IA,AEQ.RTR,AEQ.MEAN,AEQ.POS,AEQ.NEG), labels=label_AEQ)
write.csv(AEQ.vars, args[2], row.names=FALSE, na="")
