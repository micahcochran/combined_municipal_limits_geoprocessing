"""
This has GIS ETL Classes that could be used in other projects.
"""

from typing import Iterable, Optional, Type, Union
import logging

# imports from external libraries, that may have to be installed
import geopandas as gpd
import pandas as pd

# This is a workaround for a problem in which shapefiles crs are not read
# in the first go-around.  This is an bug from the installation on this machine.
# PERSISTENT_CRS_BUG_WORKAROUND = True
PERSISTENT_CRS_BUG_WORKAROUND = False

class EmptyGISLayer(object):
    """
    This class is a framework for functionality that is defined in
    derived class.
    """
    def __init__(self):
        # if these fields do not exist, make empty tuples so they will 
        # not cause errors from being undefined.
        if not hasattr(self, 'add_fields_list'):
            self.add_fields_list = tuple()
            
        if not hasattr(self, 'delete_fields_list'):
            self.delete_fields_list = []

        if not hasattr(self, 'required_fields'):
            self.required_fields = tuple()
            
       
    def add_fields(self):
        pass

    def copy_fields(self):
        pass

    def delete_fields(self):
        pass

    def select_by_attributes(self):
        pass
        
    def geometry_operations(self):
        pass
        
    def set_projection(self, crs=None):
        pass

    def reproject(self, crs=None):
        pass


class GISLayer(EmptyGISLayer):
    """This add basically"""
    def __init__(self, filename=None, driver: Optional[str] = None, layer: Optional[str] = None, gdf=None):
        EmptyGISLayer.__init__(self)
        self.filename = filename
        
        # check if parameters are interables and not a string
        if not hasattr(self.add_fields_list,'__iter__') and not isinstance(self.add_fields_list, str):
            raise TypeError("add_fields_list parameter must be an iterable (list or tuple) not a string")
        if not hasattr(self.delete_fields_list,'__iter__') and not isinstance(self.delete_fields_list, str):
            raise TypeError("delete_fields_list parameter must be an iterable (list or tuple) not a string")
        if not hasattr(self.required_fields,'__iter__') and not isinstance(self.required_fields, str):
            raise TypeError("required_fields parameter must be an iterable (list or tuple) not a string")
            
        
        if isinstance(gdf, gpd.GeoDataFrame):
            self.gdf = gdf
                        
        # self.gdf = gpd.GeoDataFrame.from_file(filename, driver, layer)
        elif self.filename == None:
            self.gdf = gpd.GeoDataFrame()
        else:
            if PERSISTENT_CRS_BUG_WORKAROUND is True:
                tmp = gpd.read_file(self.filename, driver=driver, layer=layer)
                del tmp
            self.gdf = gpd.read_file(self.filename, driver=driver, layer=layer)
            logging.info("reading {0}".format(self.filename))
        
        self.check_required_fields()
        
    def check_required_fields(self) -> None:
        """
        Checks if the required fields are in the layer.
           logs error if it does not have the required fields.
        """
        
        if isinstance(self.required_fields, str):
            logging.error("self.required fields should not be a string")
        
        required_fields_set = set(self.required_fields)
        
        if len(required_fields_set) == 0:
            return
        
        fields_in_layer_set = set(self.gdf.keys())
        
        if not required_fields_set.issubset(fields_in_layer_set):
            missing_fields = required_fields_set - fields_in_layer_set
            # ugh oh, a required fields isn't here
            logging.error("Required field(s) {0} are not in the layer with filename \"{1}\"".format(list(missing_fields), self.filename))


    def append(self, otherlayers):
        """
        Appends otherlayers to the source layer.
        
        otherlayers can be a GISLayer or an iterable(list, tuple, etc.)
        
        Note: the CRS must be the same for this operation.

        returns a new GISLayer object
        """
        # append in Pandas works to put layers together into the same dataset and create a new copy
        # append in ArcGIS Desktop works to put layers together into the same dataset into the target datasets
        # in ArcGIS Desktop terms the Pandas one would be called merge
        # 2023-04-30 - This is accomplished with a concat operation in geopandas.
