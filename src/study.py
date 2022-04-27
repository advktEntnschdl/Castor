import inspect
import itertools
import operator
import os
import pickle
import shutil
from concurrent.futures import ProcessPoolExecutor, as_completed
from difflib import get_close_matches

from .job import Job, getReplaceDictList
from .journal import errorMessage, infoMessage, message
from .utils import toList


class Study:
    def __init__(self, studyDict):
        self.checkFields(studyDict)

        self.name = studyDict["name"]
        self.resDir = os.path.abspath(studyDict["resDir"])
        # self.inpDir = os.path.join(self.resDir, "input")

        head = os.path.split(inspect.stack()[1].filename)[0]
        self.CastorShareDir = os.path.join(os.path.abspath(head), "share")

        self.type = studyDict["type"]
        self.simConfig = studyDict["simConfig"]

        self.replaceInstructions = studyDict["replaceInstructions"]

        self.providedFiles = toList(studyDict["providedFiles"])
        self.shareDir = os.path.join(self.resDir, "share")

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

        possibleTypes = ["EdelweissFE", "mpFEM"]
        if studyDict["type"] not in possibleTypes:
            errorMessage(
                'Type "{}" not a valid study type. Valid study types: {}'.format(
                    studyDict["type"],
                    ", ".join(map(lambda x: '"{}"'.format(x), possibleTypes)),
                )
            )
            raiseError = True

        if (
            not studyDict["replaceInstructions"]
            or not type(studyDict["replaceInstructions"]) == dict
        ):
            errorMessage(
                'Value of "replaceInstructions" must be a dictionary with at least one key value pair: <fileName>: <parameterDictionary>.'
            )
            raiseError = True

        for key, val in studyDict["replaceInstructions"].items():
            if os.path.isabs(key):
                infoMessage(
                    "Path to template files must be relative to <study.resDir>/share/."
                )
                infoMessage("Template files must be provided to the study.")
                errorMessage("Path {} is not a relative path.".format(key))
                raiseError = True
            if not os.path.exists(key):
                errorMessage("File {} not found.".format(key))
                raise FileNotFoundError
            if not val or not type(val) == dict:
                errorMessage(
                    "Replace instruction must be a dictionary with at least one key value pair: <parameter>: <value or valueList>."
                )
                raiseError = True

        if not studyDict["providedFiles"]:
            errorMessage("No Files provided for study.")
            raiseError = True

        if raiseError:
            raise ValueError

    def run(self, args):
        if os.path.exists(self.resDir):
            if args.overwrite:
                message("Overwriting directory {}".format(self.resDir))
                shutil.rmtree(self.resDir)
            else:
                message(
                    "Directory {} exists. Use --overwrite keyword if you want to overwrite it.".format(
                        self.resDir
                    )
                )

        self.generateJobListFromConfig()

        os.mkdir(self.resDir)

        os.mkdir(self.shareDir)
        self.getProvidedFiles()

        self.export()

        if self.type == "EdelweissFE":
            inputFile = self.simConfig["inputFile"]
            if not os.path.exists(inputFile):
                errorMessage(
                    'Input file "{}" not found'.format(os.path.abspath(inputFile))
                )
                raise FileNotFoundError
            # toDo: check if inputFile is in provided files (or dirs)

        elif self.type == "mpFEM":
            # inputFolder = self.simConfig["input"]
            # shutil.copytree(inputFolder, self.inpDir)
            pass

        os.chdir(self.resDir)

        self.performPreProcessing()

        del (
            self.replaceInstructions
        )  # magic happens here; without deleting the parallel job execution does not behave as expected; the dependentReplaceInstructions are not needed after generating the jobList

        runJob = operator.methodcaller("run")
        if args.parallelJobs[0] > 1:
            with ProcessPoolExecutor(max_workers=args.parallelJobs[0]) as executor:
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

    def getProvidedFiles(self):
        for file in self.providedFiles:
            if not os.path.exists(file):
                errorMessage('File "{}" not found'.format(file))
                raise FileNotFoundError
            if os.path.isdir(file):
                infoMessage("Copy folder {}".format(file))
                shutil.copytree(
                    file, os.path.join(self.shareDir, os.path.relpath(file))
                )
            else:
                shutil.copy(file, os.path.join(self.shareDir, os.path.relpath(file)))

        return

    def performPreProcessing(self):
        for ppFun in self.prepFunList:
            ppFun(self)

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
            if "independent" in paramDict:
                independentParamDict = paramDict["independent"]
            else:
                independentParamDict = paramDict
            replaceDefsPerFile.append(
                [
                    (templateFile, replaceDict)
                    for replaceDict in getReplaceDictList(independentParamDict)
                ]
            )

        replaceDefsPerJob = list(itertools.product(*replaceDefsPerFile))

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

        return replaceDefsPerJob

    def export(self):
        exportName = "jobNames.pickle"
        jobNames = [job.name for job in self.jobList]

        with open(os.path.join(self.resDir, exportName), "wb") as fout:
            pickle.dump(jobNames, fout)

        return
