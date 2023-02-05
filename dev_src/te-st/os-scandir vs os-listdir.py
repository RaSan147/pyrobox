"""
Using os.scandir() instead of os.listdir().

=================================================
                    RESULT
    scandir() wins by a significant margin.
=================================================

"""


import os
import queue
import time

class LimitExceed(Exception):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)


def check_access(path):
	"""
	Check if the user has access to the file.

	path: path to the file
	"""
	if os.path.exists(path):
		try:
			with open(path):
				return True
		except Exception:
			pass
	return False

def get_stat(path):
	"""
	Get the stat of a file.

	path: path to the file

	* can act as check_access(path)
	"""
	try:
		return os.stat(path)
	except Exception:
		return False
	
	
def _get_tree_count(path):
	count = 0

	Q = queue.Queue()
	Q.put(path)
	while not Q.empty():
		path = Q.get()
		
		try:
			dir = os.scandir(path)
		except OSError:
			continue
		for entry in dir:
			try:
				is_dir = entry.is_dir(follow_symlinks=False)
			except OSError as error:
				continue
			if is_dir:
				Q.put(entry.path)
			else:
				count += 1
	
		dir.close()
	return count


def get_file_count(path):
	"""
	Get the number of files in a directory.
	"""

	return sum(1 for _, _, files in os.walk(path) for f in files)

def _get_tree_size(path, limit=None, return_list= False, full_dir=True, both=False, must_read=False):
	r=[] #if return_list
	total = 0
	start_path = path

	Q= queue.Queue()
	Q.put(path)
	while not Q.empty():
		path = Q.get()

		try:
			dir = os.scandir(path)
		except OSError:
			continue
		for entry in dir:
			try:
				is_dir = entry.is_dir(follow_symlinks=False)
			except OSError as error:
				continue
			if is_dir:
				Q.put(entry.path)
			else:
				try:
					total += entry.stat(follow_symlinks=False).st_size
					if limit and total>limit:
						raise LimitExceed
				except OSError:
					continue
				
				if must_read:
					try:
						with open(entry.path, "rb") as f:
							f.read(1)
					except Exception:
						continue

				if return_list:
					_path = entry.path
					if both: r.append((_path, _path.replace(start_path, "", 1)))
					else:    r.append(_path if full_dir else _path.replace(start_path, "", 1))

		dir.close()

	if return_list: return total, r
	return total

def get_dir_size(start_path = '.', limit=None, return_list= False, full_dir=True, both=False, must_read=False):
	"""
	Get the size of a directory and all its subdirectories.

	start_path: path to start calculating from
	limit (int): maximum folder size, if bigger returns `-1`
	return_list (bool): if True returns a tuple of (total folder size, list of contents)
	full_dir (bool): if True returns a full path, else relative path
	both (bool): if True returns a tuple of (total folder size, (full path, relative path))
	must_read (bool): if True only counts files that can be read
	"""
	r=[] #if return_list
	total_size = 0
	start_path = os.path.normpath(start_path)

	for dirpath, dirnames, filenames in os.walk(start_path, onerror= None):
		for f in filenames:
			fp = os.path.join(dirpath, f)
			if os.path.islink(fp):
				continue

			stat = get_stat(fp)
			if not stat: continue
			if must_read and not check_access(fp): continue

			total_size += stat.st_size
			if limit!=None and total_size>limit:
				if return_list: return -1, False
				return -1

			if return_list:
				if both: r.append((fp, fp.replace(start_path, "", 1)))
				else:    r.append(fp if full_dir else fp.replace(start_path, "", 1))

	if return_list: return total_size, r
	return total_size

def _get_tree_count_n_size(path):
	total = 0
	count = 0
	Q= queue.Queue()
	Q.put(path)
	while not Q.empty():
		path = Q.get()
		
		try:
			dir = os.scandir(path)
		except OSError:
			continue
		for entry in dir:
			try:
				is_dir = entry.is_dir(follow_symlinks=False)
			except OSError as error:
				continue
			if is_dir:
				Q.put(entry.path)
			else:
				try:
					total += entry.stat(follow_symlinks=False).st_size
					count += 1
				except OSError as error:
					continue

		dir.close()
	return count, total

def get_tree_count_n_size(start_path):
	"""
	Get the size of a directory and all its subdirectories.
	returns a tuple of (total folder size, total file count)
	"""

	size = 0
	count = 0
	for dirpath, dirnames, filenames in os.walk(start_path, onerror= None):
		for f in filenames:
			count +=1
			fp = os.path.join(dirpath, f)
			if os.path.islink(fp):
				continue

			stat = get_stat(fp)
			if not stat: continue

			size += stat.st_size

	return count, size


# test above functions performance
if __name__ == '__main__':
	path = r'C:\Windows'
	r1 = 'nothing'

	t1 = time.time()
	for i in range(10):
		r1 = get_dir_size(path, return_list= True)
	t2 = time.time()
	print('get_dir_size + fList', t2-t1, len(r1[1]), r1[0], sep='\t')

	t1 = time.time()
	for i in range(10):
		r1 = _get_tree_size(path, return_list= True)
	t2 = time.time()
	print('_get_tree_size + fList', t2-t1, len(r1[1]), r1[0], sep='\t')

	print()



	t1 = time.time()
	for i in range(10):
		r1 = _get_tree_count_n_size(path)
	t2 = time.time()
	print('_get_tree_count_n_size', t2-t1, r1[0], r1[1], sep='\t')

	t1 = time.time()
	for i in range(10):
		r1 = get_tree_count_n_size(path)
	t2 = time.time()
	print('get_tree_count_n_size', t2-t1, r1[0], r1[1], sep='\t')

	print()


	
	t1 = time.time()
	for i in range(10):
		r1 = get_file_count(path)
	t2 = time.time()
	print('get_file_count    ', t2-t1, r1, sep='\t')

	t1 = time.time()
	for i in range(10):
		r1 = _get_tree_count(path)
	t2 = time.time()
	print('_get_tree_count    ', t2-t1, r1, sep='\t')




# output
"""
tested with Python 3.11.1
CPU

	13th Gen Intel(R) Core(TM) i5-13600K

	Base speed:	3.50 GHz
	Sockets:	1
	Cores:	14
	Logical processors:	20
	Virtualization:	Enabled
	L1 cache:	1.2 MB
	L2 cache:	20.0 MB
	L3 cache:	24.0 MB




1X:
------------------
    FUNCTIONS        --       TIME          --  COUNT --    SIZE
get_dir_size + fList    6.4411609172821045      128346  35645837962
_get_tree_size + fList  1.3937323093414307      128346  35645840982

_get_tree_count_n_size  1.4096884727478027      128346  35645840982 <-
get_tree_count_n_size   6.35251784324646        128346  35645840982 <-

get_file_count          1.844714879989624       128346
_get_tree_count         1.3371014595031738      128346

NOTE: swapped position to make sure if cache is making any difference



10X:
------------------
	FUNCTIONS        --       TIME          --  COUNT --    SIZE
get_dir_size + fList    80.24487638473511       128346  35645847686
_get_tree_size + fList  14.458052635192871      128346  35645847686

_get_tree_count_n_size  14.372668743133545      128346  35645847686 <-
get_tree_count_n_size   73.73284935951233       128346  35645847686 <-

get_file_count          18.661930561065674      128346
_get_tree_count         13.298812866210938      128346

NOTE: swapped position to make sure if cache is making any difference

"""