#import glob, os
#os.chdir("python")
import os
n = 0
for root, dirs, files in os.walk("."):
    for file in files:
        if file.endswith(".py") or file.endswith(".html") or file.endswith(".css") or file.endswith(".js") :
             print(os.path.join(root, file))
             for t in open(os.path.join(root, file),"rb").readlines():
                 if t.strip()!=b"":n+=1


print("\n\nTOTAL LINES:", n)
