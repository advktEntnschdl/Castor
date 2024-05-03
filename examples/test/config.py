import os

import numpy as np
import PyPDF4
from matplotlib import pyplot as plt


def makeJobPlot(job):
    os.chdir(job.resDir)

    fig, ax = plt.subplots()
    ax.set_xlabel("U")
    ax.set_ylabel("RF")
    ax.grid()
    lines = []

    xData = np.loadtxt("U.csv")[:, 1]
    yData = np.loadtxt("RF.csv")[:, 1]

    lines.extend(ax.plot(xData, yData))

    ax.set_title(job.name)
    fig.savefig(os.path.join(job.resDir, job.name + ".pdf"))


def makeStudyPlot(study):
    os.chdir(study.resDir)

    fig, ax = plt.subplots()
    ax.set_xlabel("U")
    ax.set_ylabel("RF")
    ax.grid()
    ax.set_title(study.name)
    contourList = []
    lines = []

    for job in study.jobList:
        xData = np.loadtxt(os.path.join(job.resDir, "U.csv"))[:, 1]
        yData = np.loadtxt(os.path.join(job.resDir, "RF.csv"))[:, 1]

        lines.extend(ax.plot(xData, yData, label=job.name))
        contourList.append(os.path.join(job.resDir, "contour.png"))

    dummyLegend = ax.legend()
    fig.canvas.draw()
    nCols = int(
        ax.get_tightbbox(fig.canvas.get_renderer()).width
        / dummyLegend.get_frame().get_width()
    )
    dummyLegend.remove

    legend = ax.legend(bbox_to_anchor=(0.5, -0.12), loc="upper center", ncol=nCols)
    fig.savefig("plot.pdf", bbox_extra_artists=(legend,), bbox_inches="tight")


def mergePDFs(study):
    mergedPdf = PyPDF4.PdfFileMerger()

    mergedPdf.append(os.path.join(study.resDir, "plot.pdf"))
    mergedPdf.addBookmark(study.name, len(mergedPdf.pages) - 1)

    for job in study.jobList:
        mergedPdf.append(os.path.join(job.resDir, "{}.pdf".format(job.name)))
        mergedPdf.addBookmark(job.name, len(mergedPdf.pages) - 1)

    mergedPdf.write("{}.pdf".format(study.name))
    os.remove(os.path.join(study.resDir, "plot.pdf"))
    return


studyName = "_test"

inputTemplate = "input.inp"

paramDict = {
    "_A_": [1, 2],
    "_C_": [3, 4],
}

config = {
    "parameterStudies": {
        studyName: {
            "name": studyName,
            "type": "EdelweissFE",
            "simConfig": {
                "executable": "~/projects/EdelweissFE/edelweiss.py",
                "inputFile": inputTemplate,
                "numThreads": 1,
            },
            "resDir": studyName,
            "replaceInstructions": {
                "inp1.inc": {
                    "_A_": [1, 2],
                },
                "inp2.inc": {
                    "_C_": [3, 4],
                },
                # add replace instructions here
            },
            "dependentReplaceInstructions": {
                "_B_": lambda x: x["_A_"] + 10,
                "_D_": lambda x: x["_C_"] + 1000,
            },
            "preProcessingInstructions": {
                # "beforeStudy":
            },
            "postProcessingInstructions": {
                # "afterJob": makeJobPlot,
                # "afterStudy": [makeStudyPlot, mergePDFs],
            },
            "active": True,
        },
    },
}
