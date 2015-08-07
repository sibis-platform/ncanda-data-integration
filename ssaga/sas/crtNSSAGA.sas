/*                                                                      */
/*  Copyright 2015 SRI International                                    */
/*  License: https://ncanda.sri.com/software-license.txt                */
/*                                                                      */
/*  $Revision$                                                   */
/*  $LastChangedBy$                                          */
/*  $LastChangedDate$    */
/*                                                                      */
libname ncanda 'Z:\tmp\ssaga';

***************************************;
** CHANGE libname (above);
*** CHANGE pathnames for 5 %include files;
********************************************;

data v3; set ncanda.prenssaga_v3;
   if (change_id=5)*(real_id ne '') then do;
     put ind_id change_id= real_id=;
         ind_id=real_id;
   end;
  
data dset;set v3(drop=MH10a);  ** will not necessary to drop in next version;
  *******************************************;
 data dset;set dset(rename=(MJ19Qsx=MJ19QSx1));
   
       

   
  ***************************************;
   *if 1<=AL4f3<=4 then AL8=5;
   if 0 <=AS_ar15 <15 then AS15b=1;
   if 0 <=AS_ar16 <15 then AS16b=1;
   
   if 0 <=AS_ar17 <15 then do;
      AS18c=1;
          AS18d=1;
   end;
   if AS1_ao18>=15 and AS2_ao18>=15 then AS18b=1;

 
    rename AskSite=HE_AskSite;
    rename DM4=AGE;
    rename DMRec13=DM13Rec;
   drop
    TBCrit1-TBCrit7
	TBSxNum10-TBSxNum14
    AlcEver
        AnyDrug
        AnyDrugEver
        DM9_CNT
    AskRelationship
   
    CURRDTE


    ConfirmAge
    DayToday
        IND_ID2
        IND_ID3
        IND_ID4
      
        
    DPSxNum01
        DPSxNum02
        DPSxNum03
        DPSxNum04
        DPSxNum05
        DPSxNum06
        DPSxNum07
        DPSxNum08
        DPSxNum09
        DPSxNum10
        DPSxNum11
        DPSxNum12
        DPSxNum13
        DPSxNum14
        DPSxNum15
        DPSxNum16
        DPSxNum17
        DPSxNum18
        DPSxNum19
        DPSxNum20
        DPSxNum21

    MonthsElapsed
    NOW
    
    RecYrIntrvl
    
        SubstanceCount
    SubstanceString
        
        AlcEver
    AnyDrug
    AnyDrugEver
        
;
drop DR1a2_10-DR1a2_34
     TB16sx1-TB16sx9; 
   

   drop 
    AD10Another1
        AD10Another2
        AD5Another1
        AD5Another2
        
        AL21Another
        AL21Another2
        AL21Another3
        AL21Another4
        AL32Another
        AL39Another
        AL39Another2
        AL39Another3
        AL39Another4
        Al37Another
        Al37Another2
        Al37Another3
        Al37Another4
        Al38Another
        Al38Another2
        Al38Another3
        Al38Another4
        DP18Another1
        DP18Another2
        DP18Another3
        DP22Another1
        DP22Another2
        DP23Another
        DP33Another1
        DP33Another2
        MH6aAnother1
        MH6aAnother2
        MH6aAnother3
        MH6aAnother4
        MH6aAnother5
        MH6aAnother6
        MH6aAnother7
        MH6aAnother8
        MH6aAnother9
        MH6aAnother10
        MH6aAnother11
        MH6aAnother12
        MH6aAnother13
        MH6aAnother14
        MH6aAnother15
        MH6aAnother16
        MH6aAnother17
        MH6aAnother18
        MH6aAnother19
        MH6aAnother20
        MH6aAnother21
        MH6aAnother22
        MH6aAnother23
        MH6aAnother24
        MH6aAnother25
        MH6aAnother26
        MH6aAnother27
        MH6aAnother28
        MH6bAnother1
        MH6bAnother2
        MH6bAnother3
        MH6bAnother4
        MH6bAnother5
        MH6bAnother6
        MH6bAnother7
        MH6bAnother8
        MH6bAnother9
        MH6bAnother10
        MH6bAnother11
        MH6bAnother12
        MH6bAnother13
        MH6bAnother14
        MH6bAnother15
        MH6bAnother16
        MH6bAnother17
        MH6bAnother18
        MH6bAnother19
        MH6bAnother20
        MH6bAnother21
        MH6bAnother22
        MH6bAnother23
        MH6bAnother24
        MH6bAnother25
        MH6bAnother26
        MH6bAnother27
        MH6bAnother28
        MH6bAnother29
        MH6bAnother30
        MH6bAnother31
        MH6bAnother32
        MJ18Another
        MJ18Another2
        MJ18Another3
        MJ18Another4
        PN11Another1
        PN11Another2
        
        ;

