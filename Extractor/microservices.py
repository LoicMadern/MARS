import glob
import os
import re

def extract(root):
    microservices = []
    print(root)
    rootpath = root.split("Source")[0]
    exclude_file = open(rootpath + "/exclude.txt", 'r')
    excluded_services = exclude_file.read().split()
    all_services = glob.glob(root + "/*/")
    for service in all_services:
        ms_name = service.split("/")[-2]
        if ms_name not in excluded_services:
            microservices.append(ms_name)

    return microservices


def getlang(service):
    enry = os.popen("./enry " + service)
    toplang = enry.read()
    if toplang:
        return toplang.split("%")[1].split()[0].lower().strip()
    else:
        return "unknown"


def getlocs(service):
    cloc = os.popen("cloc " + service)
    output = cloc.read()
    values = [1, 1, 1, 1]
    if "-----" in output:
        lines = output.splitlines()
        for line in lines:
            if line.lower().startswith("java"):
                values = re.findall('\d+', line)
    return values
