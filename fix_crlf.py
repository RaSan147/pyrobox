# win crlf to linux lf converter
import os



def detect_txt_file(file):
	try:
		with open(file, "r", encoding="utf-8") as f:
			f.read(1000)
			return True
	except UnicodeDecodeError:
		return False


def crlf_2_lf(path):
	# replacement strings
	WINDOWS_LINE_ENDING = b'\r\n'
	UNIX_LINE_ENDING = b'\n'

	# relative or absolute file path, e.g.:


	with open(path, 'rb') as open_file:
		content = open_file.read()
		
	if not b"\r\n" in content:
		return
		
	# Windows ➡ Unix
	content = content.replace(WINDOWS_LINE_ENDING, UNIX_LINE_ENDING)

	# Unix ➡ Windows
	# content = content.replace(UNIX_LINE_ENDING, WINDOWS_LINE_ENDING)

	with open(path, 'wb') as open_file:
		open_file.write(content)
		
		
n = 0
		
# iterate of directories
for root, dirs, files in os.walk("."):
	for file in files:
		path = os.path.join(root, file)
		#print(file, detect_txt_file(path))
		if detect_txt_file(path):
			print(path)
			crlf_2_lf(path)
			n+=1
			
			
print("\n\naTOTAL CONVERTED: ", n)
		