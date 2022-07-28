import pandas as pd

with open("../projects/name_projects.txt", "r") as file:
    projects = file.readlines()
    projects = [line.rstrip() for line in projects]

    for project in projects:
        root = "../projects/" + project + "/"
        df = pd.read_csv(root + "calls.csv", delimiter=',', header=None)
        tab = []
        final_tab = []
        for value in df.values :
            if [value[0].split("/")[0],value[1].split("/")[0]] not in tab and value[0].split("/")[0]!=value[1].split("/")[0]:
                tab.append([value[0].split("/")[0],value[1].split("/")[0]])
        for element in tab :
            if [element[1] , element[0]] in tab and not  [element[1] , element[0]] in final_tab or  [element[0] , element[1]] in final_tab:
                final_tab.append(element)
        print(project)
        print(final_tab)

