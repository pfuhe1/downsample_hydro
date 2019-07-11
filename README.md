# downsample_hydro
Scripts to downsample river hydrography (e.g. accumulation and flow directions) to lower resolutions

## Main scripts:
### downsample_hydro.py
 
 Requires: 
  - scikit-image (uses skimage.measure.block_reduce) https://scikit-image.org/
  - gdalutils (from https://github.com/jsosa/gdalutils)
  
 Inputs (in GeoTiff format):
  - accumulation and strahler order arrays at 3s resolution along river network (for calculation of flow directions)
  - DEM at 3s resolution
  
 Main Steps:
  - Downsamples accumulation and strahler order to lower resolution (using max over each block)
  - Also down-samples the 3s DEM to lower resolution (using the mean over each block)
  - Calculates flow directions over river network by tracing along the rivers from upstream to downstream. 
 
 ### call_streamnet_downsample.py
 
 Requires: 
 - mpiexec
 - streamnet from TauDEM (https://github.com/dtarb/TauDEM)
 - split module from LFPtools (https://github.com/jsosa/LFPtools)
  
 Inputs (in GeoTiff format):
  - dir, net, dem, acc, ord (arrays output by downsample_hydro.py)
  
 Main Steps:
  - Calls streamnet from TauDEM to calculate vector river network
  - calls 'connections' from split in LFPtools to create 'rec' csv file which is used as input to LFPtools to build a lisflood model
