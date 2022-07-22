import argparse
import os
import json
import dependencies
import microservices
import javaparser
import dockerfiles
import shutil

parser = argparse.ArgumentParser()
parser.add_argument("--project", type=str, required=True)

args = parser.parse_args()

mbsroot = "../../projects/"+ args.project
metamodel_file = mbsroot + "/metamodel.json"

if os.path.exists(metamodel_file):
    os.remove(metamodel_file)
    
shutil.copy("../blank_metamodel.json", metamodel_file)


print("Thank you, excluding folders from analysis...")
with open("../../projects/" +  args.project +"/exclude.txt", "r") as excl:
    excluded = excl.readlines()
    excluded = [line.rstrip() for line in excluded]

folders = [f.name for f in os.scandir(mbsroot) if f.is_dir()]

print("Folders excluded, building meta-model...")
print("Excluded folders : ")
print("\n".join(excluded))

mm_file = open(metamodel_file, "r")
mm = json.load(mm_file)
mm_file.close()

mm["gitRepository"] = args.project
mm["system"]["folders"] = folders

##################################
# Extracting system dependencies #
##################################

print("Extracting system wide dependencies")
system_deps = dependencies.extract(mbsroot)
print("Dependencies extracted, writing to meta-model")

mm["system"]["dependencies"] = system_deps
mm_file = open(metamodel_file, "w")
json.dump(mm, mm_file)
mm_file.close()
print("Writing done")

####################################
# Extracting root config files     #
####################################
print("Extracting root configuration files")
system_config = javaparser.getrootconfigfiles(mbsroot)
print("")
mm["system"]["config_files"] = system_config
mm_file = open(metamodel_file, "w")
json.dump(mm, mm_file)
mm_file.close()
print("Writing done")

########################################
# Extracting root hardcoded endpoints  #
########################################

mm["system"]["http"] = []
for f in mm["system"]["config_files"]:
    print("Extracting http for " + f)
    http_root = javaparser.gethttpdb(f)
    mm["system"]["http"] += http_root
mm_file = open(metamodel_file, "w")
json.dump(mm, mm_file)
mm_file.close()
print("Writing done")
##################################
# Extracting microservices       #
##################################

print("Extracting microservices")
system_ms = microservices.extract(mbsroot)
ms_node = []
print("microservices extracted, reading information")
for microservice in system_ms:
    ms_data = {}
    service_path = mbsroot + "/" + microservice
    cloc_out = microservices.getlocs(service_path)
    ms_data["name"] = microservice
    ms_data["language"] = microservices.getlang(service_path)
    ms_data["nb_files"] = cloc_out[0]  # The first returned value
    ms_data["locs"] = cloc_out[3]  # The third returned value
    ms_data["dependencies"] = dependencies.extract(service_path)
    ms_data["code"] = dict()
    ms_data["code"]["imports"] = []
    ms_data["code"]["annotations"] = []
    ms_data["code"]["methods"] = []
    ms_data["code"]["http"] = []
    ms_data["code"]["databases"] = dict()
    ms_data["code"]["databases"]["datasources"] = []
    ms_data["code"]["databases"]["create"] = []
    ms_data["code"]["source_files"] = javaparser.getsourcefiles(service_path)
    ms_data["config"] = dict()
    ms_data["config"]["config_files"] = javaparser.getconfigfiles(service_path)
    ms_data["deployment"] = dict()
    ms_data["deployment"]["docker_files"] = dockerfiles.getdockerfiles(service_path)
    ms_data["deployment"]["images"] = []
    ms_data["env"] = dict()
    ms_data["env"]["env_files"] = javaparser.getenvfiles(service_path)
    # For every source file in this microservice
    for source in ms_data["code"]["source_files"]:
        # Build his AST tree
        tree = javaparser.parse(source)
        ms_data["code"]["annotations"] += javaparser.getannotations(tree)
        ms_data["code"]["methods"] += javaparser.getmethods(tree)
        ms_data["code"]["imports"] += javaparser.getimports(tree)

        # Removing potential duplicates
        ms_data["code"]["annotations"] = list(dict.fromkeys(ms_data["code"]["annotations"]))
        ms_data["code"]["methods"] = list(dict.fromkeys(ms_data["code"]["methods"]))
        ms_data["code"]["imports"] = list(dict.fromkeys(ms_data["code"]["imports"]))

    httpdb_related = ms_data["code"]["source_files"] + ms_data["config"]["config_files"] + ms_data["env"]["env_files"]
    for f in httpdb_related:
        http = javaparser.gethttpdb(f)
        ms_data["code"]["http"] += http
        dbsources = javaparser.getdatasourceurls(f)
        dbcreate = javaparser.getcreatedbstatements(f)
        ms_data["code"]["databases"]["datasources"] += dbsources
        ms_data["code"]["databases"]["create"] += dbcreate


    for dockerfile in ms_data["deployment"]["docker_files"]:
        parsed_dockerfile = dockerfiles.parse(dockerfile)
        ms_data["deployment"]["images"].append(parsed_dockerfile.baseimage)

    ms_node.append(ms_data)


print("Writing microservices info into meta-model")

mm_file = open(metamodel_file, "r")
mm = json.load(mm_file)
mm_file.close()

mm["system"]["microservices"] = ms_node

mm_file = open(metamodel_file, "w")
json.dump(mm, mm_file)
mm_file.close()
print("Writing done")
