from __future__ import print_function
import httplib2
import os
import time
import io

from apiclient import discovery
from apiclient.http import MediaIoBaseDownload, MediaFileUpload
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

from parser import is_ecg, is_ppg, parse_data, TYPE_ECG
from filters import power_line_noise_filter
from filters import high_pass_filter
from filters import low_pass_filter
from plots import ecg_to_png

import numpy as np
import matplotlib.pyplot as plot

ECG_FS = 512
LOW_PASS_CUTOFF = 35
HIGH_PASS_CUTOFF = 0.5

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/drive-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Drive API Python Quickstart'
CHANGES_START_TOKEN_FILE = 'changes_start_token.txt'
MONITOR_FOLDER_ID = '1JhRkeKNactLp40gmVUSUMKklB5LJwx7j'
PNG_FOLDER_ID = '1G0pFjG8pp1qG2KxcnE-xIZ64CuKeRkGW'
POLLING_CHANGES_SECOND = 45
CACHE_FOLDER = '.cache'

def create_cache_dir():
    if not os.path.exists(CACHE_FOLDER):
       os.makedirs(CACHE_FOLDER)

def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'drive-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def get_latest_start_page_token(service):
    resp = service.changes().getStartPageToken().execute()
    return resp.get('startPageToken')

def get_saved_start_page_token():
    if not os.path.exists(CHANGES_START_TOKEN_FILE):
        return None

    f = open(CHANGES_START_TOKEN_FILE, "r")
    token = f.readline().rstrip("\n")
    f.close()
    return token

def save_start_page_token(token):
    f = open(CHANGES_START_TOKEN_FILE, "w")
    f.write(token)
    f.close()

def get_start_page_token(service):
    token = get_saved_start_page_token()
    if token is None:
        token = get_latest_start_page_token(service)
        save_start_page_token(token)
    return token

def list_changes(service, token):
    """ Return changes and newStartPageToken """
    start = token
    while True:
        resp = service.changes().list(pageToken=start, spaces='drive').execute()
        yield (resp.get('changes'), resp.get('newStartPageToken'))

        if resp.get('nextPageToken'):
            start = resp.get('nextPageToken')
        if resp.get('newStartPageToken'):
            break;

def filter_changes(service, token):
    """ Return (trashed, change, newStartPageToken) """
    for changes, new in list_changes(service, token):
        for c in changes:
            if c.get('file'):
                ignore = False
                # check if the parent directoy is what we want
                resp = service.files().get(fileId=c.get('file').get('id'), fields='trashed,parents').execute()
                if resp.get('parents') and resp.get('parents')[0] == MONITOR_FOLDER_ID:
                    if resp.get('trashed'):
                        # ignore those files moved to trash can
                        yield True, c, new
                    else:
                        yield False, c, new

def download_file(service, file_id):
    req = service.files().get_media(fileId=file_id)
    f = io.BytesIO()
    downloader = MediaIoBaseDownload(f, req)
    done = False
    while not done:
       status, done = downloader.next_chunk()
       print('downloading: ', status.progress())
    # seek to the begining of the file and reuse
    f.seek(0)
    return f

def upload_png(service, local_file_path, remote_file_name):
    file_metadata = {'name': remote_file_name,
                     'parents': [PNG_FOLDER_ID]}
    media = MediaFileUpload(local_file_path, mimetype='image/png')
    resp = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print('Uploaded: ', resp)

def process(service, change):
    # debug
    print(change)
    # prepare png name
    file_name = change.get('file').get('name')
    png_name = os.path.splitext(file_name)[0] + '.png'
    local_png_path = os.path.join(CACHE_FOLDER, png_name)
    # download from upstream
    f = download_file(service, change.get('file').get('id'))
    # parse
    data = parse_data(f, TYPE_ECG)
    data = np.array(data)
    # filter
    filtered = data[:,1]
    filtered = power_line_noise_filter(filtered, ECG_FS)
    filtered = high_pass_filter(filtered, ECG_FS, HIGH_PASS_CUTOFF)
    filtered = low_pass_filter(filtered, ECG_FS, LOW_PASS_CUTOFF)
    filtered = np.column_stack((data[:,0], filtered))
    # save to png
    ecg_to_png(filtered, local_png_path)
    # upload
    upload_png(service, local_png_path, png_name)

def main():
    create_cache_dir()
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('drive', 'v3', http=http)

    curr_token = get_start_page_token(service)

    while True:
        print('current token: ', curr_token)
        new_token = None
        for trashed, c, new_token in filter_changes(service, curr_token):
            # process changes
            if not trashed and c:
                process(service, c)

        print('new token: ', new_token)
        if new_token:
             save_start_page_token(new_token)
             curr_token = new_token

        # print('sleep!')
	time.sleep(POLLING_CHANGES_SECOND)
        # print('wakeup!')

    #results = service.files().list(
    #    pageSize=10,fields="nextPageToken, files(id, name)").execute()
    #items = results.get('files', [])
    #if not items:
    #    print('No files found.')
    #else:
    #    print('Files:')
    #    for item in items:
    #        print(type(item))
    #        print(item)
    #        #print('{0} ({1})'.format(item['name'], item['id']))

if __name__ == '__main__':
    main()
