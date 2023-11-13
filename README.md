#################################
# MACHINE PREREQUISITES         #
#################################

- sudo apt install python (3.x)
- sudo apt install python3-pip
- sudo apt install ruby (2.7)
- sudo apt-get install ruby2.7-dev
- sudo apt install nodejs (16.14)
- sudo apt install npm (8.5)
- sudo apt install cloc
- pip3 install -r requirements.txt
- gem install bibliothecary


#################################
# RUNNING THE TOOL #
#################################

Some scripts were developped in order to make handling easier the tool.
When you'll execute for the first time a folder named projects will be created.
It will be on computer at the same level as the tool itself.It will store the projects that you will analyze.

#1st step download your project
- sudo sh download-repo.sh project_name url_repo

project_name is the argument for creating a folder named project_name in projects folder.It will contain the repo that you to analyze

url_repo is the argument for the repository url on github that you want to analyze


#2nd prepare your project to be analysed by MARS
- cd ../projects/project_name
- vim exclude.txt 
- add folders you want to exclude (Each one in a new line)
- close vim
- modify the calls.CSV file. You'll make a callgraphs by couple of microservices of the project by using comma separator.
( you can use IDE as intellijea, if you can't, go on the next step and don't take in account the circular dependencies analysis)

#3th step launch MARS
- cd ..
- sudo sh analyze.sh project_name url_repo

#4th watch the result
- cd projects/project_name
- metamodel.json and output have been generated

For further informations, please contact :

Imene Trabelsi : imen.trabelsi.1@ens.etsmtl.ca
Manel Abdellatif :
manel.abdellatif@etsmtl.ca
