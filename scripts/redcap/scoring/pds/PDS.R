#############################
# Pubertal Development Scale
# Related Documents: PDS Scoring Criteria-Fiona.docx
#                    Pubertal Development Scale.docx
#                    carskadon_acebo_pubertyscale.pdf
# Author: Chieko & Shana
# Date of Last Revision: 2252014
# KMC edits Feb 28 2014 (disolved CK's "arrays", removed print calls, removed test/dummy input, ended with a dataframe with 1 row and good var names) )
# Reviewed: SEE
# Script Name: PDS_2_20.R
#############################

#### Reading the raw data
args <- commandArgs(trailingOnly = TRUE)
case1=read.csv(args[1], sep=",",na.strings=TRUE,header=TRUE)

#### Extracting the correct variable names from inside brackets
vars=names(case1)
vars1=grep("\\.\\.(.*)\\.",as.character(vars),value=TRUE)#Searching the variable names with brackets
vars1=sub(".*\\.\\.(.*)\\..*", "\\1", vars1, perl=TRUE)#Extracting the strings inside the bracket

#### Creating a new data set with the variable names without brakets 
case1_1=case1[1,grep("\\.\\.(.*)\\.",as.character(vars))]
colnames(case1_1)=(vars1)  # Replacing the column names with the strings inside the blacket
case_1_1=as.data.frame(case1_1)
case1=cbind(case1,case1_1)    
attach(case1)


#### Calculating Pubertal Development Scale Score
invisible(ifelse(is.na(pdsf5b),(PDSF<-1),(PDSF<-4))) # Recoding pdsf5a (Y=4,N=1)
invisible(ifelse((ydi2==1),(PDSS=(pdsm1+pdsm2+pdsm3+pdsm4+pdsm5)/5),(PDSS=(pdsf1+pdsf2+pdsf3+pdsf4+PDSF)/5)))


#### Calculating Pubertal Category Score 
invisible(ifelse((ydi2==1),(PCS_M=(pdsm2+pdsm4+pdsm5)),(PCS_M=NA)))
invisible(ifelse((ydi2==0),(PCS_F=(pdsf2+pdsf4)),(PCS_F=NA)) )

#### Category codes as coded in REDCap
Prepubertal <- "P1"
EarlyPubertal <- "P2"
Midpubertal <- "P3"
LatePubertal <- "P4"
Postpubertal <- "P5"

#### Calculating Pubertal Category
pubcat <- NA
invisible(ifelse(PCS_M==3,(pubcat<-Prepubertal),
       ifelse((PCS_M==4|PCS_M==5) & (pdsm2!=3&pdsm4!=3&pdsm5!=3),(pubcat<-EarlyPubertal),                     
              ifelse((PCS_M==4|PCS_M==5) & (pdsm2==3|pdsm4==3|pdsm5==3),(pubcat<-Midpubertal),
                   ifelse((PCS_M>=6&PCS_M<=8) & (pdsm2!=4&pdsm4!=4&pdsm5!=4),(pubcat<-Midpubertal),
                          ifelse((PCS_M>=6&PCS_M<=8) & (pdsm2==4|pdsm4==4|pdsm5==4),(pubcat<-LatePubertal),  
                                 ifelse(PCS_M>=9 & PCS_M<=11,(pubcat<-LatePubertal),
                                        ifelse(PCS_M==12,(pubcat<-Postpubertal),(PCS_M=NA)))))))))

invisible(ifelse(PCS_F==2 & pdsf5a %in% c("N",0),(pubcat<-Prepubertal),
       ifelse(PCS_F==3 & pdsf5a %in% c("N",0),(pubcat<-EarlyPubertal),
              ifelse(PCS_F>3 & pdsf5a %in% c("N",0),(pubcat<-Midpubertal),
                     ifelse(PCS_F<=7 & pdsf5a %in% c("Y",1),(pubcat<-LatePubertal),
                            ifelse(PCS_F==8 & pdsf5a %in% c("Y",1),(pubcat<-Postpubertal),(PCS_F=NA)))))))

#### Output
PDS.vars=as.data.frame(cbind(PDSS,pubcat))
write.csv(PDS.vars, args[2], row.names=FALSE, na="")
