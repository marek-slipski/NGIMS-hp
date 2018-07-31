#!env/bin python

import pandas as pd
import numpy as np
import datetime as dt
import argparse
import sys

################################################################################
#
#
# Marek Slipski
# 20170627
# 20170705
################################################################################
def input_parse(parser):
    in_parser = parser.add_argument_group('Are files coming from pipe or files?')
    ingroup = in_parser.add_mutually_exclusive_group()
    ingroup.add_argument('-p','--pipe',action='store_true',dest='pipe',
                         help='Pipe in list of files (e.g. from find_ngi_files)')
    ingroup.add_argument('-f','--infile',action='store',dest='infile',type=file,
                         help='Give filename that contains one file per line')

    return ingroup

def files_from_parse(pargs):
    '''
    Take arguments from parser from input_parse and return list of files
    '''
    if pargs.pipe:
        files = []
        for line in sys.stdin:
            files.append(line.strip())
    elif pargs.infile:
        with open(args.infile) as f:
            files = [x.strip() for x in f]
    else:
        sys.exit('Pipe or input file?')

    return files

def tid_to_orb(tidnum,orbtidfile='data/processed/maven/ngims_tid_orbit.dat'):
    '''
    Function to convert TID number to orbit number.
    Requires orbtidfile from find_ngi_files.make_orb_tid()
    '''
    with open(orbtidfile,'rb') as orbf:
        for line in orbf:
            line = line.rstrip().split(',')
            if line[-1] == str(tidnum).zfill(5):
                orb = line[1]
                return int(orb)

def orb_num(filename):
    return tid_to_orb(filename[60:65])

def read(filename,usecols=None):
    '''
    Open raw file, return dataframe
    '''
    if usecols == None:
        return pd.read_csv(filename,na_values=[' ','NaN']).drop_duplicates()
    else:
        return pd.read_csv(filename,na_values=[' ','NaN'],usecols=usecols).drop_duplicates()

def sp_profile(filename,species,rm_null=True):
    '''
    Return altitude profile of single species for one orbit (inb and outb)
    '''
    cols = ['alt','species','abundance']
    df_read = read(filename,usecols=cols)
    df = df_read[(df_read['species']==species)] #just species
    if rm_null == True:
        with pd.option_context('mode.use_inf_as_null', True): #get rid of 'inf's
            df = df.dropna()
        #df = df_read[(~df_read['abundance'].isnull())]
    return df

def IO(sp_data,io):
    '''
    Grab only inbound or outbound data for single species DF
    '''
    peri = sp_data.index[sp_data['alt']==sp_data['alt'].min()].values #int64 index list
    if len(peri) == 2:
        #print '2 rows with same minimum altitude found.\n'
        if np.abs(peri[1]-peri[0]) == 1:
            if io == 'I':
                peri = peri[0:1]
            else:
                peri = peri[1:]
    elif len(peri) == 3:
        peri = peri[1:2]
    elif len(peri) > 3:
        sys.exit('More than 3 rows found for minimum altitude.\n'+\
                str(sp_data.species.unique())+' unique species in DF.\n'+\
                'Indicies of rows: '+str(peri))
    if io == 'I':
        return sp_data[sp_data.index<=peri[0]]
    elif io == 'O':
        return sp_data[sp_data.index>=peri[0]]

def savgol_density(den_prof,winsize=9,poly=2):
    from scipy.signal import savgol_filter
    '''
    Take a density profile in asc/des alts and apply savitsky_golay filter
    to the log of density to remove high frequency noise
    '''
    return np.exp(savgol_filter(np.log(den_prof),winsize,poly))

def combine_files(filelist,io='I'):
    pieces = []
    for f in filelist:
        df = IO_orb(read(f),io)
        pieces.append(df)
    return pd.concat(pieces)

def IO_orb(orbdata,io='I'):
    minalt = orbdata['alt'].min()
    peri_t = orbdata[orbdata['alt']==minalt]['t_unix'].unique()
    #if len(peri_t)>1:
    #    sys.exit('Non-unique time found at periapse '+str(orbdata['orbit'].unique()))
    #else:
    if io == 'I':
        return orbdata[orbdata['t_unix']<=peri_t[0]]
    elif io =='O':
        return orbdata[orbdata['t_unix']>peri_t[0]]
    else:
        return orbdata

def realign(data):
    '''
    data should be inbound or outbound

    Takes data from any number of orbits, and reorirents them such that
    abundances of diff species at same time/alt are given in same row.
    This allows for easier calculations/binning of abundances
    '''
    #L2 columns (v07 r01)
    col_rename = ['focusmode','mass','cps_dt_bkd',
                   'abundance','precision','quality'] #sp independent
    cols_on = ['orbit','alt','lat','long','sza','lst','t_utc',
                't_tid','t_sclk_cor','t_unix','tid'] #species dependent
    sp_sep = {} # init dict for dataframes
    for sp in data['species'].unique(): #loop through each species in data
        sp_sep[sp] = data[data['species']==sp].drop('species',axis=1) #sp specific DF
        # rename sp-dependent columns
        sp_sep[sp].rename(columns={x:x+'_'+sp for x in col_rename},inplace=True)
    picksp = sp_sep.keys()[0] # choose some species for starting DF
    newdf = sp_sep[picksp] #create DF to update
    for sp in sp_sep: #loop though each separate species DF
        if sp == picksp: #don't update for first species
            continue
        # Combine on species-independent rows
        newdf = pd.merge(newdf,sp_sep[sp],on=cols_on,how='outer')
    return newdf


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Parse input files and read options')
    # Arguments for files being used
    file_parse = parser.add_argument_group('NGIMS files arguments')
    input_parse(file_parse)

    read_parse = parser.add_argument_group('Read arguments')
    read_parse.add_argument('-i','--io',action='store',default='I',
                            help='[I]nbound or [O]outbound')
    read_parse.add_argument('-r','--realign',action='store_true',default=False,
                            help='Realign DataFrame with all species on each row')
    read_parse.add_argument('-s','--save',action='store',
                            help='Save final DataFrame to SAVE')

    args = parser.parse_args()

    files = files_from_parse(args) #get files
    ############################################################################

    df = combine_files(files,io=args.io) #all files (in,out,or all) into one DF

    ### Plotting options???
    ######

    if args.realign:
        df = realign(df)

    if args.save:
        df.to_csv(args.save)
