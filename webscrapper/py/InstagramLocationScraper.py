import re
import sys
import ast
import time
import json
import requests
import mysql.connector
from bs4 import BeautifulSoup
from selenium import webdriver
from mysql.connector import errorcode

config = {
  'user': 'root',
  'password': 'root',
  'host': 'localhost',
  'database': 'scraper',
  'raise_on_warnings': True,
}

# Chrome driver executable is in py directory, no need to specify path
driver = webdriver.Chrome()

def extractLinksFromTopPosts():
	url = 'https://www.instagram.com/explore/locations/215009654/ottawa-ontario/'
	driver.get(url)
	# List of links of all the pictures on the page
	links = [a.get_attribute('href') for a in driver.find_elements_by_css_selector('div._f2mse a')]
	parseLinks(driver, links)

def parseLinks(driver, links):
	str_tags_arr = []
	for link in range(9): # Instagram posts 9 top stories per region
		# NOTE: JSON object has no way of getting user profile links. Driver is best solution for now
		# Go to URL of user
		driver.get(links[link])
		# Get user's URL
		username = [a.get_attribute('href') for a in driver.find_elements_by_css_selector('div._eeohz a')] # Consider renaming to user_url
		# Get request of user's page
		# Start using soup instead of webdriver (less cost)
		r = requests.get(username[0])
		# Get html of user's page
		html = r.text
		# Turn html into soup object
		soup = BeautifulSoup(html, 'lxml')
		# Extract all scirpt tags from soup
		tags = soup.find_all('script')
		# Extract script tag with important data
		str_tags = str(tags[2])
		# Remove front end of script tag to only have JS object
		str_tags = str_tags.split('_sharedData = ', 1)[-1]
		# Remove back end of script tag to only have JS object
		str_tags = str_tags.replace(" ", "").rstrip(str_tags[-10:])
		# Turn new JS object string into JSON object
		str_tags_arr.append(json.loads(str_tags))
	extractDataFromJSON(str_tags_arr)

def extractDataFromJSON(tags_json):
	for i in range(len(tags_json)):
		# Extract wanted data form JSON object
		user_followers = tags_json[i]['entry_data']['ProfilePage'][0]['user']['followed_by']['count']
		user_following = tags_json[i]['entry_data']['ProfilePage'][0]['user']['follows']['count']
		username = tags_json[i]['entry_data']['ProfilePage'][0]['user']['username']
		user_posts = tags_json[i]['entry_data']['ProfilePage'][0]['user']['media']['count']
		user_profile_picture = tags_json[i]['entry_data']['ProfilePage'][0]['user']['profile_pic_url_hd']
		user_url = ('https://instagram.com/' + username)
		user_recents = ""
		print(user_followers)
		print(user_following)
		print(username)
		print(user_posts)
		print(user_url)
		print(user_profile_picture)
		storeData(username, user_url, user_posts, user_followers, user_following, user_profile_picture, user_recents)

def storeData(username, user_url, user_posts, user_followers, user_following, user_profile_picture, user_recents):
	try:
		cnx = mysql.connector.connect(**config)

	except mysql.connector.Error as err:
		if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
			print("Something is wrong with your user name or password")
		elif err.errno == errorcode.ER_BAD_DB_ERROR:
			print("Database does not exist")
		else:
			print(err)
	else:
		cursor = cnx.cursor()
		add_info = ("INSERT INTO ottawa_instagram "
               "(username, user_url, user_posts, user_followers, user_following, user_profile_picture, user_recents) "
               "VALUES (%s, %s, %s, %s, %s, %s, %s)")
		info_data = (username, user_url, user_posts, user_followers, user_following, user_profile_picture, user_recents)
		cursor.execute(add_info, info_data)
		cnx.commit()
		cursor.close()
		cnx.close()

extractLinksFromTopPosts()


# driver.close()