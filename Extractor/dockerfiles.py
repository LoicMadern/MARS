import glob
from dockerfile_parse import DockerfileParser


def getdockerfiles(service_path):
    docker_files = []
    with open("files_needles/docker_files.txt", "r") as files:
        possibles = files.read().splitlines()
        for possible in possibles:
            fileslist = glob.glob(service_path + "/**/" + possible, recursive=True)
            for f in fileslist:
                docker_files.append(f)
        return docker_files


def parse(dockerfile):
    dfp = DockerfileParser()
    file = open(dockerfile, "r")
    dfp.content = file.read()
    file.close()

    return dfp
