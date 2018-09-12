import pandas as pd
import numpy as np
import datetime as dt
import scipy.stats as sps
import matplotlib.pyplot as plt

import find_ngi_files as fnf
import read_raw as rr



def hp_parse(parser):
    hp_parser = parser.add_argument_group('Homopause calculation parameters')
    hp_parser.add_argument('--ratio',default=1.25,
                          help='N2/Ar ratio in the lower atmosphere')
    hp_parser.add_argument('--hp_alt',action='store_true',default=False,
                          help='Calculate homopause altitude')
    hp_parser.add_argument('--hp_den',action='store_true',default=False,
                          help='Calculate homopause level in CO2 density space')
    hp_parser.add_argument('--hp_maxalt',action='store',default=190.,
                          help='Maximum altitude for fit')
    hp_parser.add_argument('--hp_maxden',action='store',default=1.e+8,
                          help='Minimum CO2 density for fit')
    
def hp_N2Ar_ratio(N2,Ar,alt,ratio=1.25):
    '''
    Calculate homopause from NGIMS L2 data (profile)
    Fits line to N2/Ar data (profile)
    Uses fit to find where N2/Ar data is equal to lower atmospheric ratio
    (extrapolates down)

    Inputs
    ------
    N2, Ar: altitude profiles of densities
    alt: altitudes of densities
    ratio: float, ratio of N2/Ar in lower atmosphere

    Outputs
    -------
    hp: float, homopause altitude in (km)
    fp: fit parameters of N2/Ar profile (see scipy.stats.linregress)
    '''
    N2Ar = N2/Ar
    fp = sps.linregress(alt,np.log(N2Ar))
    hp = (np.log(ratio)-fp[1])/fp[0]
    return hp,fp

def CO2_hp(bm,ratio=1.25):
    fp = sps.linregress(np.log(bm['abundance_CO2']),np.log(bm['abundance_N2']/bm['abundance_Ar']))
    hp = np.exp((np.log(ratio)-fp[1])/fp[0])
    return hp,fp
    
def main(data,parameters):
    hp_dict = {}
    if parameters.hp_alt:
        alt_data = data[data['alt']<parameters.hp_maxalt]
        alt_hp_fit = hp_N2Ar_ratio(alt_data['abundance_N2'],alt_data['abundance_Ar'],
                                   alt_data['alt'])
        hp_dict['alt'] = alt_hp_fit
        
    if parameters.hp_den:
        den_data = data[data['abundance_CO2']>parameters.hp_maxden]
        den_hp_fit = CO2_hp(den_data)
        hp_dict['den'] = den_hp_fit
        
    return hp_dict

if __name__=='__main__':

    # Date Parameters
    date_s = dt.datetime(2015,10,25) # start date
    date_e = dt.datetime(2015,10,27) # end date
    daybin = 2 # total days in each bin
    date = date_s + dt.timedelta(days = daybin/2.) # adj start date to bin center

    # Data Parameters
    source =  'neutrals'
    version = 7
    revision = 1

    # Homopause Parameters
    max_alt = 200.

    # Plot Parameters
    plots = False

    # March through dates
    while date <= date_e - dt.timedelta(days = daybin/2.):
        print date
        bin_start = date - dt.timedelta(days = daybin/2.) # half of days before
        bin_end = date + dt.timedelta(days = daybin/2.) # half after

        # Collect filenames
        bin_files = fnf.files_from_daterange(bin_start,bin_end,source,version,revision) 



        date = date + dt.timedelta(days = daybin) # advance one bin width
    
    
    
    
    
    