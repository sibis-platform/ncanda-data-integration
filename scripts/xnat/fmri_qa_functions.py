#!/usr/bin/env python

##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##

import re
import os
import os.path
import tempfile
import shutil

from sibispy import sibislogger as slog
from sibispy import utils as sutil

# QA metric thresholds - defines a general threshold, either upper or lower.
#  Having this as a class makes it easier to put all thresholds, upper and lower, into a single table.
class QAMetric:
    # Create object
    def __init__( self, thresh, name, sign ):
        self._thresh = thresh
        self._name = name
        self._sign = sign

    # Check whether a value exceeds this metric threshold (either above or below, depending on "_sign"
    def exceeds( self, value ):
        if (value * self._sign) > (self._thresh * self._sign):
            return True
        else:
            return False


# QA metric thresholds: 'sign' is +1 for upper limits (these should not be exceeded), and -1 for lower limits (these must be exceeded)
QA_thresholds = { 'percentFluc': QAMetric( .15, 'Percent Fluctuation', +1 ),
                  'drift': QAMetric( 0.7, 'Drift', +1 ),
                  'driftfit': QAMetric( 0.7, 'Drift Fit', +1 ),
                  'SNR': QAMetric( 200, 'Signal-to-Noise Ratio', -1 ),
                  'SFNR': QAMetric( 200, 'Signal-to-Fluctuation-Noise Ratio', -1 ) }

# Run Phantom QA procedure on a single scan series
def run_phantom_qa( interface, project, subject, session, label, dicom_path ):
    # Make a temporary directory
    temp_dir = tempfile.mkdtemp()

    # Switch to temp directory
    original_wd = os.getcwd()
    os.chdir(temp_dir)

    # Make XML file as wrapper for the DICOM files
    bxh_file = '%s.bxh' % session[7:]
    if (not sutil.dicom2bxh(dicom_path, bxh_file)) or (not os.path.exists( bxh_file )):
        error = "ERROR: BXH file was not created from DICOM files"
        slog.info(session,error,
                  bxh_file = bxh_file,
                  dicom_path = dicom_path)
        return

    # Run the PERL QA script and capture its output
    html_dir = './html'
    script_output = os.popen( 'fmriqa_phantomqa.pl %s %s 2> /dev/null' % (bxh_file,html_dir) ).readlines()
    if not os.path.exists( '%s/index.html' % html_dir ):
        error =  "ERROR: html file %s/index.html was not created from BXH file %s (session %s/%s)" % ( html_dir, bxh_file, session, label )
        qa_script_output = '\n'.join( script_output )
        slog.info('session {}/{}'.format(session, label),error,
                      html_dir = html_dir,
                      bxh_file = bxh_file,
                      qa_script_output = qa_script_output)
        return

    # Copy the entire output to a text file for upload to XNAT
    details_file_path = '%s/QA-Details.txt' % temp_dir
    script_output_file = open( details_file_path, 'w' )
    script_output_file.writelines( script_output )
    script_output_file.close()

    # Upload detail file to XNAT
    try:
        qa_file = interface.select.project( project ).subject( subject ).experiment( session ).resource('QA').file( 'QA-Details.txt' )
        qa_file.insert( details_file_path, format='text', tags='qa,fbirn,txt', content='QA Analysis Details', overwrite=True )
    except:
        print "Something bad happened uploading QA details file to Experiment %s/%s/%s" % (project,session,label)

    # Step through QA output, line by line, and check for measures for which we have thresholds defined.
    for line in script_output:
        # Parse current line into key=value pairs
        match = re.match( '^#([A-Za-z]+)=(.*)$', line )

        # Is this key in the list of thresholds?
        if match and (match.group(1) in QA_thresholds.keys()):
            value = float( match.group(2) )
            metric = QA_thresholds[match.group(1)]
            if metric.exceeds(value):
                error = 'QA metric fails to meet threshhold.'
                slog.info(session,error,
                              project_id = project,
                              experiment_site_id = label,
                              metric_name=metric._name,
                              metric_key=match.group(1),
                              metric_value=value,
                              metric_threshold=metric._thresh)

    # Convert QA results from html to pdf
    summary_file_path = '%s/QA-Summary.pdf' % temp_dir
    if sutils.htmldoc('htmldoc --quiet --webpage --no-title --no-toc --compression=9 --outfile %s %s/index.html' % (summary_file_path,html_dir)) and os.path.exists( summary_file_path ):
        # Upload QA files to XNAT as file resources
        try:
            qa_file = interface.select.project( project ).subject( subject ).experiment( session ).resource('QA').file( 'QA-Summary.pdf' )
            qa_file.insert( summary_file_path, format='pdf', tags='qa,fbirn,pdf', content='QA Analysis Summary', overwrite=True )
        except:
            print "Something bad happened uploading QA summary file to Experiment %s/%s" % (session,label)
    else:
        print "Unable to create PDF QA summary file %s from DICOMs in %s (session %s/%s)" % (summary_file_path, dicom_path, session, label )

    # Clean up - remove temp directory
    os.chdir( original_wd )
    shutil.rmtree( temp_dir )


