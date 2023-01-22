import os 

os.system("python -m build")
os.system("pip install ./dist/pyrobox-0.6.1.tar.gz")
os.system("pyrobox 45454")