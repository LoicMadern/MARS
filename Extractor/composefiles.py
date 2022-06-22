import glob


def getcomposefiles(service_path):
    compose_files = []
    with open("files_needles/docker_compose.txt", "r") as files:
        possibles = files.read().splitlines()
        for possible in possibles:
            fileslist = glob.glob(service_path + "/**/" + possible, recursive=True)
            for f in fileslist:
                compose_files.append(f)
        return compose_files
