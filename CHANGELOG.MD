# Version 0.9.6
  ## Client-side Changes:
  * Fixed Logout button in account (No more Sword Art Online)
  * Updated Video Player and fixed the UI bugs. Key binding works.
  * Added MOV and MKV support for video player (if supported by browser)

  ## Server-side Changes:
  * **Core:** Added CORS policy setting method
  * **Core:** Improved control over logging (on startup details) [`_log_details`, `_get_details`]
  * **Core:** Removed `httpd` from global scope.
  * **Core:** Server can be initialized without starting the server [`init_server` -> use `init_server.run` to start server]. Previous `run(...)` will keep working as usual.
  * **Server** Improved upload process (using buffer limit to reduce RAM load)
  * **Server:** Improved security (naming files and renaming)
  * **Server:** Added QR support (needs implementation)
  * **Server:** Updated and improved databased package (pyroDB) with improved speed and application
  * **Server:** Added 7z support (if installed in device)
  * **Server:** Added QR code for easy access to the server (from terminal -q)

  ## Fixes:
  * Fixed video player
  * Fixed some zip issues
  * Fixed some upload issues

  ## TODO:
  * add zip in the dynamic island (maybe use session storage to store zip data)

# Version 0.9.5
  ## Client-side Changes:
  * Fixed unexpected upload cancel

  ## Server-side Changes:
  * Improved upload process (using thread and queue)

  ## Fixes:
  * Fixed upload being cancelled unexpectedly

  ## TODO:
  * add zip in the dynamic island (maybe use session storage to store zip data)

# Version 0.9.4
  ## Client-side Changes:
  * Nothing to notice

  ## Server-side Changes:
  * Improved code quality
  * Fixed zip, when empty folder has \ in name
  * Added security check for POST requests to prevent directory traversal

  ## Fixes:
  * Fixed zip, when empty folder has \ in name

  ## TODO:
  * add zip in the dynamic island (maybe use session storage to store zip data)


# Version 0.9.5
  ## Client-side Changes:
  * Fixed unexpected upload cancel

  ## Server-side Changes:
  * Improved upload proceess (using thread and queue)

  ## Fixes:
  * Fixed upload being cancelled unexpectedly

  ## TODO:
  * add zip in the dynamic island (maybe use session storage to store zip data)


# Version 0.9.4
  ## Client-side Changes:
  * Nothing to notice

  ## Server-side Changes:
  * Improved code quality
  * Fixed zip, when empty folder has \ in name
  * Added security check for POST requests to prevent directory traversal

  ## Fixes:
  * Fixed zip, when empty folder has \ in name

  ## TODO:
  * add zip in the dynamic island (maybe use session storage to store zip data)


# Version 0.9.3
  ## Client-side Changes:
  * Fixed zip downloader as a PWA
  * Now empty folders are included in zip

  ## Server-side Changes:
  * Support empty folders in zip
  * Added zip as a PWA

  ## Fixes:
  * Fixed zip downloader page
  * Fixed unwanted URL encoding in Top-nav
  * Video player page now uses innerHTML instead of innerText (error message was wrongly shown)

  ## TODO:
  * add zip in the dynamic island (maybe use session storage to store zip data)



# Version 0.9.2
  ## Client-side Changes:
  * Added optional Account system.
  * Converted the Entire website structure in single page mode (kinda PWA like)
  * Added dynamic island for uploading.
  * Fixed video player double tap
  * Added sidebar for user preference and admin panel
  * Admin can change user permission, add/remove user
  * UI reflects based on permissions

  ## Server-side Changes:
  * Using pyroDB database to store server data
  * added more methods
  * added permission system and flags

  ## Fixes:
  * fixed uploaded temp file with broken name

  ## TODO:
  * add zip in pwa system and dynamic island




# Version 0.8.1
  ## Client-side Changes:
  * Clicking on text files should show in UTF-8
  ## Server-side Changes:
  1. Added cookies
  2. Introduced  cache_control in send_file()
  3. Fixed multiple send_response() code issue
  4. Added  send_header_string()
  5. Text files now have `charset=utf-8` in header content-type
  ## Fixes:
  * text was not showing in UTF-8
  ## TODO:
  * make sidebar and user management
  * drag and drop upload in entire page (show drop here popup like GITHUB)



# Version 0.8.0
  ## Client-side Changes:
  * Zip page shows more info (Calculating notice)
  ## Server-side Changes:
  * (RENAMED) Server.py util files
  * Improved zip functionality and cache based speed boost
  ## Fixes:
  * While calculating zip size, client kept requesting zip size, which caused server to calculate zip size again and again
    * and make new zip instance again and again
  ## TODO:
  * Study hard, exam soon



# Version 0.7.4
  ## Client-side Changes:
  * Updated Error page (with http.cat 😸)
  ## Server-side Changes:
  * Server.py file is now separated into multiple files
    * `fs_utils.py` : File system utils
    * `server.py` : Server
    * `exceptions.py` : Exceptions
    * `arg_parser.py` : New Argument parser
    * `page_templates.py` : Page templates
    * `zipfly_local.py` : Zipfly local version
  * Added `--no-upload` and lots of other flags
  ## Fixes:
  * Fixed showing wrong port number
  ## TODO:
  * On flags, remove some right click options




