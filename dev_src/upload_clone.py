"""push_clone.py
Reverse clone: upload local folder contents to a pyrobox server

Usage example:
  python push_clone.py --url http://host:6969/path/ --local ./myfiles --password SECRET --workers 6

The script walks the local folder and uploads files as multipart/form-data to the server's ?upload endpoint.
It mimics the browser form by sending fields:
  post-type=upload, password=<password>, and file[] entries with the filename set to the relative path.

This is a best-effort, simple uploader compatible with the server upload handler in dev_src/server.py.
"""

import os
import sys
import argparse
import threading
import mimetypes
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, urlunparse, quote

import requests
import getpass

# no-op debug variable removed; keep file clean


def iter_files(base_path, ignore_hidden=False):
    """Yield (full_path, rel_path) for every file under base_path."""
    base_path = os.path.abspath(base_path)
    for root, dirs, files in os.walk(base_path):
        if ignore_hidden:
            # filter hidden dirs in-place so walk won't descend into them
            dirs[:] = [d for d in dirs if not d.startswith('.')]
        for f in files:
            if ignore_hidden and f.startswith('.'):
                continue
            full = os.path.join(root, f)
            rel = os.path.relpath(full, base_path).replace('\\', '/')
            yield full, rel


def upload_file(session, upload_url, full_path, rel_path, password, timeout=60, retries=3, retry_delay=2, base_dir_url=None):
    """Upload a single file with retry.

    If base_dir_url is provided, performs a HEAD request to check remote Content-Length and skips upload when sizes match.
    Returns: (rel_path, success_bool, status_code_or_None, message)
    """
    data = {'post-type': 'upload', 'password': password}

    # existence check based on server JSON ?size endpoint (fallback to HEAD Content-Length)
    if base_dir_url:
        # try JSON size API first: GET on file?size
        try:
            parts = [quote(p) for p in rel_path.lstrip('/').split('/')]
            qpath = '/'.join(parts)
            size_url = base_dir_url.rstrip('/') + '/' + qpath + '?size'
            r = session.get(size_url, timeout=8)
            if r.status_code == 200:
                try:
                    j = r.json()
                    # server returns {"status":1, "byte": size, ...}
                    remote_size = int(j.get('byte', 0))
                    local_size = os.path.getsize(full_path)
                    if remote_size == local_size:
                        return rel_path, True, 200, 'Exists'
                except Exception:
                    pass
        except Exception:
            pass

        # fallback to HEAD content-length
        try:
            parts = [quote(p) for p in rel_path.lstrip('/').split('/')]
            qpath = '/'.join(parts)
            head_url = base_dir_url.rstrip('/') + '/' + qpath
            h = session.head(head_url, timeout=10, allow_redirects=True)
            if h.status_code == 200 and 'content-length' in h.headers:
                try:
                    remote_size = int(h.headers.get('content-length', 0))
                    local_size = os.path.getsize(full_path)
                    if remote_size == local_size:
                        return rel_path, True, 200, 'Exists'
                except Exception:
                    pass
        except Exception:
            # ignore HEAD failures
            pass

    attempt = 0
    last_err = None
    import time as _time
    while attempt < retries:
        attempt += 1
        # open file for this attempt so requests can stream and close safely
        fileobj = open(full_path, 'rb')
        files = {'file[]': (rel_path, fileobj, mimetypes.guess_type(full_path)[0] or 'application/octet-stream')}
        try:
            r = session.post(upload_url, data=data, files=files, timeout=timeout)
            return rel_path, r.ok, r.status_code, r.text
        except Exception as e:
            last_err = e
            if attempt < retries:
                _time.sleep(retry_delay)
                continue
            return rel_path, False, None, str(e)
        finally:
            try:
                fileobj.close()
            except Exception:
                pass


