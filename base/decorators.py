""" This module provides function-style decorators for implementing ArcGIS input parameters

Understanding this code requires an understanding of python decorators which are
an advanced feature of the python language.

This module became necessary as the amount of tools grew, it is used for two reasons:
1. Forces tools to present input parameters consistently
2. Saves LOTS of code. As an example, using it on
   tools.raster.zonal_stats_as_table
   saves around *** 100 *** lines of code. So over the project this module saves THOUSANDS of lines of code.

Basically, the base.BaseTool class getParameterInfo method is implemented to return an empty list.

The decorators are applied to the descendant's getParameterInfo method whereby then create their parameters and inject them into the parameter collection.

Works very well.

"""
from arcpy import Parameter, ListEnvironments
from functools import wraps
from base.utils import raster_formats, resample_methods, aggregation_methods, data_nodata, expand_trunc, stats_type, pixel_type, raster_formats2, transform_methods


def parameter(name, display_name, data_type, parameter_type, multi_value, direction, value_list, default_environment, dependancy_list, default_value, category=None, enabled=True):
    """ Wrap a function with a function that generates a generic parameter


    """

    validate_parameter(name, display_name, data_type, parameter_type, multi_value, direction, value_list, default_environment, dependancy_list, default_value)

    par = Parameter(name=name, displayName=display_name, datatype=data_type, parameterType=parameter_type, multiValue=multi_value, direction=direction,
                    category=category)

    if value_list:  # and data_type == "GPString":
        if value_list[0] == "Range" and len(value_list) == 3:  # a range, probably need to extend this usage a bit in hindsight
            try:
                par.filter.type = "Range"
                par.filter.list = value_list[1:3]
            except:
                pass
        else:
            try:
                par.filter.list = value_list
            except:
                pass

    if default_environment:
        par.defaultEnvironmentName = default_environment

    if default_value:
        par.value = default_value

    if dependancy_list:
        par.parameterDependencies = dependancy_list  # should be constant

    if not enabled:
        par.enabled = False

    def decorated(f):
        """

        Args:
            f:

        Returns:

        """

        @wraps(f)
        def wrapped(*args, **kwargs):
            """

            Args:
                args:
                kwargs:

            Returns:

            """
            params = f(*args, **kwargs)

            params.insert(0, par)

            return params

        return wrapped

    return decorated


def validate_parameter(name, display_name, data_type, parameter_type, multi_value, direction, value_list, default_environment, dependancy_list, default_value):
    """ Ensure the arguments for the parameter wrappers are half-way sensible

    Args:
        name ():
        display_name ():
        data_type ():
        parameter_type ():
        multi_value ():
        direction ():
        value_list ():
        default_environment ():
        dependancy_list ():
        default_value ():

    Returns:

    """
    if not isinstance(name, basestring):
        raise ValueError("name must be a string {0}".format(name))

    if not isinstance(display_name, basestring):
        raise ValueError("display_name must be a string {0}".format(name))

    if not isinstance(data_type, (basestring, list)):
        raise ValueError("data_type must be a string or a list{0}".format(name))
    if isinstance(data_type, list):
        for dt in data_type:
            if dt not in arc_parameter_datatype_list():
                raise ValueError("data_type must be one of {0}\nGot {1}".format(arc_parameter_datatype_list(), dt))

    pt_list = ("Required", "Derived", "Optional")
    if parameter_type not in pt_list:
        raise ValueError("parameter_type must be in {0}\nGot {1}".format(pt_list, parameter_type))
    if parameter_type == "Derived" and direction != "Output":
        raise ValueError("Derived parameter types must have direction set to 'Output', not '{0}'".format(direction))

    if value_list and not isinstance(value_list, list):
        raise ValueError("value_list must be a list {0}".format(value_list))

    if value_list and default_value and default_value not in value_list:
        raise ValueError("default_value is not in value_list {0} IS NOT IN {1}".format(default_value, value_list))

    if not isinstance(multi_value, bool):
        raise ValueError("multi_value must be a boolean")

    directions = ["Input", "Output", "Derived"]
    if direction not in directions:
        raise ValueError("direction must be one of {0}".format(directions))

    if default_environment and default_environment not in arc_environment_list():
        raise ValueError("default_environment must be one of {0}".format(arc_environment_list))

    if dependancy_list and not isinstance(dependancy_list, list):
        raise ValueError("dependancy_list must be a list {0}".format(dependancy_list))

    return


