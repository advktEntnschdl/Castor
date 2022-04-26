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


class Study:
    def __init__(self, studyDict):
        self.checkFields(studyDict)
        self.checkValues(studyDict)

        self.name = studyDict.get("name")
        self.resDir = os.path.abspath(studyDict.get("resDir"))
        self.inpDir = os.path.join(self.resDir, "input")
        head = os.path.split(inspect.stack()[1].filename)[0]
        self.shareDir = os.path.join(os.path.abspath(head), "share")

        self.type = studyDict.get("type")
        self.simConfig = studyDict["simConfig"]

        self.replaceInstructions = studyDict.get("replaceInstructions")
        self.dependentReplaceInstructions = studyDict.get(
            "dependentReplaceInstructions"
        )

        self.preProcessingInstructions = studyDict["preProcessingInstructions"]
        prepFuns = self.preProcessingInstructions.get("beforeStudy")

        if prepFuns:
            if type(prepFuns) == list:
                self.prepFunList = prepFuns
            else:
                self.prepFunList = [prepFuns]
        else:
            self.prepFunList = []

        self.postProcessingInstructions = studyDict["postProcessingInstructions"]
        ppFuns = self.postProcessingInstructions.get("afterStudy")

        if ppFuns:
            if type(ppFuns) == list:
                self.ppFunList = ppFuns
            else:
                self.ppFunList = [ppFuns]
        else:
            self.ppFunList = []

        self.active = studyDict.get("active") if studyDict.get("active") else True

        self.generateJobListFromConfig()

        return

    def checkFields(self, studyDict):
        raiseError = False

        neccessaryFields = [
            "name",
            "type",
            "resDir",
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
            if not os.path.exists(key):
                errorMessage("File {} not found.".format(key))
                raiseError = True
            if not val or not type(val) == dict:
                errorMessage(
                    "Replace instruction must be a dictionary with at least one key value pair: <parameter>: <value or valueList>."
                )
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

        os.mkdir(self.resDir)
        self.export()

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

        self.performPreProcessing()

        del (
            self.dependentReplaceInstructions
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
            templateFile = os.path.basename(templateFile)
            replaceDefsPerFile.append(
                [
                    (os.path.join(self.inpDir, templateFile), replaceDict)
                    for replaceDict in getReplaceDictList(paramDict)
                ]
            )
        replaceDefsPerJob = list(itertools.product(*replaceDefsPerFile))

        for replaceDef in replaceDefsPerJob:
            for file, replaceDict in replaceDef:
                if self.dependentReplaceInstructions:
                    for (
                        key,
                        getValueFromReplaceDict,
                    ) in self.dependentReplaceInstructions.items():
                        try:
                            dependentValue = getValueFromReplaceDict(replaceDict)
                            replaceDict.update({key: dependentValue})
                        except:
                            pass

        return replaceDefsPerJob

    def export(self):
        exportName = "jobNames.pickle"
        jobNames = [job.name for job in self.jobList]

        with open(os.path.join(self.resDir, exportName), "wb") as fout:
            pickle.dump(jobNames, fout)

        return
