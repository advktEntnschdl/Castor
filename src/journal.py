from rich import print


def printHeader():
    printSepline()
    print("|{:^70s}|".format("CASTOR"))
    print("|{:^70s}|".format(""))
    print("|{:^70s}|".format("-- MaterialModelingToolbox --"))
    print("|{:^70s}|".format("github.com/MAteRialMOdelingToolbox"))
    print("|{:^70s}|".format(""))
    printSepline()


def errorMessage(*args, **kwargs):

    message(args, style="bold red", **kwargs)


def message(*args, **kwargs):

    string = args[0]
    for arg in args[1:]:
        string = " ".join((string, arg))

    print("|{:<70s}|".format(string), **kwargs)


def printSepline():
    message(70 * "=")


def printLine():
    message(70 * "-")
