# -*- coding: utf-8 -*-
import arcpy
import datetime
from arcpy.sa import *

class Toolbox(object):
    def __init__(self):
        self.label = "Rock Segmentation Toolbox"
        self.alias = "RockSeg"
        self.tools = [RockWatershedTool]

class RockWatershedTool(object):
    def __init__(self):
        self.label = "Grow Rock Polygons"
        self.description = "Hybrid Fusion logic using seeds to define basins."
        self.canRunInBackground = False

    def getParameterInfo(self):
        param0 = arcpy.Parameter(name="in_seeds", displayName="Input Rock Seeds",
                                 datatype="GPFeatureLayer", parameterType="Required", direction="Input")
        param1 = arcpy.Parameter(name="in_lrm", displayName="Input Optimized LRM",
                                 datatype="GPRasterLayer", parameterType="Required", direction="Input")
        param2 = arcpy.Parameter(name="fill_depth", displayName="Fill Depth",
                                 datatype="GPDouble", parameterType="Required", direction="Input")
        param2.value = 0.15 
        param3 = arcpy.Parameter(name="out_polygons", displayName="Output Rock Polygons",
                                 datatype="DEFeatureClass", parameterType="Required", direction="Output")
        param3.value = "Rock_Watersheds_V"
        return [param0, param1, param2, param3]

    def execute(self, parameters, messages):
        def log(msg):
            arcpy.AddMessage(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}")

        seeds = parameters[0].valueAsText
        lrm = Raster(parameters[1].valueAsText)
        fill_val = float(parameters[2].value)
        out_fc = parameters[3].valueAsText

        arcpy.env.overwriteOutput = True
        arcpy.CheckOutExtension("spatial")

        try:
            log("Step 1: Generating Seed-Based Influence...")
            # Anchor the watershed to specific seed points
            temp_seed_ras = "memory\\seed_ras"
            arcpy.conversion.FeatureToRaster(seeds, "OBJECTID", temp_seed_ras, lrm)
            seed_dist = EucDistance(temp_seed_ras)
            
            log("Step 2: Hybrid Surface Fusion (Inverted Logic)...")
            # Following V6/V7 logic: (inverted_height * multiplier) + constraint
            # This makes rock peaks the 'bottom' of the basin
            inverted = (lrm * -1) 
            
            # Multiply height by 100 to make the rock shapes 'dominant'
            # Add seed_dist so that the 'bowl' gets deeper as you get closer to a seed
            hybrid_surface = (inverted * 100) + (seed_dist * 5)
            
            log("Step 3: Hydrological Slicing...")
            # Critical Fill/Flow/Watershed chain from early model
            filled = Fill(hybrid_surface, fill_val)
            fdir = FlowDirection(filled, "NORMAL")
            
            # Watershed using seeds as the pour points ensures 1-to-1 mapping
            w_raster = Watershed(fdir, temp_seed_ras)
            
            log("Step 4: Applying KWL Height Mask & Vectorizing...")
            # Uses the Con(height > 0.03) logic from V6/V7 scripts to kill ground noise
            masked_w = Con(lrm > 0.30, w_raster)
            
            arcpy.conversion.RasterToPolygon(masked_w, out_fc, "NO_SIMPLIFY")
            
            log(f"SUCCESS: Rock polygons generated using KWL Hybrid logic.")

        except Exception as e:
            arcpy.AddError(f"Error: {str(e)}")
        finally:
            arcpy.CheckInExtension("spatial")
