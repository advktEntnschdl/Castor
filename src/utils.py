import os


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
