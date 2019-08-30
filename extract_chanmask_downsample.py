#!/usr/bin/env python

# inst: university of bristol
# auth: Peter Uhe
# mail: peter.uhe@bristol.ac.uk

import os
import gdalutils # From https://github.com/jsosa/gdalutils
import numpy as np
from skimage.measure import block_reduce
import subprocess
import copy


#########################################################################################
# Simple function to return number of values > 0 for use in block_reduce
#
d8_dirs = np.array([ [-1, 1] , [-1, 0] , [-1, -1], [0,-1], [ 1, -1], [1, 0], [1, 1] ])
d4_dirs = np.array([ [0,1] , [-1, 0] , [0,-1], [1, 0] ])

def count(data,axis=None):
	return (data>0).sum(axis=axis)

# recursive search function to locate mask values adjacent to river network
# Identified mask values are set to the value 2
def search_mask(mask,net,jvals,ivals,depth,maxdepth):
	if depth == maxdepth:
		print('warning reached max recursion',maxdepth)
		return
	else:
		for j,i in zip(jvals,ivals):
			try:
				if mask[j,i] == 1:
					print('ji',j,i)
					mask[j,i] = 2
					nextijs = d4_dirs+[j,i]
					search_mask(mask,net,nextijs[:,0],nextijs[:,1],depth+1,maxdepth)
			except:
				continue

# search function to locate mask values adjacent to river network
# Loops over list of indices until none are left
# Identified mask values are set to the value 2
def search_mask2(mask,net,indices):
	while len(indices)>0:
		j,i = indices.pop()
		try:
			if mask[j,i] == 1:
				print('ji',j,i)
				mask[j,i] = 2
				for d in range(4):
					nextij = tuple(d4_dirs[d,:]+[j,i])
					#if nextij not in indices:
					indices.append(nextij)
		except:
			continue
	return mask

# search function to locate mask values adjacent to river network
# Loops over list of indices until none are left
# Identified mask values are set to the value 2
#
# PFU: this is an attempt to check the distance between the stream network and a point. 
# However, the distance needs to be between the closest point on the stream network rather than the first point? OR use a buffer around the stream network...
def search_mask3(mask,net,indices,maxdist):
	indices0 = copy.deepcopy(indices)
	while len(indices)>0:
		j,i = indices.pop(0)
		j0,i0 = indices0.pop(0)
		try:
			if mask[j,i] == 1:
				dist = ((j-j0)**2+(i-i0)**2)**0.5
				print('ji',j,i,dist)
				mask[j,i] = 2
				if dist < maxdist:
					for d in range(4):
						nextij = tuple(d4_dirs[d,:]+[j,i])
						indices.append(nextij)
						indices0.append((j0,i0))
		except:
			continue
	return mask


def clean_mask(mask,net,maxdist):
	# Get list of indices in network
	#jvals,ivals = np.unravel_index(np.where(net==1),net.shape)
	jvals,ivals = np.asarray(net==1).nonzero()
	print('network indices',jvals.shape,ivals.shape)
	indices = list(zip(jvals,ivals))
	mask = search_mask2(mask,net,indices)
	#mask = search_mask3(mask,net,indices,maxdist)

#	for j,i in zip(jvals,ivals):
#		search_mask2(mask,net,[j],[i],j,i,100)
	return mask == 2
		

#########################################################################################
# Main code
if __name__ == '__main__':

	#########################################################################################
	# Input parameters for algorithm

	# nwindow is block of ( nwindow x nwindow ) cells to aggregate over

	# count thresh is the minimum number of river cells within each window (otherwise this window is not included in the downsampled river network

	# For 30s resolution
	#nwindow = 10 
	#count_thresh = 5 # minimum river cells needed within a ( nwindow x nwindow ) block

	# For 9s resolution
	#nwindow = 3
	#count_thresh = 2

	# For 15s resolution
	nwindow = 5
	count_thresh = 3


	# For full_res output
	#nwindow = None

	if nwindow is not None:
		resstr = '_'+str(nwindow*3)+'s'
	else:
		resstr = ''

	#########################################################################################
	# Set up paths

	# Input files for 3s river network
	indir = '/home/pu17449/data2/lfp-tools/splitd8_v2/077/'
	# Accumulation at each point at the river network, masked for accumulation > 250 km^2
	wthtif = os.path.join(indir,'077_wth_redo.tif')
	nettif = os.path.join(indir,'077_net.tif')

	# input from downsampled network
	net_downsample = os.path.join(indir,'net_downsample'+resstr+'.tif')
	
	# Output at 3s
	maskrawtif = os.path.join(indir,'077_maskraw.tif')
	maskcleantif = os.path.join(indir,'077_maskclean.tif')

	# Output downsampled
	maskraw_downsample = os.path.join(indir,'maskraw_downsample'+resstr+'.tif')
	maskclean_downsample = os.path.join(indir,'maskclean_downsample'+resstr+'.tif')

	#########################################################################################
	# First create full res chanmask from wthtif (values -1 or greater than 0)	
	if not os.path.exists(maskrawtif):
		cmd = ['gdal_calc.py',"--calc","logical_or(A==-1.0,A>0.0)",'--format','GTiff','--type','Int16','-A',wthtif,'--A_band','1','--co','COMPRESS=DEFLATE','--outfile',maskrawtif]
		print(cmd)
		subprocess.call(cmd)

	# Get geometry information from chanmask tif
	#
	geo = gdalutils.get_geo(maskrawtif)
	print(geo)

	if nwindow is not None:
		#########################################################################################

		# modify number of cells: divide by nwindow and round up (block_reduce pads the arrays)
		geo[4] = int(np.ceil(geo[4]/nwindow))
		geo[5] = int(np.ceil(geo[5]/nwindow))
		# modify resolution: multiply by nwindow
		geo[6] = geo[6]*nwindow
		geo[7] = geo[7]*nwindow

		#########################################################################################
		# Downsample chanmask arrays 
		if not os.path.exists(maskraw_downsample):
			data = gdalutils.get_data(maskrawtif)
			downsample_count = block_reduce(data,block_size=(nwindow,nwindow),func = count,cval=-32767)
			data_mask = downsample_count>=count_thresh
			print('downsampled mask',data_mask.shape)
			gdalutils.write_raster(data_mask, maskraw_downsample, geo, 'Int16', -9999)
		else:
			data_mask = gdalutils.get_data(maskraw_downsample)
		#########################################################################################
		# Clean chanmask - remove values away from stream network
		data_net = gdalutils.get_data(net_downsample)
		data_maskclean = clean_mask(data_mask,data_net,900)
		gdalutils.write_raster(data_maskclean, maskclean_downsample, geo, 'Int16', -9999)
	
	else:
		if not os.path.exists(maskcleantif):
			data_mask = gdalutils.get_data(maskrawtif)

			#########################################################################################
			# Clean chanmask - remove values away from stream network
			data_net = gdalutils.get_data(nettif)
			data_maskclean = clean_mask(data_mask,data_net,100)
			gdalutils.write_raster(data_maskclean, maskcleantif, geo, 'Int16', -9999)