class TableSetting(object):
    """

    """

    def __init__(self, data_type):
        """

        Args:
            data_type:

        Returns:

        """

        data_types = ["geodata", "raster", "feature", "xml", "cdf"]

        if data_type not in data_types:
            raise ValueError("Unsupported type: '{}' is not a member of {}".format(data_type, data_types))

        self.table_name = "{}_table".format(data_type)
        self.fields = "{0} {1} Required {0}".format(data_type, data_type.title())

        if len(data_type) != 3:  # for T.L.A.s we will capitalise
            self.table_display_name = "Table for {}".format(data_type.title())
        else:
            self.table_display_name = "Table for {}".format(data_type.upper())

        return


def parse_fields(fields):
    """

    Args:
        fields:

    Returns:
        Parsed List

    """

    parsed_list = []

    if not isinstance(fields, str):
        raise ValueError("Bad fields descriptor '{}': should be like 'a b c d, e f g h, ...'".format(fields))

    field_list = fields.split(",")  # ["w x y z", "w x y z", ...]
    print field_list

    for f in field_list:

        x = f.split()  # [["w", "x", "y", "z"]] or [["w", "x", "y", "z"], ["w", "x", "y", "z"], ...]
        assert len(x) == 4

        x[2].replace("_", " ")

        if x[3] == "None":
            x[3] = None

        parsed_list.append(x)

    return parsed_list


def input_tableview(data_type="geodata", multi_value=False, other_fields=None, ob_name=None, ob_title=None):
    """ Wrap a function with a function that generates an input tableview parameter

    Args:
        ob_title ():
        ob_name ():
        other_fields ():
        data_type ():
        multi_value ():

    Returns:
        Wrapped function

    """

    # setup and validate
    if data_type:
        tset = TableSetting(data_type)
        required_fields = parse_fields(tset.fields)
    else:
        required_fields = []

    if other_fields:
        other_fields = parse_fields(other_fields)
        required_fields.extend(other_fields)

    # create parameter
    pn = ob_name or tset.table_name
    dn = ob_title or tset.table_display_name

    par = Parameter(name=pn,
                    displayName=dn,
                    datatype="GPTableView",
                    parameterType="Required",
                    multiValue=multi_value,
                    direction="Input")
    pars = [par]

    # create dependent parameters

    for f_name, f_disp, f_type, f_default in required_fields:

        f_disp = f_disp.replace("_", " ").title()

        p = Parameter(name=f_name,
                      displayName="Field for {0}".format(f_disp),
                      datatype="Field",
                      parameterType=f_type,
                      multiValue=False,
                      direction="Input")
        if f_default:
            if f_default == "None":
                f_default = None
            p.value = f_default

        p.parameterDependencies = [pn]  # should be constant

        pars.append(p)

    # wrapper

    def decorator(f):
        """

        Args:
            f:

        Returns:

        """

        @wraps(f)
        def wrapper(*args, **kwargs):
            """

            Args:
                args:
                kwargs:

            Returns:

            """
            params = f(*args, **kwargs)

            try:
                for i, par in enumerate(pars):
                    params.insert(i, par)
            except:
                params = pars

            print "input_tableview", [p.name for p in params]

            return params

        return wrapper

    return decorator


