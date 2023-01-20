import os 

os.system("python -m build")
os.system("pip install ./dist/pyrobox-0.5.0.tar.gz")
os.system("pyrobox 45454")