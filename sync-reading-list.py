import orgparse
import datetime
import re
import requests
import os
import json
from ebooklib import epub
import fileinput
from rapidfuzz import fuzz

with open("options.json", 'r') as f:
    options = json.load(f)
    ORG_FILE = options["ORG_FILE"]
    MARGINALIA_DIRECTORY = options["MARGINALIA_DIRECTORY"]
    REMARKABLE_FOLDER_NAME = options["REMARKABLE_FOLDER_NAME"]
    REMARKABLE_ADDRESS = options["REMARKABLE_ADDRESS"]

LAST_SYNC_FILE = 'last-sync-datetime.txt'

# reMarkable USB web interface API documented (not entirely accurately) here:
# https://remarkable.guide/tech/usb-web-interface.html

def needs_sync(node, todo_states, last_sync_datetime):
    if node.todo not in todo_states:
        return False
    if not node.repeated_tasks:
        return False
    reading_datetime = max(state.start
                           for state in node.repeated_tasks
                           if state.after in todo_states)
    return reading_datetime > last_sync_datetime


def get_remarkable_folder_id():
    '''Get the folder guid, and set it as the
    current directory for uploads'''

    r = requests.get(f"{REMARKABLE_ADDRESS}/documents/")
    for folder_metadata in r.json():
        if folder_metadata['VissibleName'] == REMARKABLE_FOLDER_NAME:
            # Requesting the folder's contents is how the reMarkable
            # web interface knows which folder to upload things to later
            guid = folder_metadata['ID']
            requests.get(f"{REMARKABLE_ADDRESS}/documents/{guid}")
            return guid

    print(f"Couldn't find folder on remarkable named {REMARKABLE_FOLDER_NAME}")


def get_book_filename(node):
    file_link = node.get_property('FILE')
    if not file_link:
        print(f"{node.heading} does not have a linked file.")
        return

    marginalia_link = node.get_property('MARGINALIA')
    if marginalia_link and  get_yes_no_input(f'{node.heading} has marginalia saved. Do you want to upload that instead of the original file?'):
        file_link = marginalia_link

    m = re.match(r"\[\[file:(.+)\]\[Link to file\]\]", file_link)
    if m is None:
        print(f"{node.heading} has an incorrectly formatted file link")
        return

    return os.path.expanduser(m.group(1))


def upload_to_remarkable(node):
    filename = get_book_filename(node)
    if filename is None:
        return

    print(f"Uploading {node.heading}")

    # This uploads to most recently requested directory, which we've already handled.
    url = f"{REMARKABLE_ADDRESS}/upload"
    headers = {
        'Origin': REMARKABLE_ADDRESS,
        'Accept': '*/*',
        'Referer': REMARKABLE_ADDRESS + "/",
        'Connection': 'keep-alive'
    }
    files = {'file': open(filename, 'rb')}
    r = requests.post(url, headers=headers, files=files)
    if r.status_code == 201:
        print(f"Successfully uploaded {filename}")
    else:
        print(f"Failed to upload {filename}")
        print(f"HTTP response {r.status_code}")
        print(f"text: {r.text}")


def get_yes_no_input(prompt):
    while True:
        user_input = input(prompt + " (y/n): ").lower()
        if user_input in ("y", "yes"):
            return True
        elif user_input in ("n", "no"):
            return False
        else:
            print("Invalid input. Please enter 'y' for yes or 'n' for no.")


def get_remarkable_guid(book_filename, reading_folder_guid):
    # This seems to be how reMarkable names things
    if book_filename[-4:] == '.pdf':
        vissiblename = os.path.basename(book_filename)
    elif book_filename[-5:] == '.epub':
        book = epub.read_epub(book_filename)
        vissiblename = book.title
    else:
        print("Unsupported file format; must be .epub or .pdf")
        return

    r = requests.get(f"{REMARKABLE_ADDRESS}/documents/{reading_folder_guid}")

    # Exact matches we'll return automatically, but apparently some characters
    # get messed up, so if there's no exact match we'll find the best fuzzy
    # match and confirm with user.
    best_match = (None, None, 0)
    for item_metadata in r.json():
        if item_metadata['VissibleName'] == vissiblename:
            return item_metadata['ID']
        match_score = fuzz.ratio(vissiblename, item_metadata['VissibleName'])
        if match_score > best_match[2]:
            best_match = (item_metadata['ID'], item_metadata['VissibleName'], match_score)

    if get_yes_no_input(f"No exact match found, is {best_match[1]} right?"):
        return best_match[0]


def download_marginalia(node, reading_folder_guid):
    filename = get_book_filename(node)
    if not filename:
        return
    guid = get_remarkable_guid(filename, reading_folder_guid)
    if not guid:
        print("Failed to resolve guid of book on reMarkable. Please manually export.")
        return

    marginalia_filename = MARGINALIA_DIRECTORY + os.path.basename(filename)
    if marginalia_filename[-5:] == '.epub':
        marginalia_filename = marginalia_filename[:-5] + '.pdf'

    r = requests.get(f"{REMARKABLE_ADDRESS}/download/{guid}/placeholder")
    if r.status_code != 200:
        print("Failed to download marginalia from reMarkable. Please manually export.")
        return
    with open(marginalia_filename, "wb") as f:
        f.write(r.content)
    print("Successfully saved marginalia to")
    print(marginalia_filename)
    return marginalia_filename


def add_marginalia_link(node, marginalia_filename):
    book_filename = get_book_filename(node)
    if not book_filename:
        return

    print("Adding marginalia link to reading list.")
    for line in fileinput.FileInput(ORG_FILE, inplace=True):
        if book_filename in line and ':FILE:' in line:
            line += f":MARGINALIA: [[file:{marginalia_filename}][Link to file]]" + os.linesep
            print(line, end="") # Trusting there's only one :FILE: link per node
        elif marginalia_filename in line and ':MARGINALIA:' in line:
            print('', end="") # Deletes old marginalia link
        else:
            print(line, end="")


def main():
    org_root = orgparse.load(ORG_FILE)
    with open(LAST_SYNC_FILE) as f:
        last_sync_datetime = datetime.datetime.fromisoformat(f.read().strip())

    print(f"\nLast sync: {last_sync_datetime}\n")

    try:
        reading_folder_guid = get_remarkable_folder_id()
    except Exception as e:
        print("Failed to connect to reMarkable. Try restarting it (ssh remarkable 'systemctl restart xochitl'). Error:\n")
        print(e)
        return

    for node in org_root[1:]:
        try:
            if needs_sync(node, ['READING'], last_sync_datetime):
                upload_to_remarkable(node)
            if needs_sync(node, ['READ', 'ABANDONED'], last_sync_datetime):
                if get_yes_no_input(f"Do you want to download marginalia for {node.heading}?"):
                    marginalia_filename = download_marginalia(node, reading_folder_guid)
                    if marginalia_filename:
                        add_marginalia_link(node, marginalia_filename)
                print(f"Don't forget to delete {node.heading} manually (and bother reMarkable about adding deletion to the web interface).")
                print()
        except Exception as e:
            print("Failed to process a node:\n")
            print(node)
            print("\nError:\n")
            print(e)

    with open(LAST_SYNC_FILE, 'w') as f:
        f.write(datetime.datetime.now().isoformat())


main()