#       pdb.set_trace()

        # FIXME: Should check if self.gdf is empty.

        if isinstance(otherlayers, str):
            raise TypeError("otherlayer is not a GISLayer or an iterable(list, tuple, etc.)")

        if not ( hasattr(otherlayers,'__iter__') or isinstance(otherlayers, GISLayer) ):
            raise TypeError("otherlayer is not a GISLayer or an iterable(list, tuple, etc.)")
            
        if not hasattr(otherlayers,'__iter__'):  # not an iterable
            # other layers is just one layer
            joined = pd.concat([otherlayers.gdf, self.gdf])
        else:
            join_layers_list = [l.gdf for l in otherlayers]
            join_layers_list.append(self.gdf)
            joined = pd.concat(join_layers_list)

        joined.set_geometry(self.gdf._geometry_column_name, inplace=True, crs=self.gdf.crs)

        return GISLayer(gdf=new_gdf)

    def concat(self, layers: Iterable):
        # Used documentation https://geopandas.org/en/stable/docs/user_guide/mergingdata.html#appending
        # get just the geodata frames
        layers_gdf = [l.gdf for l in layers]
        joined = pd.concat(layers_gdf)
        return GISLayer(gdf=joined)

    def combine_geometry_multipart(self):
        """ combines all the geometry in a layer into one row with a Multipolygon.
        
        This is also called singlepart geometry to multipart geometry.
        
        """
        # this is a type shapely.geometry.multipolygon.MultiPolygon
        union_geom = self.gdf.unary_union  
        
        # copies first record's properties, not ideal
        properties = self.gdf.iloc[0].to_dict()
        del properties['geometry']
        
        # using pygeoif is to make this into features is a bit hackish
        # shapely does not support features
        # feature = pygeoif.Feature(pygeoif.MultiPolygon(uni), props)
        
        # create a new GeoDataFrame with the union geometry and properties
        self.gdf = gpd.GeoDataFrame(data=[properties], geometry=[union_geom], crs=self.gdf.crs)
    
    def clip(self, clip_layer):
        # reproject if projection is different from county_boundary
        if clip_layer.crs != self.gdf.crs:
            clip_layer = clip_layer.to_crs(crs=self.gdf.crs)
        
        
        return self.gdf['geometry'].intersection(clip_layer.unary_union)
    
    def delete_fields (self):
        logging.debug('delete_fields() called')
        EmptyGISLayer.delete_fields(self)

        # is the list None
        if self.delete_fields_list is None:
            return
        
        if not isinstance(self.delete_fields_list, list):
            raise TypeError("self.delete_fields_list is not a list")

        if len(self.delete_fields_list) > 0:
            # delete if not an empty list
            logging.info('deleting fields: {}'.format(str(self.delete_fields_list)))
            logging.debug('self.gdf has fields: {}'.format(str(self.gdf.keys())))
            
            # check if columns are in the geodataframe
            for field in self.delete_fields_list:
                if field not in self.gdf:
                    raise KeyError("Field '{}' not is layer".format(field))
                
            #    self.gdf.drop(columns=field, inplace=True)

            self.gdf.drop(columns=self.delete_fields_list, inplace=True)


# NOTE: This class is unused.
class ServiceAreaLayer(object):     
    # this could also be accomplished in this manner
    # geopandas.tools.overlay(county_boundary_102630, municipal_boundaries, 'difference')
    # followed by a singlepart -> multipart conversion
    def county_service_area_mask(self, county_boundary, other_service_areas):
        """
        Creates a mask that shows only the portion in the county.
        
        """
        
        # this does a spatial difference algorithm
        
        # BIG ASSUMPTION the county boundary is one polygon,
        # geopandas (or me) does not seem to be able to get this to work
        # otherwise
        if len(county_boundary.index) != 1:
            raise ValueError("county_boundary can only have one row, is has {} rows".format(len(county_boundary.index)))
        
        # reproject if projection is different from county_boundary
        if other_service_areas.crs != county_boundary.crs:
            other_service_areas = other_service_areas.to_crs(crs=county_boundary.crs)
        
        
        other_service_areas_flat = gpd.GeoSeries(other_service_areas.geometry.unary_union, crs=county_boundary.crs)
        
        service_area = county_boundary.copy()
        
        # replace geometry, leave attributes intact
        service_area.geometry = county_boundary.difference(other_service_areas_flat)
        
        return service_area
    
    def service_area_from_spreadsheet(self, county_boundary, 
                                      other_service_areas, spreadsheet_filename, sheet_name, key='GNIS', delete_fields='county_boundary'):
        """
        Creates a service area based on a spreadsheet and geometry.
        """
        # this could probably be made more generic
        
        # deletes fields
        if 'county_boundary' in delete_fields:
            remove_fields = list(county_boundary.keys())
            remove_fields.remove(key)
            remove_fields.remove('geometry')
            county_boundary.drop(remove_fields)

        # reproject if projection is different from county_boundary
        if other_service_areas.crs != county_boundary.crs:
            other_service_areas = other_service_areas.to_crs(crs=county_boundary.crs)

        spreadsheet = pd.read_excel(spreadsheet_filename, sheet_name)
            
        other_service_areas_joined = pd.merge(other_service_areas, spreadsheet, how='left', on=key)
        
        # filter out ones that do not have 'Yes' in DifferentJurisdictionfromCounty field
        filtered_service_areas = other_service_areas_joined[ other_service_areas_joined['DifferentJurisdictionfromCounty'] == 'Yes' ]

        
        county_boundary_joined = pd.merge(county_boundary, spreadsheet, how='left', on=key)
        
        # append geodataframes
        ret = filtered_service_areas.append(county_boundary_joined)
        return ret

