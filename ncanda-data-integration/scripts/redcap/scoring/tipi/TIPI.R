##
##  Copyright 2015 SRI International
##  License: https://ncanda.sri.com/software-license.txt
##
##  $Revision: 2121 $
##  $LastChangedBy: nicholsn $
##  $LastChangedDate: 2015-08-07 14:27:43 -0700 (Fri, 07 Aug 2015) $
##
#####################################
# Ten Item Personality Inventry(TIPI)
# Related Docs: N-CANDA Scoring Criteria.doc
#               TIPI_NCANDA.pdf
#               teaching_self_observer.pdf
#               TIPI-psychometrics_Gosling2003.pdf
# Author: Chieko & Shana
# Date of Last Revision: 111413
# Reviewed: SEE,JK
# Script Name: TIPI_11_14.R
#####################################

#### Reading the raw data
args <- commandArgs(trailingOnly = TRUE)
case1=read.csv(args[1], sep=",",na.strings=TRUE,header=TRUE)

#### Extracting the correct variable names from inside brackets
vars=names(case1)
vars1=grep("\\.\\.(.*)\\.",as.character(vars),value=TRUE) #Searching the variable names with brackets
vars1=sub(".*\\.\\.(.*)\\..*", "\\1", vars1, perl=TRUE) #Extracting the strings inside the bracket

#### Create a data set that cotains only variables with brackets
case1_1=case1[1,grep("\\.\\.(.*)\\.",as.character(vars))]
colnames(case1_1)=(vars1)  # Replacing the column names with the strings inside the bracket
case_1_1=as.data.frame(case1_1)
case1=cbind(case1,case1_1)    
attach(case1)

#### Creating Labels
TIPI.ary<-as.data.frame(matrix(nrow=1,ncol=5))
colnames(TIPI.ary)<-c("TIPI.ETV","TIPI.AGV","TIPI.CSC","TIPI.EMS","TIPI.OPE")
TIPI.ary=t(TIPI.ary)

label_TIPI.ary<-as.data.frame(matrix(nrow=5,ncol=1))
colnames(label_TIPI.ary)<-c("Label")
label_TIPI.ary[,1]<-c("Extraversion",
                     "Agreeableness",
                     "Conscientiousness",
                     "Emotional Stability",
                     "Openness to Experiences")

#### Calculating summary variables
TIPI.ETV=(tipi1+8-tipi6)/2   # Extraversion
TIPI.AGB=(8-tipi2+tipi7)/2   # Agreeableness
TIPI.CSC=(tipi3+8-tipi8)/2   # Conscientiousness
TIPI.EMS=(8-tipi4+tipi9)/2   # Emotional Stability
TIPI.OPE=(tipi5+8-tipi10)/2  # Openness to Experiences

#### Output
TIPI.ary[,1]=c(TIPI.ETV,TIPI.AGB,TIPI.CSC,TIPI.EMS,TIPI.OPE)
TIPI.ary=cbind(label_TIPI.ary,TIPI.ary)
write.csv(TIPI.ary, args[2], row.names=FALSE, na="")
