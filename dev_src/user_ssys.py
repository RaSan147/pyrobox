import os
import sys
import shutil
import json
import hashlib
import time, datetime
import traceback
from threading import  Thread
from tempfile import NamedTemporaryFile
from collections import deque

import atexit
import signal

import _fs_utils as F_sys
#import net_sys
#import TIME_sys

from data_types import GETdict, Flag

#############################################
#				USERS HANDLER			  #
#############################################

class UserDB(GETdict):
	def __init__(self, path) -> None:
		self.path = path
		self.users = {}
		self.load_or_make()

		self.dthread = None # the var for the thread that handles the save process

		self.must_save()


	def load_or_make(self):
		try:
			self.load()
		except Exception as e:
			#traceback.print_exc()
			self.make()
			self.load()

	def load(self):
		"""Loads the user_db.json file
		"""
		json_data = json.load(open(self.path, 'r'))
		for key in json_data:
			self[key] = json_data[key]

	def make(self):
		"""Makes the user_db.json file
		"""
		self.dump()


	def _dump(self):
		'''Dump to a temporary file, and then move to the actual location'''
		data = json.dumps(self)
		F_sys.writer(self.path, "w", data)

	def dump(self):
		'''Force dump memory db to file'''
		self.dthread = Thread(target=self._dump)
		self.dthread.start()
		self.dthread.join()
		return True


	def must_save(self):
		"""This will make sure the last save request was perfectly handled even at the verge of death
		"""
		def handle_exit(*args, **kwargs):
			if self.dthread is not None:
				self.dthread.join()
			sys.exit(0)
		atexit.register(handle_exit)
		signal.signal(signal.SIGTERM, handle_exit)
		signal.signal(signal.SIGINT, handle_exit)

	def destroy(self):
		if os.path.isfile(self.path):
			os.remove(self.path)

	delete = destroy


if __name__ == "__main__":
	users = UserDB("./te-st/new.db")
	users[99] = 69
	users.dump()
	print(users)
	#users.delete()



class User(GETdict):
	"""can get and set user data like a js object

	to set item, use dict["key"] = value for the 1st time,
	then use dict.key or dict["key"] to both get and set value

	but using dick.key = value 1st, will assign it as attribute and its temporary
	"""
	def __init__(self, username=""):


		self.username = username
		self.user_path = os.path.join(appConfig.user_data_dir, username)
		self.file_path = os.path.join(self.user_path, '__init__.json')



		self.flags = Flag()
		self.chat = Flag()
		self.chat.intent = deque(maxlen=20)
		self.user_client_time = 0.0 # in seconds
		self.user_client_time_offset = 0.0 # in seconds
		self.user_client_dt = datetime.datetime.now() #will be replaced on new msg
		# self.pointer = self.msg_id = 0

		# self.skins = {}
		self.loaded_skin = None
		self.skins = {}


		# if the data asked for is already there
		data = F_sys.reader(self.file_path, on_missing=None)
		if not data:
			raise Exception("User not found")

		try:
			json_data = json.loads(data)
			#for key in json_data:
