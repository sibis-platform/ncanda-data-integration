##
##  Copyright 2016 SRI International
##  See COPYING file distributed along with the package for the copyright and license terms.
##
#############################
# Peer Group Deviance
# Related Document: N-CANDA scoring criteria.docx
#                   Peer Group Deviance (PGD).pdf
# Author: Shana
# Date of Last Revision: 111813
# Reviewed: SEE,JK
# Script Name: PGD_11_18.R
#############################

#### Reading the raw data
args <- commandArgs(trailingOnly = TRUE)
case1=read.csv(args[1], sep=",",na.strings=TRUE,header=TRUE)

#### Extracting the correct variable names from inside brackets
vars=names(case1)
vars1=grep("\\.\\.(.*)\\.",as.character(vars),value=TRUE) # Searching the variable names with brackets
vars1=sub(".*\\.\\.(.*)\\..*", "\\1", vars1, perl=TRUE)   # Extracting the strings inside the bracket

#### Creating a new data set with the variable names without brackets
case1_1=case1[1,grep("\\.\\.(.*)\\.",as.character(vars))]
colnames(case1_1)=(vars1)  # Replacing the column names with the strings inside the bracket
case_1_1=as.data.frame(case1_1)
case1=cbind(case1,case1_1)
attach(case1)

#### Caluculating PGD scores
PGD.SUM=(pgd1+pgd2+pgd3+pgd4+pgd5+pgd6+pgd7+pgd8+pgd9+pgd10+pgd11+pgd12) 

#### Output
PGD.vars=as.data.frame(cbind(PGD.SUM))
write.csv(PGD.vars, args[2], row.names=FALSE, na="")
