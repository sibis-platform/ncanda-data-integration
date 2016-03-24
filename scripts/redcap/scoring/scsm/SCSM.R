##
##  Copyright 2015 SRI International
##  See COPYING file distributed along with the package for the copyright and license terms.
##
#####################################
# Smith Composite Scale of Morningness
# Related Documents: Smith Sleep Q-scoring,refs.docx
#                    Smith Composite Scale of Morningness.pdf
# Authors: Chieko & Shana
# Date of last revision: 111413
# Reviewed: SEE & JK
# Script Name: SCSM_11_14.R
#####################################

##
## THIS SCRIPT IS NOT ACTUALLY BEING EXECUTED - IT HAS BEEN PORTED TO BE
## EXECUTED DIRECTLY IN PYTHON INSTEAD.
##

#### Reading the raw data
args <- commandArgs(trailingOnly = TRUE)
case1=read.csv(args[1], sep=",",na.strings=TRUE,header=TRUE)

#### Extracting the correct variable names from inside brackets
vars=names(case1)
vars1=grep("\\.\\.(.*)\\.",as.character(vars),value=TRUE) # Searching the variable names with brackets
vars1=sub(".*\\.\\.(.*)\\..*", "\\1", vars1, perl=TRUE) # Extracting the strings inside the bracket

#### Creating a new data set with the variable names without brackets 
case1_1=case1[1,grep("\\.\\.(.*)\\.",as.character(vars))]
colnames(case1_1)=(vars1)  # Replacing the column names with the strings inside the bracket
case_1_1=as.data.frame(case1_1)
case1=cbind(case1,case1_1)    
attach(case1)

#### Creating Labels
SMITH.ary<-as.data.frame(matrix(nrow=1,ncol=1))
colnames(SMITH.ary)<-c("SMITHTOT")
SMITH.ary=t(SMITH.ary)
label_SMITH.ary<-as.data.frame(matrix(nrow=1,ncol=1))
colnames(label_SMITH.ary)<-c("Label")
label_SMITH.ary[,1]<-c("Total")
                    
#### Calculating Smith Composite Scale of Morningness total 
SMITHTOT=6-scsm1+6-scsm2+scsm3+scsm4+scsm5+5-scsm6+6-scsm7+5-scsm8+5-scsm9+5-scsm10+scsm11+5-scsm12+5-scsm13

#### Output
SMITH.ary[,1]=SMITHTOT
SMITHTOT=cbind(label_SMITH.ary,SMITH.ary)
write.csv(SMITHTOT, args[2], row.names=FALSE, na="")
