#!/usr/bin/env python

##
##  Copyright 2016 SRI International
##  See COPYING file distributed along with the package for the copyright and license terms.
##
"""
Generate a plot of the SNR across NCANDA sites.
"""
__author__ = "Nolan Nichols"

import os
import glob
import dateutil

import pandas as pd
import lxml.etree as etree
import matplotlib.pyplot as plt

# start with just the SRI phantoms

archive = os.path.abspath('/fs/ncanda-xnat/archive')
sri_glob = 'sri_incoming/arc001/B-99999-P-9-*'
upmc_glob = 'upmc_incoming/arc001/A-99999-P-9-*'
duke_glob = 'duke_incoming/arc001/C-99999-P-9-*'
ucsd_glob = 'ucsd_incoming/arc001/E-99999-P-9-*'
ohsu_glob = 'ohsu_incoming/arc001/D-99999-P-9-*'
phantom = 'RESOURCES/QA/phantom.xml'
xml_dict = dict(sri=glob.glob(os.path.join(archive, sri_glob, phantom)),
                upmc=glob.glob(os.path.join(archive, upmc_glob, phantom)),
                duke=glob.glob(os.path.join(archive, duke_glob, phantom)),
                ucsd=glob.glob(os.path.join(archive, ucsd_glob, phantom)),
                ohsu=glob.glob(os.path.join(archive, ohsu_glob, phantom)))


def get_phantom_ts(xml_list, metric):
    """
    Get a timeseries of phantom metrics
    :param xml_list:
    :param metric: cnr or snr
    :return:
    """
    # Get a list of all the dates to use as indices
    timepoints = [dateutil.parser.parse(fi.split('/')[6].split('-')[-1]) for fi in xml_list]

    # Get a list of all the metric values
    m = [float(etree.ElementTree(file=fi).find('./{0}'.format(metric)).text) for fi in xml_list]

    # Build a pandas timeseries
    series = pd.Series(data=m, index=timepoints)
    return series

snr = {k: get_phantom_ts(v, 'snr') for k, v in xml_dict.iteritems()}
snr_plots = [v.plot(label=k) for k, v in snr.iteritems()]
snr_ledgend = [i.legend(loc="bottom right") for i in snr_plots]


#cnr = {k: get_phantom_ts(v, 'cnr') for k, v in xml_dict.iteritems()}
#cnr_plots = [v.plot(label=k) for k, v in cnr.iteritems()]
#cnr_ledgend = [i.legend(loc="bottom right") for i in cnr_plots]

plt.show()

