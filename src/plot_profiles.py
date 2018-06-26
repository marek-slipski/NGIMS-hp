#!env/bin python
# Marek Slipski
# 20180625

import pandas as pd
import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
import argparse

def plot_parse(parser):
    plot_parser = parser.add_argument_group('Plotting Parser')
    plot_parser.add_argument('--den_plot',action='store_true',
                            help='Plot number densities for various species')
    plot_parser.add_argument('--den_save',action='store',default=None,
                            help='File to save density plot')
    

def density_plot(data,species=['N2','Ar','CO2'],savefile=None):
    figd, axd = plt.subplots()
    for sp in species:
        axd.scatter(data['abundance_'+sp],data['alt'])
    axd.set_xscale('log')
    axd.set_xlabel(r'Number density (cm$^{-3}$)')
    axd.set_ylabel('Altitude (km)')
    if savefile:
        plt.savefig(savefile,dpi=300)
    return axd

def mixing_plot(data,mrs=['N2/Ar'],savefile=None):
    figr, axr = plt.subplots()
    for mr in mrs:
        sps = mr.split('/')
        axr.scatter(bin_df_re['abundance_'+sps[0]]/bin_df_re['abundance_'+sp[1]],
                bin_df_re['alt'],c='purple',s=5,linewidth=0)
    axr.set_xscale('log')
    axr.set_xlabel(r'Mixing ratio')
    axr.set_ylabel('Altitude (km)')
    if savefile:
        axr.savefig(savefile,dpi=300)
    return axr

def main(data,plotinfo):
    plot_dict = {}
    if plotinfo.den_plot:
        plot_dict['den'] = density_plot(data,savefile=plotinfo.den_save)
    if plotinfo.mr_plot:
        plot_dict['mr'] = mixing_plot(data,savefile=plotinfo.mr_save)
        
        
if __name__=='__main__':
    import read_raw as rr
    
    parser = argparse.ArgumentParser()
    
    rr.input_parse(parser)
    
    plot_parse(parser)
    
    args = parser.parse_args()

    files = rr.files_from_parse(args)
    bin_df = rr.combine_files(files,io='I')  # inbound only
    bin_df_re = rr.realign(bin_df) # convert sp and abun columns to species-specific abunds
    bin_df_re.sort_values('alt',ascending=False,inplace=True) # order by dec altitude
    
    
    
    main(bin_df_re,args)
    