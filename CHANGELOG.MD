# Version 0.6.6
  ## Client-side Changes:
  * Nothing to notice
  ## Server-side Changes:
  * Nothing to notice
  ## Fixes:
  * Added requests in requirements


# Version 0.6.6
  ## Client-side Changes:
  * Nothing to notice
  ## Server-side Changes:
  * os.scandir() -> item.is_dir to item.is_dir()
  ## Fixes:
  * Fixed where files had "/" at the end of their name


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



-----------------------------------------------------------------------


# Version 0.6.4
  ## Client-side Changes:
  * Nothing to notice
  ## Server-side Changes:
  * HOTFIX: run_update is using `--user` flag due to permission issues
  ## Fixes:
  * fixed update not working due to permission issues


------------------------------------------------------------------------


# Version 0.6.3
  ## Client-side Changes:
  * Nothing to notice
  ## Server-side Changes:
  * HOTFIX: log_message now works like print funtion (*args), not like logger.log(format, *args)
  ## Fixes:
  * fixed log_message not working


------------------------------------------------------------------------

# Version 0.6.2
  ## Client-side Changes:
  * Nothing to notice
  ## Server-side Changes:
  * HOTFIX: added `action="?upload"` to upload form
  ## Fixes:
  * fixed upload form not working due to missing `action="?upload"` which is required for POST requests


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
