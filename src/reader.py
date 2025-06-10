import pandas as pd

class NGIMSReader():
    """
    Class to read a single NGIMS file.
    """
    def __init__(self, pds=True):
        self.pds = pds

    def read(self, filename, level="L2", filetype="csn", **kwargs):
        if level=="L2" and filetype=="csn":
            na_values = [-9999, "", "  ", "-999"]  # values to treat as NaN
            df = pd.read_csv(filename,na_values=na_values, **kwargs).drop_duplicates()
        return df

#class NGIMSLoader():
