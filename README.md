# combined_municipal_limits_geoprocessing

## Description

A Python command line ETL (Extract Tranform Load) script that combines City Limits from multiple GIS layers into one GIS layer using a unified schema for Limestone County (Alabama, USA).  This takes five (5) files, with four (4) different schema and two (2) projections.  The script merges the files are merged into one layer with one projection and one schema.

The GIS data is stored in the  [municipal_limits/](/municipal_limits) folder.  The provided GIS data is AS IS.  It is provided for the purpose of testing the script.  If you need current data, contact the respective local governments for current official data.  
 
The script is robust enough that if you add a newer city limit layer that it will pull the most recent one based on the folder being named a newer date.  The folder dates are in the format ``"YYYY MM DD"``.  For some of the city layers, it will use this folder date to populate the attribute table.  For the Athens City Layer, it pulls the most recent layer from the a File GeoDatabase based on the layer's name.

Outputs to a shapefile: `municipal_limits/2021-02-23--limestone_co_municipal_limits.shp` and all of the other files associated with a shapefile.

The original goal was to output to ESRI's File GeoDatabase format, but that is and ESRI proprietary format that is not as easy for someone to casually use.  Code was left so that might be able to be reenabled with some work.

## Requirements

This has been brought up to work with Python 3.10, so that needs to be installed.  (The minimum version is atleast 3.7 because of the function like `datetime.datetime.fromisoformat()` being used, type hints, and f-strings being used.)


* Linux works best--the packages can be installed just with `pip`.   (On a fresh install you may need to install the `gcc` Compiler.)  Most popular distributions like Ubuntu come with Python 3.x preinstalled.

* MacOS will likely work fine.  

* Window: I would suggest installing WSL2 (Windows Subsystem for Linux version 2).  This installs a Linux Virtual Machine that runs with Linux and works very well. The first versions were developed on Windows using the [OSGeo4W project](https://trac.osgeo.org/osgeo4w/). OSGeo4W project software installed was a little out of date, but most everything including Python can be installed from it.  The Old Notes section discusses OSGeo4W.  

Note: Installation Step 6 is the hardest and Linux will probably work best.  **I am probably leaving out software needs to be installed.**


Note: Anaconda (conda) might be another way to install the libraries without having to compile binaries.

## Installation

1. Download the software from GitHub.  Download the ZIP or use git to clone the repository.
2. Go to the Terminal.  
3. Use the command line to `cd` change directories to where you saved this file.
4. Create an environment. (Use conda if you want to, but that is an exercise left to the reader):
```bash
python -m venv geoprocess-env
```
5. Activate the environment.  Deactivate conda or other environments before (`conda deactivate`). Note that `activate` below is for bash shell, and there is activate for different shells--csh (`activate.csh`), fish shell (`activate.fish`), and Powershell (`Activate.ps1`):
```bash
source geoprocess-env/bin/activate
```
6. Install packages in the environment.
```bash
pip install -r requirements.txt
```
Read the messages from `pip` and make sure that nothing caused errors.

## Run 

(Activate the environment -> run `source geoprocess-env/bin/activate`)
```bash
python municipal_limits_geoprocess.py
```

There are lots of log messages that are mostly debug messages.  That doesn't mean that anything is wrong. A raised exception means that something went wrong.

Optionally, the run the bash shell script `run_geoprocess.sh` (it activates the environment and runs `municipal_limits_geoprocess.py`).  This script assumes that you are using the `venv` geoprocess-env.

## 2023 Updates

As of 2023, the program was updated to work with Python 3.10.  This update also updates to newer software versions.

Modifications based on new version in `gislayer.py`:
1. `combine_geometry_multipart()` had to be modified, which allowed removal of the external library `pygeoif`.
2. `combine_layers()`, appending
3. Added type hints  in areas where code that I worked on.  (Type hints were new standard feature in Python 3.5.)  These help with readability.
4. Combining layers had to be done differently using the geopandas `concat()`.  Perhaps there are more data checks in place.
5. Had to do some fiddling to convert date strings for some of the layers into pandas Timestamps.

GDAL 3.6.x (first released on 2022-11-11) in the OpenFileGDB driver added supports writing to File Geodatabases for ArcGIS 10.x.  Before this, you had to install FileGDB, which was linked to ESRI's proprietary code for writing the File GeoDatabases.  Because of that Fiona would make it easy to write ESRI File Geodatabases. 

## Old Notes (from ~2015 with slight updates)

The first version of this was created as a GeoKettle ETL "script"--this was a visual ETL process.

OSGeo4W provides a good foundation for some of this software, but it isn't required.

The following external modules must be installed
  * geopandas
     - which requires pandas and Fiona
  * Fiona
     - probably easiest to install by a wheel https://www.lfd.uci.edu/~gohlke/pythonlibs/#fiona
     - requires GDAL
  * ~~pygeoif~~
  * shapely (OSGeo4W provides)
  * pyproj (OSGeo4W provides)