def main():
    parser = argparse.ArgumentParser(description='Push (upload) a local folder to a pyrobox server')
    parser.add_argument('--url', required=False, help='Base URL of target server (include path where files should be uploaded). Example: http://host:6969/folder/')
    parser.add_argument('--local', '-l', required=False, help='Local directory to upload')
    parser.add_argument('--password', '-p', required=False, help='Upload password for the server (if not provided you will be prompted)')
    parser.add_argument('--username', '-u', required=False, help='Username to login as before uploading (optional). If provided, the script will POST to ?do_login to obtain cookies.')
    parser.add_argument('--workers', '-w', type=int, default=6, help='Number of concurrent uploads')
    parser.add_argument('--retries', type=int, default=3, help='Number of attempts per file on error')
    parser.add_argument('--retry-delay', type=float, default=2.0, help='Seconds to wait between retries')
    parser.add_argument('--ignore-hidden', action='store_true', help='Ignore hidden files and directories')
    parser.add_argument('--dry-run', action='store_true', help="Don't actually upload, just list files that would be uploaded")
    parser.add_argument('--batch-size', type=int, default=1, help='Number of files to include in a single multipart POST (1 = no batching)')
    parser.add_argument('--yes', '-y', action='store_true', help='Assume yes for confirmations')
    args = parser.parse_args()

    # Interactive prompts when required args aren't supplied
    if not args.url or not args.local:
        print('Interactive push-clone: enter target server details')
        if not args.url:
            args.url = input('Server URL (e.g. http://host:6969/target/path/): ').strip()
        if not args.local:
            args.local = input('Local folder to upload: ').strip()
        if not args.username:
            un = input('Username (leave empty to skip login): ').strip()
            args.username = un or None
        if not args.password:
            args.password = getpass.getpass(prompt='Password (upload or account password): ')
        w = input(f'Workers (concurrent uploads) [{args.workers}]: ').strip()
        if w:
            try:
                args.workers = int(w)
            except Exception:
                pass
        ih = input('Ignore hidden files/directories? (y/N): ').strip().lower()
        args.ignore_hidden = ih in ('y', 'yes')
        dr = input("Dry run (list files only) ? (y/N): ").strip().lower()
        args.dry_run = dr in ('y', 'yes')

    base = args.local
    if not os.path.isdir(base):
        print(f"Local path not found or not a directory: {base}")
        sys.exit(2)

    # server upload endpoint is '?upload' appended to target path
    upload_url = args.url
    # ensure trailing slash so urljoin works with relative filenames if needed
    if not upload_url.endswith('/'):
        upload_url += '/'
    # requests should post to '?upload' query param
    upload_url = upload_url + '?upload'

    files = list(iter_files(base, ignore_hidden=args.ignore_hidden))
    print(f"Found {len(files)} files to upload under {base}")
    if args.dry_run:
        print('Dry run mode — listing files:')
        for full, rel in files:
            print(rel)
        return

    # Ask for confirmation before proceeding (unless --yes)
    if not args.yes:
        # default to yes (press Enter to proceed)
        confirm = input(f"Proceed to upload {len(files)} files to {args.url}? (Y/n): ").strip().lower()
        if confirm in ('n', 'no'):
            print('Aborted by user')
            return
    # determine password (prompt if not supplied)
    if not args.password:
        # prompt securely
        args.password = getpass.getpass(prompt='Upload password (server password or account password): ')

    # prepare session and detect whether server requires login
    session = requests.Session()

    # normalize base url (without query)
    parsed = urlparse(args.url)
    base_dir_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path if parsed.path else '/', '', '', ''))

    def server_requires_login():
        """Return True if server appears to require a logged-in account (login page or 401)."""
        # Prefer checking the upload endpoint first with HEAD: if it returns 401/403, login required
        try:
            h = session.head(upload_url, timeout=8, allow_redirects=True)
            if h.status_code in (401, 403):
                return True
        except Exception:
            # if HEAD failed, fall back to directory GET below
            pass

        # Fallback: check directory HTML for a login form marker — but treat this as heuristic only
        try:
            r = session.get(base_dir_url, timeout=10)
        except Exception:
            return False

        if r.status_code in (401, 403):
            return True

        body = r.text.lower()
        # look for explicit username/password form fields together
        if ('name="username"' in body or "name='username'" in body) and 'password' in body and '<form' in body:
            return True

        return False

    def do_login(username, password):
        """Attempt to login via ?do_login. Returns True on success and cookies are kept in session."""
        login_url = base_dir_url.rstrip('/') + '/?do_login'
        data = {
            'post-type': 'login',
            'username': username,
            'password': password,
        }
        try:
            r = session.post(login_url, data=data, timeout=15)
        except Exception as e:
            print('Login request failed:', e)
            return False

        # server returns JSON on success/failure; try to parse it
        try:
            j = r.json()
            if isinstance(j, dict) and j.get('status') == 'success':
                return True
        except Exception:
            pass

        # as fallback, check for presence of cookie named 'user' or 'token'
        ck = session.cookies.get('user') or session.cookies.get('token')
        if ck:
            return True

        # login unsuccessful
        return False

    # If server seems to require login and user supplied username, try to login.
    needs_login = server_requires_login()
    if needs_login and not args.username:
        print('Target server appears to require an authenticated account to upload. Provide --username to login first.')
        sys.exit(3)

    if args.username:
        ok = do_login(args.username, args.password)
        if not ok:
            print('Login failed. Check username/password and try again.')
            sys.exit(4)
    if args.dry_run:
        print(f"Dry run: {len(files)} files found under {base}")
        for full, rel in files:
            print(rel)
        return

    # helper: check remote file size using JSON ?size or HEAD fallback
    def check_remote_size(session, base_dir_url, rel_path, full_path):
        if not base_dir_url:
            return None
        try:
            parts = [quote(p) for p in rel_path.lstrip('/').split('/')]
            qpath = '/'.join(parts)
            size_url = base_dir_url.rstrip('/') + '/' + qpath + '?size'
            r = session.get(size_url, timeout=8)
            if r.status_code == 200:
                try:
                    j = r.json()
                    remote_size = int(j.get('byte', 0))
                    return remote_size
                except Exception:
                    pass
        except Exception:
            pass
        try:
            parts = [quote(p) for p in rel_path.lstrip('/').split('/')]
            qpath = '/'.join(parts)
            head_url = base_dir_url.rstrip('/') + '/' + qpath
            h = session.head(head_url, timeout=10, allow_redirects=True)
            if h.status_code == 200 and 'content-length' in h.headers:
                try:
                    val = int(h.headers.get('content-length', 0))
                    return val
                except Exception:
                    return None
        except Exception:
            pass
        return None

    def upload_batch(session, upload_url, files_list, password, timeout=60, retries=3, retry_delay=2, base_dir_url=None):
        """Upload multiple files in one multipart POST. files_list is [(full_path, rel_path), ...].
        Returns list of (rel_path, success_bool, status_code_or_None, message)
        """
        results = []
        # prepare files to actually upload after existence checks
        to_send = []
        for full, rel in files_list:
            try:
                remote_size = None
                if base_dir_url:
                    remote_size = check_remote_size(session, base_dir_url, rel, full)
                if remote_size is not None:
                    local_size = os.path.getsize(full)
                    if remote_size == local_size:
                        results.append((rel, True, 200, 'Exists'))
                        continue
            except Exception:
                pass
            to_send.append((full, rel))

        if not to_send:
            return results

        attempt = 0
        import time as _time
        last_exc = None
        while attempt < retries:
            attempt += 1
            # open all file handles for this attempt
            file_objs = []
            files_payload = []
            try:
                for full, rel in to_send:
                    fobj = open(full, 'rb')
                    file_objs.append(fobj)
                    files_payload.append(('file[]', (rel, fobj, mimetypes.guess_type(full)[0] or 'application/octet-stream')))

                data = {'post-type': 'upload', 'password': password}
                r = session.post(upload_url, data=data, files=files_payload, timeout=timeout)
                # if request succeeded, mark all sent files with r.ok
                for full, rel in to_send:
                    results.append((rel, r.ok, r.status_code, r.text if not r.ok else 'Uploaded'))
                return results
            except Exception as e:
                last_exc = e
                if attempt < retries:
                    _time.sleep(retry_delay)
                    continue
                # final failure: mark batch files as failed
                for full, rel in to_send:
                    results.append((rel, False, None, str(e)))
                return results
            finally:
                for fo in file_objs:
                    try:
                        fo.close()
                    except Exception:
                        pass

    results = []
    lock = threading.Lock()
    attempted_dirs = set()
    failed_dirs = {}  # rel_dir -> reason
    uploaded_rel_paths = set()

    def create_remote_dir(session, base_dir_url, rel_dir, retries=3, retry_delay=1):
        # Server accepts POST to ?new_folder with post-type=new_folder and name=<folder>
        if not rel_dir or rel_dir in ('.', ''):
            return True, None
        # Check if directory already exists by HEADing the directory URL (with trailing slash)
        try:
            dir_url = base_dir_url.rstrip('/') + '/' + rel_dir.strip('/') + '/'
            h = session.head(dir_url, timeout=8, allow_redirects=True)
            if h.status_code == 200:
                return True, None
        except Exception:
            # ignore HEAD failures and fall back to attempting create
            pass
        url = base_dir_url.rstrip('/') + '/?new_folder'
        data = {'post-type': 'new_folder', 'name': rel_dir}
        import time as _t
        attempt = 0
        while attempt < retries:
            attempt += 1
            try:
                r = session.post(url, data=data, timeout=10)
                # permission or auth errors
                if r.status_code in (401, 403):
                    return False, 'permission-denied'

                # parse JSON response if present
                if r.status_code == 200:
                    try:
                        j = r.json()
                        # expected format: {"head": "Success"/"Failed", "body": ...}
                        head = j.get('head') if isinstance(j, dict) else None
                        if head and head.lower().startswith('success'):
                            return True, None
                        if head and head.lower().startswith('failed'):
                            body = j.get('body', '')
                            if 'Folder Already Exists' in body:
                                return True, None
                            return False, 'server-failed'
                    except Exception:
                        pass
                    # fallback to textual checks
                    if 'Folder Already Exists' in r.text or 'New Folder Created' in r.text or 'Success' in r.text:
                        return True, None
                    return False, 'unknown-response'
            except Exception:
                pass
            if attempt < retries:
                _t.sleep(retry_delay)
        return False, 'network-error'

    # chunk files according to batch-size and submit upload tasks
    def chunks(lst, n):
        for i in range(0, len(lst), n):
            yield lst[i:i+n]

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = []
        for group in chunks(files, max(1, args.batch_size)):
            # ensure remote dirs exist for files in this group
            dirs = set(os.path.dirname(rel) for _, rel in group if os.path.dirname(rel) not in ('', '.'))
            for rel_dir in dirs:
                if rel_dir and rel_dir not in attempted_dirs:
                    attempted_dirs.add(rel_dir)
                    ok_dir, reason = create_remote_dir(session, base_dir_url, rel_dir, retries=args.retries, retry_delay=args.retry_delay)
                    if not ok_dir:
                        # record failure; postpone deciding whether to warn until after uploads
                        failed_dirs[rel_dir] = reason
                        # immediate permission errors are important to show
                        if reason == 'permission-denied':
                            print(f"Permission denied creating remote dir '{rel_dir}'; uploads may still create it if server allows upload-based directory creation")

            # submit either a single-file upload or a batch upload
            if args.batch_size <= 1 and len(group) == 1:
                full, rel = group[0]
                futures.append(ex.submit(upload_file, session, upload_url, full, rel, args.password, timeout=60, retries=args.retries, retry_delay=args.retry_delay, base_dir_url=base_dir_url))
            else:
                futures.append(ex.submit(upload_batch, session, upload_url, group, args.password, timeout=120, retries=args.retries, retry_delay=args.retry_delay, base_dir_url=base_dir_url))

        for fut in as_completed(futures):
            res = fut.result()
            # upload_file returns a single tuple; upload_batch returns a list
            with lock:
                if isinstance(res, list):
                    for rel, ok, status, text in res:
                        if ok:
                            uploaded_rel_paths.add(rel)
                            # print Exists explicitly when server indicated so
                            if text == 'Exists':
                                print(f"Exists:   {rel}")
                            else:
                                print(f"Uploaded: {rel} (HTTP {status})")
                        else:
                            print(f"Failed:   {rel} (status={status}) -> {text}")
                else:
                    rel, ok, status, text = res
                    if ok:
                        uploaded_rel_paths.add(rel)
                        if text == 'Exists':
                            print(f"Exists:   {rel}")
                        else:
                            print(f"Uploaded: {rel} (HTTP {status})")
                    else:
                        print(f"Failed:   {rel} (status={status}) -> {text}")

        # after all uploads, summarize directory-create failures
        if failed_dirs:
            # categorize each failed dir: created during upload (some file uploaded) vs still missing
            created = []
            missing = []
            for d, reason in failed_dirs.items():
                # check whether any uploaded file path starts with this dir path
                prefix = d.rstrip('/') + '/'
                any_uploaded = any(p == d or p.startswith(prefix) for p in uploaded_rel_paths)
                if any_uploaded:
                    created.append(d)
                else:
                    missing.append((d, reason))

            for d in created:
                print(f"Note: server created remote dir '{d}' during upload")
            for d, reason in missing:
                if reason == 'permission-denied':
                    print(f"Permission denied creating remote dir '{d}'; uploads may have failed or may require manual intervention")
                else:
                    print(f"Warning: failed to create remote dir '{d}' ({reason}); server may not contain these files or you may need to create the directory manually")


if __name__ == '__main__':
    main()
