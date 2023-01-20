from setuptools import setup

setup(
    name='pyrobox_Rasan147',
    version='0.5.0',
    package_dir={"pyrobox_Rasan147": "src",},
    install_requires=[
        'natsort',
        "send2trash"
    ],
    entry_points='''
        [console_scripts]
        pyrobox=pyrobox_Rasan147:server.run
        # pyrobox-clone=pyrobox_Rasan147:clone
    ''',
)