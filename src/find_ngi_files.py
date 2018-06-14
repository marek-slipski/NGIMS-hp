#!env/bin python

import argparse
import glob
import numpy as np
import datetime as dt
import yaml
import sys
import os

######################################################################
# Script to search for NGIMS L2 files within date range or orbit range,
# csn, cso, or osion, and to create new file that is a list of filenames
#
# Marek Slipski
# 20170613
######################################################################

with open('config.local','rb') as cf:
    config = yaml.load(cf)
tempbase = config['data_path']
pathbase = 'maven/data/sci/ngi/l2/'
base = os.path.expanduser(tempbase+pathbase)


## Not specifying some other things
time = 'T[0-9][0-9][0-9][0-9][0-9][0-9]'


###### Filename setup ####################################
#example: 'mvn_ngi_l2_csn-abund-18714_20160201T060713_v06_r02.csv'

## Source specify
def source_to_search(source):
    '''
    String to use in search for csn/cso/ion

    Inputs
    ------
    source: str, ['neutrals','csn','cso','ion']

    Outputs
    -------
    ss: str
    '''
    if source == 'neutrals':
        ss = 'c[a-z][a-z]'
    else:
        ss = source
    return ss

def vr_to_search(v,r):
    '''verion/revision string in file
    v,r: ints
    versrev: str, found in L2 files (v07_r01)
    '''
    versrev = 'v'+str(v).zfill(2)+'_r'+str(r).zfill(2)
    return versrev


def orb_to_tid(orbnum,orbtidfile='src/ngims_tid_orbit.dat'):
    dType = [str,int,int]
    with open(orbtidfile,'rb') as f:
        for line in f:
            linelist = line.rstrip().split(',')
            linelist = [t(x) for t,x in zip(dType,linelist)]
            if linelist[1] == orbnum:
                return linelist[2]

def tid_to_orb(tidnum,orbtidfile='src/ngims_tid_orbit.dat'):
    '''
    Function to convert TID number to orbit number.
    Requires orbtidfile from make_orb_tid()
    '''
    with open(orbtidfile,'rb') as orbf:
        for line in orbf:
            linelist = line.rstrip().split(',')
            if linelist[2] == tidnum:
                orb = linelist[1]
                return orb

def orb_from_path(path):
    dirs = path.split('/')
    fname = dirs[-1]
    parts = fname.split('_')
    tid_pieces = parts[3].split('-')
    orb = tid_to_orb(tid_pieces[-1])
    return int(orb)

def orb_num(filename):
    return tid_to_orb(filename[60:65])

def datetime_from_file(filename):
    dstring = filename[-27:-12]
    return dt.datetime.strptime(dstring,'%Y%m%dT%H%M%S')

################################################################################
################################################################################

def all_files(v,r,source='neutrals'):
    '''
    Finds all NGIMS L2 (csn/cso) files
    '''
    year = '[0-9]'*4
    month = '[0-9]'*2
    fullbase = base + year + '/'+month+'/'
    source_str = source_to_search(source)
    versrev=vr_to_search(v,r)
    return glob.glob(fullbase+'*_'+source_str+'*'+versrev+'.csv')

def make_orb_tid(source,vers,rev,savefile):
    os.system('rm -f '+savefile) #remove old, create new
    allfiles = all_files(vers,rev,source)
    print 'Creating new NGIMS orbit/tid file...'
    for f in allfiles:
        #read focusmode, tid, and orbit columns from csv file
        #then append to new savefile
        os.system('awk -F, \'NR == 2 {OFS=","; print $7,$6,$5}\' ' +f + ' >> '+savefile)
#########################################################

### Find all orbs/dates #################################
def get_orbrange(start,stop):
    '''
    List of orbits to loop through to find matching files
    '''
    orbrange = np.arange(start,stop+1) #to loop through
    return orbrange

def get_daterange(start,stop):
    '''
    List of dates to loop through to find matching files
    Inputs
    ------
    start,stop: str, date formated as YYYYMMDD

    Outputs
    -------
    daterange: list of datetime objects
    '''
    d1 = dt.datetime.strptime(str(start),'%Y%m%d')
    d2 = dt.datetime.strptime(str(stop),'%Y%m%d')
    daterange = [d1 + dt.timedelta(days=x) for x in range((d2-d1).days + 1)]
    return daterange

def parse_dt_input(dtinput):
    if type(dtinput) == int:
        dtinput = str(dtinput)
        if len(str(dtinput))==8: #date...
            fmt = '%Y%m%d'
        elif len(str(dtinput))==14: #...or datetime
            fmt = '%Y%m%d%H%M%S'
        return dt.datetime.strptime(dtinput,fmt)
    elif type(dtinput) == dt.datetime:
        return dtinput

def yearmo_to_dates(ym):
    import calendar
    # Months to use
    ym = str(ym)
    starts = ym+'01'
    ends = ym+str(calendar.monthrange(int(ym[0:4]), int(ym[4:]))[-1]).zfill(2)
    return starts,ends

