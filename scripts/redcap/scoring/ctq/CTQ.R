##
##  Copyright 2016 SRI International
##  See COPYING file distributed along with the package for the copyright and license terms.
##
##############################
# Childhood Trauma Questionnaie
# Related Documents: CTQ-scoring.pdf
#                    ctq4.pdf
#                    Childhood Trauma Questionnaire 2 (CTQ2).pdf
#                    ctq6.pdf
# Author: Chieko & Shana
# Date of Last Revision: 111313
# Reviewed: SEE & JK
# Script Name: CTQ_11_14.R
#########################################

#### Reading the raw data
args <- commandArgs(trailingOnly = TRUE)
case1=read.csv(args[1], sep=",",na.strings=TRUE,header=TRUE)

#### Extracting the correct variable names from inside brackets
vars=names(case1)
vars1=grep("\\.\\.(.*)\\.",as.character(vars),value=TRUE) #Searching the variable names with brackets
vars1=sub(".*\\.\\.(.*)\\..*", "\\1", vars1, perl=TRUE) #Extracting the strings inside the bracket

#### Creating a new data set with the variable names without brakets 
case1_1=case1[1,grep("\\.\\.(.*)\\.",as.character(vars))] #Select variables with brackets by subsetting the original data
colnames(case1_1)=(vars1)  # Replacing the column names with the variable names inside the blackets
case_1_1=as.data.frame(case1_1)
case1=cbind(case1,case1_1)   # Combine the original data set and the new data set
attach(case1)

#### Creating label
CTQ.ary<-as.data.frame(matrix(nrow=1,ncol=6))
colnames(CTQ.ary)<-c("CTQ.EA","CTQ.PA","CTQ.SA","CTQ.EN","CTQ.PN","CTQ.MINDS")
CTQ.ary=t(CTQ.ary)

label_CTQ.ary<-as.data.frame(matrix(nrow=6,ncol=1))
colnames(label_CTQ.ary)<-c("Label")
label_CTQ.ary[,1]<-c("Emotional Abuse Scale Total Score",
                     "Physical Abuse Scale Total Score",
                     "Sexual Abuse Scale Total Score",
                     "Emotional Neglect Scale Total Score",
                     "Physical Neglect Scale Total Score",
                     "Minimization/Denial Scale Total Score")

#### CTQ Scoring with (Lime survey coding is off by 1)
CTQ.EA=sum(1+ctq3,1+ctq8,1+ct14,1+ctq18,1+ctq25)    # Emotional Abuse Scale Total Score
CTQ.PA=sum(1+ctq9,1+ct11,1+ct12,1+ctq15,1+ctq17)    # Physical Abuse Scale Total Score
CTQ.SA=sum(1+ctq20,1+ctq21,1+ctq23,1+ctq24,1+ctq27) # Sexual Abuse Scale Total Score
CTQ.EN=sum(5-ctq5,5-ctq7,5-ct13,5-ctq19,5-ctq28) # Emotional Neglect Scale Total Score
CTQ.PN=sum(1+ctq1,5-ctq2,1+ctq4,1+ctq6,5-ctq26) # Physical Neglect Scale Total Score

#### New variables for CTQ.MINDS calculation                     
ctq10.1=NA
ctq16.1=NA
ctq22.1=NA

ifelse(is.na(ct10),(ctq10.1=ctq10.1),
       ifelse(ct10==4,(ctq10.1=1),(ctq10.1=0)))
ifelse(is.na(ctq16),(ctq16.1=ctq16.1),
       ifelse(ctq16==4,(ctq16.1=1),(ctq16.1=0)))
ifelse(is.na(ctq22),(ctq22.1=ctq22.1),
       ifelse(ctq22==4,(ctq22.1=1),(ctq22.1=0)))

#### Calculating Minimizatioin/Denial Scale Total Score
CTQ.MINDS=sum(ctq10.1,ctq16.1,ctq22.1) 
 

#### Outputs
CTQ.ary[,1]=c(CTQ.EA,CTQ.PA,CTQ.SA,CTQ.EN,CTQ.PN,CTQ.MINDS)
CTQ.ary=cbind(label_CTQ.ary,CTQ.ary)
write.csv(CTQ.ary, args[2], row.names=FALSE, na="")
