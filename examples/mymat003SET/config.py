import subprocess
import time
from datetime import datetime
import os
import numpy as np
from datetime import datetime

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

pythonCmd = "/usr/bin/python"

studyName = "_SET"
studyName += "_"
studyName += datetime.now().strftime("%Y%m%dT%H%M")

templateFile = "triaxTemplate.inp"

paramDict = {
    "_PINI_": [10, 20, 30],
    "_GC2G_": [0.1],
}


def generatePdfPage(job):
    print("Nice Job " + job.name + "!")
    fig, ax = plt.subplots()
    fig.set_size_inches(paper[0], paper[1])
    ax.set_xlabel("U")
    ax.set_ylabel("RF")
    ax.grid()
    lines = []

    cwd = os.getcwd()
    os.chdir(job.resDir)

    resU = -np.loadtxt("U.csv")[:, 1]
    resRF = -np.loadtxt("RF.csv")[:, 1]

    if len(lines):
        lines[-1].set_alpha(0.0)  # alpha = 0.0 hides the previously drawn line
        lines[-1].set_color("gray")

    lines.extend(ax.plot(resU, resRF))

    ax.set_title(job.name)
    fig.savefig("plot.pdf")

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

    args = [
        "pdfjam",
        "--quiet",
        "--a5paper",
        "--templatesize",
        "'{\\paperwidth}{\\paperheight}'",
        "--outfile",
        "temp.pdf",
        "plot.pdf",
        "contour.png",
    ]
    # os.system(" ".join(args))
    # subprocess.run(args)
    subprocess.run(" ".join(args), shell=True)

    args = [
        "pdfjam",
        "--quiet",
        "--a4paper",
        "--landscape",
        "--nup",
        "2x1",
        "--outfile",
        "{}.pdf".format(job.name),
        "temp.pdf",
    ]
    # os.system(" ".join(args))
    # subprocess.run(args)
    subprocess.run(" ".join(args), shell=True)
    os.remove("temp.pdf")

    args = [
        "pdftk",
        os.path.join(job.study.shareDir, "UIBK_A4Landscape.pdf"),
        "stamp",
        "{}.pdf".format(job.name),
        "output",
        "temp.pdf",
    ]
    # os.system(" ".join(args))
    # subprocess.run(args)
    subprocess.run(" ".join(args), shell=True)
    os.rename("temp.pdf", job.name + ".pdf")

    os.chdir(cwd)

    return


config = {
    "parameterStudies": {
        studyName: {
            "name": studyName,
            "type": "EdelweissFE",
            "edelweissConfig": {
                "executable": "/home/paul/projects/EdelweissFE/edelweiss.py",
                "inputFile": "triaxTemplate.inp",
                "numThreads": 1,
            },
            "resDir": studyName,
            "replaceInstructions": {
                "triaxTemplate.inp": paramDict,
                # add replace instructions here
            },
            "postProcessingInstructions": {
                "afterJob": generatePdfPage,
                "afterStudy": None,
            },
            "active": True,
        },
    },
}