#				self[key] = json_data[key]
			self.update(json_data)
		except Exception as e:
			traceback.print_exc()
			raise Exception("User data corrupted") from e

	# def __eq__(self, __o: object) -> bool:
	# 	if (bool(__o) or bool(self.username)) is False:
	# 		# is user is none
	# 		return True
	# 	return super().__eq__(__o)

	def __setitem__(self, key, value):
		super().__setitem__(key, value)
		self.save()


	def __setattr__(self, key, value):
		if self(key):
			self.__setitem__(key, value)
		else:
			super().__setattr__(key, value)


	# def __getattribute__(self, __name: str):
	# 	return super().__getattribute__(__name)


	def save(self):
		"""Saves updated dict in users folder
		"""
		new = json.dumps(self, indent="\t", sort_keys=True)
		F_sys.writer("__init__.json", 'w', new, self.user_path)

	def get_chat(self, pointer=-1):
		if pointer == -1:
			pointer = self.pointer
		pointer = str(pointer)
		file_path = os.path.join(self.user_path, pointer+'.json')

		# if the data asked for is already there
		data = F_sys.reader(file_path, on_missing=None)
		if data:
			return json.loads(data)

		return None

	demo_chat = {
		"id": 0,
		"msg": "hello Asuna",
		"time": 123456789,
		"user": "USER",
		"parsed_msg": "hello <:ai_name>",
		"rTo": -1,
		"intent": "",
		# intent of user message can't be determined immediately
		# so it will be determined later, on bot's reply
	}

	def add_chat(self, msg, mtime, user=1, parsed_msg="", rTo=-1, intent=(), context=()):
		"""
		msg: message sent
		mtime: time of message
		user: 1 if user, 0 if bot
		parsed_msg: parsed message by basic_output
		rTo: reply to message id (-1 if not reply)
		"""
		pointer = self.pointer
		old = self.get_chat(pointer)
		if old is None:
			old = []

		if len(old) >= 100:
			self.pointer += 1
			old = []
		pointer = str(self.pointer)


		chat = self.demo_chat.copy()

		if user:
			user= "USER"
			# actual time on user side
			chat["uTime"] = str(TIME_sys.ts2dt(self.user_client_time, self.user_client_time_offset))
		else:
			user= "BOT"

		id = self.msg_id

		self.msg_id += 1 # starts from 0 => User, 1 => Bot, 2 => User, 3 => Bot, ...

		chat['id'] = id
		chat['msg'] = msg # dict, contains msg, script and render mode
		chat['time'] = str(TIME_sys.utc_to_bd_time(mtime))
		chat["parsed_msg"] = parsed_msg
		chat['rTo'] = rTo
		chat['intent'] = "+".join(intent)
		chat['user'] = user

		old.append(chat)

		J = json.dumps(old, indent="\t", separators=(',', ':'))
		F_sys.writer(pointer+'.json', 'w', J, self.user_path)

		return id


	def get_user_dt(self):
		return TIME_sys.ts2dt(self.user_client_time, self.user_client_time_offset)



