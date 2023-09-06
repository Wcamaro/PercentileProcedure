


from osgeo import gdal
import numpy as np
from exceptions import TypeError, ImportError
import os,sys
import datetime
from datetime import timedelta, date
from netCDF4 import Dataset
from osgeo import gdal_array
from osgeo import osr
global bbox_trmm2_daily
global cells_degree
global cells_size
import datetime

"""
bbox bin
"""

bbox_trmm2_daily = {
        'top': 50,
        'bottom': -50,
        'left': -180,
        'right': 180
}


"""
General Parameters
"""

cells_size = 0.25
cells_degree = 1/cells_size

def init(filename,bbox=None,rt=None):
    """
    Loads a TRMM data into a matrix. The Open method is set to load the :0 band of the file
    which corresponds to the precipitation data. To load the error switch to the :1. By. Simone Dalmasso
    """
    ext = os.path.splitext(filename)[-1]
    bbox = checkBbox(bbox)
    reshaped = reshape(filename,ext,rt)
    rearranged = rearrange(reshaped)
    matrix = cut(rearranged,bbox)
    return matrix, bbox 
    
    

def checkBbox(bbox):
    """
    Returns the correct bbox. By Simone Dalmasso. 
    """
    if not bbox:
                    bbox = bbox_trmm2_daily
    elif not isinstance(bbox,dict):
            raise TypeError('BBOX must be a dictionary in key: values pairs !!!!')
    return bbox

def reshape(filename,ext,rt=None):
    """
    Opens and reshapes an image file. By Simone Dalmasso.
    """
    if ext == '.bin':
        fp = open(filename, 'rb')
        data_string = fp.read()
        fp.close()
        raw_file = np.fromstring(data_string, np.float32)
        raw_file = raw_file.byteswap()
        raw_file = np.asarray(raw_file, np.float32)
        if rt == 1:
            reshaped_matrix = raw_file.reshape(480, 1440)
            reshaped_matrix = reshaped_matrix[40:440]
        else:
            reshaped_matrix = raw_file.reshape(400, 1440)
        reshaped_matrix = np.flipud(reshaped_matrix)
        return reshaped_matrix
    elif ext == '.nc4':
        raw_file = Dataset(filename)
        array = raw_file['precipitation'][:]
        array_rot = np.rot90(array)
        right_array = array_rot[:, 720:]
        left_array = array_rot[:, :720]
        reversed_array = np.hstack((right_array, left_array))
        if rt == 1:
            reversed_array = reversed_array[40:440]
        return reversed_array


def rearrange(matrix):
    b = np.split(matrix,2,axis=1)[0]
    a = np.split(matrix,2,axis=1)[1]
    rearranged = np.concatenate((a,b),axis=1)
    return rearranged
    
def cut(raw_matrix,bbox):
    """
    Fuction for slicing the given matrix based on the passed bounding box
    By Simone Dalmasso.
    """

    bbox_matrix = bbox_trmm2_daily
    cell_bbox_size = {
            'x': abs(bbox['left']-bbox['right'])*cells_degree,
            'y': abs(bbox['top']-bbox['bottom'])*cells_degree
    }
    slice_start = {
            'x': abs(bbox_matrix['left']-bbox['left'])*cells_degree,
            'y': abs(bbox_matrix['top']-bbox['top'])*cells_degree
    }
    slice_end = {
            'x': slice_start['x']+cell_bbox_size['x'],
            'y': slice_start['y']+cell_bbox_size['y'],
    }
    matrix_sliced_y = raw_matrix[slice_start['y']:slice_end['y']]
    matrix_sliced = [row[slice_start['x']:slice_end['x']] for row in matrix_sliced_y]
    return matrix_sliced

