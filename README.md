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
- cd Mars/Extractor
- pip install -r requirements.txt
- gem install bibliothecary
- cd ../GitImporter
- pip install -r requirements.txt
# Optional to run with GUI #
- cd ../frontend
- npm install

#################################
# RUNNING THE TOOL WITHOUT GUI  #
#################################

- cd ../gradle_parser
- npm start
- in another terminal : 
    - cd Mars/GitImporter
    - python main.py URL_OF_GIT_REPO (ex. https://github.com/microservices-patterns/ftgo-application)
    - cd ../CurrentMBS
    - vim exclude.txt 
    - add folders you want to exclude (Each one in a new line)
    - cd ../Extractor
    - python main.py
    - Metamodel should be generated
    - cd ../Detector
    - python main.py --metamodel PATH_TO_METAMODEL_FILE | tee outputfile.txt 
        (ex python main.py --metamodel ../metamodel.json | tee ../output.txt)
    - check output file for result (less ../output.txt)

#################################
# RUNNING THE TOOL WITH GUI     #
#################################

- cd ../gradle_parser
- npm start
- in another terminal : 
    - cd Mars/Extractor
    - export FLASK_APP=app
    - flask run -p 3000

- in yet another terminal :
    - cd Mars/frontend
    - npm start

- in your browser :
    - localhost:8080