# Version 0.7.1 - 0.7.3
  ## Client-side Changes:
  * Nothing to notice
  ## Server-side Changes:
  * Nothing to notice
  ## Fixes:
  * Fixed "send_txt" function not working



# Version 0.7.0
  ## Client-side Changes:
  * Video plater page shows title of video
  * Video player page predicts whether video is playable or not by Browser
  ## Server-side Changes:
  * Added manual password, use `--password` or `-k` flag to set password
  * Using pyroboxCore as External module
  * all prints are now using `logger.log|info|warn|error|debug` instead of `print`
  * `TODO`: To change log level, use `--log-level` or `-l` flag
  * To change log level programmatically, use `pyroboxCore.logger.setLevel(logging.DEBUG|INFO|WARN|ERROR)`
  * REMOVED `pyrobox.clone` module (stil available in `dev_src` folder)
  * The Entire server is now using `@SimpleHTTPRequestHandler.on_req` decorator importing from pyroboxCore to handle requests 
    ### check v0.6.1 for more info
  * added send_file function to pyroboxCore
  * improved POST request handling

  ## Fixes:
  * FIXED Python 3.7 support
  * Fixed Video player text issue https://github.com/RaSan147/pyrobox/issues/70
  * Fixed zip download not working
  * Fixed many bugs
------------------------------------------------------------------------
------------------------------------------------------------------------


# Version 0.6.9
  ## Client-side Changes:
  * Nothing to notice
  ## Server-side Changes:
  * Nothing to notice
  ## Fixes:
  * Forgot to increment version number in `server.py`

------------------------------------------------------------------------
------------------------------------------------------------------------

# Version 0.6.8
  ## Client-side Changes:
  * Nothing to notice
  ## Server-side Changes:
  * Nothing to notice
  ## Fixes:
  * Reload_server button now works

------------------------------------------------------------------------
------------------------------------------------------------------------

# Version 0.6.7
  ## Client-side Changes:
  * Nothing to notice
  ## Server-side Changes:
  * Nothing to notice
  ## Fixes:
  * Added requests in requirements

------------------------------------------------------------------------
------------------------------------------------------------------------

# Version 0.6.6
  ## Client-side Changes:
  * Nothing to notice
  ## Server-side Changes:
  * os.scandir() -> item.is_dir to item.is_dir()
  ## Fixes:
  * Fixed where files had "/" at the end of their name

------------------------------------------------------------------------
------------------------------------------------------------------------

# Version 0.6.5
  ## Client-side Changes:
  * Folder info view now recieved a huge speed boost
  * Any file can be downloaded via R-Click -> Download
  * Updated some emojis
  ## Server-side Changes:
  * moving towards pyroboxCore for future updates
  * Using os.scandir() instead of os.listdir() for speed boost
  * Post request handling is now done more cleanly, like how form data works
  ## Fixes:
  * Nothing to notice since 0.6.4

------------------------------------------------------------------------
------------------------------------------------------------------------


# Version 0.6.4
  ## Client-side Changes:
  * Nothing to notice
  ## Server-side Changes:
  * HOTFIX: run_update is using `--user` flag due to permission issues
  ## Fixes:
  * fixed update not working due to permission issues


------------------------------------------------------------------------
------------------------------------------------------------------------


# Version 0.6.3
  ## Client-side Changes:
  * Nothing to notice
  ## Server-side Changes:
  * HOTFIX: log_message now works like print funtion (*args), not like logger.log(format, *args)
  ## Fixes:
  * fixed log_message not working


------------------------------------------------------------------------
------------------------------------------------------------------------

# Version 0.6.2
  ## Client-side Changes:
  * Nothing to notice
  ## Server-side Changes:
  * HOTFIX: added `action="?upload"` to upload form
  ## Fixes:
  * fixed upload form not working due to missing `action="?upload"` which is required for POST requests


------------------------------------------------------------------------
------------------------------------------------------------------------

# Version 0.6.1
  ## Client-side Changes:
  * Nothing to notice
  ## Server-side Changes:
  * Completely changed server structure, now using` @SimpleHTTPRequestHandler.on_req` decorator to handle requests.
    ### `@SimpleHTTPRequestHandler.on_req(request_type, conditions)`
  * request_type: GET, POST, HEAD # use HEAD instead of GET since it will be called in get anyway **must**
  * conditions: url, query, fragment
  * sends `return func(self, url_path=url_path, query=query, fragment=fragment, path=path, spathsplit=spathsplit)` to the function.
    * self: SimpleHTTPRequestHandler
    * url_path: url path (no query, no fragment)
    * query: query dict (custom_dict)
    * fragment: fragment (excluding #)
    * path: Translated path (the actual path on OS file system)
    * spathsplit: path split (list)
  * Improved POST request handling (maybe)
  * IMPROVED update with pip on server
  * Server prints ==== request_id ==== on every request
    * `==` : start
    * `++` : request handling
    * `--` : end
    * `##` : separator
  * Update will print log on console
  ## Fixes:
  * zip download now works (used to keep reloading and downloading)
  * Removed New folder creation with '../' in name [Security concern](/SECURITY%20PLAN.MD)
  * maybe some more that I forgot