drop 
        AS22Qsx
        AS22Qsx2-AS22Qsx21
      Al40Qsx
        Al40Qsx2-Al40Qsx32
      Al40aQsx
        Al40aQsx2-Al40aQsx32
        DR19Qsx
        DR19Qsx2-DR19Qsx95
        DR19aQsx
        DR19aQsx2-DR19aQsx95
      MJ10dQsx
        MJ10dQsx2-MJ10dQsx7
        MJ19Qsx1
        MJ19Qsx2-MJ19Qsx18
        MJ19dQsx
        MJ19dQsx2-MJ19dQsx18
        al37aQsx
        al37aQsx2-al37aQsx10
        TBSxList01-TBSxList14
        TBSxPastList01-TBSxPastList14
        TBSxNum01-TBSxNum09
        Varname10-Varname11
        Varname01-Varname09
        DrinkSum31-DrinkSum37
        DrinkSum41-DrinkSum47
;
;
drop
    DM4Decade
    DM5
   AgeMinus1
    mwho fwho
    IntvMo
    BrthMnth
 ;


data ss2;set dset;
 

    
  rename 
   
   DM11a=DM11A1
   DM12a=DM12a1
   
   MH3Yr=MH3Yr1
   

   MJ22FromMnth_ =MJ22FromMnth1 
   MJ22FromMnth_2 =MJ22FromMnth2 
   MJ22FromMnth_3=MJ22FromMnth3
   MJ22FromMnth_4=MJ22FromMnth4
   
   MJ22ToYr_ =MJ22ToYr1 
   MJ22ToYr_2 =MJ22ToYr2 
   MJ22ToYr_3=MJ22ToYr3
   MJ22ToYr_4=MJ22ToYr4
   

AL43FromMnth_=AL43FromMnth1
AL43FromMnth_2 =AL43FromMnth2 
AL43FromMnth_3=AL43FromMnth3
AL43FromMnth_4=AL43FromMnth4

AL43FromYr_=AL43FromYr1
AL43FromYr_2=AL43FromYr2
AL43FromYr_3=AL43FromYr3
AL43FromYr_4=AL43FromYr4

AL43ToMnth_=AL43ToMnth1
AL43ToMnth_2=AL43ToMnth2
AL43ToMnth_3=AL43ToMnth3
AL43ToMnth_4=AL43ToMnth4

AL43ToYR_=AL43ToYR1
AL43ToYR_2=AL43ToYR2
AL43ToYR_3=AL43ToYR3
AL43ToYR_4=AL43ToYR4

BEER=BEER1
WINE=WINE1
DM14_MO=DM14_MO1
DM14_YR=DM14_YR1

LIQUOR=LIQUOR1

MH3_=MH3_1

MJ22FromMnth_=MJ22FromMnth1
MJ22FromMnth_2 =MJ22FromMnth2 
MJ22FromMnth_3=MJ22FromMnth3
MJ22FromMnth_4=MJ22FromMnth4

MJ22FromYr_=MJ22FromYr1
MJ22FromYr_2=MJ22FromYr2
MJ22FromYr_3=MJ22FromYr3
MJ22FromYr_4=MJ22FromYr4

MJ22ToMnth_=MJ22ToMnth1
MJ22ToMnth_2=MJ22ToMnth2
MJ22ToMnth_3=MJ22ToMnth3
MJ22ToMnth_4=MJ22ToMnth4

OTHER=OTHER1
    ;
rename
   
