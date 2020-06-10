import datetime as dt
import marstime as mt

def peri_row(orbdata):
    minalt = orbdata['alt'].min()
    peri_row = orbdata[orbdata["alt"]==minalt]
    return peri_t

def dt_to_Ls(date):
    ref = dt.datetime(2000,1,1,12,0,0)
    delta = date - ref
    j2000_offset = delta.days + delta.seconds/86400
    return mt.Mars_Ls(j2000_offset)

def dt_to_mtfnc(date, mt_fnc):
    ref = dt.datetime(2000,1,1,12,0,0)
    delta = date - ref
    j2000_offset = delta.days + delta.seconds/86400
    return mt_fnc(j2000_offset)