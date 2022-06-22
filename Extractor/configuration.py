import glob


def getconfigfiles(service_path):
    config_files = []
    with open("files_needles/config_files.txt", "r") as files:
        possibles = files.read().splitlines()
        for possible in possibles:
            fileslist = glob.glob(service_path + "/**/" + possible, recursive=True)
            for f in fileslist:
                if "test" not in f.lower():
                    config_files.append(f)
        return config_files
