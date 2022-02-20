# httpserver_with_many_feat

` Note ` UPLOAD PASSWORD: `SECret`
# Requesting for more suggesions and ideas

Server side requirement
----------------------------------------------------------------
* Python 3.7 or higher (need to test lower versions)
* Basic knowledge about Python
* `send2trash` pip package (will be auto installed when the code runs)

How to use
----------------------------------------------------------------
1. Simply running the code will create a server on `G:\ Drive` for windows on `Port: 6969`
1. On browser (same device as server), go to `localhost:port_number` to see the output
1. To change the server running directory, 
   - i) either edit the code  
   - ii) or add `-d` or -`--directory` command line argument when launching the program
        - `local_server.py -d .` to launch the server in current directory (where the file is)
        - `local_server.py -d "D:\Server\Public folder\`  (Use Double-Quotation while directory has space)
        - `local_server.py -d "D:/Server/Public folder` (Forward or backward slash really doesn't matter)
 1. To change port number
    - i) just edit the code for permanent change  
    - ii) or add the port number at the end of the command line arg  
       -  `local_server.py 45678`
       -  `local_server.py -d . 45678`

1. To specify alternate bind address
    - Add bind add `-bind {address}`


 Extra FEATURES 
----------------------------------------------------------------
* PAUSE AND RESUME
* UPLOAD WITH PASSWORD
* FFOLDER DOWNLOAD (but you need to delete temp folder manually, working on it)
* VIDEO PLAYER
* DELETE FILE FROM REMOTE (RECYCLE BIN) # PERMANENTLY DELETE IS VULNERABLE
* RELOAD SERVER FROM REMOTE [DEBUG PURPOSE]
* MULTIPLE FILE UPLOAD
* ADD FOLDER CREATION
* Add pop-up messages from Web leach
* More comming soon

 TODO:
--------------------------------------------------------------

* RIGHT CLICK CONTEXT MENU
* Add side bar to do something 🤔
* check output ip and port accuracy on multiple os  


# Support for more features
