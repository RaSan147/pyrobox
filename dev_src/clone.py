import os
import email, time, traceback
from queue import Queue
from datetime import datetime, timezone

#print(datetime.datetime.now())

import requests

os.umask(0) # make sure permissions are set correctly
session = requests.session()

def date_time_string(timestamp=None):
	"""Return the current date and time formatted for a message header."""
	if timestamp is None:
		timestamp = time.time()
	return email.utils.formatdate(timestamp, usegmt=True)
	


def get_list_dir(path):
	"""Get a list of files in a directory
	"""
	if path[-1] != "/":
		path += "/"

	o = []
	for f in os.listdir(path):
		if os.path.isdir(path+f):
			o.append(f+"/")
		else:
			o.append(f)
	return o
	
def check_exist(url, path, check_method):
	# print(check_method)
	try:
		header = session.head(url).headers

	except Exception:
		print("ALERT:  Server is probably down")
		traceback.print_exc()
		return None
	
	# original_last_modify = email.utils.parsedate_to_datetime(header["Last-Modified"]).replace(tzinfo=timezone.utc).timestamp()
	original_modify = email.utils.parsedate_to_datetime(header["Last-Modified"])#.timestamp()

	
	if original_modify.tzinfo is None:
		# obsolete format with no timezone, cf.
		# https://tools.ietf.org/html/rfc7231#section-7.1.1.1
		original_modify = original_modify.replace(tzinfo=timezone.utc)
		
		
		
	if not os.path.isfile(path):
		return False
	
	if check_method =="date":
		tt = os.path.getmtime(path)
		
		# tt = fs.st_mtime
			
		if original_modify.tzinfo is timezone.utc:
			# compare to UTC datetime of last modification
			local_last_modify = datetime.fromtimestamp(tt, timezone.utc)
			# remove microseconds, like in If-Modified-Since
			local_last_modify = local_last_modify.replace(microsecond=0)

			if local_last_modify == original_modify:
				return True

			# print("LOCAL: ", path, "==", local_last_modify)
			# print("REMOTE:", path, "==", original_modify)
			
	if check_method == "size":
		local_size = int(os.path.getsize(path))
		original_size = int(header["Content-length"])
		
		if local_size==original_size:
			return True
		
		# print("LOCAL: ", path, "==", local_size)
		# print("REMOTE:", path, "==", original_size)
		
			
	return False
	
	
	
	


def dl(url, path, overwrite, check_method):
	"""Download a file from a url
	url: url to download from (local_server.py)
	path: path to download to
	overwrite: overwrite existing files (False) 
	"""
	if not overwrite:
		exist = check_exist(url, path, check_method)
		
		if exist is True: 
			print("EXIST: ", path)
			return
		if exist is None: return # failed response


	local_filename = path + ".cloneTMP"
	
	mtime = None

	try:
		with requests.get(url, stream=True) as r:
			mtime =  email.utils.parsedate_to_datetime(r.headers["Last-Modified"]).timestamp()
			r.raise_for_status()
			with open(local_filename, 'wb') as f:
				for chunk in r.iter_content(chunk_size=8192): 
					f.write(chunk)
	except Exception:
		traceback.print_exc()
		print("ALERT:  [dl] Server is probably down")
		try:
			os.remove(local_filename)
		except OSError:
			return
	
	
	os.replace(local_filename, path)
	os.utime(path, (mtime, mtime))

	print("SAVED: ", path)
		
from concurrent.futures import ThreadPoolExecutor, as_completed

executor = ThreadPoolExecutor(8)

futures = []

def clone(url, path = "./", overwrite = False, check_exist = "date", delete_extras = False):
	"""Clone a directory from a url
	url: url to clone from (local_server.py)
	path: path to clone to (./)
	overwrite: overwrite existing files reguardless of checking existance (False)
	check_exist: check if file exists by "date" or "size" or None to ignore totally (date)
	"""
	Q = Queue()
	def get_json(url):
		
		try:
			u = url+"?json"
			#print(u)
			json = session.get(u).json()
			return json
		except Exception:
			traceback.print_exc()
			print("ALERT:  [clone] Server is probably down")
			return 

	def run_Q(url, path = "./", overwrite = False, check_exist = "date", delete_extras = False):
		nonlocal Q

		if path[-1] != "/":
			path += "/"

		json = get_json(url)
		if not json:
			return
			
		os.makedirs(path, exist_ok=True)


		remote_list = []


		for link, name in json:
			remote_list.append(name)
			if link.endswith("/"):
				Q.put((url+link, path+name, overwrite, check_exist))
				continue
				
			futures.append(executor.submit(dl, url+link, path+name, overwrite, check_exist))

			
		if delete_extras:
			# get local file list with os.listdir(path)
			local_list = get_list_dir(path)
			#print(local_list)
			
			for name in local_list:
				if name not in remote_list:
					print("DELETE: [", path+name, "]")
					os.remove(path+name)


	Q.put((url, path, overwrite, check_exist))

	while not Q.empty():
		run_Q(*Q.get())




		
		
		
		
			
		
if __name__ == "__main__":
	clone("SOURCE_DIR", "DESTINATION_DIR", False, "date", True)

	for future in as_completed(futures):
		bool(future.result())

