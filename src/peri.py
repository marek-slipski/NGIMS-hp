import pandas as pd
import numpy as np
import datetime as dt
import sys

import find_ngi_files as fnf
import read_raw as rr
import MT

#tid = pd.read_csv('src/ngims_tid_orbit_v0801.dat',names=['csn','orbit','tid'])
orbs = list(tid['orbit'])

peri_dict = {}
for orb in orbs:
    if orb % 100 == 0:
        print orb
    binfiles = fnf.files_from_orbrange(orb,orb,'neutrals','08','01','src/ngims_tid_orbit_v0801.dat')
    
    if len(binfiles) == 0:
        continue
          
    # BELOW SHOULD BE READ_RAW.MAIN()
    bin_df = rr.combine_files(binfiles,io='I')  # inbound only
    bin_df_re = rr.realign(bin_df)# convert sp and abun columns to species-specific abunds
    
    
    if orb == 713:
        cols = bin_df_re.columns
        for col in cols:
            peri_dict[col] = []
        peri_dict['Ls'] = []
    
    peri = bin_df_re[bin_df_re['alt']==bin_df_re['alt'].min()]#int64 index list
    if len(peri) == 2:
        #print '2 rows with same minimum altitude found.\n'
        peri = peri[0:1]
       
    for col in cols:
        peri_dict[col].append(peri[col].item())
       
    peri_dt = dt.datetime.strptime(peri['t_utc'].item(),'%Y-%m-%dT%H:%M:%S')
    peri_dict['Ls'].append(MT.getMTfromTime(peri_dt))
    
    if orb == 725:
        print pd.DataFrame(peri_dict)
        
        
peri_df = pd.DataFrame(peri_dict).to_csv('peri.csv',index=False)
