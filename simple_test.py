print("Python is working!")
print("Current directory test")

import os
print(f"Current working directory: {os.getcwd()}")

# Check if key files exist
files_to_check = ["DIBBs.py", "crm_app.py", "crm.db"]
for file in files_to_check:
    exists = os.path.exists(file)
    print(f"{file}: {'EXISTS' if exists else 'NOT FOUND'}")

# Check if directories exist
dirs_to_check = ["To Process", "templates", "static"]
for dir in dirs_to_check:
    exists = os.path.exists(dir)
    print(f"{dir}/: {'EXISTS' if exists else 'NOT FOUND'}")