MH6aCd1 =MH6aCd1_1
MH6aCd6 =MH6aCd1_2
MH6aCd11 =MH6aCd1_3
MH6aCd16 =MH6aCd1_4
MH6aCd21 =MH6aCd1_5
MH6aCd26 =MH6aCd1_6
MH6aCd31 =MH6aCd1_7
MH6aCd2 =MH6aCd2_1
MH6aCd7 =MH6aCd2_2
MH6aCd12 =MH6aCd2_3
MH6aCd17 =MH6aCd2_4
MH6aCd22 =MH6aCd2_5
MH6aCd27 =MH6aCd2_6
MH6aCd32 =MH6aCd2_7
MH6aCd3 =MH6aCd3_1
MH6aCd8 =MH6aCd3_2
MH6aCd13 =MH6aCd3_3
MH6aCd18 =MH6aCd3_4
MH6aCd23 =MH6aCd3_5
MH6aCd28 =MH6aCd3_6
MH6aCd33 =MH6aCd3_7
MH6aCd4 =MH6aCd4_1
MH6aCd9 =MH6aCd4_2
MH6aCd14 =MH6aCd4_3
MH6aCd19 =MH6aCd4_4
MH6aCd24 =MH6aCd4_5
MH6aCd29 =MH6aCd4_6
MH6aCd34 =MH6aCd4_7
MH6aCd5 =MH6aCd5_1
MH6aCd10 =MH6aCd5_2
MH6aCd15 =MH6aCd5_3
MH6aCd20 =MH6aCd5_4
MH6aCd25 =MH6aCd5_5
MH6aCd30 =MH6aCd5_6
MH6aCd35 =MH6aCd5_7
MH6aSpecify1 =MH6aSpecify1_1
MH6aSpecify6 =MH6aSpecify1_2
MH6aSpecify11 =MH6aSpecify1_3
MH6aSpecify16 =MH6aSpecify1_4
MH6aSpecify21 =MH6aSpecify1_5
MH6aSpecify26 =MH6aSpecify1_6
MH6aSpecify31 =MH6aSpecify1_7
MH6aSpecify2 =MH6aSpecify2_1
MH6aSpecify7 =MH6aSpecify2_2
MH6aSpecify12 =MH6aSpecify2_3
MH6aSpecify17 =MH6aSpecify2_4
MH6aSpecify22 =MH6aSpecify2_5
MH6aSpecify27 =MH6aSpecify2_6
MH6aSpecify32 =MH6aSpecify2_7
MH6aSpecify3 =MH6aSpecify3_1
MH6aSpecify8 =MH6aSpecify3_2
MH6aSpecify13 =MH6aSpecify3_3
MH6aSpecify18 =MH6aSpecify3_4
MH6aSpecify23 =MH6aSpecify3_5
MH6aSpecify28 =MH6aSpecify3_6
MH6aSpecify33 =MH6aSpecify3_7
MH6aSpecify4 =MH6aSpecify4_1
MH6aSpecify9 =MH6aSpecify4_2
MH6aSpecify14 =MH6aSpecify4_3
MH6aSpecify19 =MH6aSpecify4_4
MH6aSpecify24 =MH6aSpecify4_5
MH6aSpecify29 =MH6aSpecify4_6
MH6aSpecify34 =MH6aSpecify4_7
MH6aSpecify5 =MH6aSpecify5_1
MH6aSpecify10 =MH6aSpecify5_2
MH6aSpecify15 =MH6aSpecify5_3
MH6aSpecify20 =MH6aSpecify5_4
MH6aSpecify25 =MH6aSpecify5_5
MH6aSpecify30 =MH6aSpecify5_6
MH6aSpecify35 =MH6aSpecify5_7
MH6b =MH6b_1
MH6b2 =MH6b_2
MH6b3 =MH6b_3
MH6b4 =MH6b_4
MH6b5 =MH6b_5
MH6b6 =MH6b_6
MH6b7 =MH6b_7
MH6b8 =MH6b_8

