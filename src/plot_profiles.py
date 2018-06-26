#!env/bin python
# Marek Slipski
# 20180625

import pandas as pd
import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
import argparse

label = {'alt':'Altitude (km)','den':r'CO$_2$ number density (cm${-3}$)'}
ycol = {'alt':'alt','den':'abundance_CO2'}

def plot_parse(parser):
    plot_parser = parser.add_argument_group('Plotting Parser')
    plot_parser.add_argument('--den_plot',action='store_true',
                            help='Plot number densities for various species')
    plot_parser.add_argument('--den_save',action='store',default=None,
                            help='File to save density plot')
    plot_parser.add_argument('--mr_plot',action='store_true',
                            help='Plot mixing ratios for various species')
    plot_parser.add_argument('--mr_save',action='store',default=None,
                            help='File to save mixing ratio plot to')
    plot_parser.add_argument('--yaxis',action='store',default='alt',choices=['alt','den'],
                            help='Y-axis units')
    

def density_plot(data,species=['N2','Ar','CO2'],savefile=None,yaxis='alt'):
    colors = {'CO2':'g','N2':'b','Ar':'r'}
    figd, axd = plt.subplots()
    for sp in species:
        axd.scatter(data['abundance_'+sp],data[ycol[yaxis]],color=colors[sp],
                   s=2,linewidth=1,label=sp)
    axd.set_xscale('log')
    axd.set_xlabel(r'Number density (cm$^{-3}$)')
    if yaxis == 'den':
        axd.set_yscale('log')
        axd.invert_yaxis()
    axd.set_ylabel(label[yaxis])
    axd.legend()
    if savefile:
        plt.savefig(savefile,dpi=300)
    return axd

def mixing_plot(data,mrs=['N2/Ar','CO2/N2','CO2/Ar'],savefile=None,yaxis='alt'):
    colors  = {'N2/Ar':'purple','CO2/N2':'teal','CO2/Ar':'goldenrod'}
    figr, axr = plt.subplots()
    for mr in mrs:
        sps = mr.split('/')
        axr.scatter(data['abundance_'+sps[0]]/data['abundance_'+sps[1]],
                   data[ycol[yaxis]],s=2,color=colors[mr],linewidth=1,alpha=0.3,
                   label=mr)
    axr.set_xscale('log')
    axr.set_xlabel(r'Mixing ratio')
    if yaxis == 'den':
        axr.set_yscale('log')
        axr.invert_yaxis()
    axr.set_ylabel(label[yaxis])
    axr.legend()
    if savefile:
        plt.savefig(savefile,dpi=300)
    return axr

def main(data,plotinfo):
    plot_dict = {}
    if plotinfo.den_plot:
        plot_dict['den'] = density_plot(data,savefile=plotinfo.den_save,yaxis=plotinfo.yaxis)
    if plotinfo.mr_plot:
        plot_dict['mr'] = mixing_plot(data,savefile=plotinfo.mr_save,yaxis=plotinfo.yaxis)
        
        
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
    