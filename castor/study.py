import inspect
import itertools
import operator
import os
import shutil
import time
from concurrent.futures import ProcessPoolExecutor
from difflib import get_close_matches

import dill as pickle

from .job import Job, getParamDict, getParamStr, getReplaceDictList
from .journal import errorMessage, infoMessage, message, printStatus
from .utils import listFiles, toList


class Study:
    def __init__(self, studyDict, args):
        self.checkFields(studyDict)

        self.name = studyDict["name"]
        self.resDir = os.path.abspath(studyDict["resDir"])

        head = os.path.split(inspect.stack()[1].filename)[0]
        self.castorShareDir = os.path.join(os.path.abspath(head), "share")

        self.type = studyDict["type"]
        self.simConfig = studyDict["simConfig"]

        self.replaceInstructions = studyDict["replaceInstructions"]
        self.reuseReplaceInstructions = studyDict.get("reuseReplaceInstructions")

        self.providedFiles = toList(studyDict["providedFiles"])
        self.shareDir = os.path.join(self.resDir, "share")
        self.expDir = os.path.join(self.resDir, "export")

        self.preProcessingInstructions = studyDict["preProcessingInstructions"]
        prepFuns = self.preProcessingInstructions.get("beforeStudy")

        if prepFuns:
            self.prepFunList = toList(prepFuns)
        else:
            self.prepFunList = []

        self.postProcessingInstructions = studyDict["postProcessingInstructions"]
        ppFuns = self.postProcessingInstructions.get("afterStudy")

        if ppFuns:
            self.ppFunList = toList(ppFuns)
        else:
            self.ppFunList = []

        self.active = studyDict.get("active") if studyDict.get("active") else True

        self.checkValues(studyDict)

        if os.path.exists(self.resDir):
            if args.overwrite:
                message("Overwriting directory {}".format(self.resDir))
                shutil.rmtree(self.resDir)
            else:
                raise FileExistsError(
                    "Directory {} exists. Use --overwrite keyword if you want to overwrite it.".format(
                        self.resDir
                    )
                )

        os.makedirs(self.resDir)
        os.makedirs(self.shareDir)
        os.makedirs(self.expDir)

        self.getProvidedFiles()

        self.generateJobListFromConfig()

        printStatus(self)

        self.export()

        return

    def checkFields(self, studyDict):
        raiseError = False

        neccessaryFields = [
            "name",
            "type",
            "resDir",
            "providedFiles",
            "replaceInstructions",
            "preProcessingInstructions",
            "postProcessingInstructions",
        ]

        for field in neccessaryFields:
            if field not in studyDict:
                errorMessage(
                    'Field "{}" of config dictionary must be set.'.format(field)
                )
                matchingKeys = get_close_matches(field, studyDict.keys(), cutoff=0.6)
                if matchingKeys:
                    infoMessage(
                        'You specified "{}". Did you mean "{}"?'.format(
                            matchingKeys[0], field
                        )
                    )
                raiseError = True

        if raiseError:
            raise ValueError

        return

    def checkValues(self, studyDict):
        raiseError = False

        possibleTypes = ["EdelweissFE", "mpFEM", "Abaqus"]
        if studyDict["type"] not in possibleTypes:
            errorMessage(
                'Type "{}" not a valid study type. Valid study types: {}'.format(
                    studyDict["type"],
                    ", ".join(map(lambda x: '"{}"'.format(x), possibleTypes)),
                )
            )
            raiseError = True

        if not studyDict["replaceInstructions"] or not isinstance(
            studyDict["replaceInstructions"], dict
        ):
            errorMessage(
                'Value of "replaceInstructions" must be a dictionary with at least one key value pair: <fileName>: <parameterDictionary>.'
            )
            raiseError = True

        if not studyDict["providedFiles"]:
            errorMessage("No Files provided for study.")
            raiseError = True

        providedFilesList = []
        for file in toList(studyDict["providedFiles"]):
            file = os.path.expanduser(file)
            if os.path.isdir(file):
                fileList = listFiles(file)
                (head, tail) = os.path.split(file)
                fileList = [os.path.relpath(file, start=head) for file in fileList]
                providedFilesList.extend(fileList)
            else:
                providedFilesList.append(os.path.basename(file))
            if not os.path.exists(file):
                fileType = {True: "directory", False: "file"}[os.path.isdir(file)]
                infoMessage(file)
                errorMessage("Provided {} {} not found.".format(fileType, file))
                raise FileNotFoundError

        for file in studyDict["replaceInstructions"]:
            if file not in providedFilesList:
                infoMessage("Template files must be provided to the study.")
                errorMessage("File {} needs to be provided.".format(file))
                raise FileNotFoundError

        for key, val in studyDict["replaceInstructions"].items():
            if os.path.isabs(key):
                infoMessage("Path to template files must be relative to share/.")
                errorMessage("Path {} is not a relative path.".format(key))
                raiseError = True

            if not val or not isinstance(val, dict):
                errorMessage(
                    "Replace instruction must be a dictionary with at least one key value pair: <parameter>: <value or valueList>."
                )
                raiseError = True

        if studyDict["type"] == "EdelweissFE":
            inputFile = studyDict["simConfig"]["inputFile"]

            if inputFile not in providedFilesList:
                errorMessage(
                    "EdelweissFE input file {} needs to be provided.".format(inputFile)
                )
                raise FileNotFoundError
            if not os.path.relpath(inputFile):
                infoMessage(
                    "Path to EdelweissFE input file must be relative to share/."
                )
                errorMessage("Path to EdelweissFE input file is not a relative path.")
                raiseError = True

        if raiseError:
            raise ValueError

    def run(self, args):

        os.chdir(self.resDir)

        self.performPreProcessing()

        del (
            self.replaceInstructions
        )  # magic happens here; without deleting the (dependent) replace instructions, parallel job execution does not behave as expected; the replace instructions are not needed after generating the jobList

        runJob = operator.methodcaller("run")
        if args.parallelJobs[0] > 1:
            with ProcessPoolExecutor(max_workers=args.parallelJobs[0]) as executor:
                futures = list(
                    map(lambda job: executor.submit(runJob, job), self.jobList)
                )

                lastChange = 0.0
                latestChange = 0.0
                while not all([future.done() for future in futures]):
                    for job in self.jobList:
                        latestChange = max(latestChange, os.path.getmtime(job.staFile))
                    if latestChange > lastChange:
                        lastChange = latestChange
                        printStatus(self)
                    time.sleep(0.1)
                else:
                    printStatus(self)

        else:
            for result in map(runJob, self.jobList):

                printStatus(self)
                pass

        self.performPostProcessing()

        return

    def getProvidedFiles(self):
        for file in self.providedFiles:
            file = os.path.expanduser(file)
            file = file.rstrip("/")
            if not os.path.exists(file):
                errorMessage('File "{}" not found'.format(file))
                raise FileNotFoundError
            if os.path.isdir(file):
                infoMessage("Providing folder {}".format(file))
                shutil.copytree(
                    file, os.path.join(self.shareDir, os.path.basename(file))
                )
            else:
                infoMessage("Providing file {}".format(file))
                shutil.copy(file, os.path.join(self.shareDir, os.path.basename(file)))

        return

    def performPreProcessing(self):
        for ppFun in self.prepFunList:
            os.chdir(self.resDir)
            ppFun(self)

    def performPostProcessing(self):
        for ppFun in self.ppFunList:
            os.chdir(self.resDir)
            ppFun(self)

        return

    def generateJobListFromConfig(self):
        replaceDefsPerJob, jobNames, paramDicts = self.getReplaceDefsPerJob()
        # breakpoint()

        jobList = []
        jId = 0
        for replaceDef, jobName, paramDict in zip(
            replaceDefsPerJob, jobNames, paramDicts
        ):
            jobList.append(Job(self, jobName, paramDict, jId, replaceDef))
            jId += 1
        self.jobList = jobList

        if not len(jobList) > 0:
            raise IOError("Job list is empty. Check input!")

        return

    def getReplaceDefsPerJob(self):
        replaceDefsPerFile = []
        for templateFile, paramDict in self.replaceInstructions.items():
            if "independent" in paramDict:
                independentParamDict = paramDict["independent"]
            else:
                independentParamDict = paramDict
            replaceDefsPerFile.append(
                [
                    (templateFile, replaceDict)
                    for replaceDict in getReplaceDictList(
                        independentParamDict, self.expDir
                    )
                ]
            )

        replaceDefsPerJob = list(itertools.product(*replaceDefsPerFile))
        jobNames = [getParamStr(replaceDef) for replaceDef in replaceDefsPerJob]
        jobDicts = [getParamDict(replaceDef) for replaceDef in replaceDefsPerJob]

        for replaceDef in replaceDefsPerJob:
            for templateFile, replaceDict in replaceDef:
                dependentReplaceInstructions = self.replaceInstructions[
                    templateFile
                ].get("dependent")
                if dependentReplaceInstructions:
                    for (
                        key,
                        getValueFromReplaceDict,
                    ) in dependentReplaceInstructions.items():
                        try:
                            dependentValue = getValueFromReplaceDict(replaceDict)
                            replaceDict.update({key: dependentValue})
                        finally:
                            pass

        # not the yellow from the egg
        if self.reuseReplaceInstructions:
            newReplaceDefsPerJob = []
            for reusewhat, reusefor in self.reuseReplaceInstructions.items():
                for replaceDefs in replaceDefsPerJob:
                    replaceDefs = list(replaceDefs)
                    for replaceDef in replaceDefs:
                        if replaceDef[0] == reusewhat:
                            replaceDefs.append((reusefor, replaceDef[1]))
                    newReplaceDefsPerJob.append(replaceDefs)
            replaceDefsPerJob = tuple(newReplaceDefsPerJob)

        return replaceDefsPerJob, jobNames, jobDicts

    def export(self):
        exportName = "jobNames.pickle"
        jobNames = [job.name for job in self.jobList]
        with open(os.path.join(self.expDir, exportName), "wb") as fout:
            pickle.dump(jobNames, fout)

        exportName = "jobs.pickle"
        with open(os.path.join(self.expDir, exportName), "wb") as fout:
            pickle.dump(self.jobList, fout)

        exportName = "jobDicts.pickle"
        jobDicts = [
            dict(
                name=job.name,
                parameters=job.paramDict,
                resultDir=os.path.relpath(job.resDir, os.path.dirname(self.resDir)),
            )
            for job in self.jobList
        ]
        with open(os.path.join(self.expDir, exportName), "wb") as fout:
            pickle.dump(jobDicts, fout)

        exportName = "study.pickle"
        with open(os.path.join(self.expDir, exportName), "wb") as fout:
            pickle.dump(self, fout)

        return