def mat_to_dict(folder_root,idate,edate,bbox1=None,rt=None):
    dict_matrix = {}
    for cdate in range(idate,edate+1):
            year_curr = str(date.fromordinal(cdate).year)
            if len(str(date.fromordinal(cdate).month))==2:
                month_curr = str(date.fromordinal(cdate).month)
            else:
                month_curr = '0%s' % str(date.fromordinal(cdate).month)
            if len(str(date.fromordinal(cdate).day))==2:
                day_curr = str(date.fromordinal(cdate).day)
            else:
                day_curr = '0%s' % str(date.fromordinal(cdate).day)
            if os.path.exists(r'%s/%s/%s/3B42_daily.%s.%s.%s.7.bin' % (folder_root, year_curr, month_curr, year_curr, month_curr, day_curr)):
                filename = r'%s/%s/%s/3B42_daily.%s.%s.%s.7.bin' % (folder_root, year_curr, month_curr, year_curr, month_curr, day_curr)
                RT = None
            elif os.path.exists(r'%s\%s\%s\3B42_Daily.%s%s%s.7.nc4' % (folder_root, year_curr, month_curr, year_curr, month_curr, day_curr)):
                filename = r'%s\%s\%s\3B42_Daily.%s%s%s.7.nc4' % (folder_root, year_curr, month_curr, year_curr, month_curr, day_curr)
                RT = None
            else:
                filename = None
                print 'Not current_date file: %s' % date.fromordinal(cdate)
                continue
            (matrix,bbox) = init(filename, bbox=bbox1, rt=RT)
            matrix = np.asarray(matrix)
            matrix [matrix == -9999.9] = -99
            dict_matrix[cdate-idate] = matrix
    return dict_matrix
        
def perct_dict(dict_matrix,minvalue,perc):
    dict_shape = np.shape(dict_matrix[dict_matrix.keys()[0]])
    dim_flat = dict_shape[0]*dict_shape[1]
    percvector = []
    for pos in range(0,dim_flat):
        vect =np.asarray([dict_matrix[k].flat[pos] for k in dict_matrix.keys()],dtype = np.float32)
        vect = vect[vect>minvalue]
        if len(vect)>0:
            percv = np.percentile(vect, perc)
        else:
            percv = -99
        percvector = np.append(percvector, percv)
    percarray = np.reshape(percvector, dict_shape)
    return percarray

def dict_to_mat(dict_x):
    coords = sorted(dict_x.keys(), reverse=True)
    array = dict_x[coords[0]]
    for coord in coords[1:]:
        array = np.append(array, dict_x[coord], axis=0)
        print coord
    return array 

def WriteGTiff_perc(dict_x,folder,period,xmin,xmax,ymin,perc):
    """
    Write a Gtiff, from a dictionary (Elements = Numpy Array type) defining each
    element from the dictionary like a Raster.
    """
    gdal.AllRegister()
    driver = gdal.GetDriverByName('Gtiff')
    array = dict_to_mat(dict_x)
    nrows,ncols = np.shape(array)
    array[np.isnan(array)] = -99
    array[np.isinf(array)] = -99
    xres = (xmax-xmin)/float(ncols)
    ymax = max(dict_x.keys())
    ymin = ymin
    yres = (ymax-ymin)/float(nrows)
    geotransform = (xmin,xres,0,ymax,0,-yres)
    filename = r'%s/Trmm3B42_%sPercentile_%s.%s_%s.tif' % (folder,str(perc),period,str(ymax),str(ymin))
    outDataset = driver.Create(filename,ncols,nrows,1,gdal.GDT_Float32)
    outDataset.SetGeoTransform(geotransform)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    outDataset.SetProjection(srs.ExportToWkt())
    nband = 1
    outband = outDataset.GetRasterBand(nband)
    outband.SetNoDataValue(-99)
    outband.WriteArray(array)
    outband.GetStatistics(0,1)
    outband = None
    outDataset = None

def cumulatedict(dict_x,cumulate):
    cumulate_dict_matrix = {}
    keys = dict_x.keys()
    keys.sort()
    for key in keys[cumulate:]:
        cumulate_value = np.zeros_like(dict_x.keys()[0])
        for k in range(key-cumulate,key+1):
            if k in keys:
                cumulate_value = cumulate_value + (dict_x[k] * (dict_x[k] >= 0))
            else:
                break
            cumulate_dict_matrix[key] = cumulate_value
    return cumulate_dict_matrix

        
def nvalues_dict(dict_matrix,minvalue):
    dict_shape = np.shape(dict_matrix[0])
    dim_flat = dict_shape[0]*dict_shape[1]
    quantvector = []
    for pos in range(0,dim_flat):
        vect =np.asarray([dict_matrix[k].flat[pos] for k in dict_matrix.keys()],dtype = np.float32)
        vect = vect[vect>minvalue]
        quantvector = np.append(quantvector, len(vect))
    quantarray = np.reshape(quantvector, dict_shape)
    return quantarray
      

    
