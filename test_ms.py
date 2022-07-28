import os.path

from os.path import isfile, join
from os import walk

if __name__ == '__main__':
    with open("../projects/name_projects.txt", "r") as file:
        projects = file.readlines()
        projects = [line.rstrip() for line in projects]

        for project  in projects :
            root = "../projects/" + project +"/"
            folders =[]
            with open(root + "exclude.txt", "r") as doc:
                excludes = doc.readlines()
                excludes = [line.rstrip() for line in excludes]
                for f in os.listdir(root):
                    if len(f.split("."))==0 or f not in excludes and f not in folders:
                        folders.append(f)









