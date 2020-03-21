def peri_row(orbdata):
    minalt = orbdata['alt'].min()
    peri_row = orbdata[orbdata["alt"]==minalt]
    return peri_t