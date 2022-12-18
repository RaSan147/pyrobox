### Help Needed
# py_httpserver_Ult

` Note ` UPLOAD PASSWORD: `SECret`
# Requesting for more suggesions and ideas

Basic FEATURES
----------------------------------------------------------------
* File Hosting system (Serve files from local Storage system)
* Access Shared File System from Multiple Devices

 Extra FEATURES 
----------------------------------------------------------------
* 🔽 DOWNLOAD AND VIDEO STREAM WITH **PAUSE AND RESUME**
* 🔼 UPLOAD WITH **PASSWORD**
* 📈 MULTIPLE FILE **UPLOAD**
* 📝 RENAME
* 📁 FOLDER DOWNLOAD as **ZIP** (uses temp folder)[^1]
* ⏯ VIDEO PLAYER
* 🔁 **DELETE FILE** (MOVE TO RECYCLE BIN)
* 🔥 PERMANENTLY DELETE
* ⛓ `File manager` like `NAVIGATION BAR`
* 🧨 RELOAD SERVER FROM REMOTE [DEBUG PURPOSE]
* 🆕 FOLDER CREATION
* 💬 Pop-up messages UI(from my Web leach repo)
* 🌐 If you are using REAL IP AND ALLOW PYTHON TO USE PUBLIC NETWORK, YOUR SERVER CAN BE VISIBLE AROUND THE GLOBE. (also vulnerable, since you can't control access *yet*)
* 🔜 More comming soon

[^1]: Currently using 7zip which requires temp directory to create the zip. But on my way to depricate 7zip use.

Server side requirement
----------------------------------------------------------------
* Python 3.7 or higher. Older support available.[^2]
* Basic knowledge about Python
* `send2trash` pip package (will be auto installed when the code runs)
* (for windows) no need to download 7z[^1] (from here), it will be automatically downloaded

[^2]: [3.4 compat](https://github.com/RaSan147/py_httpserver_Ult/blob/main/src/local_server%20(py%7E3.4).py) version to support till 3.4, but will not maintain that often. Also not recommended since it got EOL)


Installation
----------------------------------------------------------------
1. Download the `local_server.py`
2. yes, only the `local_server.py`. Other files are not necessary.
3. Install Python 3.7 or higher and run the `local_server.py`
4. The server will show your ip and port, use that with and local device browser under the same network
   * Like this `192.168.0.100:6969/`

### On Linux (Optional)
To run code directly like a script on a linux machine. Just paste these lines on a terminal.
```
wget https://raw.githubusercontent.com/RaSan147/py_httpserver_Ult/main/local_server.py # download script
chmod +x local_server.py # give permissions
./local_server.py # run like a script
```

Customization
----------------------------------------------------------------
1. Simply running the code will create a server on `G:\ Drive` for windows on `Port: 6969`
1. On browser (same device as server), go to `localhost:port_number` to see the output
1. To change the server running directory, 
   - i) either edit the code  
   - ii) or add `-d` or `--directory` command line argument when launching the program
        - `local_server.py -d .` to launch the server in current directory (where the file is)
        - `local_server.py -d "D:\Server\Public folder\"`  (Use Double-Quotation while directory has space)
        - `local_server.py -d "D:/Server/Public folder"` (Forward or backward slash really doesn't matter, unless your terminal thinks otherwise)
 1. To change port number
    - i) just edit the code for permanent change  
    - ii) or add the port number at the end of the command line arg  
       -  `local_server.py 45678`
       -  `local_server.py -d . 45678`

1. To specify alternate bind address
    - Add bind add `-bind {address}`

 TODO:
--------------------------------------------------------------

* https://github.com/RaSan147/py_httpserver_Ult/issues/31 Show upload progress (almost done)
* https://github.com/RaSan147/py_httpserver_Ult/issues/32 Use HTML5 drag and drop uploader
* https://github.com/RaSan147/py_httpserver_Ult/issues/33 Show thumbnails, for png and jpg (how to do with just standard library?), For others, just show extension.
* https://github.com/RaSan147/py_httpserver_Ult/issues/34 Copy stream URL for videos to play with any video player
* https://github.com/RaSan147/py_httpserver_Ult/issues/35 RIGHT CLICK CONTEXT MENU
* https://github.com/RaSan147/py_httpserver_Ult/issues/36 Add side bar to do something 🤔
* check output ip and port accuracy on multiple os  
* https://github.com/RaSan147/py_httpserver_Ult/issues/37 Backup code if Reload causes unhandled issue and can't be accessed
* https://github.com/RaSan147/py_httpserver_Ult/issues/38 command line arg for passwords (vulnerable on reload)
* https://github.com/RaSan147/py_httpserver_Ult/issues/39 User login and user based permission set. 🔑

# Support for more features


Context menu:
--------------------------------------------------------------
  <img src="https://user-images.githubusercontent.com/34002411/174422718-e19d33b2-4937-47d7-bcc2-610141c1e437.jpg" width=200>