MH6bCd1 =MH6bCd1_1
MH6bCd6 =MH6bCd1_2
MH6bCd11 =MH6bCd1_3
MH6bCd16 =MH6bCd1_4
MH6bCd21 =MH6bCd1_5
MH6bCd26 =MH6bCd1_6
MH6bCd31 =MH6bCd1_7
MH6bCd36 =MH6bCd1_8
MH6bCd2 =MH6bCd2_1
MH6bCd7 =MH6bCd2_2
MH6bCd12 =MH6bCd2_3
MH6bCd17 =MH6bCd2_4
MH6bCd22 =MH6bCd2_5
MH6bCd27 =MH6bCd2_6
MH6bCd32 =MH6bCd2_7
MH6bCd37 =MH6bCd2_8
MH6bCd3 =MH6bCd3_1
MH6bCd8 =MH6bCd3_2
MH6bCd13 =MH6bCd3_3
MH6bCd18 =MH6bCd3_4
MH6bCd23 =MH6bCd3_5
MH6bCd28 =MH6bCd3_6
MH6bCd33 =MH6bCd3_7
MH6bCd38 =MH6bCd3_8
MH6bCd4 =MH6bCd4_1
MH6bCd9 =MH6bCd4_2
MH6bCd14 =MH6bCd4_3
MH6bCd19 =MH6bCd4_4
MH6bCd24 =MH6bCd4_5
MH6bCd29 =MH6bCd4_6
MH6bCd34 =MH6bCd4_7
MH6bCd39 =MH6bCd4_8
MH6bCd5 =MH6bCd5_1
MH6bCd10 =MH6bCd5_2
MH6bCd15 =MH6bCd5_3
MH6bCd20 =MH6bCd5_4
MH6bCd25 =MH6bCd5_5
MH6bCd30 =MH6bCd5_6
MH6bCd35 =MH6bCd5_7
MH6bCd40 =MH6bCd5_8
MH6bSpecify1 =MH6bSpecify1_1
MH6bSpecify6 =MH6bSpecify1_2
MH6bSpecify11 =MH6bSpecify1_3
MH6bSpecify16 =MH6bSpecify1_4
MH6bSpecify21 =MH6bSpecify1_5
MH6bSpecify26 =MH6bSpecify1_6
MH6bSpecify31 =MH6bSpecify1_7
MH6bSpecify36 =MH6bSpecify1_8
MH6bSpecify2 =MH6bSpecify2_1
MH6bSpecify7 =MH6bSpecify2_2
MH6bSpecify12 =MH6bSpecify2_3
MH6bSpecify17 =MH6bSpecify2_4
MH6bSpecify22 =MH6bSpecify2_5
MH6bSpecify27 =MH6bSpecify2_6
MH6bSpecify32 =MH6bSpecify2_7
MH6bSpecify37 =MH6bSpecify2_8
MH6bSpecify3 =MH6bSpecify3_1
MH6bSpecify8 =MH6bSpecify3_2
MH6bSpecify13 =MH6bSpecify3_3
MH6bSpecify18 =MH6bSpecify3_4
MH6bSpecify23 =MH6bSpecify3_5
MH6bSpecify28 =MH6bSpecify3_6
MH6bSpecify33 =MH6bSpecify3_7
MH6bSpecify38 =MH6bSpecify3_8
MH6bSpecify4 =MH6bSpecify4_1
MH6bSpecify9 =MH6bSpecify4_2
MH6bSpecify14 =MH6bSpecify4_3
MH6bSpecify19 =MH6bSpecify4_4
MH6bSpecify24 =MH6bSpecify4_5
MH6bSpecify29 =MH6bSpecify4_6
MH6bSpecify34 =MH6bSpecify4_7
MH6bSpecify39 =MH6bSpecify4_8
MH6bSpecify5 =MH6bSpecify5_1
MH6bSpecify10 =MH6bSpecify5_2
MH6bSpecify15 =MH6bSpecify5_3
MH6bSpecify20 =MH6bSpecify5_4
MH6bSpecify25 =MH6bSpecify5_5
MH6bSpecify30 =MH6bSpecify5_6
MH6bSpecify35 =MH6bSpecify5_7
MH6bSpecify40 =MH6bSpecify5_8
Mh6a =Mh6a_1
Mh6a2 =Mh6a_2
Mh6a3 =Mh6a_3
Mh6a4 =Mh6a_4
Mh6a5 =Mh6a_5
Mh6a6 =Mh6a_6
Mh6a7 =Mh6a_7
;
 
