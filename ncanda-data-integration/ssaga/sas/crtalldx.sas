/*                                                                      */
/*  Copyright 2015 SRI International                                    */
/*  License: https://ncanda.sri.com/software-license.txt                */
/*                                                                      */
/*  $Revision: 2120 $                                                   */
/*  $LastChangedBy: nicholsn $                                          */
/*  $LastChangedDate: 2015-08-07 14:23:35 -0700 (Fri, 07 Aug 2015) $    */
/*                                                                      */
libname ncanda 'z:\tmp\ssaga';
******************************************;
** CHANGE libname (above);
*** CHANGE all pathnames for txt files below;
*************************************************;
options source2;

%macro crtdx(dset);
data dx_&dset;
set ncanda.&dset;
   keep ind_id dm1;  
   if DRUG5 ne '' then do;
      OtherDrugName=DRUG5;
      OtherDrugCode=DR2_Code;
   end;
   label OtherDrugName='OtherDrugName:DRUG5 (see DR2)';
   label OtherDrugCode='OtherDrugCode=DRUG5_Code (see DR2)';
   %include 's:\TB_DSMIVrv.txt';
   %include 's:\FTND.txt';
   %include 's:\AL_DSMIIIRrv.txt';
   %include 's:\AL_DSMIVrv.txt';
   %include 's:\AL_ICD10rv.txt';
   %include 's:\AL_FGNrv.txt';
   %include 's:\ALGeneticModelsDx.txt';
   %include 's:\MJ_DSMIIIR.txt';
   %include 's:\MJ_DSMIV.txt';
   %include 's:\MJ_ICD10.txt';
   %include 's:\DR_DSMIIIRrv.txt';
   %include 's:\DR_DSMIVrv.txt';
   %include 's:\DR_ICD10rv.txt';
   %include 's:\AN_DSMIV.txt';
   
   %include 's:\DP_DSMIVrv.txt';
   %include 's:\AS_DSMIVrv2.txt';
   %include 's:\AD_DSMIV.txt';
   
   %include 's:\PT_DSMIV.txt';
   %include 's:\OCD_DSMIV.txt';
   
   %include 's:\PN_DSMIV.txt';
   
   keep OtherDrugName OtherDrugCode;
 

%mend;

%crtdx(nssaga)

data ncanda.dx_nssaga; set dx_nssaga;

run;

