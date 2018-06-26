#!env/bin python
# Marek Slipski
# 20180625

import os
import argparse
import yaml
import json

import numpy as np
import pandas as pd

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

pp.plot_parse(parser)
plot_parse.add_argument('--hpfit',action='store',default=False,
                       help='Make additional mixing ratio plot with HP fit.')

hp.hp_parse(parser)

#hpcalc_parser = subparsers.add_parser('hpcalc',help='Calculate Homopause')

#fnf.parser_main(parser)

args = parser.parse_args()

if args.savedir:
    savedir = 'output/'+args.savedir
    if not os.path.exists(savedir):
        os.makedirs(savedir)
    with open(savedir+'/result.json', 'w') as saveparams:
        json.dump(vars(args), saveparams)
    if 'plot' in args.tasks:
        if args.den_plot:
            den_fig_dir = savedir+'/figs/density_profiles/'
            if not os.path.exists(den_fig_dir):
                os.makedirs(den_fig_dir)
        if args.mr_plot:
            mr_fig_dir = savedir+'/figs/ratio_profiles/'
            if not os.path.exists(mr_fig_dir):
                os.makedirs(mr_fig_dir)
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
        orbend = orbstart + 1
orbs = np.arange(orbstart,orbend)

for orb in orbs:
    binstart = orb - args.binorbits/2.
    binend = orb + args.binorbits/2.
    binfiles = fnf.files_from_orbrange(binstart,binend,args.source,args.version,args.revision)
        
        
    # BELOW SHOULD BE READ_RAW.MAIN()
    bin_df = rr.combine_files(binfiles,io=args.IO)  # inbound only
    bin_df_re = rr.realign(bin_df) # convert sp and abun columns to species-specific abunds
    bin_df_re.sort_values('alt',ascending=False,inplace=True) # order by dec altitude
    
    if 'plot' in args.tasks:
        if args.den_plot:
            args.den_save = den_fig_dir+str(orb).zfill(5)
        if args.mr_plot:
            args.mr_save = mr_fig_dir+str(orb).zfill(5)
            
        plot_res = pp.main(bin_df_re,args)
        
    if 'hpcalc' in args.tasks:
        hp_res =  hp.main(bin_df_re,args)
        for key in hp_res.keys():
            if args.savedir:
                hp_to_dict = vars(hp_res[key][1])
                hp_to_dict['hp_'+key] = hp_res[key][0]
                hp_to_dict['orbit'] = orb
                hp_to_dict['count'] = len(binfiles)
                pieces[key].append(hp_to_dict)
        
            
if args.savedir:
    if args.hp_alt and not args.hp_den:
        pd.DataFrame(pieces['alt']).to_csv(savedir+'/homopause.csv',index=False)
    elif args.hp_den and not args.hp_alt:
        pd.DataFrame(pieces['den']).to_csv(savedir+'/homopause.csv',index=False)
    elif args.hp_alt and args.hp_den:
        alt_df = pd.DataFrame(pieces['alt'])
        den_df = pd.DataFrame(pieces['den'])
        merged = pd.merge(alt_df,den_df,on='orbit',suffixes=('alt','den'))
        merged.to_csv(savedir+'/homopause.csv',index=False)
    
    
        
    
    