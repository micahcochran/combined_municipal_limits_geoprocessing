# geopandas using development version as of 2015-09-28
# hopefully a prerelease of geopandas 0.2


# Using Python 3.5+.

# Standard Modules
import datetime
import logging
# import pprint
from pathlib import Path
from typing import Optional
import time
from collections import OrderedDict

# These modules are external and will need to be installed.
import dateutil.parser
import pandas as pd
import geopandas as gpd
import fiona

# modules for this program
import gislayer

# for DEBUG
# import faulthandler; faulthandler.enable()

# When True, this does a test run without actually writing any data. 
NO_WRITE = False

# alabama_state_plane_feet_west_crs = {'init':'esri:102630'}
# The above syntax is no longer valid as of PROJ version 6+:
# https://pyproj4.github.io/pyproj/stable/gotchas.html#axis-order-changes-in-proj-6

ALABAMA_SP_FT_WEST_CRS = 'ESRI:102630'
# Note: This projection uses the U.S. Survey Foot.
# The U.S. Survey Foot has been deprecated as for 2022-12-31
# see:  https://www.federalregister.gov/d/2020-21902
# As of perhaps 2019, the Alabama Department of Revenue Property Tax Map specifications required the U.S. Survey Foot.

# Technically, this should be MunicipalLimitLayer
class CityLimitLayer (gislayer.GISLayer):
    """This class gives basic functionality for all derived city limit layers."""
    def __init__(self, filename=None,  driver: Optional[str] = None,
                 layer: Optional[str] = None, parse_folder_date_flag: bool = True):
        
        # indicates there is date information in the folder that needs to be parsed
        self.parse_folder_date_flag = parse_folder_date_flag
        # call the super layer
        gislayer.GISLayer.__init__(self, filename=filename, driver=driver, layer=layer)
        
        if self.filename != None:
            self.geoprocess()
        
    def set_projection(self, crs=ALABAMA_SP_FT_WEST_CRS):
        # NOTE this may change in a future version of geopandas (above 0.5.0)
        if not isinstance(crs, (dict, str)):
            raise TypeError(f"crs must be a proj4 dictionary or proj4 string, not {type(crs)}: {crs}")
        
        self.gdf.crs = crs
    
    def geoprocess(self):
        """
        These are the process that run to geoprocess the layer.  
        This says what functions should be called in what order. 
        """
        if self.parse_folder_date_flag == True:
            self.parse_folder_date()
        
        self.select_by_attributes()

        # geometry operations
        self.geometry_operations()
        self.reproject()

        # deal with fields
        self.copy_fields()
        
        for (field, value) in self.add_fields_list:
            self.gdf[field] = value
            
        self.add_fields()
        self.copy_fields()
        # took a different approach, by just only writing the desired fields to the file.
#        self.delete_fields()
        
        for field in self.delete_fields_list:
            if field not in self.gdf.columns:
                raise KeyError( 'column "{0}" does not exist in filename: {1}'.format(field, self.filename) )
            del self.gdf[field]

        self.calculate_area()
        
    def reproject(self):
        pass
        
    def parse_folder_date(self):
        """
        Parses the date from self.filename.
        
        sets self.folder_date to a dateime.date object of the date.
        
        Example:
           self.filename = r'C:\projects\departments\limestone_county\municipal_limits\cities\decatur\2019 06 10\Decatur_Corporate_Limits.shp'
           returns self.folder_date = datetime.date(2019, 6, 10)
        """
        # this worked on Linux
        # folder_date_str = os.path.dirname(self.filename).split('/').pop()
 
        # hopefully this is more cross platform.
        folder_date_str = Path(self.filename).parts[-2]
        
        # this is a dateime.date object
        folder_date = datetime.date(*dateutil.parser.parse(folder_date_str).utctimetuple()[0:3])
        # OLD version converted to a string :-(
        # self.folder_date = str(folder_date)
        # stores data in column a pandas Timestamp.
        self.folder_date = pd.Timestamp(folder_date)
        
    def calculate_area(self):
        # set area for MUNIAREA (Square Miles) field, 43560 sq ft in an acre, 640 acres in a sq mile
        # area is in the native units, which in this case is square US Survey Feet.
        self.gdf['MUNIAREA'] = self.gdf.area / 43560 / 640


