import requests
import logging
import os
import threading
import queue
import time
import argparse
from urllib.parse import urljoin
from bs4 import BeautifulSoup


logging.basicConfig(format='%(asctime)s | %(filename)s:%(lineno)s:%(funcName)s | %(levelname)s:%(message)s',
                            level=logging.INFO)
logger = logging.getLogger()


def get_parser():
    parser = argparse.ArgumentParser(
        description="""downloader for Talk Python To Me and Python Bytes podcasts""",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '-a', '--episodes_amount', help="number of episodes to download, 0 for all",
        type=int, nargs='?', default=0)
    parser.add_argument(
        '-t', '--threads', help="number of threads to use for downloading",
        type=int, nargs='?', default=1)
    parser.add_argument(
        '-f', '--folder', help="folder to store mp3 files",
        type=str, nargs='?', default=".")
    parser.add_argument(
        '-n', '--podcast_name', help="podcast to download (Talk Python To Me or Python Bytes)",
        type=str, nargs='?', default="tptm", choices=["tptm", "bytes"])
    return parser


class BaseDownloader:
    def __init__(self, start_page: str, download_folder: str="."):
        """
        init downloader with start page uri
        :param start_page: uri of start page
        """
        self.session = requests.session()
        self.start_page = start_page
        self.download_folder = download_folder

    @staticmethod
    def download_mp3(mp3_link: str, folder: str = ".", filename: str = None) -> str:
        """
        download mp3 by given link
        :param mp3_link: link to mp3
        :param folder: folder where to save mp3
        :param filename: custom filename to store
        :return:
        """
        if not filename:
            filename = mp3_link.split("/")[-1]
        logger.info("starting download mp3: {}".format(filename))
        if not os.path.exists(folder):
            logger.info("making directory: {}".format(folder))
            os.makedirs(folder)
        full_path = os.path.join(folder, filename)
        mp3 = requests.get(mp3_link)
        with open(full_path, 'wb') as f:
            f.write(mp3.content)
        logger.info("finished download mp3: {}".format(filename))
        return full_path

    def parallel_download(self, links: list, threads_number: int=1):
        start_timestamp = time.time()
        tasks = []
        links_queue = queue.Queue()
        for each in links:
            links_queue.put(each)
        for i in range(threads_number):
            task = threading.Thread(
                target=self.download_task, name="dnld_thread_{}".format(i), args=(links_queue, )
            )
            tasks.append(task)
        for task in tasks:
            task.start()
        for task in tasks:
            task.join()
        logger.info("estimated for parallel download with {} threads: {}".format(
            threads_number, time.time() - start_timestamp
        ))

    def download_task(self, *args, **kwargs):
        raise NotImplementedError


class TptmDownloader(BaseDownloader):
    def parse_and_get_mp3_link(self, uri) -> str:
        """
        get mp3 link from given uri
        :param uri: uri to find mp3 link
        :return: link to mp3
        """
        req = self.session.get(uri)
        soup = BeautifulSoup(req.text)
        buttons = soup.find("div", {"class": "episode-buttons"})
        for button in buttons.find_all('a'):
            try:
                if "download" in button.text.lower():
                    link = urljoin(uri, button.get("href"))
                    return link
            except BaseException:
                logger.exception("something went wrong while trying to download mp3")
        return ""

    def get_links(self, count: int=None) -> list:
        """
        get links to podcasts from given start page
        :param count: count of links to return. None for all
        :return:
        """
        req = self.session.get(self.start_page)
        soup = BeautifulSoup(req.text)
        tbl = soup.find("table", {"class": "episodes"})
        trs = tbl.find_all("tr")
        links = []
        for tr in trs:
            link_raw = tr.find("a")
            if link_raw:
                link = urljoin(self.start_page, link_raw.get("href"))
                links.append(link)
        if count:
            return links[:count]
        return links

    def download_task(self, links_queue: queue.Queue):
        """
        :param links_queue: queue object
        :return:
        """
        while not links_queue.empty():
            cur_thread = threading.current_thread()
            link = links_queue.get()
            logger.info("{}: get link to process: {}".format(cur_thread.name, link))
            if link is None:
                break
            mp3_link = self.parse_and_get_mp3_link(link)
            logger.info("{}: get mp3 link: {}".format(cur_thread.name, mp3_link))
            splitted = mp3_link.split("/")
            filename = "{}-{}".format(splitted[-2], splitted[-1])
            self.download_mp3(mp3_link, self.download_folder, filename)
            logger.info("{}: download task done".format(cur_thread.name))
            links_queue.task_done()

if __name__ == "__main__":
    parsed_args = get_parser().parse_args()
    if parsed_args.podcast_name == "tptm":
        start_uri = "https://talkpython.fm/episodes/all"
    elif parsed_args.podcast_name == "bytes":
        start_uri = "https://pythonbytes.fm/episodes/all"
    else:
        print("unsupported podcast name: {}".format(parsed_args.podcast_name))
        exit(-1)
    dnldr = TptmDownloader(start_page=start_uri, download_folder=parsed_args.folder)
    lnks = dnldr.get_links()
    if parsed_args.episodes_amount == 0:
        links_to_download = lnks
    else:
        links_to_download = lnks[:parsed_args.episodes_amount]
    dnldr.parallel_download(links_to_download, parsed_args.threads)
