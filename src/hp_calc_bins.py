import pandas as pd
import numpy as np
import datetime as dt
import argparse
import sys
import scipy.stats as sps
import scipy.integrate as spi

import matplotlib.pyplot as plt

import src.find_ngi_files as fnf
import src.read_raw as rr

#Some constants
g = 3.81 #m/s^2 surface gravity
M_Mars =  0.64171e+24 #kg
R_Mars = 3396.2e+3 #m
Grav = 6.67408e-11 #m^3 kg^-1 s^-2
amu = 1.660539040e-27 #kg
kboltz = 1.38064852e-23 #J/K

################################################################################
# Pressure - temperature functions, Snowden method, etc
################################################################################
def x_to_T(slope,mass):
    '''
    Convert slope of log of density (from fit) to a temperature.
    The slope is the negative recipricol of the scale height

    Inputs
    ------
    slope:
    mass: atmoic (amu)

    Outputs
    -------
    T: Temperature in Kelvin
    '''

    g = 3.71/1000 #km/s^2
    kboltzkm = kboltz/1000**2 #boltzmann constant (km^2 kg s^-2 K^-1)
    return (slope**-1*-1)*(mass*amu*g/kboltzkm)

def hp_parse(parser):
    hp_parser = parser.add_argument_group('Homopause calculation parameters')
    hp_parser.add_argument('--ratio',default=1.25,
                          help='N2/Ar ratio in the lower atmosphere')
    hp_parser.add_argument('--hp_maxalt',action='store',default=190.,
                          help='Maximum altitude for fit')
    hp_parser.add_argument('--hp_maxden',action='store',default=1.e+7,
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

def CO2_hp(N2,Ar,den,ratio=1.25):
    fp = sps.linregress(np.log(den),np.log(N2/Ar))
    hp = np.exp((np.log(ratio)-fp[1])/fp[0])
    return hp,fp

def exo_Ar_int(CO2,Ar,alt,exsp=['CO2'],ArXsec=[3.e-15],\
           Ntop=[0.,0.],taufrange=[0.,5], minpts=10):
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
        Tau_sp_dz[i] = CO2*xsec[s] #calc n*sigma
    Tau_tot_dz = np.sum(Tau_sp_dz,axis=0) #add each sp n*sigma together
    Tau_int = spi.cumtrapz(Tau_tot_dz,altkm*-1) #n*dz*sigma=N*sigma=Tau
    altmids = ((altkm[1:] + altkm[:-1]) / 2)/1.e+5 #gid mid alts in km
    findTau1 = np.where((Tau_int>taufrange[0])&(Tau_int<taufrange[-1])) #cond to find Tau=1
    if len(Tau_int[findTau1])<minpts: #warn if fitting line to only a few pts
        if np.max(Tau_int) < 1:
            return np.NaN, (np.NaN,np.NaN,np.NaN,np.NaN,np.NaN)
        else:
            return np.NaN, (np.NaN,np.NaN,np.NaN,np.NaN,np.NaN)
    fitTau = sps.linregress(altmids[findTau1],Tau_int[findTau1])
    exo = (1-fitTau[1])/fitTau[0] #find alt where Tau=1
    return exo,fitTau #return exobase altitude
    
def main(data,parameters,N2col='abundance_N2',Arcol='abundance_Ar',CO2col='abundance_CO2'):
    hp_dict = {}
    alt_data = data[data['alt']<parameters.hp_maxalt]
    alt_hp_fit = hp_N2Ar_ratio(alt_data[N2col],alt_data[Arcol],
                               alt_data['alt'])
    hp_dict['hp_alt'] = alt_hp_fit
        
    den_data = data[data[CO2col]>parameters.hp_maxden]
    den_hp_fit = CO2_hp(den_data[N2col],den_data[Arcol],den_data[CO2col])
    hp_dict['hp_den'] = den_hp_fit
        
    return hp_dict

def exo(data,parameters,N2col='abundance_N2',Arcol='abundance_Ar',CO2col='abundance_CO2'):
    exo_dict = {}
    bins = np.arange(110,300,5)
    binmids = (bins[:-1]+bins[1:])/2.
    data['bin_alt'] = pd.cut(data['alt'],bins,labels=binmids)
    newdf = data[['bin_alt','alt',CO2col,Arcol]].groupby(data['bin_alt']).mean().reset_index().sort_values('alt',ascending=False)
    newdf = newdf[~newdf.isin([np.nan, np.inf, -np.inf]).any(1)]
    newdf.dropna(inplace=True)
    exo_dict['exo'] = exo_Ar_int(newdf[CO2col],newdf[Arcol],newdf['alt'])[0]
    Ardenfit = sps.linregress(newdf['alt'],np.log(newdf[Arcol]))
    exo_dict['SH_Ar'] = x_to_T(Ardenfit[0],40)
    return exo_dict

if __name__=='__main__':
    # Parse Input
    parser = argparse.ArgumentParser() # initialize
    rr.input_parse(parser) # data input
    hp_parse(parser) # homopause options
    args = parser.parse_args() # parse
    
    # Open and preprocess data
    files = rr.files_from_parse(args)
    bin_df = rr.combine_files(files,io='I')  # inbound only
    bin_df_re = rr.realign(bin_df) # convert sp and abun columns to species-specific abunds
    bin_df_re.sort_values('alt',ascending=False,inplace=True) # order by dec altitude
    
    # Calculate Homopause altitude and density
    hp = main(bin_df_re,args)
    print(hp)
    
    
    
    
    
    