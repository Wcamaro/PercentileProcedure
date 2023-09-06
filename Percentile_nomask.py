"""
Author: Walther C.A. Camaro G. : walther.camaro@gmail.com
"""


from process_percentile_nomask import mat_to_dict, perct_dict, WriteGTiff_perc, cumulatedict
import datetime
from datetime import timedelta, date
import numpy as np
import os
import time

folder_root = r'D:\Python_Projects\Data\TRMM\TRMM_3B42_daily'
initial_date = datetime.date(1998,01,01)
end_date = datetime.date(2016,11,30)
idate = date.toordinal(initial_date)
edate = date.toordinal(end_date)
days = date.toordinal(end_date)-date.toordinal(initial_date)+1
percs = [95,97,99]
minvalue = 0
for cumulate in range(0,3):
    for perc in percs:
        dict_percentile = {}
        for i in range(50,-50,-10):
            bbox1 = {
                    'top': i,
                    'bottom': i-10,
                    'left': -180,
                    'right': 180
            }
            dict_matrix = mat_to_dict(folder_root,idate,edate,bbox1=bbox1,rt=None)
            if cumulate >0:
                dict_cumulate = cumulatedict(dict_matrix,cumulate)
            else:
                dict_cumulate = dict_matrix
            perc_array = perct_dict(dict_cumulate,minvalue,perc)
            perc_array = np.asarray(perc_array, dtype=np.float32)
            dict_percentile[i]=perc_array
        folder_output = r'D:\Python_Projects\Results\TRMM\Percentile2017\%sDays' % (str(cumulate+1))
        if not os.path.exists(folder_output):
                        os.makedirs(folder_output)
        period_name = '%s.%s.%s_%s.%s.%s.%sDaysCumulated' % (initial_date.day,initial_date.month,initial_date.year,end_date.day,end_date.month,end_date.year,str(cumulate+1))
        WriteGTiff_perc(dict_percentile,folder_output,period_name,bbox1['left'],bbox1['right'],bbox1['bottom'],perc)
print 'Thank You, Procedure Finished. By W.Camaro'

