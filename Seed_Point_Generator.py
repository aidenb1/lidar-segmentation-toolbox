# -*- coding: utf-8 -*-
"""
Tool: Rock Seed Refiner (Topological Centroid Edition)
Author: Aiden Black (BCIT / KWL Practicum)
"""

import arcpy
import datetime
from arcpy.sa import *

class Toolbox(object):
    def __init__(self):
        self.label = "Diagnostic Tools"
        self.alias = "Diag_Tools"
        self.tools = [RockSeedRefinerTool]

class RockSeedRefinerTool(object):
    def __init__(self):
        self.label = "Seed Point Generator"
        self.description = "Captures missed rocks by using topological peaks instead of a fixed radius."
        self.canRunInBackground = False

    def getParameterInfo(self):
        param0 = arcpy.Parameter(name="in_raster", displayName="Input Optimized LRM",
                                 datatype="GPRasterLayer", parameterType="Required", direction="Input")
        
        # Reduced default radius to find smaller rocks 
        param1 = arcpy.Parameter(name="sensitivity_radius", displayName="Small Rock Sensitivity (Cells)",
                                 datatype="GPLong", parameterType="Required", direction="Input")
        param1.value = 5 

        param2 = arcpy.Parameter(name="height_thresh", displayName="Min Rock Height (m)",
                                 datatype="GPDouble", parameterType="Required", direction="Input")
        param2.value = 0.30 # Change to capture lowest desired rock heights

        param3 = arcpy.Parameter(name="out_seeds", displayName="Output Refined Seeds",
                                 datatype="DEFeatureClass", parameterType="Required", direction="Output")
        param3.value = "Rock_Seeds"
        
        return [param0, param1, param2, param3]

    def execute(self, parameters, messages):
        def log(msg):
            arcpy.AddMessage(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}")

        in_r = Raster(parameters[0].valueAsText)
        sens = int(parameters[1].value)
        thresh = float(parameters[2].value)
        out_fc = parameters[3].valueAsText
        
        arcpy.env.overwriteOutput = True
        arcpy.CheckOutExtension("spatial")

        try:
            log("Step 1: Identifying Topological Peaks...")
            # Use a smaller focal max to catch smaller rocks
            focal_max = FocalStatistics(in_r, NbrCircle(sens, "CELL"), "MAXIMUM")
            
            # Identify potential peak pixels
            peaks_raw = Con((in_r == focal_max) & (in_r > thresh), 1)
            
            log("Step 2: Grouping Plateau Pixels...")
            # This links adjacent 'peak' pixels into a single Island
            peak_islands = RegionGroup(peaks_raw, "EIGHT", "WITHIN")
            
            log("Step 3: Calculating Geometric Centroids...")
            # One point per rock
            temp_islands_shp = "memory\\islands"
            arcpy.conversion.RasterToPolygon(peak_islands, temp_islands_shp, "NO_SIMPLIFY")
            
            # Create a single point at the true center of each rock dome
            arcpy.management.FeatureToPoint(temp_islands_shp, out_fc, "INSIDE")
            
            final_count = arcpy.management.GetCount(out_fc)
            log(f"SUCCESS: Captured {final_count} rocks. Centroids locked.")

        except Exception as e:
            arcpy.AddError(f"Error: {str(e)}")
        finally:
            arcpy.CheckInExtension("spatial")
