"""
Author: Walther C.A. Camaro G. : walther.camaro@gmail.com
"""

import process_percentile
from process_percentile import mat_to_dict, nvalues_dict, WriteGTiff_perc
import datetime
from datetime import timedelta, date
import numpy as np
import os
import time

folder_root = r'/media/sf_Share_VM/TRMM_3B42_daily'
initial_date = datetime.date(1998,01,01)
end_date = datetime.date(2013,8,31)
t1 = time.time()
idate = date.toordinal(initial_date)
edate = date.toordinal(end_date)
days = date.toordinal(end_date)-date.toordinal(initial_date)+1
minvalue = 40
dict_nvalues = {}
for i in range(50,-50,-2):
    bbox1 = {
            'top': i,
            'bottom': i-2,
            'left': -180,
            'right': 180
            }
    dict_matrix = mat_to_dict(folder_root,idate,edate,bbox1=bbox1,rt=None)
    nvalues_array = nvalues_dict(dict_matrix,minvalue)
    nvalues_array = np.asarray(nvalues_array, dtype=np.float32)
    dict_nvalues[i]=nvalues_array
    t2 = time.time()
    print t2 - t1
    print i
    folder_output = r'/media/sf_Share_VM/TRMM_TEST/Percentile/' 
if not os.path.exists(folder_output):
    os.makedirs(folder_output)
period_name = '%s.%s.%s_%s.%s.%s' % (initial_date.day,initial_date.month,initial_date.year,end_date.day,end_date.month,end_date.year)
WriteGTiff_perc(dict_nvalues,folder_output,period_name,bbox1['left'],bbox1['right'],'NValuesBigger40mm')
t3 = time.time()
print t3-t2
print 'Days = %s' % str(days)
print 'Thank You, Procedure Finished. By W.Camaro'