rename DM14Sex=DM14Sex1; 
%macro renameDR_1;
   %do i=1 %to 157;
      %let DR1var=%scan(&dr1lst,&i);
        &DR1var=&DR1var.1
         %end;
 %mend renameDR_1;
 

 %let DR1lst=
        DR9aMnthCl_ 
        DR9aYrCl_ 
        DR9a_ 
        DR1a2_
		
        DR10MnthCl_ 
        DR10YrCl_ 
        DR10_ 
        DR11a10_ 
        DR11a11_ 
        DR11a12_ 
        DR11a13_ 
        DR11a14_ 
        DR11a15_ 
        DR11a16_ 
        DR11a17_ 
        DR11a18_ 
        DR11a19_ 
        DR11a1_ 
        DR11a20_ 
        DR11a21_ 
        DR11a22_ 
        DR11a23_ 
        DR11a24_ 
        DR11a25_ 
        DR11a26_ 
        DR11a27_ 
        DR11a28_ 
        DR11a29_ 
        DR11a2_ 
        DR11a3_ 
        DR11a4_ 
        DR11a5_ 
        DR11a6_ 
        DR11a7_ 
        DR11a8_ 
        DR11a9_ 
        DR11b1_ 
        DR11bAgeOns_ 
        DR11bAgeRec_ 
        DR11bMnthCl_ 
        DR11bOns_ 
        DR11bRec_ 
        DR11bYrCl_ 
        DR11b_ 
        DR11c_ 
        DR11d_ 
        DR11e2MnthCl_ 
        DR11e2YrCl_ 
        DR11e2_ 
        DR11eAgeOns_ 
        DR11eAgeRec_ 
        DR11eOns_ 
        DR11eRec_ 
        DR11e_ 
        DR12a1_ 
        DR12a2MnthCl_ 
        DR12a2YrCl_ 
        DR12a2_ 
        DR12a_ 
        DR12b1MnthCl_ 
        DR12b1YrCl_ 
        DR12b1_ 
        DR12b_ 
        DR12c1MnthCl_ 
        DR12c1YrCl_ 
        DR12c1_ 
        DR12cSpecify_ 
        DR12c_ 
        DR13a_ 
        DR13b_ 
        DR13c_ 
        DR13dMnthCl_ 
        DR13dYrCl_ 
        DR13d_ 
        DR14_ 
        DR14a_ 
        DR14bMnthCl_ 
        DR14bYrCl_ 
        DR14b_ 
        DR15_ 
        DR15aMnthCl_ 
        DR15aYrCl_ 
        DR15a_ 
        DR15b_ 
        DR16MnthCl_ 
        DR16YrCl_ 
        DR16_ 
        DR16a_ 
        DR17MnthCl_ 
        DR17YrCl_ 
        DR17_ 
        DR17a_ 
        DR18_1_ 
        DR18_2_ 
        DR18_3_ 
        DR18_4_ 
        DR18_5_ 
        DR18aMnthCl_ 
        DR18aYrCl_ 
        DR18a_ 
        DR19AgeOns_ 
        DR19AgeRec_ 
        DR19Ons_ 
        DR19Rec_ 
		DR19SxAgeOns_
		DR19SxAgeRec_
		DR19SxOns_
		DR19SxRec_
        DR1_ 
        DR1a1_ 
        DR1a_ 
		DR1a2_ 
        DR1bAgeOns_ 
        DR1bAgeRec_ 
        DR1bOns_ 
        DR1bRec_ 
        DR1c_ 
        DR1f1_ 
        DR1fAgeOns_ 
        DR1fAgeRec_ 
        DR1fOns_ 
        DR1fRec_ 
        DR1f_ 
        DR22A_ 
        DR22_ 
        DR2A_ 
        DR2AgeOns_ 
        DR2B1_ 
        DR2B2_ 
        DR2B_ 
        DR2_NUM_ 
        DR2_UNIT_ 
        DR3_ 
        DR3a_ 
        DR5AgeOns_ 
        DR5AgeRec_ 
        DR5MnthCl_ 
        DR5Ons_ 
        DR5Rec_ 
        DR5YrCl_ 
        DR5_ 
        DR6MnthCl_ 
        DR6YrCl_ 
        DR6_ 	
        DR7MnthCl_ 
        DR7YrCl_ 
        DR7_ 
        DR7aMnthCl_ 
        DR7aYrCl_ 
        DR7a_ 
        DR7bMnthCl_ 
        DR7bYrCl_ 
        DR7b_ 
        DR8MnthCl_ 
        DR8YrCl_ 
        DR8_ 
        DR9_
		DR1iCODEa

        
        ;
rename %renameDR_1 ;

drop   
        DR1a_10-DR1a_34 DR1a1_10-DR1a1_34 
            DR1bAgeOns_10-DR1bAgeons_34
                DR1bOns_10-DR1bOns_34 DR1bAgeRec_10-DR1bAgeRec_34
                DR1bRec_10-DR1bRec_34;
