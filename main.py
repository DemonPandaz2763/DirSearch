#!/usr/bin/env python3
import argparse
import requests
import sys
import signal
import time
import concurrent.futures
import threading
import json

from http import HTTPStatus

def print_banner_with_info(url, wordlist, extensions, threads, timeout, exclude):
    banner = r'''
                                        ⠀⠀⠀⠀⢰⣿⡿⠗⠀⠠⠄⡀⠀⠀⠀⠀
  ___  _     ___                  _     ⠀⠀⠀⠀⡜⢁⣀⡀⠀⠀⠀⠈⠑⢶⣶⡄
 |   \(_)_ _/ __| ___ __ _ _ _ __| |_   ⢀⣶⣦⣸⠈⢿⣟⡇⠀⠀⣀⣀⠀⠘⡿⠃
 | |) | | '_\__ \/ -_) _` | '_/ _| ' \  ⠀⢿⣿⣿⣄⠒⠀⠠⢶⡂⢫⣿⢇⢀⠃⠀
 |___/|_|_| |___/\___\__,_|_| \__|_||_| ⠀⠈⢿⡿⣿⣿⣶⣤⣀⣄⣀⣂⡠⠊⠀⠀
    v1.0.0                              ⠀⠀⠀⡇⠀⠀⠉⠙⠛⠿⣿⣿⣧⠀⠀⠀
                                        ⠀⠀⠀⣿⠀⠀⠀⠀⠀⠀⠘⣿⣿⡇⠀⠀
                                        ⠀⠀⠀⣿⣧⡤⠄⣀⣀⣀⣴⡟⠿⠃⠀⠀
                                        ⠀⠀⠀⢻⣿⣿⠉⠉⢹⣿⣿⠁⠀⠀⠀⠀
                                        ⠀⠀⠀⠀⠉⠁⠀⠀⠀⠉⠁⠀⠀⠀⠀⠀
'''
    
    info_block = f'''========================================================================================
Exts: {extensions} | Threads: {threads} | Timeout: {timeout} | Excluding: {exclude}

Target:       {url}
Wordlist:     {wordlist}
========================================================================================
'''
    full_banner = banner + info_block
    print(full_banner)


