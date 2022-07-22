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
# RUNNING THE TOOL WITHOUT GUI  #
#################################


#1st step download your project
- cd ./GitImporter
- python main.py URL_OF_GIT_REPO (ex. https://github.com/microservices-patterns/ftgo-application)

#2nd prepare your project to be analysed by MARS
- cd ../projects
- vim exclude.txt 
- add folders you want to exclude (Each one in a new line)
- close vim
- add callgraph CSV by class with ; separator 

#3th step launch MARS
- cd ..
- sudo sh analyze.sh NAME_PROJECT (ex. ftgo-application)

#4th watch the result
- cd projects/NAME_PROJECT
- metamodel.json and output have been generated
