import msgpack, time, os
#print(os.getcwd())
st = time.time()
n = [b'spam', 'eggs']*1000
fname = "__test.mdb"

m = None
for i in range(10):
	with open(fname, "wb") as f:
		f.write(msgpack.packb(n))
		
	with open(fname, "rb") as f:
		m =msgpack.unpackb(f.read())
		
	
et = time.time()
print("msgpack \n" + "-"*50)
print("match:", m == [b'spam', 'eggs']*1000)
print("items:", 2*1000)


print("save and restore 10times:", et - st)

print("avg:", (et-st)/10)
print("file size: ", os.stat(fname).st_size, "bytes")