class DirScanner:
    def __init__(self, base_url, wordlist_path, extensions, threads=25, timeout=5, delay=0,
                 headers=None, proxies=None, recursive=False, max_depth=2, exclusions=None):
        self.base_url = base_url.rstrip('/')
        self.wordlist_path = wordlist_path
        self.extensions = extensions
        self.threads = threads
        self.timeout = timeout
        self.delay = delay
        self.headers = headers or {}
        self.proxies = proxies or {}
        self.recursive = recursive
        self.max_depth = max_depth
        self.exclusions = exclusions if exclusions is not None else [404]
        self.shutdown_flag = threading.Event()
        self.wordlist = self.prep_wordlist(wordlist_path)

    def signal_handler(self, sig, frame):
        if not self.shutdown_flag.is_set():
            self.shutdown_flag.set()

    def prep_wordlist(self, wordlist_path):
        try:
            with open(wordlist_path, 'r') as f:
                return [line.strip() for line in f if line.strip()]

        except FileNotFoundError:
            print(f"\033[91m[!]\033[0m Error getting wordlist: {wordlist_path}")
            sys.exit(1)

    def update_progress(self, current, total, start_time, bar_length=40):
        elapsed = time.time() - start_time
        req_rate = current / elapsed if elapsed > 0 else 0
        percent = float(current) / total

        hashes = f"\033[96m#\033[0m" * int(round(percent * bar_length))
        spaces = ' ' * (bar_length - len(hashes))
        progress_line = f"Scanning: [{hashes}{spaces}] {int(round(percent * 100))}% ({req_rate:.2f} req/s)"

        sys.stdout.write("\r\033[K" + progress_line)
        sys.stdout.flush()

    def print_message(self, message, current, total, start_time, bar_length=40):
        sys.stdout.write("\r\033[K")
        print(message)
        self.update_progress(current, total, start_time, bar_length)

    def build_urls(self, base_url):
        urls = []

        for word in self.wordlist:
            url = f"{base_url}/{word.lstrip('/')}"
            urls.append(url)
            for ext in self.extensions:
                urls.append(f"{url}.{ext}")

        seen = set()
        deduped_urls = []

        for u in urls:
            if u not in seen:
                deduped_urls.append(u)
                seen.add(u)
        return deduped_urls

    def parse_detailed_status(self, res):
        status = res.status_code
        if status in (301, 302):
            location = res.headers.get('Location', '')
            return f"[\033[93m{status}\033[0m] {HTTPStatus(status).phrase} -> \033[94m{location}\033[0m"
        else:
            if status == 200:
                return f"[\033[92m{status}\033[0m] {HTTPStatus(status).phrase}"
            else:
                return f"[\033[91m{status}\033[0m] {HTTPStatus(status).phrase}"

    def is_directory_listing(self, text):
        return text and "Index of" in text

    def worker_sync(self, full_url):
        if self.shutdown_flag.is_set():
            return (full_url, None, None, None, 'Shutdown in progress')

        try:
            res = self.session.get(full_url, timeout=self.timeout, headers=self.headers, proxies=self.proxies)
            numeric_status = res.status_code
            detailed_status = self.parse_detailed_status(res)
            response_text = res.text

            if self.delay:
                time.sleep(self.delay)
            return (full_url, numeric_status, detailed_status, response_text, None)

        except requests.RequestException as e:
            return (full_url, None, None, None, str(e))

    def scan_sync(self, base_url, current_depth=0):
        urls = self.build_urls(base_url)
        total_urls = len(urls)
        processed = 0
        start_time = time.time()
        self.session = requests.Session()

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.threads) as executor:
            future_to_url = {executor.submit(self.worker_sync, url): url for url in urls}
            for future in concurrent.futures.as_completed(future_to_url):
                if self.shutdown_flag.is_set():
                    for fut in future_to_url:
                        fut.cancel()
                    break

                url, numeric_status, detailed_status, response_text, error = future.result()
                processed += 1

                if numeric_status in self.exclusions:
                    self.update_progress(processed, total_urls, start_time)
                    continue

                if error:
                    self.print_message(f"\033[91m[!]\033[0m Error requesting {url}: {error}", processed, total_urls, start_time)
                else:
                    self.print_message(f"{detailed_status} Found: \033[94m{url}\033[0m", processed, total_urls, start_time)

                    if self.recursive and current_depth < self.max_depth and self.is_directory_listing(response_text):
                        print(f"\n\033[96mRecursively scanning: {url}\033[0m")
                        self.scan_sync(url, current_depth + 1)
        
        self.session.close()
        if self.shutdown_flag.is_set():
            print(f'\n\033[91m[!]\033[0m Scan interrupted by user.')
        else:
            sys.stdout.write("\n")

    def run(self):
        self.scan_sync(self.base_url)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--url', required=True, type=str, help='Target URL')
    parser.add_argument('-w', '--wordlist', required=True, help='Path to the wordlist file')
    parser.add_argument('-e', '--extensions', default='php,txt,jsp,html,js', type=str, help='Comma-separated list of extensions (e.g. php,txt,jsp,html,js)')
    parser.add_argument('-t', '--threads', default=25, type=int, help='Number of threads (default: 25)')
    parser.add_argument('--timeout', default=5, type=int, help='Timeout for requests (default: 5)')
    parser.add_argument('--delay', default=0, type=float, help='Delay between requests in seconds')
    parser.add_argument('--headers', type=str, help='Custom headers as JSON string')
    parser.add_argument('--proxy', type=str, help='Proxy URL (e.g., http://proxy:port)')
    parser.add_argument('--recursive', action='store_true', help='Enable recursive scanning')
    parser.add_argument('--max-depth', default=2, type=int, help='Maximum recursion depth')
    parser.add_argument('--exclude', default='404', type=str, help='Comma-separated list of status codes to ignore (default: 404)')
    args = parser.parse_args()

    extensions = [ext.strip() for ext in args.extensions.strip(',').split(',') if ext.strip()]

    headers = {}
    if args.headers:
        try:
            headers = json.loads(args.headers)
        except json.JSONDecodeError:
            print(f"\033[91m[!]\033[0m Invalid JSON for headers.")
            sys.exit(1)

    proxies = {}
    if args.proxy:
        proxies = {'http': args.proxy, 'https': args.proxy}

    exclusions = [int(code.strip()) for code in args.exclude.split(',') if code.strip()]

    print_banner_with_info(
        url=args.url,
        wordlist=args.wordlist,
        extensions=extensions,
        threads=args.threads,
        timeout=args.timeout,
        exclude=exclusions
    )

    scanner = DirScanner(
        base_url=args.url,
        wordlist_path=args.wordlist,
        extensions=extensions,
        threads=args.threads,
        timeout=args.timeout,
        delay=args.delay,
        headers=headers,
        proxies=proxies,
        recursive=args.recursive,
        max_depth=args.max_depth,
        exclusions=exclusions
    )

    signal.signal(signal.SIGINT, scanner.signal_handler)
    scanner.run()

if __name__ == '__main__':
    main()
