/*                                                                      */
/*  Copyright 2015 SRI International                                    */
/*  License: https://ncanda.sri.com/software-license.txt                */
/*                                                                      */
/*  $Revision: 2120 $                                                   */
/*  $LastChangedBy: nicholsn $                                          */
/*  $LastChangedDate: 2015-08-07 14:23:35 -0700 (Fri, 07 Aug 2015) $    */
/*                                                                      */
LIBNAME stat 'Z:\tmp\ssaga';
 DATA stat.new_dx_nssaga; 
	SET stat.dx_nssaga; 
RUN;

proc export data=stat.new_dx_nssaga
	   outfile='z:\tmp\ssaga\dx_nssaga.csv'
	   dbms=csv
       replace;
run;
