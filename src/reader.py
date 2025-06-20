import datetime as dt
import pandas as pd
from typing import List, Union, Tuple

from data_path_handler import choose_formatter

import requests
from io import StringIO
import pandas as pd
import time

class NGIMSReader():
    """
    Class to read a single NGIMS file.
    """
    def __init__(self, pds=True):
        self.pds = pds
        self.columns = [
            "t_utc",
            "t_unix",
            "t_sclk_cor",
            "t_tid",
            "tid",
            "orbit",
            "focusmode",
            "alt",
            "lst",
            "long",
            "lat",
            "sza",
            "mass",
            "species",
            "cps_dt_bkd",
            "abundance",
            "precision",
            "quality"
        ]

    def read(self, filename: str, level="L2", file_label="csn-abund", usecols=None, **kwargs):
        if usecols is None:
            usecols = self.columns
        if level=="L2" and file_label=="csn-abund":
            na_values = [-9999, "", "  ", "-999"]  # values to treat as NaN
            if "https" in filename:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
                    'Accept': 'application/json',
                }
                tries = 0
                success  = 0
                while tries<10 and success==0:
                    try: 
                        response = requests.get(filename, headers=headers, timeout=30)
                        response.raise_for_status()
                        to_read = StringIO(response.content.decode('utf8'))
                        success=1
                    except requests.exceptions.Timeout:
                        print("Request timed out. Will retry...")
                        time.sleep(10)
                        tries += 1
                    except requests.exceptions.RequestException as e:
                        print("Reading error, will retry...")
                        time.sleep(10)
                        tries += 1
            else:
                to_read = filename
            try:
                df = pd.read_csv(to_read,na_values=na_values, parse_dates=["t_utc"], **kwargs).drop_duplicates()
            except pd.errors.ParserError as e:
                print(f"Error parsing file {filename}:\n{e}")
                df = pd.DataFrame(columns=usecols)
        return df

class NGIMSLoader():
    def __init__(self, pds=True) -> None:
        self.pds = pds
        self.reader = NGIMSReader(self.pds)
        self.file_formatter = choose_formatter(pds=self.pds)

    def load(
            self,
            files: Union[List[str], str, None]=None, 
            date_range: Union[Tuple[dt.datetime, dt.datetime], None]=None,
            file_label = "csn-abund",
            **kwargs
        ):
        if isinstance(files, str):
            files = [files]
        elif files is None and date_range is not None:
            files = self.file_formatter.find_files_within_date_range(*date_range, file_label=file_label)
        else:
            NotImplementedError()
        if len(files) < 1:
            return None
        dfs = [self.reader.read(f, **kwargs) for f in files]  # load all files
        if len(dfs) < 1:
            return None
        df = pd.concat(dfs)  # combine
        if df.empty:
            return None
        return df