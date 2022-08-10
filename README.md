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
The script will create a folder named projects in the same level as the tool itself

#1st step download your project
- sudo sh download-repo.sh folder_name url_repo

the folder_name will be the folder that will contains the application
it will be store in the folder projects

#2nd prepare your project to be analysed by MARS
- cd ../projects/folder_name
- vim exclude.txt 
- add folders you want to exclude (Each one in a new line)
- close vim
- add a CSV callgraphs by package with , separator named calls

#3th step launch MARS
- cd ..
- sudo sh analyze.sh folder_name url_repo

#4th watch the result
- cd projects/NAME_PROJECT
- metamodel.json and output have been generated
