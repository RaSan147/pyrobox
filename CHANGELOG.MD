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
