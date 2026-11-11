# Pyrobox Security & Code Quality Audit Report

A comprehensive security and code quality audit of the **Pyrobox** codebase was performed, analyzing the **source code architecture**, **HTTP API endpoints**, and static analysis results via **Ruff** (run in `dev_src`).

---

# Executive Summary

Pyrobox provides lightweight web-based file management, media playback, text editing, and folder archiving. However, several architectural and endpoint-level security deficiencies were identified:
- **Critical / High Risks**: Missing authorization enforcement on file operations (bypassing path-restriction ACLs), Stored XSS via usernames in the Admin interface leading to session takeover, Cross-Site Request Forgery (CSRF) on state-changing administrative operations exposed via HTTP `GET`/`HEAD`, plaintext password transmission in query parameters, weak single-round SHA-256 password hashing with a static salt, unrotated tokens with no server-side invalidation, and lack of transport encryption (cleartext HTTP).
- **Medium / Low Risks**: Synchronous sub-process executions causing thread exhaustion (DoS), unbounded memory allocations (`subtitle_location_map`), information disclosure (serving `.pdb` database files or `.git` directories if placed within the served directory), and missing standard HTTP defense headers.

---

# 1. Source Code & Architecture Audit

### 1.1 Insecure Session Management & Token Architecture
* **Severity**: **High**
* **CWE**: [CWE-384 (Session Fixation)](https://cwe.mitre.org/data/definitions/384.html), [CWE-613 (Insufficient Session Expiration)](https://cwe.mitre.org/data/definitions/613.html), [CWE-1004 (Sensitive Cookie Without 'HttpOnly' Flag)](https://cwe.mitre.org/data/definitions/1004.html)
* **Affected Files**: [`user_mgmt.py`](file:///p:/C_coding/Python/pyrobox/dev_src/user_mgmt.py#L240-L255), [`pyroboxCore.py`](file:///p:/C_coding/Python/pyrobox/dev_src/pyroboxCore.py#L1000-L1010)
* **Mechanics & Finding**:
  1. **Static Tokens**: In [`user_mgmt.py:L243`](file:///p:/C_coding/Python/pyrobox/dev_src/user_mgmt.py#L243), a token is generated only once when the user is created:
     ```python
     token = hashlib.sha256(p_hash + str(time.time()).encode()).digest()
     ```
     When a user logs in via `server_login()`, no new session token is created; the old token is re-issued.
  2. **No Server-Side Invalidation on Logout**: In [`server.py:L1284-L1293`](file:///p:/C_coding/Python/pyrobox/dev_src/server.py#L1284-L1293), logging out merely asks the client browser to delete its cookie (`clear_user_cookie()`). The token stored in the server database remains completely valid. An attacker who steals a token retains permanent access.
  3. **Insecure Cookie Attributes**: In [`user_mgmt.py:L664-L680`](file:///p:/C_coding/Python/pyrobox/dev_src/user_mgmt.py#L664-L680), cookies are issued with a 1-year lifespan but lack `HttpOnly`, `SameSite`, and `Secure` attributes:
     ```python
     cookie["token"] = user.token_hex
     cookie["token"]["expires"] = 365 * 86400
     cookie["token"]["path"] = "/"
     ```
     Any XSS vulnerability allows instant exfiltration of `token` via `document.cookie`.
* **Remediation**:
  - Issue ephemeral session IDs stored with expiry timestamps in memory or database.
  - Invalidate sessions on the server upon `logout`.
  - Set `HttpOnly=True`, `SameSite="Lax"` (or `"Strict"`), and `Secure=True` (when running over TLS).

---

### 1.2 Cryptographic Weakness in Password Storage
* **Severity**: **High**
* **CWE**: [CWE-916 (Use of Password Hash With Insufficient Computational Effort)](https://cwe.mitre.org/data/definitions/916.html), [CWE-760 (Use of Hard-coded, Shared Salt)](https://cwe.mitre.org/data/definitions/760.html)
* **Affected Files**: [`user_mgmt.py`](file:///p:/C_coding/Python/pyrobox/dev_src/user_mgmt.py#L237-L248), [`user_mgmt.py:L454`](file:///p:/C_coding/Python/pyrobox/dev_src/user_mgmt.py#L454)
* **Mechanics & Finding**:
  - Passwords are encrypted using a single round of SHA-256 with a hardcoded static salt:
    ```python
    self.common_salt = "0123456789"
    def salt_password(self, password) -> bytes:
        return hashlib.sha256((self.user_handler.common_salt + password).encode('utf-8')).digest()
    ```
  - Standard SHA-256 without a dynamic per-user salt or key-stretching (like Argon2id, bcrypt, or PBKDF2) allows rapid cracking of leaked database entries via GPU-based dictionary or rainbow table attacks.
* **Remediation**:
  - Replace custom SHA-256 hashing with `hashlib.scrypt` or the standard `bcrypt` / `argon2` algorithms with unique, cryptographically random per-user salts.

---

### 1.3 Path Restriction Authorization Bypass (IDOR/BOLA on File Mutations)
* **Severity**: **High**
* **CWE**: [CWE-285 (Improper Authorization)](https://cwe.mitre.org/data/definitions/285.html), [CWE-639 (Authorization Bypass Through User-Controlled Key)](https://cwe.mitre.org/data/definitions/639.html)
* **Affected Files**: [`server.py`](file:///p:/C_coding/Python/pyrobox/dev_src/server.py#L1491-L1840), [`pyrobox_ServerHost.py`](file:///p:/C_coding/Python/pyrobox/dev_src/pyrobox_ServerHost.py#L240-L250)
* **Mechanics & Finding**:
  - In [`ServerHost.do_HANDLE`](file:///p:/C_coding/Python/pyrobox/dev_src/pyrobox_ServerHost.py#L240-L250), incoming requests are checked against path restrictions:
    ```python
    req_path = urllib.parse.urlsplit(self.path).path
    if user and not user.is_path_allowed(req_path):
        self.send_error(HTTPStatus.NOT_FOUND, "File not found", cookie=cookie)
        return
    ```
  - However, for POST requests (`?upload`, `?del-f`, `?del-p`, `?rename`, `?info`, `?new_folder`, `?save-file`), the HTTP request URL is typically the root path `/` or parent directory, while the actual target file is supplied inside the POST body (e.g. form field `name` or `filename`).
  - None of the POST action handlers (`del_2_recycle`, `del_permanently`, `rename_content`, `get_info`, `new_folder`, `upload`) call `user.is_path_allowed(rltv_path)`.
  - **Impact**: A user configured with restricted folder access (e.g., allowed only in `/uploads/`) can delete, rename, inspect, or write files in unrestricted directories (e.g. `/secret/important.txt`) by sending POST operations.
* **Remediation**:
  - Enforce `user.is_path_allowed(target_rel_path)` on every endpoint before executing file read, write, rename, or deletion operations.

---

### 1.4 Insecure Defaults: Unauthenticated Write/Delete in Default Server Mode
* **Severity**: **Medium**
* **CWE**: [CWE-276 (Incorrect Default Permissions)](https://cwe.mitre.org/data/definitions/276.html), [CWE-1188 (Insecure Default Initialization of Resource)](https://cwe.mitre.org/data/definitions/1188.html)
* **Affected Files**: [`pyrobox_ServerHost.py`](file:///p:/C_coding/Python/pyrobox/dev_src/pyrobox_ServerHost.py#L168-L175), [`_arg_parser.py`](file:///p:/C_coding/Python/pyrobox/dev_src/_arg_parser.py#L10)
* **Mechanics & Finding**:
  - If started without `--server-name`, the server defaults to guest mode where visitors have `VIEW`, `DOWNLOAD`, `UPLOAD`, `ZIP`, `MODIFY`, and `DELETE` permissions enabled.
  - File upload is gated by a global password, which defaults to `"SECret"` ([`_arg_parser.py:L10`](file:///p:/C_coding/Python/pyrobox/dev_src/_arg_parser.py#L10)).
* **Remediation**:
  - Set default permissions to read-only (`VIEW`, `DOWNLOAD`) for unauthenticated guests.
  - Require the user to supply an explicit password rather than falling back to `"SECret"`.

---

### 1.5 Boolean Inversion in Size Limit Check
* **Severity**: **Medium**
* **CWE**: [CWE-697 (Incorrect Comparison)](https://cwe.mitre.org/data/definitions/697.html)
* **Affected Files**: [`pyroboxCore.py:L2283-L2291`](file:///p:/C_coding/Python/pyrobox/dev_src/pyroboxCore.py#L2283-L2291)
* **Mechanics & Finding**:
  ```python
  def check_size_limit(self, max_size=-1):
      if not max_size < 0 or self.content_length <= max_size:
          raise PostError(f"Content size limit exceeded: {self.content_length} > {max_size}")
  ```
  - In Python, `not max_size < 0` binds before `or`. If `max_size` is non-negative (e.g., 5000), `not max_size < 0` is `True`, causing `check_size_limit` to always raise an exception regardless of actual size.
* **Remediation**:
  - Correct operator precedence: `if not (max_size < 0 or self.content_length <= max_size):` or `if max_size >= 0 and self.content_length > max_size:`.

---

# 2. API Endpoint & Web Security Audit

### 2.1 Stored Cross-Site Scripting (XSS) in Admin Management
* **Severity**: **Critical**
* **CWE**: [CWE-79 (Improper Neutralization of Input During Web Page Generation)](https://cwe.mitre.org/data/definitions/79.html)
* **Affected Endpoints**: `POST /?do_signup`, `GET /?admin`, `GET /?get_users`
* **Affected Files**: [`script_admin_page.js`](file:///p:/C_coding/Python/pyrobox/dev_src/script_admin_page.js#L112-L115), [`script_admin_page.js:L342`](file:///p:/C_coding/Python/pyrobox/dev_src/script_admin_page.js#L342)
* **Mechanics**:
  1. In `handle_signup_post` ([`server.py:L1447`](file:///p:/C_coding/Python/pyrobox/dev_src/server.py#L1447)), usernames are accepted with no character sanitization.
  2. In `display_users()` ([`script_admin_page.js:L113`](file:///p:/C_coding/Python/pyrobox/dev_src/script_admin_page.js#L113)):
     ```javascript
     row.innerHTML = "<td>" + this.user_list[i] + "</td><td><div class='pagination' onclick='admin_tools.manage_user(" + i + ")'>Manage</div></td></td><td>";
     ```
  3. In `manage_user()` ([`script_admin_page.js:L342`](file:///p:/C_coding/Python/pyrobox/dev_src/script_admin_page.js#L342)):
     ```javascript
     var client_page_script = `... var username = "${username}"; ...`;
     popup_msg.open_popup(client_page_html, client_page_script);
     ```
     `open_popup` injects `client_page_script` directly into a newly created `<script>` element.
* **Impact**: An attacker registers with a payload like `test";alert(document.cookie);//`. When an administrator visits the admin user panel, the script executes with administrator privileges, capable of extracting tokens or issuing admin commands.
* **Remediation**:
  - Enforce strict alphanumeric regex validation on usernames (`^[a-zA-Z0-9_.-]{3,32}$`).
  - Use `textContent` or `document.createTextNode` instead of string interpolation into `innerHTML`.
  - Pass user data to popup handlers via JavaScript parameters or data attributes rather than string concatenation into executable script bodies.

---

### 2.2 Cross-Site Request Forgery (CSRF) on Administrative Actions
* **Severity**: **High**
* **CWE**: [CWE-352 (Cross-Site Request Forgery)](https://cwe.mitre.org/data/definitions/352.html)
* **Affected Endpoints**:
  - `GET /?add_user`
  - `GET /?delete_user`
  - `GET /?update_user_perm`
  - `GET /?reload`
  - `GET /?shutdown`
* **Affected Files**: [`server.py`](file:///p:/C_coding/Python/pyrobox/dev_src/server.py#L264-L470)
* **Mechanics**:
  - These state-changing administrative operations are registered under `@SH.on_req('HEAD', ...)` and respond to standard HTTP `GET` requests without CSRF protection tokens or `SameSite` cookies.
  - An external webpage viewed by an authenticated administrator can initiate requests such as:
    ```html
    <img src="http://pyrobox-host:45454/?delete_user&username=victim">
    <img src="http://pyrobox-host:45454/?shutdown">
    ```
* **Remediation**:
  - Convert all state-changing endpoints to HTTP `POST`.
  - Implement Anti-CSRF tokens for all state-changing requests and enforce `SameSite=Lax` or `Strict` on cookies.

---

### 2.3 Plaintext Credential Exposure in URL Parameters
* **Severity**: **Medium**
* **CWE**: [CWE-598 (Use of GET Request Method With Sensitive Query Strings)](https://cwe.mitre.org/data/definitions/598.html)
* **Affected Endpoints**: `GET /?add_user&username=...&password=...&perms=...`
* **Affected Files**: [`server.py:L408-L410`](file:///p:/C_coding/Python/pyrobox/dev_src/server.py#L408-L410)
* **Mechanics**:
  - Creating a user passes the password directly in the query string:
    ```python
    username = self.query.get("username", [None])[0]
    password = self.query.get("password", [None])[0]
    ```
  - Query strings are logged in plaintext in server logs, browser history, proxy logs, and `Referer` headers.
* **Remediation**:
  - Migrate user creation to `POST` with a JSON or form-data payload in the request body.

---

### 2.4 Denial of Service (DoS) via Synchronous Workloads & Unbounded Structures
* **Severity**: **Medium**
* **CWE**: [CWE-400 (Uncontrolled Resource Consumption)](https://cwe.mitre.org/data/definitions/400.html)
* **Affected Endpoints**:
  - `GET /path?size_n_count` ([`server.py:L523`](file:///p:/C_coding/Python/pyrobox/dev_src/server.py#L523))
  - `GET /path?vid&vid-data` ([`server.py:L728`](file:///p:/C_coding/Python/pyrobox/dev_src/server.py#L728))
  - `GET /?qr=...` ([`server.py:L237`](file:///p:/C_coding/Python/pyrobox/dev_src/server.py#L237))
* **Mechanics**:
  1. `?size_n_count` triggers a synchronous recursive tree walk over entire directory structures on the request thread.
  2. `?vid&vid-data` triggers synchronous `ffmpeg` process executions via `extract_subtitles_from_file()`, blocking request worker threads.
  3. `subtitle_location_map` ([`server.py:L725`](file:///p:/C_coding/Python/pyrobox/dev_src/server.py#L725)) is a global dict that appends UUID-to-path mappings without eviction or TTL, causing progressive memory leaks.
  4. `?qr` generates and saves a separate SVG file on disk for each unique URL without size limits or garbage collection.
* **Remediation**:
  - Offload heavy operations to asynchronous workers or rate-limit invocations.
  - Implement an LRU cache or TTL-based expiry for `subtitle_location_map` and temporary QR assets.

---

### 2.5 Reflected/DOM Attribute Injection in Breadcrumb Navigation
* **Severity**: **Low / Medium**
* **CWE**: [CWE-79 (Cross-Site Scripting)](https://cwe.mitre.org/data/definitions/79.html)
* **Affected Files**: [`_fs_utils.py:L342-L362`](file:///p:/C_coding/Python/pyrobox/dev_src/_fs_utils.py#L342-L362), [`pyroboxCore.py:L1993`](file:///p:/C_coding/Python/pyrobox/dev_src/pyroboxCore.py#L1993)
* **Mechanics**:
  - In `dir_navigator()`:
    ```python
    tag = "<a class='dir_turns' href='" + urls[i] + "'>" + names[i] + "</a>"
    ```
  - `get_displaypath()` uses `html.escape(displaypath, quote=False)`, leaving single quotes (`'`) unescaped. Directory names containing `'` break out of the single-quoted `href` attribute.
* **Remediation**:
  - Use `html.escape(..., quote=True)` whenever values are inserted into HTML attributes.

---

### 2.6 Username Enumeration & Lack of Login Rate Limiting
* **Severity**: **Low**
* **CWE**: [CWE-204 (Observable Response Discrepancy)](https://cwe.mitre.org/data/definitions/204.html), [CWE-307 (Improper Restriction of Excessive Authentication Attempts)](https://cwe.mitre.org/data/definitions/307.html)
* **Affected Endpoints**: `POST /?do_login` ([`server.py:L1408-L1445`](file:///p:/C_coding/Python/pyrobox/dev_src/server.py#L1408-L1445))
* **Mechanics**:
  - The endpoint explicitly distinguishes between `"User not found"` and `"Wrong password"`.
  - There is no rate limiting, exponential backoff, or temporary account lock on failed attempts.
* **Remediation**:
  - Return a generic error message: `"Invalid username or password"`.
  - Introduce an IP- or user-based rate limiter on authentication attempts.

---

### 2.7 Missing HTTP Security Headers
* **Severity**: **Low**
* **CWE**: [CWE-693 (Protection Mechanism Failure)](https://cwe.mitre.org/data/definitions/693.html)
* **Affected Files**: [`pyroboxCore.py`](file:///p:/C_coding/Python/pyrobox/dev_src/pyroboxCore.py#L1025-L1035)
* **Mechanics**:
  - Responses do not include standard defense-in-depth headers:
    - `X-Content-Type-Options: nosniff` (allows MIME-sniffing attacks on user-uploaded files).
    - `X-Frame-Options: SAMEORIGIN` / `Content-Security-Policy: frame-ancestors ...` (susceptible to Clickjacking).
    - `Content-Security-Policy` (CSP).
* **Remediation**:
  - Add standard security headers in `SimpleHTTPRequestHandler.end_headers()`:
    ```python
    self.send_header('X-Content-Type-Options', 'nosniff')
    self.send_header('X-Frame-Options', 'SAMEORIGIN')
    self.send_header('Referrer-Policy', 'strict-origin-when-cross-origin')
    ```

---

# Summary Matrix

| ID | Vulnerability | Location | Severity | CWE |
|---|---|---|---|---|
| **2.1** | Stored XSS in Admin Page via Unsanitized Usernames | `script_admin_page.js`, `server.py` | **Critical** | CWE-79 |
| **1.3** | Path Restriction Authorization Bypass on POST Mutations | `server.py` (`del-f`, `del-p`, `rename`, `upload`, etc.) | **High** | CWE-285, CWE-639 |
| **2.2** | CSRF on Sensitive Admin Operations via HTTP GET | `server.py` (`?add_user`, `?delete_user`, `?reload`, etc.) | **High** | CWE-352 |
| **1.1** | Weak Session Tokens, Missing Invalidation, Insecure Cookies | `user_mgmt.py`, `server.py` | **High** | CWE-384, CWE-613, CWE-1004 |
| **1.2** | Single-Round SHA-256 with Static Salt Password Hashing | `user_mgmt.py` | **High** | CWE-916, CWE-760 |
| **2.3** | Plaintext Password Transmission in Query Parameters | `server.py` (`?add_user`) | **Medium** | CWE-598 |
| **1.4** | Insecure Defaults (Default upload password, guest permissions) | `pyrobox_ServerHost.py`, `_arg_parser.py` | **Medium** | CWE-276, CWE-1188 |
| **1.5** | Operator Precedence Logic Bug in Content Size Limit | `pyroboxCore.py` | **Medium** | CWE-697 |
| **2.4** | Resource Exhaustion (DoS) via Sync FFmpeg & Tree Walks | `server.py`, `_sub_extractor.py` | **Medium** | CWE-400 |
| **2.5** | Attribute Injection / DOM XSS in Navigation Breadcrumbs | `_fs_utils.py`, `pyroboxCore.py` | **Low** | CWE-79 |
| **2.6** | User Enumeration and No Brute-Force Rate Limiting | `server.py` (`?do_login`) | **Low** | CWE-204, CWE-307 |
| **2.7** | Missing Security Headers (`nosniff`, `frame-ancestors`) | `pyroboxCore.py` | **Low** | CWE-693 |

---

# 3. Static Analysis & Ruff Scan Audit (`dev_src`)

A **Ruff scan** was executed with working directory `p:\C_coding\Python\pyrobox\dev_src`.

### 3.1 Standard Linter Results (`ruff check .`)

Ruff reported **13 errors** under standard rules:

| Rule | Location | Line | Code Snippet | Issue Description |
|---|---|---|---|---|
| **E711** | `_list_maker.py` | 124 | `if path == None:` | Comparison to `None` should use `is None` |
| **E712** | `_list_maker.py` | 167 | `if user.NOPERMISSION or user.VIEW == False:` | Avoid comparison to `False`; use `not user.VIEW` |
| **E713** | `pyroDB2.py` | 984 | `if not key in self.db:` | Convert membership test to `key not in self.db` |
| **E712** | `pyroDB2.py` | 1426 | `if exist_ok == True or exist_ok == "name":` | Avoid comparison to `True`; use `bool(exist_ok)` |
| **E712** | `pyroDB2.py` | 1448 | `if exist_ok == True:` | Avoid comparison to `True`; use `bool(exist_ok)` |
| **E713** | `pyroDB2.py` | 3006 | `if not (col in columns_names):` | Convert membership test to `col not in columns_names` |
| **E713** | `pyroDB3.py` | 1036 | `if not key in self.db:` | Convert membership test to `key not in self.db` |
| **E712** | `pyroDB3.py` | 1689 | `if exist_ok == True or exist_ok == "name":` | Avoid comparison to `True`; use `bool(exist_ok)` |
| **E712** | `pyroDB3.py` | 1711 | `if exist_ok == True:` | Avoid comparison to `True`; use `bool(exist_ok)` |
| **E713** | `pyroDB3.py` | 3329 | `if not (col in columns_names):` | Convert membership test to `col not in columns_names` |
| **E713** | `pyroboxCore.py` | 2436 | `if not self.boundary in line:` | Convert membership test to `self.boundary not in line` |
| **E711** | `pyroboxCore.py` | 2739 | `addr = (bind if bind != None else '', port)` | Comparison to `None` should use `is not None` |
| **E712** | `pyrobox_ServerHost.py` | 257 | `if user.NOPERMISSION or user.VIEW == False:` | Avoid comparison to `False`; use `not user.VIEW` |

### 3.2 Security & Bugbear Findings (`ruff check . --select S,B`)

Running with flake8-bandit (`S`) and flake8-bugbear (`B`) revealed additional security-relevant findings:

1. **Weak Hashing Algorithms (`S324`)**:
   - `user_mgmt.py:L460`: `self.common_salt = hashlib.md5(sys_Pass).hexdigest()` - Insecure use of MD5.
   - `user_mgmt.py:L478`: `uid = hashlib.sha1((str(time.time()) + username).encode("utf-8")).hexdigest()` - Insecure use of SHA-1.
2. **Hardcoded Test Passwords (`S106`)**:
   - `user_mgmt.py:L700`: `z = user_handler.server_signup(username="Admin", password="pass")` - Hardcoded credential in test/module scope.
3. **Silenced Exceptions (`S110`)**:
   - Multiple `try-except-pass` blocks without logging in `upload_clone.py` (lines 86, 110, 145, 199, 238, 282, 316, 356, 375, 403, 409) that mask connection and permission errors.
4. **Unused Loop Variables (`B007`)**:
   - Multiple unused iteration variables in `upload_clone.py` (lines 169, 262, 340, 349: `for full, rel in files:` where `full` is unused).

### 3.3 Recommended Actions for Ruff Findings
- 5 safe errors can be fixed automatically with:
  ```bash
  ruff check . --fix
  ```
- Equality comparisons to `True`/`False` (`E712`) on custom objects (`user.VIEW`, `exist_ok`) should be manually rewritten to `not user.VIEW` or explicit boolean casts to preserve intended object semantics.