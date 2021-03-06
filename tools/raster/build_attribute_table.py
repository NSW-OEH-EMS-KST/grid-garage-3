from base.base_tool import BaseTool

from base import utils
from base.decorators import input_tableview, input_output_table, parameter
import arcpy


tool_settings = {"label": "Build Attribute Table",
                 "description": "Builds attribute tables for rasters",
                 "can_run_background": "True",
                 "category": "Raster"}


class BuildAttributeTableRasterTool(BaseTool):
    """
    """

    def __init__(self):
        """

        Returns:

        """

        BaseTool.__init__(self, tool_settings)

        self.execution_list = [self.iterate]

        return

    @input_tableview(data_type="raster")
    @parameter("overwrite", "Overwrite existing table", "GPBoolean", "Required", False, "Input", None, None, None, None)
    @input_output_table()
    def getParameterInfo(self):
        """

        Returns:

        """

        return BaseTool.getParameterInfo(self)

    def iterate(self):
        """

        Returns:

        """

        self.overwrite = "Overwrite" if self.overwrite else "NONE"

        self.iterate_function_on_tableview(self.build_rat, return_to_results=True)

        return

    def build_rat(self, data):
        """

        Args:
            data:

        Returns:

        """

        ras = data["raster"]

        utils.validate_geodata(ras, raster=True)

        self.info("Building attribute table for {0}...".format(ras))

        arcpy.BuildRasterAttributeTable_management(ras, self.overwrite)

        return {"raster": ras, "attribute_table": "built"}

# "http://desktop.arcgis.com/en/arcmap/latest/tools/data-management-toolbox/build-raster-attribute-table.htm"
