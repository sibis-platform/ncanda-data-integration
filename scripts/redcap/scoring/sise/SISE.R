##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##
##################################
# Single-Item Self-Esteem Scale 
# Related Documents: Single Item Self Esteem.pdf
# Author: Chieko & Shana
# Date of last revision: 111413
# Reviewed: SEE & JK
# Script Name: SCSM_11_14.R
#####################################

##
## THIS SCRIPT IS NOT ACTUALLY EXECUTED AT ALL BECAUSE IT ONLY COPIES A SURVEY
## RESPONSE. WE CAN DO THIS MORE EASILY IN PYTHON.
##

#### Reading in raw data
args <- commandArgs(trailingOnly = TRUE)
case1=read.csv(args[1], sep=",",na.strings=TRUE,header=TRUE)

#### Creating Labels
SISE.ary<-as.data.frame(matrix(nrow=1,ncol=1))
colnames(SISE.ary)<-c("SISE")
SISE.ary=t(SISE.ary)
label_SISE.ary<-as.data.frame(matrix(nrow=1,ncol=1))
colnames(label_SISE.ary)<-c("Label")
label_SISE.ary[,1]<-c("SISE Score")

#### Output
SISE.ary[,1]=sise
SISE=cbind(label_SISE.ary,SISE.ary)
write.csv(SISE, args[2], row.names=FALSE, na="")
