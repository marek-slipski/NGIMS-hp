#!env/bin python
# Marek Slipski
# 20180625

import os
import argparse
import yaml

import numpy as np

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

hp.hp_parse(parser)

#hpcalc_parser = subparsers.add_parser('hpcalc',help='Calculate Homopause')

#fnf.parser_main(parser)

args = parser.parse_args()

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
    
    plot_res = pp.main(bin_df_re,args)
    hp_res =  hp.main(bin_df_re,args)
    
    print hp_res
    