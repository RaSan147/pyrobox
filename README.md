# Help Needed
# py_httpserver_Ult

` Note ` UPLOAD PASSWORD: `SECret`
# Requesting for more suggesions and ideas

Server side requirement
----------------------------------------------------------------
* Python 3.7 or higher (need to test lower versions)
* Basic knowledge about Python
* `send2trash` pip package (will be auto installed when the code runs)
* (for windows) no need to download 7z (from here), it will be automatically downloaded

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
   $sudo chmod +x local_Server.py
```
run like a script with :
```
   $./local_Server.py
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
        - `local_server.py -d "D:/Server/Public folder"` (Forward or backward slash really doesn't matter)
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
* 🔜 More comming soon

 TODO:
--------------------------------------------------------------

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