drop DR1c_10-DR1c_34;
      *** DR1_10-DR1_396 removed from drop list--earlier version of interview?;
     ** rewrite this for next version of interview--only 4 abstinent periods;
 %macro renameDRabst;
      array FromMnthVars(25) DR22FromMnth DR22FromMnth2-DR22FromMnth25;
          array ToMnthVars(25) DR22ToMnth DR22ToMnth2-DR22ToMnth25;
          array FromYrVars(25) DR22FromYr DR22FromYr2-DR22FromYr25;
          array ToYrVars(25) DR22ToYr DR22ToYr2-DR22ToYr25;
          %do num=1 %to 5;
                 %let NumDrug=1;
                  DR22FromMnth&Num._&NumDrug=FromMnthVars(&num);
                  DR22ToMnth&Num._&NumDrug=ToMnthVars(&num);
                  DR22FromYr&Num._&NumDrug=FromYrVars(&num);
                  DR22ToYr&Num._&NumDrug=ToYrVars(&num);
          %end;
          %do num=6 %to 25;
             %let DivI=%eval(&num/5);
                 %let MultI=%eval(&DivI*5);
                 %let ModI=%eval(&num-&MultI);
                 %if %eval(&ModI) = 0 %then %do;
                    %let xModI=5;
                        %let xNumDrug=%eval(&DivI);
                 %end;
                
                 %if %eval(&ModI)>0 %then %do;
                    %let xModi=%eval(&ModI);
                    %let xNumDrug=%eval(&DivI+1);
                  %end;
                
         DR22FromMnth&xModI._&xNumDrug=FromMnthVars(&num);
                 DR22ToMnth&xModI._&xNumDrug= ToMnthVars(&num);
                 DR22FromYr&xModI._&xNumDrug=FromYrVars(&num);
                 DR22ToYr&xModI._&xNumDrug= ToYrVars(&num);

                 
          %end;
   %mend;
   %renameDRabst

   *drop MJ19List1-MJ19list18;
    drop 
    AL43FromMnth_5 AL43ToMnth_5 AL43FromYr_5 AL43ToYr_5
    dr1i_ANOTHER dr1i_ANOTHER2-dr1i_ANOTHER5
         
         drsxcount2-drsxcount5
     DRMnthClCount2-DRMnthClCount5
     DRYrClCount DRYrClCount2-DRYrClCount5
        NumDrugs
     UseDrugFill
     Varname12-Varname14
     TBQsx TBQsx2-TBQsx14
    SPECIFY SPECIFY2-SPECIFY14
    STIMULANTS
    OPIATES
        COCAINE
        SEDATIVES
    MARIJUANA
        ALCOHOL
		OTHER15
    DRMnthClCount2-DRMnthClCount5
    PAST12Mos
	Past6Mos
    real_id
    
    FinalQuestionYN
    real_id
        CHANGE_id
        CurrYr
        CurrMnth
        
        ;

     drop dr22fromyr dr22fromyr2-dr22fromyr25
          dr22toyr dr22toyr2-dr22toyr25
          dr22frommnth dr22frommnth2-dr22frommnth25
          dr22tomnth dr22tomnth2-dr22tomnth25
          DRSxCount DrMnthClCount;
               

drop DM10a DM15d_chk5;

drop TB10c1 TBYrCl TB17Specify;

drop DP18Cd4  DP18DRUG4  DP24_YR DP24_mo DP27SxCount
       DP27dMo DP27dYr DPSxCount
      DP18Cd4  DP24_YR DP24_mo;

drop DR5a_ DR5a_2-DR5a_5;  ** will be eliminated in next version of interview;
drop DR22ToMnth5_1-DR22ToMnth5_5 DR22FromMnth5_1-DR22FromMnth5_5
        DR22ToYr5_1-DR22ToYr5_5 DR22FromYr5_1-DR22FromYr5_5;
                    ** variables for 5th abstinence period will be eliminated in next version;
drop DR1c_10-DR1c_34; 
drop DR1a1_12 DR1a1_13;
drop al39_specify1 al39_code1 AL11AGeRec AL11Rec Past6mos;
*drop TB20dCl;
drop al37tot; 
%include 'S:\renamePTprobevars.txt';
   


data ss2y;set ss2;
   *** extraneous withdrawal variables;
