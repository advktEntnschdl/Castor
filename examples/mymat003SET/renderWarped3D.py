# flake8: noqa -- this tells flake8 to ignore this file
#!/usr/bin/pvpython

import argparse
import time

from paraview.simple import *

parser = argparse.ArgumentParser(
    description="Render a paraview screenshot and export to file"
)
parser.add_argument(
    "--case=file", help="Ensight case file ", dest="case", required=True, type=str
)
parser.add_argument(
    "--out=file", help="export file name ", dest="out", required=True, type=str
)
parser.add_argument(
    "--colorby",
    help="colorby defintion, e.g.: --colorby POINTS displacement magnitude",
    dest="colorby",
    nargs="+",
    required=True,
    type=str,
)
parser.add_argument(
    "--dpi=value", help="dots per inch", dest="dpi", required=True, type=int
)
parser.add_argument(
    "--width=inch", help="figure width in inch", dest="width", required=True, type=float
)
parser.add_argument(
    "--height=inch",
    help="figure height in inch",
    dest="height",
    required=True,
    type=float,
)
parser.add_argument(
    "--scalefactor=value",
    help="warp by displacement scalefactor",
    dest="scalefactor",
    required=True,
    type=float,
)
args = parser.parse_args()

reader = EnSightReader(CaseFileName=args.case)
reader.UpdatePipeline()

warped = WarpByVector(
    Input=reader, Vectors="displacement", ScaleFactor=args.scalefactor
)

# position camera
view = GetActiveView()
if not view:
    # When using the ParaView UI, the View will be present, not otherwise.
    view = CreateRenderView()
view.UseLight = 0

# change color of edges
# find settings proxy
colorPalette = GetSettingsProxy("ColorPalette")
# Properties modified on colorPalette
colorPalette.Edges = [0.3, 0.3, 0.3]

# change text color
colorPalette.Text = [0.0, 0.0, 0.0]

# set background color
colorPalette.Background = [1.0, 1.0, 1.0]  # white


# nice setting for 3D
# view.CameraViewUp = [0, 0, 1]
# view.CameraFocalPoint = [0, 0, 0]
# view.CameraViewAngle = 45
# view.CameraPosition = [2,-5,2]
import numpy as np

campos = np.array([[1], [0], [0]])
# view rotation angles
θx = np.pi / 180 * 0
θy = np.pi / 180 * -45
θz = np.pi / 180 * 15
# rotation matrices
Rx = np.array([[1, 0, 0], [0, np.cos(θx), -np.sin(θx)], [0, np.sin(θx), np.cos(θx)]])
Ry = np.array([[np.cos(θy), 0, np.sin(θy)], [0, 1, 0], [-np.sin(θy), 0, np.cos(θy)]])
Rz = np.array([[np.cos(θz), -np.sin(θz), 0], [np.sin(θz), np.cos(θz), 0], [0, 0, 1]])

campos = Ry @ (Rz @ (campos))
campos = campos.flatten().tolist()

view.CameraPosition = campos
view.CameraFocalPoint = [0, 0, 0]
view.CameraViewUp = [0, 1, 0]
view.CameraParallelProjection = 1

timesteps = reader.TimestepValues
view.ViewTime = timesteps[-1]

# draw the object
Show()

# set image size
# 200 dpi,
# width = 3.25 inch
# height = 2.00 inch
# dpi = 200
# width_inch = 3.25
# height_inch = 4.00
height = int(args.height * args.dpi)
width = int(args.width * args.dpi)
view.ViewSize = [width, height]  # [width, height]

dp = GetDisplayProperties()

dp.BlockSelectors = ["/Root/all"]

# ColorBy( dp, value = ('POINTS', 'displacement', 'magnitude'))
# print(tuple(args.colorby))
ColorBy(dp, value=args.colorby)

# turn on legend
dp.SetScalarBarVisibility(view, True)

# get color transfer function/color map for 'displacement'
LUT = GetColorTransferFunction(args.colorby[1])
# get color legend/bar for displacementLUT in view renderView1
LUTColorBar = GetScalarBar(LUT, view)
# change scalar bar placement
LUTColorBar.Orientation = "Horizontal"
LUTColorBar.WindowLocation = "Lower Center"
LUTColorBar.ScalarBarLength = 0.4

# find settings proxy
renderViewSettings = GetSettingsProxy("RenderViewSettings")
# disable FXAA for better mesh representation
renderViewSettings.UseFXAA = 0

# hide axes
view.OrientationAxesVisibility = 0

# set point color
# dp.AmbientColor = [1, 1, 1] #red

# set surface color
# dp.DiffuseColor = [1, 1, 1] #blue

# set point size
# dp.PointSize = 2

# set representation
dp.Representation = "Surface With Edges"

Render()

# save screenshot
WriteImage(args.out)
