import itertools
import os
import shutil
import subprocess
import time

from .journal import errorMessage, infoMessage, message
from .utils import toList


class Job:
    def __init__(self, replaceDef, study):
        self.name = getParamStr(replaceDef)
        self.resDir = os.path.join(study.resDir, self.name)
        self.studyShareDir = study.shareDir
        self.shareDir = os.path.join(self.resDir, "share")
        self.castorShareDir = study.castorShareDir
        self.replaceDef = replaceDef
        self.type = study.type
        self.simConfig = study.simConfig
        self.studyResDir = study.resDir

        ppFuns = study.postProcessingInstructions.get("afterJob")
        if ppFuns:
            if type(ppFuns) == list:
                self.ppFunList = ppFuns
            else:
                self.ppFunList = [ppFuns]
        else:
            self.ppFunList = []

        return

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
        message('Job "{}" started'.format(self.name))
        os.mkdir(self.resDir)

        shutil.copytree(self.studyShareDir, self.shareDir)

        self.generateInputFromTemplates()

        os.chdir(self.resDir)

        envVars = dict(os.environ)
        args = []
        if self.type == "EdelweissFE":
            inputFile = os.path.join(
                self.shareDir, os.path.basename(self.simConfig["inputFile"])
            )
            if self.simConfig["numThreads"]:
                envVars.update({"OMP_NUM_THREADS": str(self.simConfig["numThreads"])})
            args = [
                "python",
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

        cmd = " ".join(args)
        with open("stderr.txt", "w+") as fErr, open("stdout.txt", "w+") as fOut:
            subproc = subprocess.Popen(
                cmd, stdout=fOut, stderr=fErr, env=envVars, shell=True
            )
            try:
                while subproc.poll() is None:
                    time.sleep(0.1)
            except KeyboardInterrupt:
                subproc.kill()

        infoMessage(
            'Simulation for job "{}" exited with code {}'.format(
                self.name, subproc.poll()
            )
        )

        if subproc.poll() >= 0:
            self.performPostProcessing()
            message('Job "{}" finished'.format(self.name))
        else:
            errorMessage("Job execution exited with an error:", self.name)
            message(" --> see stderr.txt or stdout.txt for more information")

        os.chdir(self.studyResDir)

        return self


def replaceInFile(filename, replacedict):

    content = ""
    with open(filename, "r") as file:
        content = file.read()
        for param in replacedict:
            content = content.replace(param, str(replacedict[param]))

    with open(filename, "w") as file:
        file.write(content)

    return


def getReplaceDictList(paramDict):
    replaceDictList = []

    params = paramDict.keys()
    groupedVals = list(
        itertools.product(*(toList(paramDict[key]) for key in paramDict))
    )

    for valGroup in groupedVals:
        auxList = [None] * (len(params) * 2)
        auxList[1::2] = [str(item) for item in valGroup]  # type: ignore <- pyright does not like slices of type None lists
        auxList[::2] = [item.replace("_", "") for item in params]  # type: ignore

        replaceDictList.append(dict(zip(params, valGroup)))

    return replaceDictList


def getParamStr(replaceDefsPerJob):
    auxList = []
    for replaceDefPerJob in replaceDefsPerJob:
        for key, value in replaceDefPerJob[1].items():
            auxList.append("_".join([key.replace("_", ""), str(value)]))
    paramStr = "_".join(auxList)

    return paramStr
