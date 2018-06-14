import pandas as pd
import numpy as np
import datetime as dt
import scipy.stats as sps
import matplotlib.pyplot as plt

import find_ngi_files as fnf
import read_raw as rr
import density_fncs as dnf

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
    bin_count = len(bin_files) # number or files/orbits
    
    print bin_count
    
    # DataFrame
    bin_df = rr.combine_files(bin_files,io='I')  # inbound only
    bin_df_re = rr.realign(bin_df) # convert sp and abun columns to species-specific abunds
    bin_df_re.sort_values('alt',ascending=False,inplace=True) # order by dec altitude
    
    # Calculate homopause levels (alt and CO2)
    hp_fit_data  = bin_df_re[bin_df_re['alt']<max_alt] #ignore above given altitude
    hp_alt = dnf.hp_N2Ar_ratio(hp_fit_data['abundance_N2'],hp_fit_data['abundance_Ar'],
                          hp_fit_data['alt'])
    hp_CO2 = dnf.hp_N2Ar_ratio(hp_fit_data['abundance_N2'],hp_fit_data['abundance_Ar'],
                          hp_fit_data['abundance_CO2'])
    print hp_alt
    print hp_CO2
    
    
    if plots:
        plt.figure()
        plt.scatter(bin_df_re['abundance_CO2'],bin_df_re['alt'],c='g',s=5,linewidth=0)
        plt.scatter(bin_df_re['abundance_N2'],bin_df_re['alt'],c='b',s=5,linewidth=0)
        plt.scatter(bin_df_re['abundance_Ar'],bin_df_re['alt'],c='r',s=5,linewidth=0)
        plt.xscale('log')
        plt.xlabel(r'Number density (cm$^{-3}$)')
        plt.ylabel('Altitude (km)')

        plt.figure()
        plt.scatter(bin_df_re['abundance_N2']/bin_df_re['abundance_Ar'],
                    bin_df_re['alt'],c='purple',s=5,linewidth=0)
        plt.xscale('log')
        plt.xlabel(r'Mixing ratio')
        plt.ylabel('Altitude (km)')

        plt.show()
        
       
    
    date = date + dt.timedelta(days = daybin) # advance one bin width
    
    
    
    
    
    