#!/usr/bin/env python
import sibis_wine
import os 
import tempfile
import shutil

sibis_wine.log("test-id","test-title", err_msg = "Nothing wrong")

(ecode,sout,eout) = sibis_wine.sas('test.sas')
if ecode != 2 : 
    print "Error:SAS:Code", ecode
    print eout

tempdir = tempfile.mkdtemp()
(ecode,sout,eout) = sibis_wine.manipula(tempdir,'/fs/storage/laptops/ncanda/sri5/Youth_SAAGAv3/NSSAGA_v3.bdb')
if ecode : 
    print "Error:manipula:Code ", ecode
    print eout

shutil.rmtree( tempdir )


