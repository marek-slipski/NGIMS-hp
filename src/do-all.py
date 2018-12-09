#!env/bin python
# Marek Slipski
# 20180625

import os
import argparse
import yaml
import json

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import find_ngi_files as fnf
import read_raw as rr
import plot_profiles as pp
import hp_calc_bins as hp

############################################
with open('config.local','rb') as cf:
    config = yaml.load(cf)

tempbase = config['data_path']
pathbase = 'maven/data/sci/ngi/l2/'
base = os.path.expanduser(tempbase+pathbase)

############################################

parser = argparse.ArgumentParser('Parameters for calculations and plotting')
parser.add_argument('--exocalc',action='store_true')

task_parser = parser.add_argument_group('Tasks to do')
task_parser.add_argument('tasks',choices=['plot','hpcalc'],nargs='+',
                        help='Which tasks to run')

setup_parser = parser.add_argument_group('Looping through many files')
setup_parser.add_argument('--bindays',action='store',type=int,default=0,
                   help='Combine all orbits within BINDAYS days together\
                   for calculations and plots.')
setup_parser.add_argument('--binorbits',action='store',type=int,default=0,
                   help='Combine all orbits within BINORBITS orbits together\
                   for calculations and plots.')
setup_parser.add_argument('--orbits',action='store',nargs='+',type=int,
                         help='Orbit to do for or start and end orbits')
setup_parser.add_argument('--savedir',action='store',type=str,
                         help='Directory to save outputs')

data_parser = parser.add_argument_group('Data options')
data_parser.add_argument('--version',action='store',default=str(config['version']).zfill(2),
                        help='NGIMS L2 version number')
data_parser.add_argument('--revision',action='store',default=str(config['revision']).zfill(2),
                        help='NGIMS L2 revision number')
data_parser.add_argument('--source',choices=['neutrals','csn','cso','ion'],default='neutrals',
                        help='Which NGIMS source to use. neutrals includes csn and cso')
data_parser.add_argument('--IO',action='store',default='I',
                        help='[I]nbound or [O]outbound')
data_parser.add_argument('--tid_file',action='store',default='src/ngims_tid_orbit.dat',
                       help='TID file to use (may vary as newer vrs are added)')

pp.plot_parse(parser)

hp.hp_parse(parser)
parser.add_argument('--hpfit',action='store_true',default=False,
                       help='Make additional mixing ratio plot with HP fit.')

#hpcalc_parser = subparsers.add_parser('hpcalc',help='Calculate Homopause')

#fnf.parser_main(parser)

args = parser.parse_args()

if args.savedir:
    savedir = 'output/'+args.savedir
    if not os.path.exists(savedir):
        os.makedirs(savedir)
    with open(savedir+'/result.json', 'w') as saveparams:
        json.dump(vars(args), saveparams,indent=4)
    if 'plot' in args.tasks:
        if args.den_plot:
            den_fig_dir = savedir+'/figs/density_profiles/'
            if not os.path.exists(den_fig_dir):
                os.makedirs(den_fig_dir)
        if args.mr_plot:
            mr_fig_dir = savedir+'/figs/ratio_profiles/'
            if not os.path.exists(mr_fig_dir):
                os.makedirs(mr_fig_dir)
        if args.hpfit:
            fit_fig_dir = savedir+'/figs/ratio_profiles_fit/'
            if not os.path.exists(fit_fig_dir):
                os.makedirs(fit_fig_dir)
    pieces = {}
    if args.hp_alt:
        pieces['alt'] = []
    if args.hp_den:
        pieces['den'] = []

if args.orbits:
    orbstart = args.orbits[0]
    if len(args.orbits) == 2:
        orbend = args.orbits[-1]
    else:
        orbend = orbstart
orbs = np.arange(orbstart,orbend+1)

for orb in orbs:
    binstart = orb - args.binorbits/2.
    binend = orb + args.binorbits/2.
    binfiles = fnf.files_from_orbrange(binstart,binend,args.source,args.version,args.revision,args.tid_file)
    
    if len(binfiles) == 0:
        continue
          
    # BELOW SHOULD BE READ_RAW.MAIN()
    bin_df = rr.combine_files(binfiles,io=args.IO)  # inbound only
    bin_df_re = rr.realign(bin_df)# convert sp and abun columns to species-specific abunds
    newdf = {'alt':[],'sg_N2':[],'sg_Ar':[],'sg_CO2':[]}
    for eachorb, orbprof in bin_df_re.groupby('orbit'): 
        newdf['alt'] += list(orbprof['alt'])
        newdf['sg_N2'] += list(rr.savgol_density(orbprof['abundance_N2']))
        newdf['sg_Ar'] += list(rr.savgol_density(orbprof['abundance_Ar']))
        newdf['sg_CO2'] += list(rr.savgol_density(orbprof['abundance_CO2']))
    newdf = pd.DataFrame(newdf)
    newdf.sort_values('alt',ascending=False,inplace=True) # order by dec altitude
    
    if 'plot' in args.tasks and args.savedir:
        if args.den_plot:
            args.den_save = den_fig_dir+str(orb).zfill(5)
        if args.mr_plot:
            args.mr_save = mr_fig_dir+str(orb).zfill(5)
            
        plot_res = pp.main(bin_df_re,args)
        
    #if 'hpcalc' in args.tasks:
    #    hp_res =  hp.main(newdf,args,N2col='sg_N2',Arcol='sg_Ar',CO2col='sg_CO2')
    #    for key in hp_res.keys():
    #        if args.savedir:
    #            hp_to_dict = vars(hp_res[key][1])
    #            hp_to_dict['hp_'+key] = hp_res[key][0]
    #            hp_to_dict['orbit'] = orb
    #            hp_to_dict['count'] = len(binfiles)
    #            pieces[key].append(hp_to_dict)
                
    if 'exocalc' in args:
        print orb
        exo_res = hp.exo(newdf,args,N2col='sg_N2',Arcol='sg_Ar',CO2col='sg_CO2')
        pieces['orbit'] = orb
        pieces['count'] = len(binfiles)
        for key in exo_res.keys():
            if args.savedir:
                pieces[key] = exo_res[key]
                
    if args.hpfit:
        fit_alts = np.linspace(newdf['alt'].min(),args.hp_maxalt,100)
        ext_alts = np.linspace(hp_res['alt'][0],250,100)
        fit_vals = np.exp(hp_res['alt'][1][0]*fit_alts + hp_res['alt'][1][1])
        ext_vals = np.exp(hp_res['alt'][1][0]*ext_alts + hp_res['alt'][1][1])
        plot_res['mr'].plot(fit_vals,fit_alts,'k')
        plot_res['mr'].plot(ext_vals,ext_alts,'k--')
        if args.savedir:
            plt.savefig(fit_fig_dir+str(orb).zfill(5))
        
    plt.close("all")
            
if args.savedir:
    if args.hp_alt and not args.hp_den:
        pd.DataFrame(pieces['alt']).to_csv(savedir+'/homopause.csv',index=False)
    elif args.hp_den and not args.hp_alt:
        pd.DataFrame(pieces['den']).to_csv(savedir+'/homopause.csv',index=False)
    elif args.hp_alt and args.hp_den:
        alt_df = pd.DataFrame(pieces['alt'])
        den_df = pd.DataFrame(pieces['den'])
        merged = pd.merge(alt_df,den_df,on=['orbit','count'],suffixes=('_alt','_den'))
        merged.to_csv(savedir+'/homopause.csv',index=False)
    elif args.exocalc:
        pd.DataFrame(pieces).to_csv(savedir+'/exo.csv',index=False)
    
    
        
    
    