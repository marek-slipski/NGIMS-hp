#!env/bin python
# Marek Slipski
# 20180625

import matplotlib
# Force matplotlib to not use any Xwindows backend.
#matplotlib.use('Tkagg')

import pandas as pd
import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
import argparse

import read_raw as rr

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
                   s=1,linewidth=0,label=sp)
    axd.set_xscale('log')
    axd.set_xlabel(r'Number density (cm$^{-3}$)')
    axd.set_xlim(1.e+2,1.e+12)
    if yaxis == 'den':
        axd.set_yscale('log')
        axd.invert_yaxis()
        axd.set_ylim(1.e+12,1.e+2)
    axd.set_ylabel(label[yaxis])
    axd.legend(scatterpoints=3)
    if savefile:
        plt.savefig(savefile,dpi=300)
    return axd

def mixing_plot(data,mrs=['N2/Ar','N2/CO2','Ar/CO2'],savefile=None,yaxis='alt'):
    colors  = {'N2/Ar':'purple','N2/CO2':'teal','Ar/CO2':'goldenrod'}
    figr, axr = plt.subplots()
    for mr in mrs:
        sps = mr.split('/')
        axr.scatter(data['abundance_'+sps[0]]/data['abundance_'+sps[1]],
                   data[ycol[yaxis]],s=1,color=colors[mr],linewidth=0,
                   label=mr)
    axr.set_xscale('log')
    axr.set_xlabel(r'Mixing ratio')
    axr.set_xlim(1.e-4,1.e+4)
    if yaxis == 'den':
        axr.set_yscale('log')
        axr.invert_yaxis()
        axr.set_ylim(1.e+12,1.e+2)
    axr.set_ylabel(label[yaxis])
    axr.legend(scatterpoints=3)
    if savefile:
        plt.savefig(savefile,dpi=300)
    return axr

def main(data,plotinfo):
    plot_dict = {}
    if plotinfo.den_plot:
        plot_dict['den'] = density_plot(data,savefile=plotinfo.den_save,yaxis=plotinfo.yaxis)
    if plotinfo.mr_plot:
        plot_dict['mr'] = mixing_plot(data,savefile=plotinfo.mr_save,yaxis=plotinfo.yaxis)
    return plot_dict
        
        
if __name__=='__main__':
    # Parse Input
    parser = argparse.ArgumentParser() # initialize 
    rr.input_parse(parser) # data input
    plot_parse(parser) # plotting options
    args = parser.parse_args() # parse

    # Open and preprocess data
    files = rr.files_from_parse(args)
    bin_df = rr.combine_files(files,io='I')  # inbound only
    bin_df_re = rr.realign(bin_df) # convert sp and abun columns to species-specific abunds
    bin_df_re.sort_values('alt',ascending=False,inplace=True) # order by dec altitude
    
    # Make plots and show
    main(bin_df_re,args)
    plt.show()
