import datetime as dt
import pandas as pd
from typing import List, Union, Tuple

from data_path_handler import choose_formatter

class NGIMSReader():
    """
    Class to read a single NGIMS file.
    """
    def __init__(self, pds=True):
        self.pds = pds

    def read(self, filename: str, level="L2", file_label="csn-abund", **kwargs):
        if level=="L2" and file_label=="csn-abund":
            na_values = [-9999, "", "  ", "-999", -999]  # values to treat as NaN
            df = pd.read_csv(filename,na_values=na_values, parse_dates=["t_utc"], **kwargs).drop_duplicates()
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
        dfs = [self.reader.read(f, **kwargs) for f in files]  # load all files
        df = pd.concat(dfs)  # combine
        return df