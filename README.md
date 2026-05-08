# LiDAR Riprap Segmentation Suite

A professional Python Toolbox (PYT) for identifying and classifying rock gradation from high-resolution LiDAR data.

### The Innovation
Instead of standard segmentation, this tool uses a **"Seed and Grow"** approach:
1. **Topological Seeding:** Identifies rock peaks to prevent polygon "shattering."
2. **Hydrological Slicing:** Inverts terrain logic to treat individual rocks as watersheds for precise boundary delineation.

### Key Scripts
* `Seed_Point_Generator.pyt`: Captures missed rocks using topological peak identification.
* `Rock_Segmentation_Toolbox.pyt`: Executes Hybrid Fusion logic to vectorize rock bodies.
