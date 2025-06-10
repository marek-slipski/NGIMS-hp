import datetime as dt
from typing import Union
from util.log import logger


class FilenameBuilder():

    utc_str_format = "%Y%m%dT%H%M%S"

    def build_filename(self, tid: int, utc: Union[dt.datetime, str], version: int, revison: int):
        if type(utc) != str:
            utc = utc.strftime(self.utc_str_format)
        return utc

class PDSFileFormatter():

    url_base = "https://atmos.nmsu.edu/PDS/data/PDS4/MAVEN/ngims_bundle/l2"

    def __init__(self, level: str, filetype: str) -> None:
        #self._check_valid_level(level)
        self.level = level # L1, L2, etc.
        self.filetype = filetype
        #self.data_record = self.level_record_map[level]
        #logger.info("Setup to load L2 files from PDS")

    #def _check_valid_level(self, level: str) -> None:
        #if level not in self.level_record_map.keys():
        #    raise ValueError(
        #        f"Level {level} not recognized. "
        #        f"Expected one of {self.level_record_map.keys()}"
        #    )

    

    def make_month_url(self, year, month):
        return f"{self.url_base}/{year}/{str(month).zfill(2)}/"

    #def build_url(self, ):