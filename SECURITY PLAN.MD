# For server:
## Security
| Flag | Action |
| ---- | ------ |
| --secure   | Require  a `--user` (admin username) a `--pass` (admin password)  to start server. Can use users (user.csv) to use predefined userlist. Otherwise admin need to log in **(only admin can)** and add users on `/admin?panel=users`. nobody can see list or do any action . However this will allow anyone to download files with direct link. <br><br> <u>**Server Side Process :**</u> <br> Verify users will be used before every request, will be ignored on file download.  This function will check Header **cookie**. *If not found will sent to log in page.* |


 --force: Can be used with secure will not apply here. So only logged in browser can download file . However this won't apply for "stream-url"
 " Stream-url" :  Users can create stream-url . This will allow nonblocking access to the file and file only . SO, anyone with force flag need to use stream-url to DL file with IDM or stream MKV on VLC . 
Format:__/ Stream ? id =(5alphanumerical) [60M links]
Stream-exp (time in min) : set stream - url expire time. '' DEFAVLT =O'' if not O , will run a thread and each minute , will check if anyone ready to die.
Mechanism: Use queue when the thread starts it will call get. If empty , will ask again after a min. f something comes in hand, it'll wait till it's deadline comes. Saves CPU. After sleep. will kill it's first url , then call for next in queue .  If it's ready to die ( 1 links need to die in the same min) , it's kill and keep calling next until somethng comes up that shouldn't be killed then or list empty .
*When a stream url is made it will be registered in a url dict and in the deadline queue ( if deadline is set)
 in JS :     stream url 
   request get : __/ stram ? url?=(sub_link)
