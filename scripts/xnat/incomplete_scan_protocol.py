#!/usr/bin/env python
##
##  Copyright 2016 SRI International
##  See COPYING file distributed along with the package for the copyright and license terms.
####  $Revision: 2110 $
##  $LastChangedBy: nicholsn $
##  $LastChangedDate: 2015-08-07 09:10:29 -0700 (Fri, 07 Aug 2015) $
##

import sys
import os

scan_manufacture = dict('A'='Seimens',
                        'B'='GE',
                        'C'='GE',
                        'D'='Seimens',
                        'E'='GE')

num_of_field_maps = dict('Seimens'= 2,
                         'GE' = 1)