class UserHandler:
	def __init__(self) -> None:
		self.users = {} #username: User()

		self.online_avatar = live2d_sys.OnLine()

		self.default_user = {
			"username": "default",
			"password" : "default",
			"created_at": datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S"),
			"last_active": datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S"),
			"pointer": 0, # current chat index (100 msg => 1 pointer)
			"nickname": "default", # current user name
			"bot": None, # user preferred bot name
			"id": "default", #
			"ai_name": "Asuna", # user preferred ai name
			"bot_charecter": "Asuna", # user preferred ai avatar
			"bot_skin": 0,
			"skin_mode": 1, # 0 = offline, 1 = online
			"room": 0,
			"custom_room": None,
			"msg_id": 0,
			"pointer": 0,
		}


	def u_path(self, username):
		"""returns user folder path"""
		return os.path.join(appConfig.user_data_dir, username)

	# def login(self, username, password):
	# 	hash = hashlib.sha256(username)

	# def get_user(self, username, uid=None):
	# 	return self.collection(username, uid)

	# def get_user_data(self, username, pointer):
	# 	user_path = self.u_path(username)
	# 	file_path = os.path.join(user_path, pointer+'.json')

	# 	# if the data asked for is already there
	# 	if os.path.exists(file_path):
	# 		with open(file_path, 'r') as f:
	# 			return json.load(f)

	# 	return None

	def create_user(self, username, password):
		hash = hashlib.sha256((username+password).encode('utf-8'))
		id = hashlib.sha1((str(time.time()) + username).encode("utf-8")).hexdigest()
		u_data = {
			"username": username,
			"password": hash.hexdigest(),
			"created_at": datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S"),
			"last_active": datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S"),
			"pointer": 0, # current chat index (100 msg => 1 pointer)
			"nickname": username, # current user name
			"bot": None, # user preferred bot name
			"id": id, #
			"ai_name": "Asuna", # user preferred ai name
			"bot_charecter": "Asuna", # user preferred ai avatar
			"bot_skin": 0,
			"skin_mode": 1, # 0 = offline, 1 = online
			"room": 0,
			"custom_room": None,
			"msg_id": 0,
			"pointer": 0,
		}

		new = json.dumps(u_data, indent=2)
		F_sys.writer("__init__.json", 'w', new, self.u_path(username))

		return id

	def update_user(self, username=None, user=None):
		"""update user data"""
		if not user:
			user = self.get_user(username)
			if user is None:
				return False

		# merge data
		temp = self.default_user
		#for key in temp:
		#	if key not in user:
		#		user[key] = temp[key]
		temp = {**temp, **user}
		self.default_user.update(temp)

	def server_signup(self, username, password):
		# check if username is already taken
		if self.get_user(username, temp=True) is not None:
			return {
				"status": "error",
				"message": "Username already taken"
			}

		# create user
		id = self.create_user(username, password)
		return {
			"status": "success",
			"message": "User created",
			"user_name": username,
			"user_id": id
		}

	def server_login(self, username, password):
		user = self.get_user(username)
		if user is None:
			return {
				"status": "error",
				"message": "User not found"
			}
		hash = hashlib.sha256((username+password).encode('utf-8'))
		if user["password"] != hash.hexdigest():
			return {
				"status": "error",
				"message": "Wrong password"
			}

		user["last_active"] = datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
		print("logged in", user)
		# user.flags.clear() # clear flags

		return {
			"status": "success",
			"message": "User logged in",
			"user_name": username,
			"user_id": user["id"]
		}

	def get_user(self, username, temp=False):
		if username in self.users:
			return self.users[username]
		try:
			user = User(username)
			if not temp:
				self.users[username] = user
				self.get_skin_link(user=user)

			return user
		except:
			traceback.print_exc()
			return None


	def server_verify(self, username, id, return_user=False):
		user = self.get_user(username)
		if not user:
			return False
		if user.get("id") != id:
			return False

		user["last_active"] = datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
		# user.flags.clear() # clear flags on refresh
		self.update_user(username)

		if return_user:
			return user
		return True


	def collection(self, username:str, uid:str):
		# verify uid from users collection
		x = self.get_user(username)
		if not x: return None
		if x.get("id")!=uid: return None
		return x

	def get_skin_link(self, username="", uid="", user=None ,retry=0):

		user = user if user else self.collection(username, uid)
		if not user:
			print("USER NOT FOUND")
			return None
		charecter = user["bot_charecter"]
		skin = user["bot_skin"]
		mode = user["skin_mode"]
		# print(user.loaded_skin)
		# print(skin)
		print(user.get("skins") , user.get("c_skin_mode"),mode , user.loaded_skin , skin)
		if user.get("skins") and user.get("c_skin_mode")==mode and user.loaded_skin == skin:
			return user.skins[skin]

		if mode == 0:
			print("INVALID MODE (UNSUPPORTED)")
			return 0
		elif mode == 1:
			try:
				_skin = self.online_avatar.get_skin_link(charecter, skin)
				user.skins = self.online_avatar.get_skins(charecter)
				print("SKINS LOADED")
				user.c_skin_mode = mode
				user.loaded_skin = skin
				return _skin
			except net_sys.NetErrors:
				traceback.print_exc()
				return None
			except Exception:
				traceback.print_exc()
				if retry: return None

				user["bot_charecter"] = self.default_user["bot_charecter"]
				user["bot_skin"] = self.default_user["bot_skin"]
				user["skin_mode"] = self.default_user["skin_mode"]

				self.get_skin_link(username, uid, 1)
		return 0

	def use_next_skin(self, username, uid):
		user = self.collection(username, uid)
		if not user:
			print("USER NOT FOUND")
			return None

		self.get_skin_link(username, uid) # init
		total_skins = len(user.skins)
		print("....current skin", user.bot_skin)
		print("....total skin ", total_skins)
		user.bot_skin = (user.bot_skin + 1)%(total_skins)
		print("sent skin", user.bot_skin)

		_skin = str(user.bot_skin)

		return _skin

	def room_bg(self, username="", uid="", command="", custom="", user:User=None):
		if not user:
			_user = self.collection(username, uid)
			if not _user:
				print("USER NOT FOUND")
				return None
			user =  _user

		if command=="change":
			user.room = (user.room+1)%len(CONSTANTS.room_bg)
			user.custom_room = None # clear custom room

		if command=="custom":
			if len(custom)>2000:
				return False
			user.custom_room = custom #set custom room bg

		if user.custom_room:
			return user.custom_room # if custom room enabled, then return it.

		room_id = user.room
		return CONSTANTS.room_bg[room_id]









	# def set_user_data(self, username, pointer):


#user_handler = UserHandler()

# user = User("test")
