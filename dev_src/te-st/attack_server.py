# ping an address for a certain amount of time


import time
import urllib3

session = urllib3.PoolManager()


# ping an address for a certain amount of time
def ping(address, duration):
	count  = 0
	
	success = 0
	fail = 0
	start = time.time()
	while time.time() - start < duration:
		try:
			r = session.request("GET", address)
			success += 1
			if not r:
				fail += 1
		except Exception as e:

			fail += 1
		count += 1

	return count, success, fail

# main
if __name__ == "__main__":
	address = "http://127.0.0.1:45454"
	duration = 10
	count, success, fail = ping(address, duration)
	print("Sent %d requests in %d seconds" % (count, duration))
	print("Sent %d requests per second" % (count / duration))
	print("average request time: %f seconds" % (duration / count))
	print("Success: %d" % success)
	print("Fail: %d" % fail)


