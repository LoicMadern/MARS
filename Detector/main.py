import json
import argparse
import math
import pandas as pd



class Detector(object):

    # Constants to act as defaults

    # Nano Service
    # Rule : (LOC < (threshold * SysAvgLocs) and NbFiles < (threshold * SysAvgNbFiles))
    NANO_SERVICE_LOC_THRESHOLD = 0.5   # If LOCs < Threshold, it's likely a nano service  -- 50% -- Service has 0.5 times lower LOCS
    NANO_SERVICE_FILES_THRESHOLD = 0.5 # If NbFiles < Threshold, it's likely a nano service -- 50% -- Service has 0.5 times lower LOCS


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

    # Rule: pourcentage_of_extensions_web_files > THR * NUMBER_FILES
    def hasWrongCuts(self):

        root = "../../projects/" + args.project_name + "/"
        folders = []
        flag_folders = []
        microservices = self._metamodel["system"]["microservices"]

        for service in range(len(microservices)):
            listeFichiers = microservices[service]["code"]["source_files"]
            number_files = len(listeFichiers)
            dict = {}
            cpt = 0

            for fichier in listeFichiers:
                if "." in fichier:
                    extension = fichier.split(".")[1]
                    if extension not in dict:
                        dict[extension] = 1
                    else:
                        dict[extension] += 1

            for key in dict:

                with open("../tools/config_extensions.txt", "r") as confTools:
                    tools_extension = confTools.readlines()
                    tools_extension = [line.rstrip() for line in tools_extension]

                    for tool_extension in tools_extension :
                        if key == tool_extension :
                            number_files -= 1

                with open("../tools/web_extensions.txt", "r") as webTools:
                    tools_web = webTools.readlines()
                    tools_web = [line.rstrip() for line in tools_web]

                    for tool_web in tools_web:
                        if key == tool_web:
                            cpt += dict[key]


            if cpt > number_files * 0.8 and microservices[service]["name"] not in flag_folders:
                flag_folders.append(microservices[service]["name"])

        self._hasWrongCuts = flag_folders

    # Rule: Msa imports MSb AND MSb imports MSa
    def hasCircularDependencies(self):
        pre_tab =[]
        tab = []
        final_tab = []
        for service in self._metamodel["system"]["microservices"]:
            for call in service["code"]["callgraph"] :
                if call!=[] :
                    pre_tab.append(call)
        for value in pre_tab:
            if [value[0].split("/")[0], value[1].split("/")[0]] not in tab and value[0].split("/")[0] != value[1].split("/")[0]:
                tab.append([value[0].split("/")[0], value[1].split("/")[0]])
        for element in tab:
            if [element[1], element[0]] in tab and not [element[1], element[0]] in final_tab or [element[0], element[
                1]] in final_tab:
                final_tab.append(element)
        self._hasCircularDeps = final_tab




    # Rule : (LOC > (threshold * SysAvgLocs)
    def hasMegaService(self):

        for service in self._metamodel["system"]["microservices"]:
            requiredLocs =  requiredLocs = self.vars["totalLocs"] *0.39

            hasMoreLocsThanAvg = int(service["locs"]) > requiredLocs

            if(hasMoreLocsThanAvg and  ("demo" not in service["name"] and "command" not in service["name"])):
                self._hasMega[service["name"]] = {
                    "locs": service["locs"],
                    "nbFiles": service["nb_files"],
                    "requiredLocs": requiredLocs
                }

    # Rule : (LOC < (threshold * SysAvgLocs) and NbFiles < (threshold * SysAvgNbFiles))
    def hasNanoService(self):
        #some services as APIs or config service should not be taking in account as a microservice
        #that why there is list of ban words in order to not counting this kind of occurrences
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

    # Rule: Microservices groups using the same dependency
    def hasSharedDependencies(self):
        dict = {}
        final_dict ={}

        with open("../tools/not_shared_dependencies.txt", "r") as confTools:
            tools = confTools.readlines()
            tools = [line.rstrip() for line in tools]

            for i in range(len(self._metamodel["system"]["microservices"])):
                #some dependencies are essential to certain services in order to work well
                #that why some dependencies are not taking in account
                #with the list from "not_shared_dependencies.txt" and the boolean flag_in_tool
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

    # Rule : intersect(Service discovery, dependencies) = 0 AND (count(URLs, source code) > 0 OR count(URLs, config files) > 0)
    def hasHardcodedEndpoints(self):
        with open("../tools/service_discovery.txt", "r") as sdTools:
            tools = sdTools.readlines()
            tools = [line.rstrip() for line in tools]
            res = []
            sysres = []
            
            # Microservice level (code)
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
            
            # System level (configuration)
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
    # AND intersect(Fallbacks, methods) = 0) OR (count(timeouts, imports) > 0 OR count(timeouts, methods) > 0)
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




    # Rule : intersect(docker-compose.yml, system) = 0 AND count(DOCKERFILE, microservices) = 0
    def hasMultipleServicesPerHost(self):
        systemHasCompose = False
        self._hasMultipleInstancesPerHost["docker_directory"] = {
            "existence": False
        }


        for file in self._metamodel["system"]["config_files"]:
            if "docker-compose.yml" in file:
                systemHasCompose = True
            for service in self._metamodel["system"]["microservices"]:
            # Microservice level

                if len(service["deployment"]["docker_files"]) == 0 :

                    self._hasMultipleInstancesPerHost[service["name"]] = {
                        "hasDockerFile": False
                    }
            
            self._hasMultipleInstancesPerHost["system"] = {
                "systemHasCompose": systemHasCompose
            }
        self._hasMultipleInstancesPerHost["system"] = {
            "systemHasCompose": systemHasCompose
        }



    #MSa uses DBx AND MSb uses DBx OR count(unique(datasource urls), source code) > 1
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

    # intersect(healthcheck libs, system) = 0
    def hasHealthCheck(self):
        with open("../tools/healthcheck.txt", "r") as sdTools:
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
                    self._hasNoHealthCheck[service["name"]] = {
                        "hasHealthcheckTools": False,
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
        if len(self._hasWrongCuts) == 0 :
            print("Wrong Cut was not detected \n")
        else  :
            print("Wrong Cut was detected \n")
            for v in self._hasWrongCuts:
                print(v)
        print("\n")


        print("Circular Dependencies : ")
        print("------------------------")
        if len(self._hasCircularDeps) == 0:
            print("Circular Depenencies was not detected \n")

        else :
            print("Circular Depenencies was detected \n")
            for value in self._hasCircularDeps :
                print(value)


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

        print("Only count the ones which has not a discoveryTool \n")
        for k, v in self._hasHardcodedEndpoints.items():
            print("- " + k)
            print("\t- Has service discovery tool : " + str(v["hasServiceDiscoveryTool"]))
            print("\t- Found URLs in microservice :")
            for url in v["FoundUrls"].split(","):
                print("\t\t- " + url.strip())
        print("\n")


        print("Manual configuration : ")
        print("-----------------------")
        print("Only count the ones which has not a configuration tool \n")
        for k, v in self._hasManualConfig.items():
            print("- " + k)
            print("\t- Has configuration tool : " + str(v["hasConfigurationTool"]))
            print("\t- Found config files in microservice :")
            for url in v["FoundConfigFiles"].split(","):
                print("\t\t- " + url.strip().split("/")[-1])
        print("\n")


        print("No CI/CD : ")
        print("-----------")

        if len(self._hasNoCiCd.items())  >= self.vars["nbServices"] and not self.vars["hasCiCdFolders"] :
            print("Antipattern detected")

        else:
            print("CI/CD information were detected")
            print("*** System has CI/CD information, however, the following microservices do not.***")
            for k, v in self._hasNoCiCd.items():
                print("- " + k + " has no CI/CD information")

        print("\n")


        print("No API Gateway : ")
        print("-----------------")
        if  len(self._hasNoApiGateway.items()) >= self.vars["nbServices"] :
            print("The antipattern was detected \n")
        else :
            print("Some API Gateway were detected however, those services do not :\n")
        for k, v in self._hasNoApiGateway.items():
            print("- " + k + " has no API Gateway tools")
        print("\n")


        print("Timeouts : ")
        print("-----------------")
        if len(self._hasTimeouts.items())==1 or (len(self._hasTimeouts.items())>1 and self._hasTimeouts["system"]["hasCircuitBreaker"]):
            print("The antipattern was not detected\n")
        else :
            print("Timeout antipattern was detected \n")
            for k, v in self._hasTimeouts.items():

                if k!="system" :
                    print("- " + k + " has possible timeout antipattern:")
                    print("\t- Has Circuit Breaker Tool : " + str(v["hasCircuitBreakerTool"]))
                    print("\t- Has Timeout methods : " + str(v["hasTOMethods"]))
                    print("\t- Has Timeout imports : " + str(v["hasTOImports"]))
                    print("\t- Has Fallback methods : " + str(v["hasFBMethods"]))
        print("\n")

        print("Multiple instances per host : ")
        print("--------------------------")
        if (len(self._hasMultipleInstancesPerHost.items()) >= self.vars["nbServices"] ) :
            print("The antipattern was detected \n")

        else :
            print("**The application has not the antipattern multiple instance per host. However, the following microservices do not have any dockerfile.***")
            for k, v in self._hasMultipleInstancesPerHost.items():
                if not "docker_directory" in k :
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
        if len(self._hasNoApiVersioning.items())>=  self.vars["nbServices"] :
            print("Antipattern detected")
        else :
            if len(self._hasNoApiVersioning.items())!=0 :
                print("Antipattern was not detected. However those services have not a API versionning ")
            else :
                print("Antipattern was not detected.")
            for k, v in self._hasNoApiVersioning.items():
                if (k != "system"):
                    print("- " + k + " has no API versioning")
        print("\n")


        print("No HealthCheck : ")
        print("-----------------")
        if len(self._hasNoHealthCheck.items()) == 0:
            print("The antipattern was detected\n")
        else :
            print("*** If you only see system on this list, you're most likely fine.\n***")
            for k, v in self._hasNoHealthCheck.items():
                print("- " + k + " has no healthcheck library")
        print("\n")

        print("Local logging : ")
        print("----------------")
        if len(self._hasLocalLogging.items())  >= self.vars["nbServices"] :
            print("The antipattern was detected\n")
        else :
            print("A logging tool was detected but it's possible some has not\n")
            for k, v in self._hasLocalLogging.items():
                print("- " + k + " has no logging tools")
        print("\n") 

        print("Insufficient monitoring : ")
        print("--------------------------")

        if len(self._hasInsufficientMonitoring.items())  >= self.vars["nbServices"] :
            print( "The antipattern was detected\n")

        else :
            print("The application has a monitoring service but some don't have \n")
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