# Process a phantom MR imaging session
def process_phantom_session( interface, project, subject, session, label, xnat_dir,force_updates=False ):
    # Get the experiment object
    experiment = interface.select.experiment( session )

    # First, see if the QA files are already there
    files = experiment.resources().files().get()
    if force_updates or not (('QA-Summary.pdf' in files) and ('QA-Details.txt' in files)):
        dicom_path=''

        # Get list of all scans in the session
        scans = experiment.scans().get()
        for scan in scans:
            # Check only 'usable' scans with the proper name
            [scan_type,quality] = experiment.scan( scan ).attrs.mget( ['type', 'quality'] )
            if re.match( '.*-rsfmri-.*', scan_type ):
                # Extract the DICOM file directory from the XML representation
                match = re.match( '.*(' + xnat_dir + '/.*)scan_.*_catalog.xml.*', experiment.scan( scan ).get(), re.DOTALL )
                if match:
                    dicom_path = match.group(1)

        if dicom_path:
            # If we found a matching scan, run the QA
            run_phantom_qa( interface, project, subject, session, label, dicom_path )
        else:
            # If there was no matching scan in the session, print a warning
            print "WARNING: fBIRN phantom session %s/%s does not have a usable rsfmri scan" % (session,label)


# Run Subject QA procedure on a single scan series
def run_subject_qa( interface, project, subject, session, scan_number, dicom_path ):
    # Make a temporary directory
    temp_dir = tempfile.mkdtemp()

    # Make XML file as wrapper for the DICOM files
    bxh_file = '%s/dicoms.bxh' % temp_dir
    if (not sutil.dicom2bxh(dicom_path, bxh_file)) or (not os.path.exists( bxh_file )):
        error = "ERROR: BXH file was not created from DICOM files"
        slog.info(session,error,
                  bxh_file = bxh_file,
                  dicom_path = dicom_path)
    return

    # Run the PERL QA script and capture its output
    html_dir = '%s/html' % temp_dir
    script_output = os.popen( 'fmriqa_generate.pl %s %s 2> /dev/null' % (bxh_file,html_dir) ).readlines()
    if not os.path.exists( html_dir ):
        error = "ERROR: html directory was not created from BXH file"
        slog.info(html_dir,error,
                      bxh_file = bxh_file)
        return

    # Convert QA results from html to pdf
    summary_file_path = '%s/QA-Summary.pdf' % temp_dir
    if sutils.htmldoc('--webpage --browserwidth 1024 --no-title --no-toc --compression=9 --outfile %s %s/index.html >& /dev/null' % (summary_file_path,html_dir)) and os.path.exists( summary_file_path ):
        # Upload QA files to XNAT as file resources
        try:
            qa_file = interface.select.project( project ).subject( subject ).experiment( session ).resource('QA').file( 'QA-%s-Summary.pdf' % scan_number )
            qa_file.insert( summary_file_path, format='pdf', tags='qa,fbirn,pdf', content='QA Analysis Summary', overwrite=True )
        except:
            print "Something bad happened uploading QA summary file to Experiment %s" % session
    else:
        print "Unable to create PDF QA summary file %s" % summary_file_path

    # Clean up - remove temp directory
    shutil.rmtree( temp_dir )


# Process a subject MR imaging session
def process_subject_session( interface, project, subject, session, xnat_dir, force_updates=False ):
    # Get the experiment object
    experiment = interface.select.experiment( session )

    # Get list of all scans in the session
    scans = experiment.scans().get()
    for scan in scans:
        # Check only 'usable' scans with the proper name
        [scan_type,quality] = experiment.scan( scan ).attrs.mget( ['type', 'quality'] )
        if re.match( '.*fmri.*', scan_type ):
            # Extract the DICOM file directory from the XML representation
            match = re.match( '.*('+ xnat_dir + '/.*)scan_.*_catalog.xml.*', experiment.scan( scan ).get(), re.DOTALL )
            if match:
                # If we found a matching scan, run the QA
                run_subject_qa( interface, project, subject, session, scan, match.group(1) )
