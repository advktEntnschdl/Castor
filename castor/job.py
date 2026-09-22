import itertools
import os
import subprocess
import time
from datetime import datetime

import numpy as np

from .utils import provideTree, toList


class Job:
    def __init__(self, study, name, paramDict, jId, replaceDef):
        self.name = name
        self.paramDict = paramDict
        self.id = jId

        self.resDir = os.path.join(study.resDir, self.name)
        self.studyShareDir = study.shareDir
        self.shareDir = os.path.join(self.resDir, "share")
        self.castorShareDir = study.castorShareDir
        self.expDir = study.expDir

        self.replaceDef = replaceDef
        self.templateFiles = study.templateFiles

        self.type = study.type
        self.simConfig = study.simConfig
        self.studyResDir = study.resDir
        self.staFile = os.path.join(self.resDir, self.name + ".cstrsta")

        ppFuns = study.postProcessingInstructions.get("afterJob")
        if ppFuns:
            if isinstance(ppFuns, list):
                self.ppFunList = ppFuns
            else:
                self.ppFunList = [ppFuns]
        else:
            self.ppFunList = []

        # set by a serial study to redraw the status monitor on every change
        self.onStatusChange = None

        os.mkdir(self.resDir)
        # link what the study marked for linking, copy the rest
        provideTree(
            self.studyShareDir,
            self.shareDir,
            link=study.linkToJob,
            relative=True,
            copyFiles=self.templateFiles,
        )
        self.generateInputFromTemplates()
        self.updateStatus("pending")

        return

    def updateStatus(self, status):
        self.status = status
        timeStr = datetime.now().strftime("%Y-%m-%d %H:%M")
        with open(self.staFile, "a") as f:
            f.write(timeStr + "\n")
            f.write(self.status + "\n")

        if self.onStatusChange:
            self.onStatusChange()

    def performPostProcessing(self):
        for ppFun in self.ppFunList:
            os.chdir(self.resDir)
            ppFun(self)
        return

    def generateInputFromTemplates(self):
        for file, replaceDict in self.replaceDef:
            filePath = os.path.join(self.shareDir, file)
            replaceInFile(filePath, replaceDict)
        return

    def run(self):
        os.chdir(self.resDir)
        self.updateStatus("running")
        # message('Job "{}" started'.format(self.name))

        envVars = dict(os.environ)
        args = []
        if self.type == "EdelweissFE":
            inputFile = os.path.join(
                self.shareDir, os.path.basename(self.simConfig["inputFile"])
            )
            if self.simConfig["numThreads"]:
                envVars.update({"OMP_NUM_THREADS": str(self.simConfig["numThreads"])})
            args = [
                self.simConfig["executable"],
                inputFile,
                "--noplot",
            ]

        elif self.type == "mpFEM":

            os.mkdir(self.simConfig["output"])

            args = [
                self.simConfig["executable"],
                "--allow_nan",
                "-i=" + os.path.join(self.shareDir, self.simConfig["input"]),
                "-f=files",
                "-r=" + self.simConfig["output"],
                "-o=result",
            ]

        elif self.type == "bash":
            inputFile = os.path.join(
                self.shareDir, os.path.basename(self.simConfig["inputFile"])
            )
            args = [
                self.simConfig["command"],
                inputFile,
            ]

        cmd = " ".join(args)
        interrupted = False
        with open("stderr.txt", "w+") as fErr, open("stdout.txt", "w+") as fOut:
            subproc = subprocess.Popen(
                cmd, stdout=fOut, stderr=fErr, env=envVars, shell=True
            )
            try:
                while subproc.poll() is None:
                    # self.updateStatus("running")
                    time.sleep(0.1)
            except KeyboardInterrupt:
                interrupted = True
                self.updateStatus("job terminated by user")
                subproc.kill()

        # only report the exit code; whether a run succeeded is up to the user
        if not interrupted:
            self.updateStatus("job exited with code {}".format(subproc.wait()))
            self.performPostProcessing()

        os.chdir(self.studyResDir)

        return self


def replaceInFile(filename, replacedict):

    content = ""
    with open(filename, "r") as file:
        content = file.read()
        for param in replacedict:
            content = content.replace(param, str(replacedict[param]))

    # never write through a link; this would modify the provided file
    if os.path.islink(filename):
        os.remove(filename)

    with open(filename, "w") as file:
        file.write(content)

    return


def generateGroupedVals(paramDict):
    return list(itertools.product(*(toList(paramDict[key]) for key in paramDict)))


def getReplaceDictList(paramDict_, expDir=""):
    paramDict = paramDict_.copy()

    additionalParamDict = {}
    for param, vals in paramDict.items():
        valList = toList(vals)
        sequenceInVals = [
            isinstance(item, (list, tuple, np.ndarray)) for item in valList
        ]
        scalarInVals = [np.isscalar(item) for item in valList]

        if not any(sequenceInVals):
            # default case
            pass

        elif any(scalarInVals) and len(valList) == 2:
            # one scalar and one sequence in valList
            idxSequence = np.argmax(sequenceInVals)
            idxScalar = 1 - idxSequence

            additionalParamDict[param] = valList[idxSequence]
            paramDict[param] = valList[idxScalar]

        else:
            Exception("Error in specified replace instructions. Check your input!")

    groupedVals = generateGroupedVals(paramDict)
    params = paramDict.keys()
    replaceDictList = [dict(zip(params, valGroup)) for valGroup in groupedVals]

    if additionalParamDict:
        with open(os.path.join(expDir, "INITIAL_Jobs.txt"), "a+") as f:
            for replaceDict in replaceDictList:
                f.write(getParamStr([[[], replaceDict]]) + "\n")

        for key, val in additionalParamDict.items():
            tempDict = paramDict.copy()
            tempDict[key] = val
            additionalGroupedVals = generateGroupedVals(tempDict)
            additionalReplaceDicts = [
                dict(zip(params, valGroup)) for valGroup in additionalGroupedVals
            ]

            with open(
                os.path.join(expDir, "{}_Jobs.txt".format(key.replace("_", ""))), "a+"
            ) as f:
                for replaceDict in additionalReplaceDicts:
                    f.write(getParamStr([[[], replaceDict]]) + "\n")

            replaceDictList.extend(additionalReplaceDicts)

    return replaceDictList


def getParamStr(replaceDefsPerJob):
    auxList = []
    for replaceDefPerJob in replaceDefsPerJob:
        for key, value in replaceDefPerJob[1].items():
            auxList.append("_".join([key.replace("_", ""), str(value)]))
    paramStr = "_".join(auxList)

    return paramStr


def getParamDict(replaceDefsPerJob):
    paramDict = {}
    for file, definition in replaceDefsPerJob:
        paramDict.update(definition)

    return paramDict
