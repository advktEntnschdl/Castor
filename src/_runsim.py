# ---------------------------------------
# Paul Hofer
# ---------------------------------------
# core functionality
# ---------------------------------------
import os
import shutil
import numpy as np
import time
from datetime import datetime

from utils import *

# ---------------------------------------
# post processing
# ---------------------------------------
import matplotlib
import matplotlib.style
from matplotlib import pyplot as plt
from matplotlib import rcParams

paper = (5.875, 4.125)  # size in inches
# paperA4 = (5.875, 4.125) # size in inches

matplotlib.style.use("seaborn-colorblind")
rcParams["font.family"] = ["monospace"]
rcParams["font.monospace"] = ["FreeMono"]

import PyPDF4

mergedPdf = PyPDF4.PdfFileMerger()
# ---------------------------------------

edelw_templfn = "triaxTemplate.inp"
edelwCmd = "python ~/projects/EdelweissFE/edelweiss.py"
# edelwCmd = "OMP_NUM_THREADS=12 python ~/projects/EdelweissFE/edelweiss.py"
pythonCmd = "/usr/bin/python"

wDir = os.getcwd()
remove = False  # if True subdirectories are removed later


studyName = "_SET"
studyName += "_"
studyName += datetime.now().strftime("%Y%m%dT%H%M")

paramDict = {
    "_PINI_": [10, 20],
    "_GC2G_": [0.1],
}

studyDict = {
    "studyName": studyName,
    "path": "/".join([wDir, studyName]),
    "paramDict": paramDict,
    "jobs": {},
}

studyDict.update({"jobs": {}})
studyDict["jobs"].update(getJobDict(studyDict))

os.mkdir(studyName)

# cp file needed for parameter study to dir
shutil.copyfile(edelw_templfn, "/".join([studyName, edelw_templfn]))
# also archive python script (optional)
scriptFile = os.path.basename(__file__)
shutil.copyfile(scriptFile, "/".join([studyName, "_" + scriptFile]))

os.chdir(studyDict["path"])

fig, ax = plt.subplots()
fig.set_size_inches(paper[0], paper[1])
ax.set_xlabel("U")
ax.set_ylabel("RF")
ax.grid()
lines = []

# contourList = []
# plotList = []
#
fig2, ax2 = plt.subplots()
fig2.set_size_inches(paper[0], paper[1])

for job in studyDict["jobs"].values():

    inpfn = job["name"] + ".inp"
    file_from_template_file(inpfn, edelw_templfn, job["replaceDict"])

    shutil.rmtree(job["subfolder"], ignore_errors=True)
    os.mkdir(job["subfolder"])
    os.rename(inpfn, "/".join([job["subfolder"], inpfn]))
    os.chdir(job["subfolder"])

    cmd = " ".join([edelwCmd, inpfn, "--noplot", "|& tee outStream.txt"])
    os.system(cmd)

    time.sleep(0.5)
    while not any(".csv" in fn for fn in os.listdir()):
        time.sleep(0.1)

    resU = -np.loadtxt("U.csv")[:, 1]
    resRF = -np.loadtxt("RF.csv")[:, 1]

    if len(lines):
        lines[-1].set_alpha(0.0)  # alpha = 0.0 hides the previously drawn line
        lines[-1].set_color("gray")

    lines.extend(ax.plot(resU, resRF))

    ax.set_title(job["paramStr"])
    fig.savefig("plot.pdf")

    ax2.plot(resU, resRF, label=job["paramStr"])

    clrString = "POINTS displacement magnitude"
    # clrString = "CELLS strain \\(partial\\)"
    # clrString = "CELLS e \\(partial\\)"
    cmd = " ".join(
        [
            pythonCmd,
            "~/projects/pvpython/renderWarped3D.py",
            "--case=esExport.case",
            "--dpi=300",
            "--width={}".format(paper[0] / 2),
            "--height={}".format(paper[1]),
            "--scalefactor=1.0",
            "--out=contour.png",
            "--colorby",
            clrString,
        ]
    )
    os.system(cmd)

    time.sleep(0.1)

    cmd = "\n".join(
        [
            "pdfjam --quiet --a5paper --templatesize '{\\paperwidth}{\\paperheight}' --outfile temp.pdf plot.pdf contour.png",
            "pdfjam --quiet --a4paper --landscape --nup 2x1 --outfile "
            + job["name"]
            + ".pdf temp.pdf",
        ]
    )
    os.system(cmd)
    os.remove("temp.pdf")

    cmd = "pdftk {logoFn} stamp {fn}.pdf output temp.pdf".format(
        logoFn="/".join([wDir, "UIBK_A4Landscape.pdf"]), fn=job["name"]
    )
    os.system(cmd)
    os.rename("temp.pdf", job["name"] + ".pdf")

    # plotList.append("/".join([os.getcwd(), "plot.pdf"]))
    # contourList.append("/".join([os.getcwd(), "contour.png"]))

    mergedPdf.append("{}.pdf".format(job["name"]))
    mergedPdf.addBookmark(job["name"], len(mergedPdf.pages) - 1)

    os.chdir(studyDict["path"])

if remove == True:
    for job in studyDict["jobs"].values():
        shutil.rmtree(job["subfolder"], ignore_errors=True)

ax2.set_xlabel("U")
ax2.set_ylabel("RF")
ax2.legend()
ax2.set_title(studyName.lstrip("_"))
ax2.grid()
fig2.savefig("plot.pdf")

mergedPdf.write("{}.pdf".format(studyName))