class AthensLimitLayer(CityLimitLayer):
    def __init__(self, filename, driver=None, layer=None):
        self.required_fields = ('GNIS', 'NAME', 'LOCALFIPS', 'MUNITYP', 
                          'ProperName', 'Source', 'SrcURL', 'LASTUPDATE')
        
        self.delete_fields_list = ['Shape_Area', 'Shape_Length']
        
        # super(CityLimitLayer, self).__init__(filename, required_fields)
        CityLimitLayer.__init__(self, filename=filename, driver=driver, layer=layer, parse_folder_date_flag=False)
    
        
    def geometry_operations(self):
        self.combine_geometry_multipart()

    def reproject(self):
        self.gdf.to_crs(crs=ALABAMA_SP_FT_WEST_CRS, inplace=True)


class HuntsvilleLimitLayer(CityLimitLayer):
    def __init__(self, filename):
        self.required_fields_list = ('CityName', 'Eff_Date', 'Mod_Date')
        self.add_fields_list = ( 
                ('GNIS' , 2404746),
                ('LOCALFIPS', '37000'),
                ('MUNITYP', 'City'),
                ('ProperName', 'City of Huntsville'),
                ('Source', 'City of Huntsville, GIS Dept.'),
                ('SrcURL', 'https://www.huntsvilleal.gov/development/building-construction/gis/data-depot/')
            )
        
#        self.delete_fields_list = ('CityName', 'Shape_area', 'Shape_len', 
#                                   'Mod_Date', 'Eff_Date')

        self.delete_fields_list = ['CityName', 'Mod_Date', 'Eff_Date', 'Mod_User',
                                   'SHAPE_STAr', 'SHAPE_STLe']

        CityLimitLayer.__init__(self, filename, parse_folder_date_flag = False)

    def copy_fields(self):
        self.gdf['NAME'] = self.gdf['CityName']
        self.gdf['LASTUPDATE'] = pd.Timestamp(max(self.gdf['Eff_Date']))

    def reproject(self):
        self.gdf.to_crs(crs=ALABAMA_SP_FT_WEST_CRS, inplace=True)


class MadisonLimitLayer(CityLimitLayer):
    def __init__(self, filename):
        self.required_fields = ('Name',)
        self.add_fields_list = (
                ('GNIS', 2404989),
                ('LOCALFIPS', '45784'),
                ('MUNITYP', 'City'),
                ('ProperName', 'City of Madison'),
                ('Source', 'City of Madison, Engineering Dept.')
                # NAME?
            )
        self.delete_fields_list = ['Name', 'Use_Status', 'Shape_area']
        CityLimitLayer.__init__(self, filename, parse_folder_date_flag = True)

    def copy_fields(self):
        self.gdf['NAME'] = self.gdf['Name']
        self.gdf['LASTUPDATE'] = self.folder_date

    def reproject(self):
        self.gdf.to_crs(crs=ALABAMA_SP_FT_WEST_CRS, inplace=True)


class DecaturLimitLayer(CityLimitLayer):
    def __init__(self, filename):
        self.add_fields_list = (
                ('GNIS', 2404206),
                ('LOCALFIPS', '20104'),
                ('MUNITYP', 'City'),
                ('NAME', 'Decatur'),
                ('ProperName', 'City of Decatur'),
                ('Source', 'City of Decatur, Information Technology Dept.'),
            )
        self.delete_fields_list = ['Shape_STAr', 'Shape_STLe']
        
        CityLimitLayer.__init__(self, filename, parse_folder_date_flag = True)
        

    def copy_fields(self):
        self.gdf['LASTUPDATE'] = self.folder_date


    def geometry_operations(self):
        self.combine_geometry_multipart()

    def reproject(self):
        self.gdf.to_crs(crs=ALABAMA_SP_FT_WEST_CRS, inplace=True)

