import json
import argparse
import math
import pandas as pd
import networkx as nx


class Detector(object):

    # Constants to act as defaults

    # Nano Service
    # Rule : (LOC < (threshold * SysAvgLocs) and NbFiles < (threshold * SysAvgNbFiles))
    NANO_SERVICE_LOC_THRESHOLD = 0.25   # If LOCs < Threshold, it's likely a nano service  -- 50% -- Service has 0.5 times lower LOCS
    NANO_SERVICE_FILES_THRESHOLD = 0.25 # If NbFiles < Threshold, it's likely a nano service -- 50% -- Service has 0.5 times lower LOCS


    # Mega Service
    # Rule : (LOC > (threshold * SysAvgLocs) and NbFiles > (threshold * SysAvgNbFiles))
    MEGA_SERVICE_LOC_THRESHOLD = 2.5  # If LOCs > Threshold, it's likely a mega service -- 150% -- Service has 1.5 times higher LOCS
    MEGA_SERVICE_FILES_THRESHOLD = 2 # If NbFiles > Threshold, it's likely a mega service -- 150% -- Service has 1.5 times higher FILES


    # Global needed vars
    vars = dict()


    # Storing info about antipatterns detected
    _hasNano = dict()
    _hasMega = dict()
    _hasWrongCuts = dict()
    _hasCircularDeps = dict()
    _hasSharedLibs = dict()
    _hasHardcodedEndpoints = dict()
    _hasManualConfig = dict()
    _hasNoCiCd = dict()
    _hasNoApiGateway = dict()
    _hasTimeouts = dict()
    _hasMultipleInstancesPerHost = dict()
    _hasSharedPersistence = dict()
    _hasNoApiVersioning = dict()
    _hasNoHealthCheck = dict()
    _hasLocalLogging = dict()
    _hasInsufficientMonitoring = dict()



    def __init__(self, metamodel:dict) -> None:
        self._metamodel = metamodel
        self.buildVars()
    

    def buildVars(self):
        self.vars["nbServices"] = self.vars.setdefault("nbServices", 0) + len(self._metamodel["system"]["microservices"])
        self.vars["totalLocs"] = self.vars.setdefault("totalLocs", 0)
        self.vars["totalFiles"] = self.vars.setdefault("totalFiles", 0)

        for service in self._metamodel["system"]["microservices"]:
            self.vars["totalLocs"] = self.vars["totalLocs"] + int(service["locs"])
            self.vars["totalFiles"] = self.vars["totalFiles"] + int(service["nb_files"])

        self.vars["avgLocs"] = self.vars.setdefault("avgLocs", 0) + (self.vars["totalLocs"] / self.vars["nbServices"])
        self.vars["avgFiles"] = self.vars.setdefault("avgFiles", 0) + (self.vars["totalFiles"] / self.vars["nbServices"])

        self.vars["hasCiCdFolders"] = self.vars.setdefault("hasCiCdFolders", False)
        
        with open("../tools/cicd_folders.txt") as cicd:
            cifolders = cicd.readlines()
            cifolders = [line.rstrip() for line in cifolders]

            for ci in cifolders:
                if ci in self._metamodel["system"]["folders"]:
                    self.vars["hasCiCdFolders"] = True
                    break

    # Rule: (MSa-lng in Programming) AND (MSb-lng NOT IN Programming) AND MSa imports MSb
    def hasWrongCuts(self):
        names = [s["name"] for s in self._metamodel["system"]["microservices"]]
        for service in self._metamodel["system"]["microservices"]:
            self._hasWrongCuts[service["name"]] = []
            for name in names:
                for imp in service["code"]["imports"]:
                    if name in imp and name != service["name"]:
                        with open("../tools/languages.txt") as prog:
                            languages = prog.readlines()
                            languages = [l.rsplit() for l in languages]

                            if service["language"] in languages and service[name]["language"] not in languages:
                                self._hasWrongCuts[service].append({
                                    "from": service["name"],
                                    "to": name
                                })


    # Rule: Msa imports MSb AND MSb imports MSa
    def hasCircularDependencies(self):
        df = pd.read_csv("../../projects/" + args.project_name + "/final-Graph.csv", delimiter=';', header=None)
        edges = [tuple(x) for x in df.values]
        graph = nx.DiGraph(edges)

        cycles = []
        for cycle in nx.simple_cycles(graph):
            if (len(cycle) > 1):
                cycles.append(cycle)

        self._hasCircularDeps = cycles





    # Rule : (LOC > (threshold * SysAvgLocs) and NbFiles > (threshold * SysAvgNbFiles))
    def hasMegaService(self):

        for service in self._metamodel["system"]["microservices"]:
            requiredLocs = math.floor(self.MEGA_SERVICE_LOC_THRESHOLD * self.vars["avgLocs"])
            requiredFiles = math.floor(self.MEGA_SERVICE_FILES_THRESHOLD * self.vars["avgFiles"])
            requiredLocs = self.vars["totalLocs"]/2

            hasMoreLocsThanAvg = int(service["locs"]) > requiredLocs
            hasMoreFilesThanAvg = int(service["nb_files"]) > requiredFiles

            if(hasMoreLocsThanAvg and hasMoreFilesThanAvg):
                self._hasMega[service["name"]] = {
                    "locs": service["locs"],
                    "nbFiles": service["nb_files"],
                    "requiredLocs": requiredLocs,
                    "requiredFiles": requiredFiles
                }

    # Rule : (LOC < (threshold * SysAvgLocs) and NbFiles < (threshold * SysAvgNbFiles))
    def hasNanoService(self):
        with open("../tools/name_ban_for_nano_services.txt", "r") as confTools:
            tools = confTools.readlines()
            tools = [line.rstrip() for line in tools]
            for service in self._metamodel["system"]["microservices"]:
                red_flag_service_name = False
                requiredLocs = math.floor(self.NANO_SERVICE_LOC_THRESHOLD * self.vars["avgLocs"])
                requiredFiles = math.floor(self.NANO_SERVICE_FILES_THRESHOLD * self.vars["avgFiles"])

                hasLessLocsThanAvg = int(service["locs"]) < requiredLocs
                hasLessFilesThanAvg = int(service["nb_files"]) < requiredFiles


                for tool_name in tools :
                    if tool_name in service["name"] :
                        red_flag_service_name = True


                if(hasLessLocsThanAvg and hasLessFilesThanAvg and not red_flag_service_name):
                    self._hasNano[service["name"]] = {
                        "locs": service["locs"],
                        "nbFiles": service["nb_files"],
                        "requiredLocs": requiredLocs,
                        "requiredFiles": requiredFiles
                    }

    # Rule: Microservices groups using the same dependencie
    def hasSharedDependencies(self):
        dict = {}
        final_dict ={}

        with open("../tools/not_shared_dependencies.txt", "r") as confTools:
            tools = confTools.readlines()
            tools = [line.rstrip() for line in tools]

            for i in range(len(self._metamodel["system"]["microservices"])):
                flag_in_tool = False
                name = self._metamodel["system"]["microservices"][i]["name"]
                deps = self._metamodel["system"]["microservices"][i]["dependencies"]


                for j in range(len(deps)) :
                    for tool in tools :
                        if tool in deps[j] :
                            flag_in_tool =True
                    if not flag_in_tool :
                        if deps[j] not in dict :
                            dict[deps[j]] = name
                        elif name not in deps[j]:
                            dict[deps[j]]+= "\n" + name

            for key in dict   :
                if len(dict[key].split("\n")) > 1 :
                    final_dict[key] = dict[key]


            self._hasSharedLibs = final_dict

    # Rule : intersect(Service discovery, dependencies) = 0 AND (count(URLs, source code) > 1 OR count(URLs, config files) > 1)
    def hasHardcodedEndpoints(self):
        with open("../tools/service_discovery.txt", "r") as sdTools:
            tools = sdTools.readlines()
            tools = [line.rstrip() for line in tools]
            res = []
            sysres = []
            
            # Microservice level
            for service in self._metamodel["system"]["microservices"]:
                for dependency in service["dependencies"]:                
                    for tool in tools:
                        if (tool in dependency):
                            res.append(tool)
            
                if (len(service["code"]["http"]) > 0):
                    self._hasHardcodedEndpoints[service["name"]] = {
                        "hasServiceDiscoveryTool": len(res) != 0,
                        "FoundUrls": ", ".join(service["code"]["http"])
                    }
            
            # System level
            for dependency in self._metamodel["system"]["dependencies"]:
                for tool in tools:
                    if (tool in dependency):
                        sysres.append(tool)
            
                if (len(self._metamodel["system"]["http"]) > 0):
                    self._hasHardcodedEndpoints["system"] = {
                        "hasServiceDiscoveryTool": len(sysres) != 0,
                        "FoundUrls": ", ".join(self._metamodel["system"]["http"])
                    }

    # Rule : intersect(Config management, dependencies) = 0 AND count(configuration files, service) > 0
    def hasManualConfiguration(self):
        with open("../tools/configuration.txt", "r") as confTools:
            tools = confTools.readlines()
            tools = [line.rstrip() for line in tools]
            res = []
            sysres = []

            # Microservice level
            for service in self._metamodel["system"]["microservices"]:
                for dependency in service["dependencies"]:
                    for tool in tools:
                        if (tool in dependency):
                            res.append(tool)

                if (len(service["config"]["config_files"]) > 0):
                    self._hasManualConfig[service["name"]] = {
                        "hasConfigurationTool": len(res) != 0,
                        "FoundConfigFiles": ", ".join(service["config"]["config_files"])
                    }

            # System level
            for dependency in self._metamodel["system"]["dependencies"]:
                for tool in tools:
                    if (tool in dependency):
                        sysres.append(tool)

                if (len(self._metamodel["system"]["config_files"]) > 0):
                    self._hasManualConfig["system"] = {
                        "hasConfigurationTool": len(sysres) != 0,
                        "FoundConfigFiles": ", ".join(self._metamodel["system"]["config_files"])
                    }

    # Rule : intersect(CI tools, dependencies) = 0 AND intersect(CI folders, system) = 0
    def hasCiCd(self):
        with open("../tools/cicd.txt", "r") as sdTools:
            tools = sdTools.readlines()
            tools = [line.rstrip() for line in tools]
            res = []

            # Microservice level
            for service in self._metamodel["system"]["microservices"]:
                for dependency in service["dependencies"]:
                    for tool in tools:
                        if (tool in dependency):
                            res.append(tool)

                if (len(res) == 0):
                    self._hasNoCiCd[service["name"]] = {
                        "hasCiCdTools": False
                    }


        # Rule : intersect(API Gateways, dependencies) = 0

    def hasApiGateway(self):
        with open("../tools/gateway.txt", "r") as sdTools:
            tools = sdTools.readlines()
            tools = [line.rstrip() for line in tools]
            res = []
            sysres = []

            # Microservice level
            for service in self._metamodel["system"]["microservices"]:
                for dependency in service["dependencies"]:
                    for tool in tools:
                        if (tool in dependency):
                            res.append(tool)

                if (len(res) == 0):
                    self._hasNoApiGateway[service["name"]] = {
                        "hasApiGatewayTool": False
                    }

            # System level
            for dependency in self._metamodel["system"]["dependencies"]:
                for tool in tools:
                    if (tool in dependency):
                        sysres.append(tool)

                if (len(sysres) == 0):
                    self._hasNoApiGateway["system"] = {
                        "hasApiGatewayTool": False
                    }


    # Rule(intersect(Circuit breakers, dependencies) = 0
    # AND intersect(Fallbacks, methods) = 0) OR (count(timeouts, imports) > 1 OR count(timeouts, methods) > 1)
    def hasTimeouts(self):
        with open("../tools/circuit_breaker.txt", "r") as sdTools:
            tools = sdTools.readlines()
            tools = [line.rstrip() for line in tools]
            res = []
            sysres = []

            # Microservice level
            for service in self._metamodel["system"]["microservices"]:
                hasTOImports = False
                hasTOMethods = False
                hasFBMethods = False
                for dependency in service["dependencies"]:
                    for tool in tools:
                        if (tool in dependency):
                            res.append(tool)
                for imp in service["code"]["imports"]:
                    if "timeout" in imp.lower():
                        hasTOImports = True
                        break

                for meth in service["code"]["methods"]:
                    if "timeout" in meth.lower():
                        hasTOMethods = True
                    if "fallback" in meth.lower():
                        hasFBMethods = True

                    if hasTOMethods or hasFBMethods:
                        break

                if ((len(res) == 0 and hasFBMethods) or (hasTOImports or hasTOMethods)):
                    self._hasTimeouts[service["name"]] = {
                        "hasCircuitBreakerTool": False,
                        "hasTOMethods": hasTOMethods,
                        "hasTOImports": hasTOImports,
                        "hasFBMethods": hasFBMethods
                    }

            # System level
            for dependency in self._metamodel["system"]["dependencies"]:
                for tool in tools:
                    if (tool in dependency):
                        sysres.append(tool)

                self._hasTimeouts["system"] = {
                    "hasCircuitBreaker": len(sysres) != 0
                }




    # Rule : intersect(docker-compose.yml, system) = 0 AND intesect(DOCKERFILE, microservices) = 0
    def hasMultipleServicesPerHost(self):
        systemHasCompose = False
        for file in self._metamodel["system"]["config_files"]:
            if "docker-compose.yml" in file:
                systemHasCompose = True

            # Microservice level
            for service in self._metamodel["system"]["microservices"]:
                if len(service["deployment"]["docker_files"]) == 0:

                    self._hasMultipleInstancesPerHost[service["name"]] = {
                        "hasDockerFile": False
                    }
            
            self._hasMultipleInstancesPerHost["system"] = {
                "systemHasCompose": systemHasCompose
            }
        self._hasMultipleInstancesPerHost["system"] = {
            "systemHasCompose": systemHasCompose
        }









    def hasSharedPersistence(self):
        dict = {}
        final_dict = {}

        for i in range(len(self._metamodel["system"]["microservices"])):
            name = self._metamodel["system"]["microservices"][i]["name"]
            dbs = self._metamodel["system"]["microservices"][i]["code"]["databases"]["datasources"]

            for i in range(len(dbs)) :
                if dbs[i] not in dict :
                    dict[dbs[i]] = (name)
                else :
                    dict[dbs[i]]+= "\n" + name

        for key in dict   :
            if len(dict[key].split("\n")) > 1 :
                final_dict[key] = dict[key]


        self._hasSharedPersistence = final_dict

        # Rule : count("apiVersion", config) < 1
    def hasNoApiVersioning(self):
        sysres = False
        for service in self._metamodel["system"]["microservices"]:
            for conf_file in service["config"]["config_files"]:
                with open(conf_file) as conf:
                    if "apiVersion" not in conf.read():
                        self._hasNoApiVersioning[service["name"]] = {
                            "hasApiVersioning": False
                        }

        for conf_file in self._metamodel["system"]["config_files"]:
            with open(conf_file) as conf:
                if "apiVersion" in conf.read():
                    sysres = True
                    break

        self._hasNoApiVersioning["system"] = {
            "hasApiVersioning": sysres
        }

    # intersect(healthcheck libs, system) = 0 OR (count(healthcheck, annotations) < 1 OR count(healthcheck, imports) < 1)
    def hasHealthCheck(self):
        with open("../tools/healthcheck.txt", "r") as sdTools:
            tools = sdTools.readlines()
            tools = [line.rstrip() for line in tools]
            res = []
            sysres = []

            # Microservice level
            for service in self._metamodel["system"]["microservices"]:
                hasHealthImports = False
                hasHealthAnnotation = False
                for dependency in service["dependencies"]:
                    for tool in tools:
                        if (tool in dependency):
                            res.append(tool)
                for imp in service["code"]["imports"]:
                    if "health" in imp.lower():
                        hasHealthImports = True
                        break

                for ann in service["code"]["annotations"]:
                    if "health" in ann.lower():
                        hasHealthAnnotation = True
                        break

                if (len(res) == 0):
                    self._hasNoHealthCheck[service["name"]] = {
                        "hasHealthcheckTools": False,
                        "hasHealthImports": hasHealthImports,
                        "hasHealthAnnotations": hasHealthAnnotation
                    }

            # System level
            for dependency in self._metamodel["system"]["dependencies"]:
                for tool in tools:
                    if (tool in dependency):
                        sysres.append(tool)

                if (len(sysres) == 0):
                    self._hasNoHealthCheck["system"] = {
                        "hasHealthcheckTools": False
                    }

    # Rule : intersect(distributed logging tool, dependencies) = 0
    def hasLocalLogging(self):
        with open("../tools/logging.txt", "r") as sdTools:
            tools = sdTools.readlines()
            tools = [line.rstrip() for line in tools]
            res = []
            sysres = []

            # Microservice level
            for service in self._metamodel["system"]["microservices"]:
                for dependency in service["dependencies"]:
                    for tool in tools:
                        if (tool in dependency):
                            res.append(tool)

                if (len(res) == 0):
                    self._hasLocalLogging[service["name"]] = {
                        "hasLoggingTool": False
                    }

            # System level
            for dependency in self._metamodel["system"]["dependencies"]:
                for tool in tools:
                    if (tool in dependency):
                        sysres.append(tool)

                if (len(sysres) == 0):
                    self._hasLocalLogging["system"] = {
                        "hasLoggingTool": False
                    }

        # Rule : intersect(monitoring libs, dependencies) = 0

    def hasInsufficientMonitoring(self):
        with open("../tools/monitoring.txt", "r") as sdTools:
            tools = sdTools.readlines()
            tools = [line.rstrip() for line in tools]
            res = []
            sysres = []


            # System level
            for dependency in self._metamodel["system"]["dependencies"]:
                for tool in tools:
                    if (tool in dependency):
                        sysres.append(tool)

                if (len(sysres) == 0) :
                    self._hasInsufficientMonitoring["system"] = {
                        "hasMonitoringTools": False
                    }

            # Microservice level
            for service in self._metamodel["system"]["microservices"]:
                for tool in tools:
                    if tool in service["name"] :
                        self._hasInsufficientMonitoring["system"] = {
                            "hasMonitoringTools": True
                        }
                        return
                    for dependency in service["dependencies"]:

                        if (tool in dependency):

                            res.append(tool)

                if (len(res) == 0):
                    self._hasInsufficientMonitoring[service["name"]] = {
                        "hasMonitoringTools": False
                    }





    def getResults(self):

        self.hasNanoService()
        self.hasMegaService()
        self.hasHardcodedEndpoints()
        self.hasManualConfiguration()
        self.hasApiGateway()
        self.hasLocalLogging()
        self.hasInsufficientMonitoring()
        self.hasCiCd()
        self.hasMultipleServicesPerHost()
        self.hasHealthCheck()
        self.hasWrongCuts()
        self.hasCircularDependencies()
        self.hasSharedDependencies()
        self.hasTimeouts()
        self.hasSharedPersistence()
        self.hasNoApiVersioning()

    def printResults(self):
        print("\n")
        print("====================================================================")
        print("Extracting antipatterns from metamodel complete. Printing results...")
        print("====================================================================")
        print("\n")

        print("System information : ")
        print("=====================")
        print("Number of microservices : {nb}".format(nb=self.vars["nbServices"]))
        print("Total lines of code : {nb}".format(nb=self.vars["totalLocs"]))
        print("Total number of files : {nb}".format(nb=self.vars["totalFiles"]))
        print("Avg LOCs per service : {nb}".format(nb=math.floor(self.vars["avgLocs"])))
        print("Avg Files per service : {nb}".format(nb=math.floor(self.vars["avgFiles"])))
        print("\n")

        print("Detection summary : ")
        print("===========================")
        print("\n")

        print("Wrong cuts : ")
        print("-------------")
        seenWc = []
        #print('number of wrongcuts couple found : ' + str(len(self._hasWrongCuts.values())) + '\n')
        if len(self._hasWrongCuts.values()) == 0 :
            print("No Wrong Cut was detected \n")
        else  :
            print("Wrong Cut was detected \n")
            for v in self._hasWrongCuts.values():
                for pair in v:
                    if ((pair["from"], pair["to"]) not in seenWc):  # Means we didn't already found it
                        print(pair["from"] + " have a wrong cut with " + pair["to"] + ":")
                        seenWc.append((pair["from"], pair["to"]))
                        seenWc.append((pair["to"], pair["from"]))
            print("\n")


        print("Circular Dependencies : ")
        print("------------------------")
        seenCD = []
        #print('Number of circluar dependencies couple found : ' + str(len(self._hasCircularDeps.values())) + '\n')
        if len(self._hasCircularDeps)!=0 :
            print("Antipattern detected")
            for v in self._hasCircularDeps:
                print(v)
        else :
            print("Antipattern NOT detected")


        print("\n")

        print("Mega services : ")
        print("----------------")

        print('Number of mega services found : ' + str(len(self._hasMega.items())) + '\n')
        for k, v in self._hasMega.items():
            print("- " + k + ": {locs} Locs, {files} Files.".format(locs=v["locs"], files=v["nbFiles"]))
        print("\n")



        print("Nano services : ")
        print("----------------")
        print('Number of nano services found : ' + str(len(self._hasNano.items())) + '\n')
        for k, v in self._hasNano.items():
            print("- " + k + ": {locs} Locs, {files} Files.".format(locs=v["locs"], files=v["nbFiles"]))
        print("\n")



        print("Shared Dependencies : ")
        print("----------------------")


        print('Number of shared libs found : ' + str(len(self._hasSharedLibs)) + '\n')

        for key in self._hasSharedLibs :
            print(key  + ": \n" + self._hasSharedLibs[key] +"\n")
        print("\n")




        print("Hardcoded Endpoints : ")
        print("----------------------")
        print('Number of hardcoded endpoints found : ' + str(len(self._hasHardcodedEndpoints.items())) + '\n')
        for k, v in self._hasHardcodedEndpoints.items():
            print("- " + k)
            print("\t- Has service discovery tool : " + str(v["hasServiceDiscoveryTool"]))
            print("\t- Found URLs in microservice :")
            for url in v["FoundUrls"].split(","):
                print("\t\t- " + url.strip())
        print("\n")


        print("Manual configuration : ")
        print("-----------------------")
        for k, v in self._hasManualConfig.items():
            print("- " + k)
            print("\t- Has configuration tool : " + str(v["hasConfigurationTool"]))
            print("\t- Found config files in microservice :")
            for url in v["FoundConfigFiles"].split(","):
                print("\t\t- " + url.strip().split("/")[-1])
        print("\n")


        print("No CI/CD : ")
        print("-----------")

        if len(self._hasNoCiCd.items())  >= self.vars["nbServices"] :
            print( "*** No CI/CD information were detected***")

        if (self.vars["hasCiCdFolders"]):
            print("*** System has CI/CD information, however, the following microservices do not.***")
            print("*** If you consider system wide CI/CD valid, please ignore this antipattern.***")
            for k, v in self._hasNoCiCd.items():
                print("- " + k + " has no CI/CD information")

        print("\n")


        print("No API Gateway : ")
        print("-----------------")
        if  len(self._hasNoApiGateway.items()) >= self.vars["nbServices"] :
            print("Any API Gateway was detected \n")
        for k, v in self._hasNoApiGateway.items():
            print("- " + k + " has no API Gateway tools")
        print("\n")


        print("Timeouts : ")
        print("-----------------")
        for k, v in self._hasTimeouts.items():
            if (k != "system"):
                print("- " + k + " has possible timeout antipattern:")
                print("\t- Has Circuit Breaker Tool : " + str(v["hasCircuitBreakerTool"]))
                print("\t- Has Timeout methods : " + str(v["hasTOMethods"]))
                print("\t- Has Timeout imports : " + str(v["hasTOImports"]))
                print("\t- Has Fallback methods : " + str(v["hasFBMethods"]))
        print("\n")

        print("Multiple instances per host : ")
        print("--------------------------")
        if (self._hasMultipleInstancesPerHost["system"]["systemHasCompose"]):

            print(
                "*** System has docker compose file. However, the following microservices do not have any dockerfile.***")
            print("*** This is a warning because the following might be on a shared host.***")

        for k, v in self._hasMultipleInstancesPerHost.items():
            print("- " + k + " has no DockerFile")
        print("\n")

        print("Shared Databases : ")
        print("-----------------")
        print('Number of shared databases found : ' + str(len(self._hasSharedPersistence)) + '\n')

        for key in self._hasSharedPersistence:
            print(key + ": \n" + self._hasSharedPersistence[key] + "\n")
        print("\n")




        print("No API Versioning : ")
        print("-----------------")
        if (self._hasNoApiVersioning["system"]["hasApiVersioning"] == True):
            print("*** System uses API versioning, if you consider this valid, you're probably fine.***")
        for k, v in self._hasNoApiVersioning.items():
            if (k != "system"):
                print("- " + k + " has no API versioning")
        print("\n")


        print("No HealthCheck : ")
        print("-----------------")



        print("*** If you only see system on this list, you're most likely fine.***")
        for k, v in self._hasNoHealthCheck.items():
            print("- " + k + " has no healthcheck library")
        print("\n")


        print("Local logging : ")
        print("----------------")
        for k, v in self._hasLocalLogging.items():
            print("- " + k + " has no logging tools")
        print("\n") 

        print("Insufficient monitoring : ")
        print("--------------------------")

        if len(self._hasInsufficientMonitoring.items())  >= self.vars["nbServices"] :
            print( "*** No monitoring tool was detected***")

        if self._hasInsufficientMonitoring["system"]["hasMonitoringTools"] :
            print("The microservice has a monitoring service \n")

        for k, v in self._hasInsufficientMonitoring.items():
            print("- " + k + " has no monitoring tools")
        print("\n") 




if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--metamodel", type=str, required=True)
    parser.add_argument("--project_name", type=str, required=True)
    args = parser.parse_args()

    metamodel_file = args.metamodel

    with open(metamodel_file) as mmfile:
        metamodel = json.load(mmfile)
        detector = Detector(metamodel)
        results = detector.getResults()

        detector.printResults()
