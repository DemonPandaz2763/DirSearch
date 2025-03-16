# DirSearch

## Overview

DirSearch is a multi-threaded directory scanning tool written in Python. It helps you discover hidden or unlisted directories and files on a target web server by appending words from a user-provided wordlist with optional file extensions. Whether you need a quick scan or a recursive deep dive, DirSearch is built to be flexible, efficient, and easy to use.

## Features
 - **Multi-threaded Scanning:** Leverages Python's threading and concurrent execution to scan multiple URLs concurrently.
 - **Custom Wordlist & Extensions:** Generate target URLs by combining base paths from a wordlist with optional file extensions.
 - **Recursive Scanning:** Optionally follow directory listings to perform recursive scans up to a specified depth.
 - **Customizable Options:** Supports custom HTTP headers, proxy settings, and request timeouts.
 - **Status Filtering:** Ignore specified HTTP status codes (e.g., 404) to focus on interesting results.

## Requirements
 - Python 3.x
 - Requests

## Installation
1. Clone the repo:
```
git clone https://github.com/Demonpandaz2763/dirscanner.git
```
3. Cd to repo directory:
```
cd dirscanner
```
4. Install the required dependencies:
```
pip3 install -r requirements.txt
```

## Usage

Run the script using Python with various options:
```
python3 main.py -u http://example.com -w /path/to/wordlists/words.txt
```

### Command-Line Options
```
usage: main.py [-h] [-u URL] [-w WORDLIST] [-e EXTENSIONS] [-t THREADS] [--timeout TIMEOUT] [--delay DELAY]
               [--headers HEADERS] [--proxy PROXY] [--recursive] [--max-depth MAX_DEPTH] [--exclude EXCLUDE]

options:
  -h, --help            show this help message and exit
  -u URL, --url URL     Target URL
  -w WORDLIST, --wordlist WORDLIST
                        Path to the wordlist file
  -e EXTENSIONS, --extensions EXTENSIONS
                        Comma-separated list of extensions (e.g. php,txt,jsp,html,js)
  -t THREADS, --threads THREADS
                        Number of threads (default: 25)
  --timeout TIMEOUT     Timeout for requests (default: 5)
  --delay DELAY         Delay between requests in seconds
  --headers HEADERS     Custom headers as JSON string
  --proxy PROXY         Proxy URL (e.g., http://proxy:port)
  --recursive           Enable recursive scanning
  --max-depth MAX_DEPTH
                        Maximum recursion depth
  --exclude EXCLUDE     Comma-separated list of status codes to ignore (default: 404)
```
---
**Note:** This is **NOT** the original DirSearch.
