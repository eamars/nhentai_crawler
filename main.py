import threading
import queue
import time
import urllib.request
import gzip
import bs4
from bs4 import BeautifulSoup
import os
import re
import hashlib
from sql import *


NUM_WORKERS = 10
DB_NAME = "nhentai"
TABLE_NAME = "downloaded"
SQL_CONFIG = {
    "host": "192.168.2.5",
    "user": "eamars",
    "password": "931105",
    "autocommit": True
}


def md5(string):
    m = hashlib.md5()
    m.update(string)
    return m.hexdigest()


def http_request(url):
    # Build custom http header
    request = urllib.request.Request(url)
    request.add_header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.71 Safari/537.36")
    request.add_header("Accept", "*/*")
    request.add_header("Accept-Encoding", "gzip, deflate, sdch")
    request.add_header("Accept-Language", "en,zh-CN;q=0.8,zh;q=0.6")

    # Get http response
    response = urllib.request.urlopen(request)

    return response


def get_page_content(tags, page_num):
    tasks = list()

    # Page template
    url = "http://nhentai.net/search/?q={}&page={}".format(tags, page_num)

    try:
        response = http_request(url)
    except Exception as e:
        print(e)
        return None

    # Decompress response and decode into plain string
    buffer = gzip.decompress(response.read()).decode("utf-8")

    # Parse content
    parsed = BeautifulSoup(buffer, 'html.parser')
    gallery = parsed.body.main.div.div
    for div in gallery:
        # Filter out NavigableString class
        if isinstance(div, bs4.NavigableString):
            continue
        album = dict()
        album["data-tags"] = div.attrs["data-tags"]
        album["href"] = div.a.attrs["href"]
        album["cover"] = div.a.img.attrs["src"]
        album["caption"] = div.a.div.get_text()
        tasks.append(album)

    return tasks


def get_cover_image(thread_id, task):
    http_template = "http:"
    download_folder_template = "download/{}"

    # Create download folder
    download_folder = download_folder_template.format(task["caption"])

    if not os.path.exists(download_folder):
        try:
            os.makedirs(download_folder)
        except Exception as e:
            print(thread_id + ": Error when creating dir [" + download_folder + " ]")
    else:
        print(thread_id + ": directory already exists [" + task["caption"] + "]")

    # Download cover
    cover_filename = download_folder + "/cover.jpg"
    cover_fp = open(cover_filename, "wb")

    url = http_template + task["cover"]
    response = http_request(url)

    cover_fp.write(response.read())
    cover_fp.close()


def get_album_image(thread_id, task):
    url_template = "http://nhentai.net{}"
    http_template = "http:"
    download_folder_template = "download/{}"

    # Create download folder
    download_folder = download_folder_template.format(task["caption"])

    # Create url
    url = url_template.format(task["href"])

    # Download image from each page
    i = 1
    while True:
        image_url = "{}{}/".format(url, i)
        print(thread_id, "downloading from ", image_url)
        try:
            response = http_request(image_url)
        except Exception as e:
            break

        buffer = gzip.decompress(response.read()).decode("utf-8")

        # Parse
        parsed = BeautifulSoup(buffer, 'html.parser')
        image_exact_url = parsed.body.main.div.div.find("section", {"id": "image-container"}).a.img.attrs["src"]

        # Download pic
        image_filename = download_folder + "/{}.jpg".format(i)
        image_fp = open(image_filename, "wb")

        response = http_request(http_template + image_exact_url)

        image_fp.write(response.read())
        image_fp.close()

        i += 1

    # Store hashed title of album
    md5string = md5(task["caption"].encode())
    datatags = task["data-tags"]

    # Download complete, then add entry to database
    connection = establish_connection(SQL_CONFIG)
    connect_database(connection, DB_NAME)
    insert_entry(connection, TABLE_NAME, "(md5hash, datatags) VALUES ('{}', '{}')".format(md5string, datatags))
    close_connection(connection)


# Workers
def worker(args):
    task_queue = args

    # Get thread id
    thread_id = threading.current_thread().name
    print(thread_id, "starts")

    while True:
        task = task_queue.get()

        # Stop condition
        if task is None:
            break

        # Make sure getting correct object
        assert isinstance(task, dict)
        print(thread_id, "receive", task)

        # Task start
        get_cover_image(thread_id, task)
        get_album_image(thread_id, task)

        # Task end
        task_queue.task_done()
        print(thread_id, "done")
    print(thread_id, "exits")


def main():
    # Create FIFO queue
    task_queue = queue.Queue()

    # Create thread pool
    thread_pool = []

    # Connect to database
    connection = establish_connection(SQL_CONFIG)
    connect_database(connection, DB_NAME)

    # Init workers
    for n in range(NUM_WORKERS):
        thread = threading.Thread(target=worker, args=[task_queue])
        thread.start()
        thread_pool.append(thread)

    # Assign tasks
    for i in range(1, 5):
        tasks = get_page_content("chinese", str(i))
        for task in tasks:
            # Test if already exists
            md5string = md5(task["caption"].encode())
            datatags = task["data-tags"]
            sql_cond = "md5hash='{}'".format(md5string)

            # If entry is already downloaded, then skip,
            # otherwise the entry is added into downloading queue
            if not entry_exists(connection, TABLE_NAME, sql_cond):
                print("Downloading album: [{}]".format(task["caption"]))
                task_queue.put(task)

            else:
                print("Album skip: [{}]".format(task["caption"]))

    # Complete tasks
    for n in range(NUM_WORKERS):
        task_queue.put(None)

    print("Waiting...")

    # Wait until all threads terminated
    for thread in thread_pool:
        thread.join()

    # Close connection
    close_connection(connection)
    print("Done")

if __name__ == "__main__":
    main()
