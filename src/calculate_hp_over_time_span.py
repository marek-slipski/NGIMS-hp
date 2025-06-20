import click
import datetime as dt
import numpy as np
import pandas as pd
import scipy.stats as sps

from reader import NGIMSLoader

N_DAYS_GROUP = 3  # Number of days to use in HP calc
MIN_N_ORBITS_GROUP = 7  # Minimum number of orbits to require for fitting

START_TIME = dt.datetime(2015, 2, 7)
END_TIME = dt.datetime(2020, 7,  1)

ROW_KEEP_COLS = ["t_utc", "t_unix", "t_sclk_cor", "t_tid", "tid", "orbit", "alt", "lst", "long", "lat", "sza"]

def IO_orb(orbdata,io='I') -> pd.DataFrame:
    minalt = orbdata['alt'].min()
    peri_t = orbdata[orbdata['alt']==minalt]['t_unix'].unique()
    #if len(peri_t)>1:
    #    sys.exit('Non-unique time found at periapse '+str(orbdata['orbit'].unique()))
    #else:
    if io == 'I':
        return orbdata[orbdata['t_unix']<=peri_t[0]]
    elif io =='O':
        return orbdata[orbdata['t_unix']>peri_t[0]]
    else:
        return orbdata
    

def hp_from_fit(ratio, slope, intercept):
    return (np.log(ratio)-intercept)/slope

@click.command()
@click.option("--start-time", default=START_TIME, type=click.DateTime())
@click.option("--end-time", default=END_TIME, type=click.DateTime())
def main(start_time, end_time):
    loader = NGIMSLoader(pds=True)
    period_start = start_time
    hps = []
    while period_start >= start_time and period_start < end_time:
        period_end = period_start + dt.timedelta(days=N_DAYS_GROUP)
        print(f"Loading data from {period_start} - {period_end}...")
        data = loader.load(date_range=(period_start, period_end), file_label="csn-abund")
        print(data)
        if data is None:
            period_start = period_end
            continue
        orb_pieces = []
        for orb_n, orb_data in data.groupby("orbit"):
            orb_pieces.append(IO_orb(orb_data, io="I"))
        inbound_data = pd.concat(orb_pieces, ignore_index=True)
        norbits = inbound_data["orbit"].nunique()
        print(f"Number of orbits={norbits}")
        if norbits < MIN_N_ORBITS_GROUP:
            period_start = period_end
            continue
        else:
            single_orb_inbound_abund = inbound_data.pivot_table(values=["abundance"], index=["alt", "species"]).unstack()
            single_orb_inbound_abund = single_orb_inbound_abund[
                ((single_orb_inbound_abund["abundance"]["Ar"])>0)
            ].dropna(subset=[("abundance", "N2"), (("abundance", "Ar"))]).sort_values("alt")
            n2ar_profile = (single_orb_inbound_abund["abundance"]["N2"]/single_orb_inbound_abund["abundance"]["Ar"])
            fit = sps.linregress(n2ar_profile.index.values, np.log(n2ar_profile.values))
            hp = hp_from_fit(1.25, fit[0], fit[1])
            print(f"HP={hp:.2f}")
            middle_orb = inbound_data["orbit"].unique()[norbits//2]
            middle_orb_peri_row = inbound_data.loc[inbound_data[inbound_data["orbit"]==middle_orb]["alt"].idxmin().squeeze()]
            middle_orb_peri_row = pd.concat([pd.Series({"hp_alt": hp}), middle_orb_peri_row[ROW_KEEP_COLS]])
            hps.append(middle_orb_peri_row)
        period_start = period_end
    results = pd.DataFrame(hps)#pd.DataFrame({"t_utc": times, "hp_alt": hps})
    print(results)
    results.to_csv("data/homopause_altitudes.csv", index=False)

if __name__=="__main__":
    main()