###### Find Files ########################################
def files_from_orbrange(start,stop,source,vers,rev):
    orbrs = get_orbrange(start,stop)
    year = '[0-9][0-9][0-9][0-9]'
    month = '[0-9][0-9]'
    day = '[0-9][0-9]'
    source_str = source_to_search(source)
    vrs = vr_to_search(vers,rev)
    filelist = [] #initialize list
    for orb in orbrs:
        tid = orb_to_tid(orb) #get TID
        if tid == None: #no data for that orbit
            if len(orbrs) ==1 :
                sys.exit('No data for Orbit '+str(orb)+' '+str(vrs)+str(rev)) #exit if no data
            else:
                continue #move on to next orbit in range
        searchfile = 'mvn_ngi_l2_'+source_str+'-abund-'+str(tid)+'_'+year+month+day+time+'_'+vrs+'.csv'
        searchpath = base+year+'/'+month+'/'+searchfile
        files = glob.glob(searchpath)
        if len(files) > 1:
            print 'more than 1 TID found for TID',tid
        else:
            filename = files[0]
        filelist.append(filename) #add to filelist
    return filelist

def files_from_daterange(start,stop,source,vers,rev):
    import itertools
    #convert inputs to datetimes
    sdt = parse_dt_input(start)
    if start == stop:
        edt = sdt + dt.timedelta(1) #do at least the whole day for single date
    else:
        edt = parse_dt_input(stop)
    tid = '[0-9][0-9][0-9][0-9][0-9]' #find any tid
    day = '[0-9][0-9]' #find any day within month
    source_str = source_to_search(source)
    vrs = vr_to_search(vers,rev)
    filelist = [] #initialize list
    #for date in daters:
    cdt = sdt # set current date in loop to start date
    while cdt <= edt:
        year = str(cdt.year).zfill(2)
        month = str(cdt.month).zfill(2)
        #day = str(cdt.day).zfill(2)
        #get all files in given month
        searchfile = 'mvn_ngi_l2_'+source_str+'-abund-'+tid+'_'+year+month+day+time+'_'+vrs+'.csv'
        searchpath = base+year+'/'+month+'/'+searchfile
        files = glob.glob(searchpath)
        for filename in files:
            filelist.append(filename) #add to filelist
        if cdt.month<12:
            cdt = cdt.replace(month=cdt.month+1,day=1)
        elif cdt.month==12:
            cdt = cdt.replace(year=cdt.year+1,month=1,day=1)
    #reduce filelist to those within range
    datelist = [datetime_from_file(x) for x in filelist]
    mask = [(y>=sdt) and (y<=edt) for y in datelist]
    filelist = list(itertools.compress(filelist,mask))
    filelist.sort(key=lambda z: int(z[-33:-28]))
    return filelist
#########################################################

if __name__=='__main__':
    #### PARSER ###########################################################
    parser = argparse.ArgumentParser(description='NGIMS L2 search options')
    parser.add_argument('-s',type=int,action='store',dest='single',
                        help='Single value to look for')
    parser.add_argument('-r',type=int,nargs=2,action='store',dest='range',
                        help='Range between which to search, inclusive')

    parser.add_argument('-ot',action='store',dest='orbtid',
                        help='Create orbit-tid file and save to input')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-o','--orbit', action='store_true',dest='orbit',
                       help='Value(s) given as [o]rbit(s)')
    group.add_argument('-d','--date', action='store_true',dest='date',
                        help='Value(s) givnen as [d]ate(s) formatted as'+\
                        'YYYYMMDD or YYYYMMDDhhmmss')

    parser.add_argument('--source',choices=['neutrals','csn','cso','ion'],
                        default='neutrals',
                        help='Which NGIMS source to use. neutrals includes csn and cso')
    parser.add_argument('--vr',action='store',dest='vers_rev',default='0701',
                        help='Version and revision: vvrr')

    parser.add_argument('-f','--file',action='store',dest='output',type=str,nargs='?',
                        help='Output file to save to')

    args = parser.parse_args()
    #######################################################################
    vers = args.vers_rev[0:2]
    rev = args.vers_rev[2:4]

    try:
        open('src/ngims_tid_orbit.dat','rb')
    except:
        make_orb_tid(args.source,vers,rev,'src/ngims_tid_orbit.dat')
    
    if args.orbtid:
        make_orb_tid(args.source,vers,rev,args.orbtid)

    if args.single:
        start = args.single
        stop = args.single
    elif args.range:
        start = args.range[0]
        stop = args.range[1]

    if args.orbit:
        file_list = files_from_orbrange(start,stop,args.source,vers,rev)
    elif args.date:
        #dates = get_daterange(start,stop)
        file_list = files_from_daterange(start,stop,args.source,vers,rev)
    else: # No target specified
        #file_list = all_files()
        sys.exit()

    for fl in file_list:
        print fl
    ####################################################

    ### OUTPUT TO SAVE FILE ###########################
    if args.output:
        with open(args.output,'wb') as of:
            for item in file_list:
                of.write("%s\n" % item)
