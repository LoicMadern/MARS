import glob
import javalang
import re
import pandas as pd
from os import walk

def getsourcefiles(service_path):
    listeFichiers = []
    for (repertoire, sousRepertoires, fichiers) in walk(service_path):
        listeFichiers.extend(fichiers)
    return listeFichiers


def calls(call_graph_path, microservice): 
    tab = []
    try :
       df = pd.read_csv(call_graph_path, delimiter=',', header=None)
       for value in df.values:
           if value[0].split("/")[0]==microservice and not  [value[0].split("/")[0], value[1].split("/")[0]] in tab:
              tab.append([value[0], value[1]])
    except : 
        pass
    return tab




def getjavasourcefiles(service_path):
    source_files = []
    with open("files_needles/source_files.txt", "r") as files:
        possibles = files.read().splitlines()
        for possible in possibles:
            fileslist = glob.glob(service_path + "/**/" + possible, recursive=True)
            for f in fileslist:
                if "test" not in f.lower():
                    source_files.append(f)
    return source_files


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


def getrootconfigfiles(service_path):
    config_files = []
    with open("files_needles/config_files.txt", "r") as files:
        possibles = files.read().splitlines()
        for possible in possibles:
            fileslist = glob.glob(service_path + "/" + possible, recursive=True)
            for f in fileslist:
                if "test" not in f.lower():
                    config_files.append(f)
        return config_files


def getenvfiles(service_path):
    env_files = []
    with open("files_needles/env_files.txt", "r") as files:
        possibles = files.read().splitlines()
        for possible in possibles:
            fileslist = glob.glob(service_path + "/**/" + possible, recursive=True)
            for f in fileslist:
                if "test" not in f.lower():
                   env_files.append(f)
        return env_files

def parse(source_file):
    file = open(source_file, "r")
    content = file.read()
    tree = javalang.parse.parse(content)
    file.close()
    return tree


def getmethods(tree):
    method = []
    for path, node in tree.filter(javalang.tree.MethodDeclaration):
        method.append(node.name)
    return method


def getannotations(tree):
    annotations = []
    for path, node in tree.filter(javalang.tree.Annotation):
        annotations.append(node.name)
    return annotations


def getimports(tree):
    imports = []
    for path, node in tree.filter(javalang.tree.Import):
        imports.append(node.path)
    return imports


def gethttpdb(source):
    file = open(source, "r")
    content = file.read()
    file.close()
    urls = []
    db_statements = []

    ###################
    # HTTP Detection  #
    ###################

    excluded_tlds = [line.strip() for line in open('tools/tlds.txt')]
    httpregex = r"((https?):((//)|(\\\\))+([\w\d:#@%/;$()~_?\+-=\\\.&](#!)?)*)"

    matches = re.findall(httpregex, content)
    if matches is not None:
        for match in matches:
            if any(ele in match[0] for ele in excluded_tlds) is False:
                if len(match[0]) > 8:
                    urls.append(match[0])
    return urls


def getdatasourceurls(source):
    ds_urls = []
    with open(source, "r") as f:
        content = f.read().splitlines()
        for line in content:
            if "mysql://" in line:
                line = line.replace('"', " ").replace("'", " ").replace(",", " ")
                ds_urls.append(line.split("mysql://")[1].split()[0])
    return list(set(ds_urls))

def getcreatedbstatements(source):
    cdb_statements = []
    with open(source, "r") as f:
        content = f.read().splitlines()
        for line in content:
            if "create database if not exists" in line.lower():
                line = line.replace(";", " ")
                print(line)
                cdb_statements.append(line.lower().split("exists")[1].split()[0])
            elif "create database" in line.lower():
                line = line.replace(";", " ")
                print(line)
                cdb_statements.append(line.lower().split("create database")[1].split()[0])
    return list(set(cdb_statements))
