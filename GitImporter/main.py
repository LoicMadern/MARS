import os
import sys
from shutil import copyfile, rmtree
from git import Repo



repo_folder = sys.argv[1]
repo_url = sys.argv[2]

print("Cloning " + repo_url + " into current analyser microservice folder...")
for root, dirs, files in os.walk('../../projects/'+repo_folder):
    for f in files:
        os.unlink(os.path.join(root, f))
    for d in dirs:
        rmtree(os.path.join(root, d))

Repo.clone_from(repo_url, "../../projects/"+repo_folder)
print("Cloning done\n")

