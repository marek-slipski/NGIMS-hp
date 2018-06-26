#! env/bin/python 
# Marek Slipski
# 20180625

import pandas as pd
import numpy as np
import datetime as dt

def bin_date(middate,daybin):
    bin_start = middate - dt.timedelta(days=daybin/2.)
    bin_end = middate + dt.timedelta(days=daybin/2.)
    return bin_start, bin_end

def bin_orbit(midorb,orbbin):
    return midorb-orbbin/2,midorb+orbbin/2.