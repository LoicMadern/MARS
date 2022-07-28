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

            flag_folders= []

            for folder in folders :
                listeFichiers = []

                for (repertoire, sousRepertoires, fichiers) in walk(root+folder):
                    listeFichiers.extend(fichiers)

                number_files = len(listeFichiers)
                dict = {}
                cpt = 0

                for fichier  in listeFichiers:
                    if "." in fichier :
                        extension = fichier.split(".")[1]
                        if extension not in dict :
                            dict[extension] = 1
                        else :
                            dict[extension] += 1

                for key in dict :
                    if key == "js" or key == "x" or key == "vue" or key == "cs" or key == "vss" or key == "html" or key == "png" or key == "json" or key=="xml" or key=="eot" or key=="woff" or key=="woff2" or key=="regular" or key=="min":
                        cpt += dict[key]

                    if key=="config" or key=="gitignore" or key=="sh" or key=="env" or key=="md":
                        number_files-=1

                if cpt>number_files *0.8 :
                    flag_folders.append(folder)

            print(project + "\n")
            print(flag_folders)
            print("\n")







