from datetime import datetime
import json
import requests
import time
import sqlite3
import threading
import uuid
import os

headers = {
	'app_version': '770',
	'platform': 'android',
	'User-Agent': 'Tinder Android Version 4.0.6',
	'os-version':   '21',
	'Content-Type': 'application/json; charset=utf-8',
	'Host': 'api.gotinder.com',
	'Connection':   'Keep-Alive',
	'Accept-Encoding':  'gzip',
}  


def check_db_exist(username):
	name_db='tinder '+username

	if os.path.isfile(name_db):
		cursor=sqlite3.connect(name_db)
		cursor.close()
	else:
		cursor=sqlite3.connect(name_db)
		cursor.execute(''' CREATE TABLE `users_liked_matched` (`user_id` TEXT, `user_name` TEXT,`sender_id`	TEXT,`match_id`	TEXT,`message_sent`	TEXT, 'all_data' TEXT, `date_added` TEXT DEFAULT CURRENT_TIMESTAMP); ''')
		cursor.execute('''CREATE TABLE `users_liked_not_matched` (`user_id`	TEXT, `user_name`	TEXT, `sender_id`	TEXT, 'all_data' TEXT,  `date_added`	TEXT DEFAULT CURRENT_TIMESTAMP);''')
		cursor.close()

	return name_db

def get_auth_token(fb_auth_token,fb_user_id):
	r=requests.post('https://api.gotinder.com/auth',data=json.dumps({'facebook_token': fb_auth_token, 'locale': 'en'}),headers=headers,verify=False)
	data = r.json()

	try:
		return data['token']
	except:
		return None

def recommendations(auth_token,list_users,user_json):
	h = headers
	h.update({'X-Auth-Token': auth_token})
	r = requests.get('https://api.gotinder.com/user/recs?locale=en', headers=h,verify=False)
	if r.status_code == 401 or r.status_code == 504:
		raise Exception('Invalid code')
		print r.content

	data=r.json()

	

	for result in data['results']:
		num=result['_id']
		list_users[num]=result['name']
		user_json[num]=str(result)
		

def like(user_id,auth_token):
	try:
		h = headers
		h.update({'X-Auth-Token': auth_token})
		u = 'https://api.gotinder.com/like/%s' % user_id
		d = requests.get(u, headers=h, verify=False).json()
		print 'liked '+user_id
	except KeyError:
		raise
	else:
		return d['match']

def nope(user_id,auth_token):
	try:
		h=headers
		h.update({'X-Auth-Token': auth_token})
		u = 'https://api.gotinder.com/pass/%s' % user_id
		requests.get(u, headers=headers,verify=False).json()
		print 'passed '+user_id
	except KeyError:
		raise

def send_message(user_id,name,auth_token):
#	try:
	h=headers
	h.update({'X-Auth-Token': auth_token})

	message='hey '+name
	u = 'https://api.gotinder.com/user/matches/%s' % user_id
	res=requests.post(u, headers=headers,data=json.dumps({'message':message }),verify=False).json()
   
	time.sleep(100)


	cursor_message=sqlite3.connect('bot_tinder')

	sql_message= 'select * from send_message'
	messages=cursor_message.execute(sql_message)
	try:
		for message in messages:   
			u = 'https://api.gotinder.com/user/matches/%s' % user_id
			res=requests.post(u, headers=headers,data=json.dumps({'message':message[0]}),verify=False).json()

			time.sleep(100)

			print 'Message Sent for '+email1
	except KeyError:
		raise


def run_bot(username,fb_auth_token,fb_user_id):

	list_users={}
	user_json={}
	
	db_name=check_db_exist(username)

	auth_token=get_auth_token(fb_auth_token,fb_user_id)
	print 'Auth token for '+username+' is ' +auth_token

	if(auth_token=='None'):
		print 'User may be blocked '+username
	else:
		print 'User working '+username


	while(True):
		try :
			cursor=sqlite3.connect(db_name)
			sql3='select * from users_liked_not_matched where sender_id =?'
			resp=cursor.execute(sql3,[fb_user_id])
			count=0
			for use in resp:
				count=count+1
				user_json[use[0]]=use[3]
				list_users[use[0]]=use[1]

			print 'No of new users added for '+username + ' is '+str(count)

			sql4='delete from users_liked_not_matched where sender_id =?'
			cursor.execute(sql4,[fb_user_id])
			cursor.commit()
			
			count=-1
			
			recommendations(auth_token,list_users,user_json)

			userss=list_users.items()
			print userss
			for user in userss :
				try:
					count=count+1
					u_id=user[0]
					u_name=user[1]
					print 'here'
					print 'User is '+u_name
					if count%3!=0:
						print ' -> like'
					  #  print user_json[user_data_count]
						match=like(u_id,auth_token)
						if match:
							sql1='insert into users_liked_matched(user_id,user_name,sender_id,match_id,message_sent,all_data) values (?,?,?,?,?,?)'
					#        print match['_id']
							print 'Match'
							try:
								send_message(match['_id'],u_name,auth_token)
								cursor.execute(sql1,(u_id,u_name,fb_user_id,match['_id'],'yes',user_json[u_id]))
							except KeyError:
								raise
								print 'Unable to send message'
								cursor.execute(sql1,(u_id,u_name,fb_user_id,match['_id'],'no',user_json[u_id]))
							cursor.commit()
						else:
							sql2='insert into users_liked_not_matched(user_id,user_name,sender_id,all_data) values (?,?,?,?)'
							cursor.execute(sql2,(u_id,u_name,fb_user_id,user_json[u_id]))
							print 'Inserted in database'
							cursor.commit()
					else:
						print ' -> pass'
						nope(u_id,auth_token)
					time.sleep(100)
					print '\n\n\n'
					cursor.commit()
				except:
					print 'Error Please Wait. '
					time.sleep(500)

			print 'Sleeping ... for '+username
			time.sleep(10000)
			list_users.clear()
			user_json.clear()
			cursor.close()
		except:
			print 'Error Please Wait.. Server maybedown '
			time.sleep(1000)
			cursor.close()
	print 'Done'



cursor=sqlite3.connect('bot_tinder')
t=datetime.now()
sql='insert into last_used(time) values(?)'
cursor.execute(sql,[t])

sql_get_token='select * from user_info'
token_info=cursor.execute("select * from user_info where status='working'")

count=0

for t in token_info:
	fb_user_id = t[3]
	fb_auth_token = t[2]
	print 'Thread created for '+t[0]
	t1=threading.Thread(target=run_bot,args=(t[0],fb_auth_token,fb_user_id))
	t1.start()

cursor.close()



