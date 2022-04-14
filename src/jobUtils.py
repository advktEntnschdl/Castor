import itertools
import operator
import os
import time
import subprocess
import shutil
from concurrent.futures import ProcessPoolExecutor, as_completed
import inspect

from .journal import message


class Study:
    def __init__(self, studyDict):
        self.checkInput(studyDict)

        self.name = studyDict.get("name")
        self.resDir = os.path.abspath(studyDict.get("resDir"))
        self.inpDir = os.path.join(self.resDir, "input")
        head = os.path.split(inspect.stack()[1].filename)[0]
        self.shareDir = os.path.join(os.path.abspath(head), "share")

        self.type = studyDict.get("type")
        self.simConfig = studyDict["simConfig"]

        self.replaceInstructions = studyDict.get("replaceInstructions")

        self.ppInstructions = studyDict["postProcessingInstructions"]
        ppFuns = self.ppInstructions.get("afterStudy")
        if ppFuns:
            if type(ppFuns) == list:
                self.ppFunList = ppFuns
            else:
                self.ppFunList = [ppFuns]
        else:
            self.ppFunList = []

        self.active = studyDict.get("active") == True

        self.generateJobListFromConfig()

        return

    def checkInput(self, studyDict):
        possibleTypes = ["EdelweissFE", "mpFEM"]

        if studyDict["type"] not in possibleTypes:
            raise ValueError(
                "Type '{}' not a valid study type. Valid study types: {}".format(
                    self.type, ", ".join(map(lambda x: "'{}'".format(x), possibleTypes))
                ),
            )

        return

    def run(self, args):
        os.mkdir(self.resDir)

        if self.type == "EdelweissFE":

            os.mkdir(self.inpDir)
            for templateFile in self.replaceInstructions:
                shutil.copy(
                    templateFile,
                    os.path.join(self.inpDir, os.path.basename(templateFile)),
                )

            inputFile = self.simConfig["inputFile"]
            if not os.path.basename(inputFile) in map(
                os.path.basename, self.replaceInstructions.keys()
            ):
                shutil.copy(
                    inputFile, os.path.join(self.inpDir, os.path.basename(inputFile))
                )

        elif self.type == "mpFEM":
            inputFolder = self.simConfig["input"]
            shutil.copytree(inputFolder, self.inpDir)

        os.chdir(self.resDir)

        runJob = operator.methodcaller("run")
        if args.parallel:
            nJobs = len(self.jobList)
            with ProcessPoolExecutor(max_workers=nJobs) as executor:
                futures = list(
                    map(lambda job: executor.submit(runJob, job), self.jobList)
                )

                for future in as_completed(futures):
                    pass
        else:
            for result in map(runJob, self.jobList):
                pass

        self.performPostProcessing()

        return

    def performPostProcessing(self):
        for ppFun in self.ppFunList:
            ppFun(self)

        return

    def generateJobListFromConfig(self):
        replaceDefsPerJob = self.getReplaceDefsPerJob()

        jobList = []
        for replaceDef in replaceDefsPerJob:
            jobList.append(Job(replaceDef, self))
        self.jobList = jobList

        return

    def getReplaceDefsPerJob(self):
        replaceDefsPerFile = []
        for templateFile, paramDict in self.replaceInstructions.items():
            templateFile = os.path.basename(templateFile)
            replaceDefsPerFile.append(
                [
                    (os.path.join(self.inpDir, templateFile), replaceDict)
                    for replaceDict in getReplaceDictList(paramDict)
                ]
            )
        replaceDefsPerJob = list(itertools.product(*replaceDefsPerFile))

        return replaceDefsPerJob


class Job:
    def __init__(self, replaceDef, study):
        self.name = getParamStr(replaceDef)
        self.resDir = os.path.join(study.resDir, self.name)
        self.inpDir = os.path.join(self.resDir, "input")
        self.replaceDef = replaceDef
        self.type = study.type
        self.study = study

        ppFuns = study.ppInstructions.get("afterJob")
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
            ppFun(self)

        return

    def generateInputFromTemplates(self):

        shutil.copytree(self.study.inpDir, self.inpDir)
        for file, replaceDict in self.replaceDef:
            filePath = os.path.join(self.inpDir, os.path.basename(file))
            replaceInFile(filePath, replaceDict)
        return

    def run(self):
        message(" Job started: " + self.name)
        os.mkdir(self.resDir)
        self.generateInputFromTemplates()

        os.chdir(self.resDir)

        envVars = dict(os.environ)
        args = []
        if self.type == "EdelweissFE":
            inputFile = os.path.join(
                self.inpDir, os.path.basename(self.study.simConfig["inputFile"])
            )
            if self.study.simConfig["numThreads"]:
                envVars.update(
                    {"OMP_NUM_THREADS": str(self.study.simConfig["numThreads"])}
                )
            args = [
                "python",
                self.study.simConfig["executable"],
                inputFile,
                "--noplot",
            ]

        elif self.type == "mpFEM":

            os.mkdir(self.study.simConfig["output"])

            args = [
                self.study.simConfig["executable"],
                "--allow_nan",
                "-i=" + self.inpDir,
                "-f=files",
                "-r=" + self.study.simConfig["output"],
                "-o=result",
            ]

        cmd = " ".join(args)
        with open("outStream.txt", "w+") as f:
            subproc = subprocess.Popen(cmd, stdout=f, stderr=f, env=envVars, shell=True)

            while subproc.poll() == None:
                time.sleep(0.1)

        if subproc.poll() == 0:
            self.performPostProcessing()
        else:
            message(" Job execution exited with an error: " + self.name)

        message(" Job finished: " + self.name)
        os.chdir(self.study.resDir)

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
    groupedVals = list(itertools.product(*(paramDict[key] for key in paramDict)))

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
