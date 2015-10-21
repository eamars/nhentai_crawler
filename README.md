Python Web Crawer
=================

Acknowledgment: Webpage may contain materials that are not suitable for you. 

A simple multi-thread web crawers that downloads comics from [nhentai (NSFW)](http://nhentai.net)

Features:
- Download comics from with certain tags
- Co-currently downloading
- MySQL database is required

Installation
------------

Download and build from source:
	
	git clone git@github.com:eamars/nhentai_crawer.git

Python Web Crawer requires bs4, mysql.connector for external functions

Usage
-----

You need to setup your mysql database before startting web crawer. An example config is shown below

```dosini
NUM_WORKERS = 10
DB_NAME = "nhentai"
TABLE_NAME = "downloaded"
SQL_CONFIG = {
	    "host": "localhost",
	    "user": "username",
	    "password": "password",
	    "autocommit": True
}
```

Before running, you need to specify the tags and page number in code. In example, "chinese" and page i were used

	tasks = get_page_content("chinese", str(i))

To start crawer, you need to run script with Python3 interpreter

	python3 main.py

Crawer will download comics into download folder in the same directory.




