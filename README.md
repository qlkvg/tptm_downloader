# Talk Python To Me downloader

Simple script to download [Talk Python To Me](https://talkpython.fm/) and [Python Bytes](https://pythonbytes.fm/) podcasts. Supports multithreaded downloading. Requires python 3.6.


## Dependencies

- [requests](https://pypi.org/project/requests/) 
- [beautifulsoup4](https://pypi.org/project/beautifulsoup4/) 


## Installation

Easiest way is to use pipenv

    pipenv install

## Usage

Just execute as any regular python script

    python3 ./tptm-downloader.py
    
By default it will download all available episodes.
For help execute

    python3 ./tptm-downloader.py --help
    