class TownsLimitLayer(CityLimitLayer):
    """
    This is a class for all of the Towns and Ardmore City.  These change less so are stored here.
    """
    def __init__(self, filename, driver, layer):
        # fill required_fields out
        self.required_fields = ('MUNITYP', 'NAME')
        self.delete_fields_list = ['Shape_Area', 'Shape_Length']
        CityLimitLayer.__init__(self, filename, driver=driver, layer=layer, parse_folder_date_flag=False)

    def select_by_attributes(self):
        # Filters by selecting by attribute where 'MUNITYP' is 'Town' or 'NAME' is 'Ardmore'.
        # In effect, this gets rid of all of the City layers except for Ardmore City in the layer.
        filter_gdf = self.gdf[(self.gdf['MUNITYP'] == 'Town') | (self.gdf['NAME'] == 'Ardmore')]
        self.gdf = filter_gdf

    def reproject(self):
        self.gdf.to_crs(crs=ALABAMA_SP_FT_WEST_CRS, inplace=True)

        
class MunicipalLimitsGeoProcess(object):
    def __init__(self, base_folder):
        self.base_folder = base_folder

    def read_layers(self):
        self.decatur = DecaturLimitLayer(self.find_most_recent_shp('decatur/'))
        self.huntsville = HuntsvilleLimitLayer(self.find_most_recent_shp('huntsville/'))

        # self.madison = MadisonLimitLayer(self.base_folder + 'madison/2016 09 02/MadCityLimits_9-2-16.shp')
        self.madison = MadisonLimitLayer(self.find_most_recent_shp('madison/'))
        self.towns = TownsLimitLayer(filename='./municipal_limits/MunicipalLimits.gdb', 
                                driver='OpenFileGDB', layer="MunicipalBoundary")

        self.athens = AthensLimitLayer(r'./municipal_limits/AthensMunicipalLimits.gdb',
                        driver='OpenFileGDB',
                        layer = self.find_most_recent_gdb(r'./municipal_limits/AthensMunicipalLimits.gdb', 
                                                          layer_prefix='AthensMunicipalBoundary')
                        )
        self.muni_layers = [self.athens, self.decatur, self.madison, self.huntsville, self.towns]
    
    def combine_layers(self):
        self.combined = CityLimitLayer()

        # self.combined = self.combined.append(self.muni_layers)
        self.combined = self.combined.concat(self.muni_layers)
        self.combined.set_projection(crs=ALABAMA_SP_FT_WEST_CRS)

        # print(self.combined.gdf['NAME'], flush=True)          # DEBUG
        # print(self.combined.gdf['LASTUPDATE'], flush=True)    # DEBUG

        most_recent_datetime = max(self.combined.gdf['LASTUPDATE'])
        # get rid of the time portion of this.
        most_recent_date = datetime.datetime.fromisoformat(str(most_recent_datetime)).date()
        # for shapefile format
        self.dataset_date = most_recent_date.isoformat()
        # for GDB format
#        dataset_date = most_recent_datetime.strftime('%Y_%m_%d')
 #       print('most_recent_date: {}'.format(most_recent_date))
        # Format date like this 2015_09_08, FileGDB dislikes dashes
#        dataset_date = most_recent_date.strftime("%Y%m%d")
        
#       pdb.set_trace()
        # the FileGDB driver crashed this
