from flask import Flask, jsonify, request
import json
import subprocess
import os


app = Flask(__name__)


@app.route('/')
def home():
    return jsonify("Hello")

@app.route('/run')
def hello():
    subprocess.run(["python", "main.py"], capture_output=False)
    with open("../metamodel.json") as jsonFile:
        jsonObject = json.load(jsonFile)
    jsonFile.close()
    return jsonify(jsonObject)

@app.route('/clone', methods=['POST'])
def clone():
    if request.method == 'POST':
        url = request.form.get('repoUrl')
        subprocess.run(["python3", "../GitImporter/main.py", url], capture_output=False)
        subfolders = [f.name for f in os.scandir("../projects/") if f.is_dir()]
    return jsonify(subfolders)
