#!/usr/bin/python3

"""
Trigger slack website to create a public* history zip for <group>.slack.com.
Slack will send an email when it's completed.
This script stupidly waits for 10 seconds instead.
It then downloads the first zip (newest) on the exports page.

* public, if you want private groups, direct, deletions etc you have to pay.
  And paying is a much better option than this script.
"""

import sys, getopt, getpass
import requests
from bs4 import BeautifulSoup
from time import sleep

group = 'bogus'
email = 'dudette@bogus.com'
zip_file = 'output.zip';

try:
  opts, args = getopt.getopt(sys.argv[1:],"hg:e:o:",["group=","email=","output="])
except getopt.GetoptError:
  print(sys.argv[0] + ' -g <group> -e <email> -o <file.zip>')
  sys.exit(2)
for opt, arg in opts:
  if opt == '-h':
    print(sys.argv[0] + ' -g <group> -e <email> -o <file.zip>')
    sys.exit()
  elif opt in ("-g", "--group"):
    group = arg
  elif opt in ("-e", "--email"):
    email = arg
  elif opt in ("-o", "--output"):
    zip_file = arg
print('Group is ' + group)
print('Email is ' + email)
print('Output file is ' + zip_file)

password = getpass.getpass("Password: ")

baseurl = 'https://' + group + '.slack.com/'
export_url = baseurl + 'services/export'
sleep_time = 10

# Persistent session to avoid password issues.
s = requests.Session()

r = s.get(export_url)
page = BeautifulSoup(r.text)
# PAGE 1 FORM: 'log in and redirect'
#<form id="signin_form" action="/" method="post" accept-encoding="UTF-8">
#	<input type="hidden" name="signin" value="1" />
#	<input type="hidden" name="redir" value="/services/export" />
#	<input type="hidden" name="crumb" value="s-1428553775-d3d1f91abc-c" />
crumb = page.find('input', attrs = {'name':'crumb'})['value']
form_data = {
  'signin' : 1,
  'redir' : '/services/export',
  'crumb' : crumb,
  'email' : email,
  'password' : password 
}

post = s.post(baseurl, data=form_data, verify=False)
page = BeautifulSoup(post.text)

# PAGE 2 FORM: 'Start Export' button
#<form action="services/export" enctype="multipart/form-data" method="post">
# <input value="s-1428554236-443a2f9d66-o" name="crumb"></input>
# <input value="1" name="start_export"></input>
crumb = page.find('input', attrs = {'name':'crumb'})['value']

form_data = {
  'crumb' : crumb,
  'start_export' : 1
}

post = s.post(export_url, data=form_data, verify=False)
# PAGE 3 is unused, we are waiting.

print('While the zip is created: sleep ' + str(sleep_time) + '...')
sleep(sleep_time)

print('Refresh export page.')
r = s.get(export_url)
page = BeautifulSoup(r.text)

# PAGE 4 download links
first_download_link = page.find(lambda tag: (tag.name == 'a' and 'Ready for download' in tag.text), href=True)['href']

zip_url = baseurl + first_download_link;
print('Downloading ' + zip_url + ' as ' + zip_file)
with open(zip_file, 'wb') as handle:
    response = s.get(zip_url, stream=True)

    if not response.ok:
        print("woops, file download failed.")

    for block in response.iter_content(1024):
        if not block:
            break

        handle.write(block)

