from bs4 import BeautifulSoup
import datetime as dt
import requests
from typing import Union, List
from util.log import logger
import time

def choose_formatter(pds):
    if pds:
        return PDSFileFormatter()
    else:
        raise NotImplementedError
    

class NGIMSFilename():
    """
    Class to build NGIMS filenames or strip info from filenames
    """
    utc_str_format = "%Y%m%dT%H%M%S"
    prefix = "mvn_ngi"

    def __init__(self, filename):
        self.filename = filename
        self.parse_filename(filename)
            
    def parse_filename(self, filename):
        parts = filename.split("_")
        prefix = f"{parts[0]}_{parts[1]}"
        if prefix != self.prefix:
            raise ValueError(f"Expected prefix {self.prefix} but found {prefix}")
        file_label_tid = parts[3].split("-")
        self.level = parts[2]
        self.tid = int(file_label_tid[-1])
        self.file_label = parts[3].replace(f"-{self.tid}", "")
        self.suffix = parts[-1].split(".")[-1]
        self.revision = parts[-1].split(".")[0].split("r")[-1]
        self.version = parts[-2].split("v")[-1]
        self.utc = dt.datetime.strptime(parts[4], self.utc_str_format)
    
    @classmethod
    def build_filename(
        cls,
        level:str=None, 
        file_label:str=None, 
        tid:int=None, 
        utc:Union[dt.datetime, str]=None, 
        version:int=None, 
        revision:int=None, 
        suffix:str=None
    ):
        if isinstance(utc, dt.datetime):
            utc_str = utc.strftime(cls.utc_str_format)
        else:
            utc_str = utc
        return cls(f"{cls.prefix}_{level}_{file_label}-{tid}_{utc_str}_v{str(version).zfill(2)}_r{str(revision).zfill(2)}.{suffix}")

    

class PDSFileFormatter():

    url_base = "https://atmos.nmsu.edu/PDS/data/PDS4/MAVEN/ngims_bundle/l2"

    def __init__(self):
        pass

    def find_files_within_date_range(self, start_date: dt.datetime, end_date: dt.datetime, file_label: str) -> List[str]:
        all_files = []
        for year in range(start_date.year, end_date.year+1):
            if year == start_date.year:
                year_month_start = start_date.month
            else:
                year_month_start = 1
            if year == end_date.year:
                year_month_end = end_date.month
            else:
                year_month_end = 12
            for month in range(year_month_start, year_month_end+1):
                url = self.make_month_url(year, month)
                file_links = self.find_all_files_in_directory(url)
                ngi_filenames = [NGIMSFilename(f) for f in file_links]
                month_paths = [f"{url}/{nf.filename}" for nf in ngi_filenames if (nf.utc >= start_date and nf.utc<end_date) and (nf.file_label==file_label)]
                all_files += month_paths
        return all_files
            
    def find_all_files_in_directory(self, url):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
            'Accept': 'application/json',
        }
        tries = 0
        success  = 0
        while tries<10 and success==0:
            try:
                response = requests.get(url,  headers=headers, timeout=180)
                response.raise_for_status()
                success = 1
            except requests.exceptions.Timeout:
                print("Request timed out looking for files. Will retry...")
                time.sleep(60)
                tries += 1
            except requests.exceptions.RequestException as e:
                print("Reading error looking for files, will retry...")
                time.sleep(60)
                tries += 1
        if success ==0:
            print(f"Failed to connect to: {url}")
            return []
        soup = BeautifulSoup(response.content, 'html.parser')
        file_links = [l for l in [link.get('href') for link in soup.find_all('a', href=True)] for ft in ["csv"] if ft in l]
        return file_links

    def make_month_url(self, year, month):
        return f"{self.url_base}/{year}/{str(month).zfill(2)}/"