drop DR11a2_4
        DR11a3_4 
        DR11a5_3 DR11a5_4
        DR11a6_3 
        DR11a7_3 DR11a7_4
        DR11a8_3 DR11a8_4
        DR11a9_3 DR11a9_4
        DR11a10_1-DR11a10_3
        DR11a11_1-DR11a11_3
        DR11a12_1-DR11a12_3
        DR11a13_1-DR11a13_3
        DR11a14_1-DR11a14_3
        DR11a15_1-DR11a15_3
        DR11a16_1-DR11a16_3
        DR11a17_1-DR11a17_3
        DR11a18_1 DR11a18_2
        DR11a19_1 DR11a19_2
        DR11a20_1 DR11a20_2
        DR11a21_1 DR11a21_2
        DR11a22_1 DR11a22_2 DR11a22_4
        DR11a23_1 DR11a23_2 DR11a23_4
        DR11a24_1 DR11a24_2 DR11a24_4
        DR11a25_1 DR11a25_2 DR11a25_4
        DR11a26_1 DR11a26_2 DR11a26_4
        DR11a27_1 DR11a27_2 DR11a27_4
        DR11a28_1 DR11a28_2 DR11a28_4
        DR11a29_1 DR11a29_2 DR11a29_4;
drop MJ22FromMnth_5 MJ22ToMnth_5 
         MJ22FromYr_5 MJ22ToYr_5;
%macro renameDRINKS;
    %do i=1 %to 7;
      rename BEER&i= AL3WEEK_BEER&I;
      rename WINE&i= AL3WEEK_WINE&I;
      rename LIQUOR&i= AL3WEEK_LIQUOR&I;
      rename OTHER&i= AL3WEEK_OTHER&I;
    %END;
    %do i=8 %to 14;
      %let j=%eval(&i-7);
      rename BEER&i= AL4WEEK_BEER&J;
      rename WINE&i= AL4WEEK_WINE&J;
      rename LIQUOR&i= AL4WEEK_LIQUOR&J;
      rename OTHER&i= AL4WEEK_OTHER&J;
    %END;
  %mend;
 %renamedrinks		 
       

data ss2x;set ss2y;
   missing K;
     **** set Unkown, Refused missing values to .K;
 %include 'S:\L1vars.include'; 
 %include 'S:\L2Vars.include'; 
 %include 'S:\L3vars.include';
 %include 'S:\L4Vars.include'; 
data blanks;set ss2x;
   if (intv_dt='')*(dm1=.)*(dm3b=.);
data ss3;set ss2x;
   if (intv_dt='')*(dm1=.)*(dm3b=.) then do;
     put 'blank record' ind_id=;
         delete;
   end;
   

 proc sort; by ind_id;
 data duplicates(keep=ind_id);set ss3;
    if ind_id=lag(ind_id);
data ss4(drop=charState1-charState53 i DM5a DM5b HE2 intv_dt day month);
   set ss3;
   
      ageplus1=age+1;
      if al1AgeRec=ageplus1 then AL1AgeRec=age;
      drop ageplus1;
     *************;

;

   length DM5a_State DM5b_State HE2_State $ 2;
   array charState(53) $('AL' 'AK' 'AR' 'AZ' 'CA' 'CO' 'CT' 'DE' 'DC' 'FL'
           'GA' 'HI' 'ID' 'IL'
           'IN' 'IA' 'KS' 'KY' 'LA' 'ME' 'MD' 'MA'
           'MI' 'MN' 'MS' 'MO' 'MT' 'NE' 'NV' 'NH' 'NJ' 'NM' 'NY'
           'NC' 'ND'
            'OH' 'OK' 'OR' 'PA' 'RI' 'SC' 'SD' 'TN' 'UT' 'TX'
           'VT' 'VI' 'VA' 'WA' 'WV' 'WI' 'WY' 'NA');

      if DM5a not in(.,.K) then do;
        i=DM5a;
        DM5a_State=charstate(i);
      end;
      if DM5b not in(.,.K) then do;
        i=DM5b;
        DM5b_State=charstate(i);
      end;
      if HE2 not in(.,.K) then do;
        i=HE2;
        HE2_State=charstate(i);
      end;
	  

   day=(substr(intv_dt,1,2))*1;
      month=(substr(intv_dt,3,2))*1;
      IntvYr=(substr(intv_dt,5,4))*1;
      IntvDate=mdy(month,day,IntvYr);
      format IntvDate Date9.;

    array numvars _NUMERIC_;
       do i=1 to dim(numvars);
         if (numvars(i)>999999)*~(1<=int(numvars(i)/10000000)<=6) then do;
               put ind_id= numvars(i)= ;
               numvars(i)=.K;
             end;
       end;
   *drop i;
   

data ncanda.nssaga;set ss4;
   proc contents;run;
  ;




run;
