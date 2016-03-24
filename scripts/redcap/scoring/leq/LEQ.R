##
##  Copyright 2015 SRI International
##  License: https://ncanda.sri.com/software-license.txt
##

##############################
# Life Event Questionnaire
# Related Documents: LEQ_Scoring.docx
#                    Life Events Questionnaire (LEQ-YA).pdf
#                    Life Events Questionnaire (LEQ-Adol).pdf
# Author: Chieko & Shana
# Date of Last Revision: 111413
# Reviewed: SEE & JK
# Script Name: LEAQ_11_14.R
##############################

#### Reading the raw data
args <- commandArgs(trailingOnly = TRUE)
case1=read.csv(args[1], sep=",",na.strings=TRUE,header=TRUE)

#### Extracting the correct variable names from inside brackets
vars=names(case1)
leaqavars=grep(".*\\.\\.lea.*\\.",as.character(vars),value=TRUE) #Searching the leaqa/leaq variables with brackets
leaqavars=sub(".*\\.\\.(.*)\\..*", "\\1", leaqavars, perl=TRUE)  #Extracting variable names from brackets

#### Creating LEQ data set
LEQ.data.ary=case1[1,grep(".*\\.\\.lea.*\\.",as.character(vars))]
colnames(LEQ.data.ary)=(leaqavars)
LEQ.data.ary=as.data.frame(LEQ.data.ary)
attach(LEQ.data.ary)

#### Creating Label for LEQ-Adolescent version
LEAQA.ary=as.data.frame(matrix(nrow=1,ncol=11))
colnames(LEAQA.ary)=c("LEAQA.DNU","LEAQA.CNU","LEAQA.DAU","LEAQA.DNC","LEAQA.CNC","LEAQA.DPC","LEAQA.NU",
                      "LEAQA.DCU","LEAQA.U","LEAQA.NC","LEAQA.C")
LEAQA.ary=t(LEAQA.ary)
label_LEAQA.ary=as.data.frame(matrix(nrow=11,ncol=1))
colnames(label_LEAQA.ary)=c("Label")
label_LEAQA.ary[,1]=c("Discrete-Negative-Uncontrollable(Adolescent)",
                      "Chronic-Negative-Uncontrollable(Adolescent)",
                      "Discrete-Ambiguous-Uncontrollable(Adolescent)",
                      "Discrete-Negative-Controllable(Adolescent)",
                      "Chronic-Negative-Controllable(Adolescent)",
                      "Diescrete-Positive-Controllable(Adolescent)",
                      "Negative-Uncontrollable(Adolescent)",
                      "Discrete-Challenging-Uncontrollable(Adolescent)",
                      "Uncontrollable(Adolescent)",
                      "Negative-Controllable(Adolescent)",
                      "Negative Composite(Adolescent)")

#### Assigning variables based on gender(ydi2: 0 female 1 male)
if(ydi2==0) leaqa25<-leaqaf25 else leaqa25 <-leaqam25
if(ydi2==0) leaqa26<-leaqaf26 else leaqa26 <-leaqam26
if(ydi2==0) leaqa27<-leaqaf27 else leaqa27 <-leaqam27
if(ydi2==0) leaqa28<-leaqaf28 else leaqa28 <-leaqam28
if(ydi2==0) leaqa31<-leaqaf31 else leaqa31 <-leaqam31
if(ydi2==0) leaqa3029<-leaqa29 else leaqa3029 <-leaqa30

#### Calculating LEQ-Adolescent Scales
LEAQA.DNU=(leaqa3+leaqa4+leaqa6+leaqa7+leaqa8+leaqa9+leaqa10+leaqa11+leaqa14+leaqa15+leaqa16+leaqa34
                                                              +leaqa37+leaqa38+leaqa48+leaqa57+leaqa58)/17
LEAQA.CNU=(leaqa33+leaqa36+leaqa43+leaqa44+leaqa50+leaqa52+leaqa53)/7
LEAQA.DAU=(leaqa1+leaqa2+leaqa12+leaqa17+leaqa31+leaqa32)/6
LEAQA.DNC=(leaqa13+leaqa25+leaqa26+leaqa27+leaqa28+leaqa3029+leaqa55+leaqa56+leaqa61)/9
LEAQA.CNC=(leaqa39+leaqa40+leaqa42+leaqa45+leaqa46+leaqa51)/6
LEAQA.DPC=(leaqa19+leaqa21+leaqa22+leaqa23+leaqa24)/5

