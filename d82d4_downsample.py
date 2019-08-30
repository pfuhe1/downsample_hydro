# Python script to process downsampled hydrography from 'downsample_hydro.py
# Calls streamnet function and creates 'rec'.csv (using jsosa/LFPtools), to describe the river network
# 
# Requires: 
# mpiexec
# streamnet from TauDEM (https://github.com/dtarb/TauDEM)
# split module from LFPtools (https://github.com/jsosa/LFPtools)

# Import python modules
import os,sys,subprocess
sys.path.append('/home/pu17449/gitsrc/LFPtools/lfptools') # Folder containing split.py
from prepdata import d82d4
from split import connections

# Paths of executables to run TauDEM
TauDEM_bindir = '/home/pu17449/gitsrc/TauDEM/bin' # contains streamnet executable
mpiexec_bindir = '/usr/bin' # contains mpiexec executable

# resolution of downscaled hydrography
res = '9s'

indir = '/home/pu17449/data2/lfp-tools/splitd8_v2/077'
# input files (produced by 'downsample_hydro.py')
fdir = os.path.join(indir,'dir_d8_downsample_'+res+'.tif')
fnet = os.path.join(indir,'net_downsample_'+res+'.tif')
fdem = os.path.join(indir,'dem_downsample_'+res+'.tif')
facc = os.path.join(indir,'acc_downsample_'+res+'.tif')
ford = os.path.join(indir,'ord_downsample_'+res+'.tif')
# output files
fdir_d4 = os.path.join(indir,'dir_d4_downsample_'+res+'.tif')
fnet_d4 = os.path.join(indir,'net_d4_downsample_'+res+'.tif')
ftree = os.path.join(indir,'strn_tree_'+res+'d4.txt')
fcoord = os.path.join(indir,'strn_coord_'+res+'d4.txt')
fnetwork = os.path.join(indir,'strn_network_'+res+'d4.out')
fwatershed = os.path.join(indir,'strn_watershed_'+res+'d4.tif')
frec = os.path.join(indir,'rec_downsample_'+res+'d4.csv')

# Call d8 to d4 script
if not os.path.exists(fdir_d4):
	print('Calling d82d4')
	d82d4(fdir,fdir_d4,fnet_d4)

# Call streamnet
if not os.path.exists(fnetwork):
        print('Calling streamnet')
        cmd = ['mpiexec','-n','4','streamnet','-fel',fdem, '-p',fdir_d4, '-ad8',facc ,'-src',fnet_d4, '-tree',ftree, '-coord',fcoord, '-net',fnetwork, '-w',fwatershed]
        print(cmd)
        ret = subprocess.call(cmd,env={'PATH':TauDEM_bindir+':'+mpiexec_bindir})
else:
        print('streamnet already exists, skipping')
        ret = 0

if ret==0:
	print('Creating rec file from tree and coords text files')
	# Creating rec dataframe
	rec = connections(ftree, fcoord)
	#  Writing XXX_rec.csv file
	rec.to_csv(frec)
else:
	print('streamnet failed: aborting')
