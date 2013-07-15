'''
A quick sketch to demonstrate uploading library trip material.
'''

import requests
import json
import urllib
import sys, os
import subprocess
from PIL import Image, ImageFilter

USERNAME = "LibraryTripperBot"
API_URL = "http://wikipaltz.org/api.php"

DIRECTORY = sys.argv[1]
COLUMN_TOLERANCE = 600

def show_userinfo():
	more_params = dict(action="query", meta="userinfo", format="json")
	r = s.get(API_URL, params=more_params)
	print r.content


def login(session=requests.Session()):

	login_params = dict(action="login",
		            lgname=USERNAME,
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


def upload(file, text, session=requests.Session()):
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
    upload_response = session.post(API_URL, params=upload_params, files=files)
    return upload_response


def ocr_read(filename, program="tesseract"):

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
    '''
    
    '''
    size = 1600,1600
    im = Image.open(filename)
    im.thumbnail(size, Image.ANTIALIAS)
    im.save("%s-resized.jpg" % filename, "JPEG")

    return im


def find_column(filename=None, image=None, tolerance=COLUMN_TOLERANCE):
    hit_pixels = {}
    detected_columns = []

    if not image:
        image = Image.open(filename)
    width, height = image.size
    rgb_im = image.convert('RGB')


    # We only want to scan the middle of the image.
    left_start = (width / 2) - 400
    right_end = (width / 2) + 400

    for w in range(left_start, right_end):
        for h in range(height):
            r, g, b = rgb_im.getpixel((w, h))
        
            if (r + g + b) < tolerance:
                # hit!
                try:
                     hit_pixels[w].append(h)
                except KeyError:
                     hit_pixels[w] = [h]

                # We only want columns that consistently hit down the page.
                if len(hit_pixels[w]) > 4:
                    # print "hit pixels: %s" % hit_pixels[w] # debug
                    detected_columns.append(w)
                    break


    # Ensure that we only have one column    
    previous_c = None
    for c in detected_columns:
        if previous_c and not (c - previous_c) < 2:
            print "Tolerance too high for %s. Columns detected at %s" % (image, detected_columns)
            return find_column(image=image, tolerance=tolerance-20)
        previous_c = c

    # Great.  We only have one.  Is it huge?
    if len(detected_columns) > 5:
        mid_column = len(detected_columns) / 2
        
        # If it is, take only the middle of it.
        detected_columns = detected_columns[(mid_column - 2):(mid_column + 2)]

    # return the left and rightmost edges of the line
    try:
	left = detected_columns[0] - 3
	right = detected_columns[-1] + 3
    except IndexError:
        raise RuntimeError('No columns found.  Hit pixels: %s' % hit_pixels)
    return left, right


def split_vertical(filename):
    image = Image.open(filename)
    width, height = image.size    

    left, right = find_column(image=image)
    left_crop = image.crop((0, 0, left, height))
    right_crop = image.crop((right, 0, width, height))

    left_crop.save('left-%s.jpg' % filename.split('/')[-1])
    right_crop.save('right-%s.jpg' % filename.split('/')[-1])


        
    

for filename in os.listdir(DIRECTORY):
    print "trying %s" % filename
    split_vertical(DIRECTORY + filename)



exit()


session = login(s)
                       

if "==NOCR==" in FILENAME:
    file_text = "[[Category:No OCR]]"
else:
    file_text = "==Tesseract OCR Result==\n%s\
		  \n==Cuneiform OCR Result==\n%s\
		  \n[[Category:Uncurated Images]][[Category:OCR]]" % (ocr_read(), ocr_read(program="cuneiform"))




resize()
print upload("%s-resized.jpg" % FILENAME, file_text, session=session).content


