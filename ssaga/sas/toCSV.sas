LIBNAME stat 'Z:\tmp\ssaga';
 DATA stat.new_dx_nssaga; 
	SET stat.dx_nssaga; 
RUN;

proc export data=stat.new_dx_nssaga
	   outfile='z:\tmp\ssaga\dx_nssaga.csv'
	   dbms=csv
       replace;
run;
