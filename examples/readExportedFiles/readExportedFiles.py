import os
import sys

import dill as pickle

baseDir = os.path.join("..", "linearElastic")
outDir = os.path.join(baseDir, "_linearElastic")
expDir = os.path.join(outDir, "export")

if not os.path.exists(outDir):
    raise FileNotFoundError("No output found. Run linearElastic example first!")

print()
print("#")
print("# jobNames.pickle")
print("#")
print()

with open(os.path.join(expDir, "jobNames.pickle"), "rb") as f:
    jobNames = pickle.load(f)

for item in jobNames:
    print(item)

print()
print("#")
print("# jobDicts.pickle")
print("#")
print()

with open(os.path.join(expDir, "jobDicts.pickle"), "rb") as f:
    jobDicts = pickle.load(f)

for item in jobDicts:
    print(item)

# pre/post processing instructions must be reachable for successful import
sys.path.append(baseDir)

print()
print("#")
print("# jobs.pickle")
print("#")
print()

with open(os.path.join(expDir, "jobs.pickle"), "rb") as f:
    jobs = pickle.load(f)

for job in jobs:
    print(job)
    for item in job.__dict__.items():
        print(item)
    print()

print()
print("#")
print("# study.pickle")
print("#")
print()

with open(os.path.join(expDir, "study.pickle"), "rb") as f:
    study = pickle.load(f)

print(study)
for item in study.__dict__.items():
    print(item)
