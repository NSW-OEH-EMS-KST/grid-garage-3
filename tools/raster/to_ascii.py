from base.base_tool import BaseTool
from base.results import result
from base import utils
from base.method_decorators import input_tableview, input_output_table_with_output_affixes, parameter, raster_formats, pixel_type, raster_formats2
import arcpy


tool_settings = {"label": "To ASCII",
                 "description": "Convert rasters to ASCII format...",
                 "can_run_background": "True",
                 "category": "Raster"}


@result
class ToAsciiRasterTool(BaseTool):

    def __init__(self):

        BaseTool.__init__(self, tool_settings)

        self.execution_list = [self.iterate]

        return

    @input_tableview("raster_table", "Table for Rasters", False, ["raster:geodata:"])
    @input_output_table_with_output_affixes
    def getParameterInfo(self):

        return BaseTool.getParameterInfo(self)

    def iterate(self):

        self.iterate_function_on_tableview(self.copy, "raster_table", ["geodata"], return_to_results=True)

        return

    def copy(self, data):

        ras = data["geodata"]

        utils.validate_geodata(ras, raster=True)
        ras_out = utils.make_raster_name(ras, self.result.output_workspace, "asc", self.output_filename_prefix, self.output_filename_suffix)

        self.info("Converting {0} -->> {1} ...".format(ras, ras_out))
        arcpy.RasterToASCII_conversion(ras, ras_out)

        return {"geodata": ras_out, "source_geodata": ras}

# "http://desktop.arcgis.com/en/arcmap/latest/tools/data-management-toolbox/copy-raster.htm"
# CopyRaster_management (in_raster, out_rasterdataset, {config_keyword}, {background_value}, {nodata_value}, {onebit_to_eightbit}, {colormap_to_RGB}, {pixel_type}, {scale_pixel_value}, {RGB_to_Colormap}, {format}, {transform})