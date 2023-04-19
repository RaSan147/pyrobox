# pyrobox 🔥

**`Note :`** DEFAULT UPLOAD PASSWORD: `SECret`
* you can change it by editing the code (see `config` class at top)
* to set password from command line, use `-k` or `--password` flag

# Status 
[![Downloads](https://static.pepy.tech/badge/pyrobox)](https://pepy.tech/project/pyrobox)


# Requesting for more suggesions and ideas

Basic FEATURES
----------------------------------------------------------------
* File Hosting system (Serve files from local Storage system)
* Access Shared File System from Multiple Devices

 Extra FEATURES 
----------------------------------------------------------------
* 🔽 DOWNLOAD AND VIDEO STREAM WITH **PAUSE AND RESUME**
* 🔼 UPLOAD WITH **PASSWORD**
* 👌 HTML5 drag and drop uploader
* 📈 MULTIPLE FILE **UPLOAD**
* 📝 RENAME
* 📁 FOLDER DOWNLOAD as **ZIP** (uses temp folder)
* ⏯ VIDEO PLAYER
* 🔁 **DELETE FILE** (MOVE TO RECYCLE BIN)
* 🔥 PERMANENTLY DELETE
* ⛓ `File manager` like `NAVIGATION BAR`
* 📑 Right click Context menu (Tap n hold on touch device)
* 🧨 RELOAD SERVER FROM REMOTE [DEBUG PURPOSE]
* 🆕 FOLDER CREATION
* 💬 Pop-up messages UI(from my Web leach repo)
* 🌐 (Didn't test yet) If you are using REAL IP AND ALLOW PYTHON TO USE PUBLIC NETWORK, YOUR SERVER CAN BE VISIBLE AROUND THE GLOBE. (also vulnerable, since you can't control access *yet*)
* 🧬 Clone entire directory from Host to Client with least changes (last modified preserved)
* 🔜 More comming soon


Server side requirement
----------------------------------------------------------------
* Python 3.7 or higher. Older support available.[^1]
* Basic knowledge about Python
* `send2trash`, `natsort` pip package (if missing, will be auto installed when the code runs)

[^1]: [<=3.4 compat] is on the way.


# Installation
----------------------------------------------------------------
  * **Install Python 3.7 or higher**
  * **Close older pyrobox process if already running**
  1. Install using PIP
  ### On Windows:
  * Open `CMD` or `PowerShell`
  * Run `pip install pyrobox`
  * Run `pyrobox` to launch the server

  ### On Linux:
  * Open `Terminal`
  * Run `pip3 install pyrobox`
  * Run `pyrobox` to launch the server


CHECK [FAQ](#faq) FOR FUTURE HELP AND ISSUE FIX


# Customization
1. Simply running the code on will create a server on `CURRENT WORKING DIRECTORY` on `Port: 6969`
1. On browser (on device under same router/wifi network), go to `deviceIP:port_number` to see the output like this: `http://192.168.0.101:6969/`
    * you must allow python in firewall to access network, check [FAQ](#faq) for more help
1. To change the server running directory, 
   - i) either edit the code  (see `config` class at top)
   - ii) or add `-d` or `--directory` command line argument when launching the program
        - `pyrobox -d .` to launch the server in current directory (where the file is)
        - `pyrobox -d "D:\Server\Public folder\"`  (Use Double-Quotation while directory has space)
        - `pyrobox -d "D:/Server/Public folder"` (Forward or backward slash really doesn't matter, unless your terminal thinks otherwise)
 1. To change port number
    - i) just edit the code for permanent change  (see `config` class at top)
    - ii) or add the port number at the end of the command line arg  
       -  `pyrobox 45678` # will run on port 45678
       -  `pyrobox -d . 45678` # will run on port 45678 in current directory

1. To specify alternate bind address
    - Add bind add `-bind {address}` # ie: `-bind 127.0.0.2` or `-bind 127.0.0.99`

1. To change upload password
    - i) or add `-k` or `--password` command line argument when launching the program
        - `pyrobox -k "my new password"` to launch the server with new password
        - `pyrobox -k ""` to launch the server without password
        - `pyrobox` to launch the server with default password (SECret)
    - ii) just edit the code for permanent change  (see `config` class at top)

1. Optional configurations

usage: `local_server_pyrobox.py [--password PASSWORD] [--no-upload] [--no-zip] [--no-update] [--no-delete] [--no-download] [--read-only] [--view-only] [--bind ADDRESS] [--directory DIRECTORY] [--version] [-h] [port]`

# positional arguments:
  | arg value             | Description |
  | --------------------- | ------------|
  | `port`                | Specify alternate port [default: 6969] |


