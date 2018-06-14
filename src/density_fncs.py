#!env/bin python

import pandas as pd
import numpy as np
import scipy.stats as sps
import scipy.integrate as spi

################################################################################
# Functions applied to NGIMS densities
#
# Marek Slipski
# 20170725
################################################################################

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
    fp = sps.linregress(np.log(bm['abundance_CO2']),np.log(bm['N2/Ar']))
    hp = np.exp((np.log(ratio)-fp[1])/fp[0])
    return hp,fp

def exo_Ar_int(CO2,Ar,alt,exsp=['CO2'],ArXsec=[3.e-15],\
           Ntop=[0.,0.],taufrange=[0.7,1.3]):
    '''
    Calculate exobase altitude from species profiles
    (BE SURE TO USE INBOUND)
    Integrates down from some initial altitude to periapse
    Determines where num_density*coll_x-sec = 1 for exo altitude

    Inputs
    ------
    exsp: list, species to use in calculation
    ArXsec: list, collisional cross section for each species in exsp
    Ntop: list, column density above top for each species

    Outputs
    -------
    exo: float, exobase altitude
    fitTau: fit parameters of Tau profile (see scipy.stats.linregress)


    **TO DO:
    cite cross section values, should extrapolate ones that don't reac tau=1
    '''
    #convert alts to cm
    #orb_df = orb_df[orb_df['abundance_CO2']>0]
    xsec = dict(zip(exsp,ArXsec))
    altkm = np.array(alt)*1.e+5
    Tau_sp_dz = np.zeros((len(exsp),len(altkm)))  #initialize Tau/z
    for i,s in enumerate(xsec): #loop through species to use
        #colname = 'abundance_'+s
        #if colname in orb_df.columns: #check given species in DF
        Tau_sp_dz[i] = CO2*xsec[s] #calc n*sigma
        #else:
        #    print 'has no column '+colname
        #    return np.NaN
    Tau_tot_dz = np.sum(Tau_sp_dz,axis=0) #add each sp n*sigma together
    Tau_int = spi.cumtrapz(Tau_tot_dz,altkm*-1) #n*dz*sigma=N*sigma=Tau
    altmids = ((altkm[1:] + altkm[:-1]) / 2)/1.e+5 #gid mid alts in km
    findTau1 = np.where((Tau_int>taufrange[0])&(Tau_int<taufrange[-1])) #cond to find Tau=1
    if len(Tau_int[findTau1])<5: #warn if fitting line to only a few pts
        if np.max(Tau_int) < 1.0:
            print 'Never reaches tau=1, <'+str(int(altmids[-1]))+'?'
            return np.NaN, (np.NaN,np.NaN,np.NaN,np.NaN,np.NaN)
        else:
            print 'Has <5 points near tau=1'
            return np.NaN, (np.NaN,np.NaN,np.NaN,np.NaN,np.NaN)
    fitTau = sps.linregress(altmids[findTau1],Tau_int[findTau1])
    exo = (1-fitTau[1])/fitTau[0] #find alt where Tau=1
    return exo,fitTau #return exobase altitude

if __name__=='__main__':
    import read_raw as rr
    import find_ngi_files as fnf
    import sys

    orb =  723
    orbr = fnf.get_orbrange(orb,orb+10)
    files = fnf.files_from_orbrange(orbr,'neutrals',7,1)

    test,tsg,tdf,tex,te1,te2 = [],[], [],[],[],[]
    for f in files:
        print '\n',f
        N2 = rr.IO(rr.sp_profile(f,'N2'),'I').drop('species',axis=1)
        Ar = rr.IO(rr.sp_profile(f,'Ar'),'I').drop('species',axis=1)
        CO2 = rr.IO(rr.sp_profile(f,'CO2'),'I').drop('species',axis=1)
        df = pd.merge_ordered(N2,Ar,on='alt',how='inner',suffixes=('_N2','_Ar'))
        df['sg_N2'] = rr.savgol_density(df['abundance_N2'])
        df['sg_Ar'] = rr.savgol_density(df['abundance_Ar'])
        tdf.append(df)
        hp0 = hp_N2Ar_ratio(df['abundance_N2'],df['abundance_Ar'],df['alt'])[0]
        hp1 =  hp_N2Ar_ratio(df['sg_N2'],df['sg_Ar'],df['alt'])[0]
        test.append(hp0),tsg.append(hp1)

        exdf = pd.merge_ordered(CO2,Ar,on='alt',how='inner',suffixes=('_CO2','_Ar'))
        exdf['sg_CO2'] = rr.savgol_density(exdf['abundance_CO2'])
        exdf['sg_Ar'] = rr.savgol_density(exdf['abundance_Ar'])
        exdf = exdf.sort_values('alt',ascending=False)
        exo = exo_Ar_int(exdf['abundance_CO2'],exdf['abundance_Ar'],exdf['alt'])[0]
        exo_sg = exo_Ar_int(exdf['sg_CO2'],exdf['sg_Ar'],exdf['alt'])[0]
        print exo,exo_sg
        te1.append(exo),te2.append(exo_sg)
        tex.append(exdf)

        if np.abs(hp1-hp0) > 3.:
            print f,'\n',hp0, hp1
    bigdf = pd.concat(tdf)
    bigexdf = pd.concat(tex)
    bigexdf = bigexdf.sort_values('alt',ascending=False)
    print '\nAverages'
    print 'HP'
    print 'mean_raw=',np.mean(test),'mean_sg=',np.mean(tsg)

    print 'EB'
    print 'mean_raw=',np.mean(te1),'mean_sg=',np.mean(te2)

    print '\n','Combined Data:'
    print 'HP'
    print 'raw=',hp_N2Ar_ratio(bigdf['abundance_N2'],bigdf['abundance_Ar'],bigdf['alt'])[0]
    print 'sg=',hp_N2Ar_ratio(bigdf['sg_N2'],bigdf['sg_Ar'],bigdf['alt'])[0]

    print 'EB'
    print 'raw=',exo_Ar_int(bigexdf['abundance_CO2'],bigexdf['abundance_Ar'],bigexdf['alt'])[0]
    print 'mean_sg=',exo_Ar_int(bigexdf['sg_CO2'],bigexdf['sg_Ar'],bigexdf['alt'])[0]
