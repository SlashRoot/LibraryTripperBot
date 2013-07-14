'''
A quick sketch to demonstrate uploading library trip material.
'''

import requests
import json
import urllib
import sys
import subprocess
from PIL import Image

API_URL = "http://wikipaltz.org/api.php"
s = requests.Session()

FILENAME = sys.argv[1]

def show_userinfo():
	more_params = dict(action="query", meta="userinfo", format="json")
	r = s.get(API_URL, params=more_params)
	print r.content


def login(session):

	login_params = dict(action="login",
		            lgname="LibraryTripperBot",
		            lgpassword=None, # Replace with password
		            format="json")

	response = s.post(API_URL, params=login_params)
	response_dict = json.loads(response.content)


	print "Getting login token:"
	print response_dict

	login_params['lgtoken'] = response_dict['login']['token']

	second_response = s.post(API_URL, params=login_params)
	response_dict = json.loads(second_response.content)

	print
	print "Attempted to login:"
	print response_dict

	return session


def get_edit_token(name):
        print
        print "Obtaining edit token:"
	get_edit_token_params = dict(action="query",
		           format="json",
		           prop="info",
		           intoken="edit",
                           titles=name,
		           )

	if name:
            get_edit_token_params['titles'] = name

	edit_token_response = s.post(API_URL, params=get_edit_token_params)
	response_dict = json.loads(edit_token_response.content)

        print edit_token_response.content
	edit_token = response_dict['query']['pages']['-1']['edittoken']
	return edit_token


def edit(edit_token):

	edit_params = dict(action="edit",
		           title="User:LibraryTripperBot",
		           format="json",
		           summary="I'm alive!",
		           text="Hi.  I'm slashRoot's Library Tripper Bot.  I automate the process of getting content gathered at library trips up on WikiPaltz.",
		           token=edit_token)

	print s.headers
	s.headers.update({"Content-Type":"application/x-www-form-urlencoded"})

	edit_response = s.post(API_URL, params=edit_params)
	response_dict = json.loads(edit_response.content)

	print response_dict
	print edit_response.headers


def upload(file, text):
    files = {'file': open(file, 'rb')}
    token = get_edit_token(file)
    print "Got edit token %s.  Now uploading." % token
    upload_params = dict(action="upload",
                         format="json",
                         ignorewarnings="true",
                         filename=file,
                         text=text,
                         token=token)

    print upload_params
    upload_response = s.post(API_URL, params=upload_params, files=files)
    return upload_response


def ocr_read(program="tesseract", filename):

	print "Starting %s Read." % program

        if program == "tesseract":
            p = subprocess.Popen('tesseract "%s" output-t' % filename, shell=True, stdout=subprocess.PIPE)

	elif program == "cuneiform":
            p = subprocess.Popen('cuneiform "%s" -o output-c.txt' % filename, shell=True, stdout=subprocess.PIPE)
        else:
            raise ValueError("Don't know how to implement %s - use either tesseract (default) or cuneiform" % program)
	
        out, err = p.communicate()
	print out, err

        result = open('output-%s.txt' % program[0], "r").read()
        return result


def resize(filename):
    size = 1600,1600
    im = Image.open(filename)
    im.thumbnail(size, Image.ANTIALIAS)
    im.save("%s-resized.jpg" % filename, "JPEG")

login(s)
                       

if "==NOCR==" in FILENAME:
    file_test = "[[Category:No OCR]]
else:
    file_text = "==Tesseract OCR Result==\n%s\
		  \n==Cuneiform OCR Result==\n%s\
		  \n[[Category:Uncurated Images]][[Category:OCR]]" % (ocr_read(), ocr_read(program="cuneiform"))


resize()
print upload("%s-resized.jpg" % FILENAME, file_text).content


