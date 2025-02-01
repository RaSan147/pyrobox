#import glob, os
#os.chdir("python")
import os

all_files = input("Enter the file extensions separated by comma: ")
if all_files == "":
    all_files = ["py", "html", "css", "js", "c", "cpp", "java", "cs", "php", "ts", "yaml", "yml", "md"]
else:
    all_files = all_files.split(",")
    all_files = [x.strip() for x in all_files]
    all_files = [x.lower() for x in all_files]
    all_files = list(set(all_files))
    all_files = [x.strip('.') for x in all_files]

all_files = ["."+x for x in all_files]

n = 0
for root, dirs, files in os.walk("."):
    for file in files:
        if file.endswith(tuple(all_files)):
            path = os.path.join(root, file)
            #  ignore node_modules, .git, .vscode, .idea, __pycache__, .pytest_cache, .mypy_cache, .tox
            if any(x in path for x in ["node_modules", ".git", ".vscode", ".idea", "__pycache__", ".pytest_cache", ".mypy_cache", ".tox"]):
                continue
            print(os.path.join(root, file))

            for t in open(os.path.join(root, file),"rb").readlines():
                if t.strip()!=b"":
                    n+=1



print("\n\nTOTAL LINES:", n)