#       gpd.io.file.to_file(combined.gdf, filename='C:/projects/departments/limestone_county/municipal_limits/MunicipalLimits.gdb', 
#                               driver='FileGDB', layer="MunicipalBoundary_"+dataset_date)
        
        #shp_filename_output = 'C:/projects/departments/limestone_county/municipal_limits/limestone_co_municipal_limits.shp'
        
        
        # VERBOSE
        # pprint.pprint(combined.gdf)

    def write(self):
        shp_filename_output = f'./municipal_limits/{self.dataset_date}--limestone_co_municipal_limits.shp'
        logging.info(f'Writing to the file {shp_filename_output}')

        # should this generate GlobalIDs if the row does not have one, using Python uuid?
        # Could feed a GeoJSON representation of the road into uuid.

        # geopandas does okay with building a schema, but the LASTUPDATE
        # field must be date it is not yet smart enough to do that.
        schema_props = OrderedDict([("NAME", "str:50"),
                                    ("ProperName", "str:50"), 
                                    ("MUNITYP", "str:10"), 
                                    ("GNIS", "int:10"), 
                                    ("LOCALFIPS", "str:5"), 
                                    ("GlobalID", "str:38"), 
                                    ("LASTEDITOR", "str:50"), 
                                    ("LASTUPDATE", "date"), 
                                    # ("LASTUPDATE", "str:8"),  # OLD way of storing a date
                                    ("ChangeDesc", "str:254"),                                   
                                    ("MUNIAREA", "float:24.3"),
                                    ("Source", "str:100"), 
                                    ("SrcURL", "str:254")])
        
        # CHECK IF NAMES MATCH SCHEMA IN DATA

        # write a shapefile
        if NO_WRITE is not True:
            self.combined.gdf.to_file(filename=shp_filename_output, 
                                      driver='ESRI Shapefile',
                                      schema={"geometry" : "Polygon",
                                              "properties": schema_props}
                                    )

        # the FileGDB driver crashed this
#        import ipdb; ipdb.set_trace()
#        gpd.io.file.to_file(combined.gdf, 
#                           filename='C:/projects/departments/limestone_county/municipal_limits/new6MunicipalLimits.gdb', 
#                           driver='FileGDB', 
#                           layer="MunicipalBoundary_"+dataset_date) #,
#                           schema={"geometry" : "Polygon",
#                                   "properties": schema_props})
        
#        print("combined.gdf.crs: {0}".format(combined.gdf.crs))        
        
#        import fiona
#        with fiona.drivers():
#            with fiona.open('C:/projects/departments/limestone_county/municipal_limits/newMunicipalLimits'+dataset_date+'.gdb',
#            with fiona.open('C:/projects/departments/limestone_county/municipal_limits/newMunicipalLimits_{}.gdb'.format(dataset_date),
#                            'w',
#                            driver='FileGDB', 
#                            layer="MunicipalBoundary_{}".format(dataset_date),
#                            crs=combined.gdf.crs,
#                            schema={"geometry" : "Polygon",
#                                       "properties": schema_props}) as out:
#                out.write(combined.gdf)

        

    # finds the most recent data set    
    def find_most_recent_gdb(self, gdb_path, layer_prefix=None):
            layer_list = [x for x in fiona.listlayers(gdb_path) if x.startswith(layer_prefix)]
            layer_list.sort(reverse=True)
            return layer_list[0]


    def find_most_recent_shp(self, rel_folder):
            shp_folder = Path(self.base_folder + rel_folder)
            # filter out not directories
            folders = [x for x in shp_folder.iterdir() if x.is_dir()]
            folders.sort(reverse=True)
            for folder in folders:
                # check for a shapefile within the folder
                result = folder.glob('*.shp')
                for shp_filename_path in result:
                    return shp_filename_path
            return None


if __name__ == '__main__':
    # DEBUG is a bit chatty
    # logging.basicConfig(format='%(levelname)s : %(message)s', level=logging.DEBUG)
    logging.basicConfig(format='%(levelname)s : %(message)s', level=logging.INFO)
    logging.info( "Started:  {0}".format(time.asctime()) )
    
    #### THIS IS THE NEW LOCATION TO STORE ALL OF THE CITY LIMIT DATA FOR ETL PROCESSING ####
    folder = './municipal_limits/cities/'
    mlgp = MunicipalLimitsGeoProcess(folder)
    mlgp.read_layers()
    mlgp.combine_layers()
    mlgp.write()
    
    logging.info( "Ended:  {0}".format(time.asctime()) )


# Fiona seems to crash python when it has an error,  such as using dashes (-) in a name.
