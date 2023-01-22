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
    * `##` : seperator
  * Update will print log on console
  ## Fixes:
  * zip download now works (used to keep reloading and downloading)
  * Removed New folder creation with '../' in name [Security concern](/SECURITY%20PLAN.MD)
  * maybe some more that i forgot