def input_output_table(affixing=False, out_file_workspace=True):
    """ Wrap a function with a function that generates output table parameters

        Kwargs:
            affixing: Flags if prefix and suffix input parameters should be built
            out_file_workspace: Flags if output file workspace input parameter should be built

        Returns:
            Wrapped function, wrapper implementing parameters

    """

    # Result Table
    par0 = Parameter(displayName="Result Table",
                     name="result_table",
                     datatype=["GPTableView"],
                     parameterType="Derived",
                     direction="Output")

    # Fail Table
    par1 = Parameter(displayName="Fail Table",
                     name="fail_table",
                     datatype=["GPTableView"],
                     parameterType="Derived",
                     direction="Output")

    # Output Workspace
    par2 = Parameter(displayName="Output Workspace",
                     name="output_workspace",
                     datatype=["DEWorkspace"],
                     parameterType="Required",
                     direction="Input")

    par2.defaultEnvironmentName = "workspace"

    pars = [par0, par1, par2]

    if affixing:
        # Output filename suffix
        par3 = Parameter(displayName="Output Filename Prefix",
                         name="output_filename_prefix",
                         datatype="GPString",
                         parameterType="Optional",
                         direction="Input",
                         category="Output Filename Affixes")

        # Output filename suffix
        par4 = Parameter(displayName="Output Filename Suffix",
                         name="output_filename_suffix",
                         datatype="GPString",
                         parameterType="Optional",
                         direction="Input",
                         category="Output Filename Affixes")

        # Output file workspace
        if out_file_workspace:
            par5 = Parameter(displayName="Output File Workspace",
                             name="output_file_workspace",
                             datatype="DEWorkspace",
                             parameterType="Optional",
                             direction="Input",
                             category="Output File (Dataset) Workspace")

            pars.extend([par3, par4, par5])
        else:
            pars.extend([par3, par4])

    # Output Table Name
    par6 = Parameter(displayName="Result Table Name",
                     name="result_table_name",
                     datatype="GPString",
                     parameterType="Required",
                     direction="Input")

    par6.value = "#run_id#"

    pars.append(par6)

    def decorator(f):
        """ Adds the parameters functionally

        Args:
            f: function to be wrapped

        Returns:
            wrapped function
        """
        @wraps(f)
        def wrapper(*args, **kwargs):
            """ Wrapper

            Args:
                args:
                kwargs:

            Returns:

            """
            params = f(*args, **kwargs)

            try:
                for i, par in enumerate(pars):
                    params.insert(i, par)
            except:
                params = pars

            return params

        return wrapper

    return decorator


def input_output_raster_format(f):
    """ Wrap a function with a function that generates an output raster format parameter

    Args:
        f ():

    Returns:

    """

    # Format
    par0 = parameter("output_raster_format", "Output Raster Format", "GPString", "Optional", False, "Input", raster_formats2, None, None, None)

    # Compression
    par1 = parameter("raster_compression", "Output Raster Compression", "GPSAGDBEnvCompression", "Optional", False, "Input", None, "compression", None, None)

    # arcpy.env.compression = "compression_type {value}"

    pars = [par0, par1]

    # def decorator(f):
    #     """
    #
    #     Args:
    #         f:
    #
    #     Returns:
    #
    #     """

    @wraps(f)
    def wrapper(*args, **kwargs):
        """

        Args:
            args:
            kwargs:

        Returns:

        """
        params = f(*args, **kwargs)

        try:
            for i, par in enumerate(pars):
                params.insert(i, par)
        except:
            params = pars

        return params

    return wrapper

    # return decorator