#### Calculating composite scales for LEQ-Adolescent
LEAQA.NU=(LEAQA.DNU+LEAQA.CNU)
LEAQA.DCU=(LEAQA.DNU+LEAQA.DAU)
LEAQA.U=(LEAQA.DNU+LEAQA.DAU+LEAQA.CNU)
LEAQA.NC=(LEAQA.DNC+LEAQA.CNC)
LEAQA.C=(LEAQA.DNU+LEAQA.CNU+LEAQA.DAU+LEAQA.DNC+LEAQA.CNC)


#### Creating Label for LEQ-Young Adult version
LEAQ.ary=as.data.frame(matrix(nrow=1,ncol=11))
colnames(LEAQ.ary)=c("LEAQ.DNU","LEAQ.CNU","LEAQ.DAU","LEAQ.DNC","LEAQ.CNC","LEAQ.DPC","LEAQ.NU",
                     "LEAQ.DCU","LEAQ.U","LEAQ.NC","LEAQ.C")
LEAQ.ary=t(LEAQ.ary)
label_LEAQ.ary=as.data.frame(matrix(nrow=11,ncol=1))
colnames(label_LEAQ.ary)=c("Label")
label_LEAQ.ary[,1]=c("Discrete-Negative-Uncontrollable(Young Adult)",
                     "Chronic-Negative-Uncontrollable(Young Adult)",
                     "Discrete-Ambiguous-Uncontrollable(Young Adult)",
                     "Discrete-Negative-Controllable(Young Adult)",
                     "Chronic-Negative-Controllable(Young Adult)",
                     "Diescrete-Positive-Controllable(Young Adult)",
                     "Negative-Uncontrollable(Young Adult)",
                     "Discrete-Challenging-Uncontrollable(Young Adult)",
                     "Uncontrollable(Young Adult)",
                     "Negative-Controllable(Young Adult)",
                     "Negative Composite(Young Adult)")

#### Calculating LEQ-Young Adult Scales
LEAQ.DNU=((leaq3+leaq4+leaq5+leaq6+leaq7+leaq8+leaq9+leaq10+leaq11+leaq14+
                                          leaq15+leaq16+leaq34+leaq37+leaq48+leaq57+leaq58+leaq59)/18)
LEAQ.CNU=((leaq33+leaq43+leaq44+leaq50+leaq52+leaq53+leaq54)/7)
LEAQ.DAU=((leaq1+leaq12+leaq17+leaq31)/4)
LEAQ.DNC=((leaq13+leaq18+leaq20+leaq25+leaq26+leaq27+leaq28+leaq47+leaq55+leaq56+leaq61)/11)
LEAQ.CNC=((leaq35+leaq36+leaq39+leaq40+leaq41+leaq45+leaq46+leaq49+leaq51)/9)
LEAQ.DPC=((leaq19+leaq21+leaq22+leaq23+leaq24+leaq60)/6)

#### Calculating composite scales for LEQ-Young Adult
LEAQ.NU=(LEAQ.DNU+LEAQ.CNU)
LEAQ.DCU=(LEAQ.DNU+LEAQ.DAU)
LEAQ.U=(LEAQ.DNU+LEAQ.DAU+LEAQ.CNU)
LEAQ.NC=(LEAQ.DNC+LEAQ.CNC)
LEAQ.C=(LEAQ.DNU+LEAQ.CNU+LEAQ.DAU+LEAQ.DNC+LEAQ.CNC)

#### Creating LEQ-Adolescent Output
LEAQA.ary[,1]=c(LEAQA.DNU,LEAQA.CNU,LEAQA.DAU,LEAQA.DNC,LEAQA.CNC,LEAQA.DPC,LEAQA.NU,LEAQA.DCU,LEAQA.U,LEAQA.NC,LEAQA.C)
LEAQA.ary=cbind(label_LEAQA.ary,LEAQA.ary)
# LEAQA.ary

#### Creating LEQ-Young Adult Output
LEAQ.ary[,1]=c(LEAQ.DNU,LEAQ.CNU,LEAQ.DAU,LEAQ.DNC,LEAQ.CNC,LEAQ.DPC,LEAQ.NU,LEAQ.DCU,LEAQ.U,LEAQ.NC,LEAQ.C)
LEAQ.ary=cbind(label_LEAQ.ary,LEAQ.ary)
# LEAQ.ary

#### Displaying final output
LEQ.ary<-0
ifelse (is.na(leaqa1), LEQ.ary<-LEAQ.ary, LEQ.ary<-LEAQA.ary)
write.csv(LEQ.ary, args[2], row.names=FALSE, na="")
