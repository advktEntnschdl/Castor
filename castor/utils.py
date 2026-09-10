import os
import shutil


def toList(arg):
    if isinstance(arg, list):
        return arg
    else:
        return [arg]


# make a list of files in a directory including files in sub directories
# https://thispointer.com/python-how-to-get-list-of-files-in-directory-and-sub-directories/
def listFiles(dirName):
    # create a list of file and sub directories
    # names in the given directory
    listOfFile = os.listdir(dirName)
    allFiles = list()
    # Iterate over all the entries
    for entry in listOfFile:
        # Create full path
        fullPath = os.path.join(dirName, entry)
        # If entry is a directory then get the list of files in this directory
        if os.path.isdir(fullPath):
            allFiles = allFiles + listFiles(fullPath)
        else:
            allFiles.append(fullPath)

    return allFiles


# provide a file as a copy or as a symlink pointing to the source
def provideFile(src, dst, link=False, relative=False):
    if not link:
        shutil.copy2(src, dst)
        return

    if relative:
        target = os.path.relpath(src, start=os.path.dirname(dst))
    else:
        target = os.path.abspath(src)

    os.symlink(target, dst)

    return


# recreate the directory tree of src at dst; dirs are always real dirs, files
# are linked if link (a bool or a predicate on the path relative to src) says
# so, except for copyFiles (relative to src), which are always copied
def provideTree(src, dst, link=False, relative=False, copyFiles=None):
    linkFile = link if callable(link) else lambda file: bool(link)
    copyFiles = [os.path.normpath(file) for file in toList(copyFiles or [])]

    os.makedirs(dst, exist_ok=True)

    for root, dirs, files in os.walk(src, followlinks=True):
        relRoot = os.path.relpath(root, start=src)
        for dirName in dirs:
            os.makedirs(os.path.join(dst, relRoot, dirName), exist_ok=True)
        for fileName in files:
            srcFile = os.path.join(root, fileName)
            relFile = os.path.normpath(os.path.join(relRoot, fileName))
            provideFile(
                srcFile,
                os.path.join(dst, relFile),
                link=linkFile(relFile) and relFile not in copyFiles,
                relative=relative,
            )

    return