# options:
  | arg `value`           | Description |
  | --------------------- | ------------|
  |--password `PASSWORD`, -k  `PASSWORD` | Upload Password (default: SECret)|
  |--directory `DIRECTORY`, -d `DIRECTORY` | Specify alternative directory [default: current directory]
  |--bind `ADDRESS`, -b `ADDRESS` | Specify alternate bind address [default: all interfaces]|


# Customisation options:
  | arg                  | Description |
  | -------------------- | ------------|
  |--no-upload, -nu      | Files can't be uploaded (default: False)|
  |--no-zip, -nz         | Disable Folder->Zip downloading (default: False)|
  |--no-update, -no      | Disable File Updating (ie: **renaming**, **overwriting existing files**) (On upload, if file exists, will add a number at the end(default: False)|
  |--no-delete, -nd      | Disable File Deletion (default: False)|
  |--no-download, -ndw   | Disable File Downloading [**videos won't play either**] (default: False)|
  |--read-only, -ro      | Read Only Mode *disables upload and any modifications ie: rename, delete* (default: False)|
  |--view-only, -vo      | Only allowed to see file list, nothing else (default: False)|
  --version, -v          | show program's version number and exit|
  -h, --help             | show this help message and exit|


 TODO:
--------------------------------------------------------------

* https://github.com/RaSan147/pyrobox/issues/33 Show thumbnails, for png and jpg (how to do with just standard library?), For others, just show extension.
* https://github.com/RaSan147/pyrobox/issues/34 Copy stream URL for videos to play with any video player
* https://github.com/RaSan147/pyrobox/issues/36 Add side bar to do something 🤔
* check output ip and port accuracy on multiple os  
* https://github.com/RaSan147/pyrobox/issues/37 Backup code if Reload causes unhandled issue and can't be accessed
* https://github.com/RaSan147/pyrobox/issues/39 User login and user based permission set. 🔑

# Support for more features


Context menu:
--------------------------------------------------------------
  **Right click on any file link**
  <img src="https://user-images.githubusercontent.com/34002411/174422718-e19d33b2-4937-47d7-bcc2-610141c1e437.jpg" width=200>

# FAQ:
<details>
  <summary>Using WSL, "PIP not found"</summary>
 
  > Run this to install `pip3` and add `pip` to path 
  ```
  sudo apt -y purge python3-pip
  sudo python3 -m pip uninstall pip
  sudo apt -y install python3-pip
  pip3 install --upgrade pip
  echo "export PATH=\"${HOME}/.local/bin:$PATH\"" >>"${HOME}"/.bashrc
  ```
  > Re-running the file should work.
</details>

<details>
  <summary>Using Linux, "PIP not found"</summary>
  
  > Run this to install `pip3` 
  ```
  sudo apt -y purge python3-pip
  sudo python3 -m pip uninstall pip
  sudo apt -y install python3-pip
  pip3 install --upgrade pip
  ```
  > Re-running the file should work.
</details>


<details>
  <summary>Deleted (Move to Recycle), But WHERE ARE THEY?? [on LINUX & WSL]</summary>
  
  > Actually the feature is working fine, unfortunately NO-GUI mode linux and WSL don't recycle bin, so you can't find it!
  > And to make things worse, **you need to manually clear the recyle bin** from `~/.local/share/Trash`
  > **SO I'D RECOMMAND USING DELETE PARMANENTLY**
</details>

<details>
  <summary>Running on WINDOWS, but can't access with other device [FIREWALL]</summary>
 
  > You probably have **FireWall ON** and Unconfigured.
  > For your safety, I'd recommand you to allow Python on private network and run the server when your network is Private.
  > IN SHORT: ALLOW PYTHON ON FIREWALL, RUN THE SERVER
 
  > *note: allowed on private but using public network on firewall will cause similar issue, you gotta make both same or allow python both on public and private*
</details>

# Thanks to:
1. https://github.com/bones7456/bones7456/blob/master/SimpleHTTPServerWithUpload.py (the guy who made upload possible)
2. https://gist.github.com/UniIsland/3346170 (the guy who made multiple file upload possible)
3. https://github.com/SethMMorton/natsort (sorting titles)
4. https://github.com/sandes/zipfly (*modified* lets you see the zip progress)
5. https://github.com/sampotts/plyr (*improved* video player)

***Disclaimer***: *the owner or the programmers or any content of this repository hold no responsibility for any kind of data loss or modification on your system and do not warrenty for such actions. I tried my best to prevent all sorts of ways (that I am currently aware of) to prevent data loss or unwanted data modification. See [Data Safety Measures](/DATA%20SAFETY.MD) taken on this projects to prevent unwanted data loss.*
