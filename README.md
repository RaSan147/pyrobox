# Help Needed
# py_httpserver_Ult

` Note ` UPLOAD PASSWORD: `SECret`
# Requesting for more suggesions and ideas

Server side requirement
----------------------------------------------------------------
* Python 3.7 or higher [^1]
* Basic knowledge about Python
* `send2trash` pip package (will be auto installed when the code runs)
* (for windows) no need to download 7z[^2] (from here), it will be automatically downloaded

[^1]: Making a working version to support till 3.4, but not sure will maintain that. Also not recommended since it got EOL)
[^2]: Planning to drop using 7z and use Python `zipfile`

Installation
----------------------------------------------------------------
1. Download the `local_server.py`
2. yes, only the `local_Server.py`. Other files are not necessary.
3. Install Python 3.7 or higher and run the `local_server.py`
4. The server will show your ip and port, use that with and local device browser under the same network
   * Like this `192.168.0.100:6969/`
# On Linux

On Linux give permissions by :
```
$sudo chmod +x local_server.py
```
run like a script with :
```
$./local_server.py
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
* 📁 FOLDER DOWNLOAD as **ZIP** (uses temp folder)
* ⏯ VIDEO PLAYER
* 🔁 **DELETE FILE** (MOVE TO RECYCLE BIN)
* 🔥 PERMANENTLY DELETE
* ⛓ `File manager` like `NAVIGATION BAR`
* 🧨 RELOAD SERVER FROM REMOTE [DEBUG PURPOSE]
* 🆕 FOLDER CREATION
* 💬 Pop-up messages UI(from my Web leach repo)
* 🌐 If you are using REAL IP AND ALLOW PYTHON TO USE PUBLIC NETWORK, YOUR SERVER CAN BE VISIBLE AROUND THE GLOBE. (also vulnerable, since you can't control access *yet*)
* 🔜 More comming soon

 TODO:
--------------------------------------------------------------

- [ ] #31 (almost done)
* #32
* #33, for png and jpg (how to do with just standard library?), For others, just show extension.
* Copy stream URL for videos to play with any video player
* RIGHT CLICK CONTEXT MENU
* Add side bar to do something 🤔
* check output ip and port accuracy on multiple os  
* Backup code if Reload causes unhandled issue and can't be accessed
* command line arg for passwords (vulnerable on reload)
* User login and user based permission set. 🔑

# Support for more features

Context menu:
--------------------------------------------------------------
  <img src="https://user-images.githubusercontent.com/34002411/174422718-e19d33b2-4937-47d7-bcc2-610141c1e437.jpg" width=200>


