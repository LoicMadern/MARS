import os
import sys
from shutil import copyfile, rmtree
from git import Repo


repo_url = sys.argv[1]

print("Cloning " + repo_url + " into current analyser microservice folder...")
for root, dirs, files in os.walk('../projects'):
    for f in files:
        os.unlink(os.path.join(root, f))
    for d in dirs:
        rmtree(os.path.join(root, d))

Repo.clone_from(sys.argv[1], "../projects")
print("Cloning done")