arc_parameter_types_string = """
Data type,datatype keyword,Description
Address Locator,DEAddressLocator,A dataset, used for geocoding, that stores the address attributes, associated indexes, and rules that define the process for translating nonspatial descriptions of places to spatial data.
Address Locator Style,GPAddressLocatorStyle,A template on which to base the new address locator.Analysis Cell Size,analysis_cell_size,The cell size used by raster tools.
Any Value,GPType,A data type that accepts any value.
ArcMap Document,DEMapDocument,A file that contains one map, its layout, and its associated layers, tables, charts, and reports.
Areal Unit,GPArealUnit,An areal unit type and value such as square meter or acre.
Boolean,GPBoolean,A Boolean value.
CAD Drawing Dataset,DECadDrawingDataset,A vector data source with a mix of feature types with symbology. The dataset is not usable for feature class-based queries or analysis.
Calculator Expression,GPCalculatorExpression,A calculator expression.
Catalog Root,DECatalogRoot,The top-level node in the Catalog tree.
Cell Size,GPSACellSize,The cell size used by ArcGIS Spatial Analyst extension.
Cell Size XY,GPCellSizeXY,Defines the two sides of a raster cell.
Composite Layer,GPCompositeLayer,A reference to several children layers, including symbology and rendering properties.
Compression,GPSAGDBEnvCompression,Specifies the type of compression used for a raster.
Coordinate System,GPCoordinateSystem,A reference framework - such as the UTM system - consisting of a set of points, lines, and/or surfaces, and a set of rules, used to define the positions of points in two- and three-dimensional space.
Coordinate Systems Folder,DESpatialReferencesFolder,A folder on disk storing coordinate systems.
Coverage,DECoverage,A coverage dataset, a proprietary data model for storing geographic features as points, arcs, and polygons with associated feature attribute tables.
Coverage Feature Class,DECoverageFeatureClasses,A coverage feature class, such as point, arc, node, route, route system, section, polygon, and region.
Data Element,DEType,A dataset visible in ArcCatalog.
Data File,GPDataFile,A data file.
Database Connections,DERemoteDatabaseFolder,The database connection folder in ArcCatalog.
Dataset,DEDatasetType,A collection of related data, usually grouped or stored together.
Date,GPDate,A date value.
dBase Table,DEDbaseTable,Attribute data stored in dBASE format.
Decimate,GP3DADecimate,Specifies a subset of nodes of a TIN to create a generalized version of that TIN.
Disk Connection,DEDiskConnection,An access path to a data storage device.
Double,GPDouble,Any floating-point number will be stored as a double-precision, 64-bit value.
Encrypted String,GPEncryptedString,Encrypted string for passwords.
Envelope,GPEnvelope,The coordinate pairs that define the minimum bounding rectangle the data source falls within.
Evaluation Scale,GPEvaluationScale,The scale value range and increment value applied to inputs in a weighted overlay operation.
Extent,GPExtent,Specifies the coordinate pairs that define the minimum bounding rectangle (xmin, ymin and xmax, ymax) of a data source. All coordinates for the data source fall within this boundary.
Extract Values,GPSAExtractValues,An extract values parameter.
Feature Class,DEFeatureClass,A collection of spatial data with the same shape type: point, multipoint, polyline, and polygon.
Feature Dataset,DEFeatureDataset,A collection of feature classes that share a common geographic area and the same spatial reference system.
Feature Layer,GPFeatureLayer,A reference to a feature class, including symbology and rendering properties.
Feature Set,GPFeatureRecordSetLayer,Interactive features; draw the features when the tool is run.
Field,Field,A column in a table that stores the values for a single attribute.
Field Info,GPFieldInfo,The details about a field in a FieldMap.
Field Mappings,GPFieldMapping,A collection of fields in one or more input tables.
File,DEFile,A file on disk.
Folder,DEFolder,Specifies a location on a disk where data is stored.
Formulated Raster,GPRasterFormulated,A raster surface whose cell values are represented by a formula or constant.
Fuzzy function,GPSAFuzzyFunction,Fuzzy function.
Geodataset,DEGeodatasetType,A collection of data with a common theme in a geodatabase.
GeoDataServer,DEGeoDataServer,A coarse-grained object that references a geodatabase.
Geometric Network,DEGeometricNetwork,A linear network represented by topologically connected edge and junction features. Feature connectivity is based on their geometric coincidence.
Geostatistical Layer,GPGALayer,A reference to a geostatistical data source, including symbology and rendering properties.
Geostatistical Search Neighborhood,GPGASearchNeighborhood,Defines the searching neighborhood parameters for a geostatistical layer.
Geostatistical Value Table,GPGALayer,A collection of data sources and fields that define a geostatistical layer.
GlobeServer,DEGlobeServer,A Globe server.
GPServer,DEGPServer,A geoprocessing server.
Graph,GPGraph,A graph.
Graph Data Table,GPGraphDataTable,A graph data table.
Group Layer,GPGroupLayer,A collection of layers that appear and act as a single layer. Group layers make it easier to organize a map, assign advanced drawing order options, and share layers for use in other maps.
Horizontal Factor,GPSAHorizontalFactor,The relationship between the horizontal cost factor and the horizontal relative moving angle.
Image Service,DEImageServer,An image service.
Index,Index,A data structure used to speed the search for records in geographic datasets and databases.
INFO Expression,GPINFOExpression,A syntax for defining and manipulating data in an INFO table.
INFO Item,GPArcInfoItem,An item in an INFO table.
INFO Table,DEArcInfoTable,A table in an INFO database.
LAS Dataset,DELasDataset,A LAS dataset stores reference to one or more LAS files on disk, as well as to additional surface features. A LAS file is a binary file that is designed to store airborne lidar data.
LAS Dataset Layer,GPLasDatasetLayer,A layer that references a LAS dataset on disk. This layer can apply filters on lidar files and surface constraints referenced by a LAS dataset.
Layer,GPLayer,A reference to a data source, such as a shapefile, coverage, geodatabase feature class, or raster, including symbology and rendering properties.
Layer File,DELayer,A file with a .lyr extension that stores the layer definition, including symbology and rendering properties.
Line,GPLine,A shape, straight or curved, defined by a connected series of unique x,y coordinate pairs.
Linear Unit,GPLinearUnit,A linear unit type and value such as meter or feet.
Long,GPLong,An integer number value.
M Domain,GPMDomain,A range of lowest and highest possible value for m coordinates.
MapServer,DEMapServer,A map server.
Mosaic Dataset,DEMosaicDataset,A collection of raster and image data that allows you to store, view, and query the data. It is a data model within the geodatabase used to manage a collection of raster datasets (images) stored as a catalog and viewed as a mosaicked image.
Mosaic Layer,GPMosaicLayer,A layer that references a mosaic dataset.
Neighborhood,GPSANeighborhood,The shape of the area around each cell used to calculate statistics.
Network Analyst Class FieldMap,NAClassFieldMap,Mapping between location properties in a Network Analyst layer (such as stops, facilities and incidents) and a point feature class.
Network Analyst Hierarchy Settings,GPNAHierarchySettings,A hierarchy attribute that divides hierarchy values of a network dataset into three groups using two integers. The first integer, high_rank_ends, sets the ending value of the first group; the second number, low_rank_begin, sets the beginning value of the third group.
Network Analyst Layer,GPNALayer,A special group layer used to express and solve network routing problems. Each sublayer held in memory in a Network Analyst layer represents some aspect of the routing problem and the routing solution.
Network Dataset,DENetworkDataset,A collection of topologically connected network elements (edges, junctions, and turns), derived from network sources and associated with a collection of network attributes.
Network Dataset Layer,GPNetworkDatasetLayer,A reference to a network dataset, including symbology and rendering properties.
Parcel Fabric,DECadastralFabric,A parcel fabric is a dataset for the storage, maintenance, and editing of a continuous surface of connected parcels or parcel network.
Parcel Fabric Layer,GPCadastralFabricLayer,A layer referencing a parcel fabric on disk. This layer works as a group layer organizing a set of related layers under a single layer.
Point,GPPoint,A pair of x,y coordinates.
Polygon,GPPolygon,A connected sequence of x,y coordinate pairs, where the first and last coordinate pair are the same.
Projection File,DEPrjFile,A file storing coordinate system information for spatial data.
Pyramid,GPSAGDBEnvPyramid,Specifies if pyramids will be built.
Radius,GPSARadius,Specifies which surrounding points will be used for interpolation.
Random Number Generator,GPRandomNumberGenerator,Specifies the seed and the generator to be used when creating random values.
Raster Band,DERasterBand,A layer in a raster dataset.
Raster Calculator Expression,GPRasterCalculatorExpression,A raster calculator expression.
Raster Catalog,DERasterCatalog,A collection of raster datasets defined in a table; each table record defines an individual raster dataset in the catalog.
Raster Catalog Layer,GPRasterCatalogLayer,A reference to a raster catalog, including symbology and rendering properties.
Raster Data Layer,GPRasterDataLayer,A raster data layer.
Raster Dataset,DERasterDataset,A single dataset built from one or more rasters.
Raster Layer,GPRasterLayer,A reference to a raster, including symbology and rendering properties.
Raster Statistics,GPSAGDBEnvStatistics,Specifies if raster statistics will be built.
Raster Type,GPRasterBuilder,Raster data is added to a mosaic dataset by specifying a raster type. The raster type identifies metadata, such as georeferencing, acquisition date, and sensor type, along with a raster format.
Record Set,GPRecordSet,Interactive table; type in the table values when the tool is run.
Relationship Class,DERelationshipClass,The details about the relationship between objects in the geodatabase.
Remap,GPSARemap,A table that defines how raster cell values will be reclassified.
Route Measure Event Properties,GPRouteMeasureEventProperties,Specifies the fields on a table that describe events that are measured by a linear reference route system.
Schematic Dataset,DESchematicDataset,A schematic dataset contains a collection of schematic diagram templates and schematic feature classes that share the same application domain, for example, water or electrical. It can reside in a personal, file, or ArcSDE geodatabase.
Schematic Diagram,DESchematicDiagram,A schematic diagram.
Schematic Folder,DESchematicFolder,A schematic folder.
Schematic Layer,GPSchematicLayer,A schematic layer is a composite layer composed of feature layers based on the schematic feature classes associated with the template on which the schematic diagram is based.
Semivariogram,GPSASemiVariogram,Specifies the distance and direction representing two locations that are used to quantify autocorrelation.
ServerConnection,DEServerConnection,A server connection.
Shapefile,DEShapefile,Spatial data in shapefile format.
Spatial Reference,GPSpatialReference,The coordinate system used to store a spatial dataset, including the spatial domain.
SQL Expression,GPSQLExpression,A syntax for defining and manipulating data from a relational database.
String,GPString,A text value.
Table,DETable,Tabular data.
Table View,GPTableView,A representation of tabular data for viewing and editing purposes, stored in memory or on disk.
Terrain Layer,GPTerrainLayer,A reference to a terrain, including symbology and rendering properties. It's used to draw a terrain.
Text File,DETextfile,Data stored in ASCII format.
Tile Size,GPSAGDBEnvTileSize,Specifies the width and the height of a data stored in block.
Time configuration,GPSATimeConfiguration,Specifies the time periods used for calculating solar radiation at specific locations.
TIN,DETin,A vector data structure that partitions geographic space into contiguous, nonoverlapping triangles. The vertices of each triangle are sample data points with x-, y-, and z-values.
Tin Layer,GPTinLayer,A reference to a TIN, including topological relationships, symbology, and rendering properties.
Tool,DETool,A geoprocessing tool.
Toolbox,DEToolbox,A geoprocessing toolbox.
Topo Features,GPSATopoFeatures,Features that are input to the interpolation.
Topology,DETopology,A topology that defines and enforces data integrity rules for spatial data.
Topology Layer,GPTopologyLayer,A reference to a topology, including symbology and rendering properties.
Value Table,GPValueTable,A collection of columns of values.
Variant,GPVariant,A data value that can contain any basic type: Boolean, date, double, long, and string.
Vertical Factor,GPSAVerticalFactor,Specifies the relationship between the vertical cost factor and the vertical, relative moving angle.
VPF Coverage,DEVPFCoverage,Spatial data stored in Vector Product Format.
VPF Table,DEVPFTable,Attribute data stored in Vector Product Format.
WCS Coverage,DEWCSCoverage,Web Coverage Service (WCS) is an open specification for sharing raster datasets on the web.
Weighted Overlay Table,GPSAWeightedOverlayTable,A table with data to combine multiple rasters by applying a common measurement scale of values to each raster, weighing each according to its importance.
Weighted Sum,GPSAWeightedSum,Specifies data for overlaying several rasters multiplied each by their given weight and then summed.
WMS Map,DEWMSMap,A WMS Map.
Workspace,DEWorkspace,A container such as a geodatabase or folder.
XY Domain,GPXYDomain,A range of lowest and highest possible values for x,y coordinates.
Z Domain,GPZDomain,A range of lowest and highest possible values for z coordinates.
"""


def arc_parameter_datatype_list():
    """ Parse the 'arc_parameter_types_string' into a list

    Returns: A list

    """

    x = arc_parameter_types_string.split("\n")[1:-1]  # remove leading + trailing blanks
    x = [v.split(",", 2) for v in x]  # split the csv into a list
    return [k for n, k, d in x][1:]  # list singly, remove the first (header)


def arc_environment_list():
    """ Wrap arcpy.ListEnvironments() - NOT USEFUL ANY MORE

    Returns: A list of environments

    """
    return ListEnvironments()
