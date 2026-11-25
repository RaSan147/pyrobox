from setuptools import setup

setup(
    packages=["pyrobox"],
    package_dir={"pyrobox": "src"},
    package_data={"pyrobox": ["*.html", "*.js", "*.css"]},
    install_requires=[
        'natsort',
        "send2trash",
        "msgpack",
        "tabulate2",
        "pyqrcode",
    ],
    extras_require={
        # pip install pyrobox[clone]
        "clone": ["requests"],
    },
    entry_points='''
        [console_scripts]
        pyrobox=pyrobox.server:run
        pyrobox-clone=pyrobox.clone:main
        pyrobox-upload-clone=pyrobox.upload_clone:main
    ''',


)
