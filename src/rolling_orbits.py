import click
import dask
import dask.dataframe as dd
import glob
import os
import pandas as pd
import numpy as np
import scipy.stats as sps
from sklearn import linear_model

from global_params import PATH_NGI_L2, NA_VALUES
from src.hp_calc_bins import exo_Ar_int, x_to_T

DEFAULT_ORBIT_SPAN = 10
DEFAULT_MAX_ALT = 200.
DEFAULT_YEARS = [2015, 2016, 2017, 2018, 2019]
OUTPUT_DIR = "output"
META_COLS = {
    "orbit": int,
    "alt": float,
    "species": str,
    "abundance": float,
    "t_unix": float
}

def make_orbit_path_map(ddf, orb_span):
    orb_path_map = ddf[["orbit", "path"]].drop_duplicates().compute()
    orb_orb_map = {
        x: list(
            range(x - orb_span//2, x + orb_span//2 + 1)
        ) for x in orb_path_map["orbit"]
    }
    orb_filename_map = {
        x: orb_path_map["path"][orb_path_map["orbit"].isin(orb_orb_map[x])].tolist() 
        for x in orb_orb_map.keys()
    }
    return orb_filename_map

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
    
def fit_log_alt(df, col):
    x = df[["alt"]]
    y = np.log(df[col])
    lr = linear_model.LinearRegression()
    lr.fit(x, y)
    return lr

def get_r2(df, lr, col):
    x = df[["alt"]]
    y = np.log(df[col])
    return lr.score(x, y)

def hp_from_fit(ratio, slope, intercept):
    return (np.log(ratio)-intercept)/slope

def compute_results_subset(orb_filename_map, max_alt, hp_ex="hp"):
    if hp_ex == "hp":
        calc_fnc = hp_files
    elif hp_ex == "exo":
        calc_fnc = exo_files
    elif hp_ex == "H":
        calc_fnc = H_files
    # Initialize results
    results_hp = []
    results_orb = []
    # Loop through each orbit
    for orb, files in orb_filename_map.items():
        results_orb.append(orb) # track orbits
        if max_alt:
            res_single = calc_fnc(files, max_alt) # calc hp and other params
        else:
            res_single = calc_fnc(files)
        results_hp.append(res_single) # track results
    results = dask.compute(*results_hp) # compute results
    res_df = pd.DataFrame(results) # convert to DF
    res_df["orbit"] = results_orb # add column
    res_df.set_index("orbit", inplace=True)
    return res_df

@dask.delayed()
def hp_files(files, max_alt):
    temp_ddf = dd.read_csv(
        files, 
        assume_missing=True, 
        usecols=META_COLS.keys(),
        dtype=META_COLS,
        na_values = NA_VALUES
    )
    temp_ddf = temp_ddf.map_partitions(IO_orb, meta=temp_ddf)
    temp_ddf = temp_ddf[(temp_ddf["abundance"] > 0.) & (temp_ddf["alt"] < max_alt) & (temp_ddf["species"].isin(["Ar", "N2"]))]
    df = temp_ddf.compute()
    #temp_ddf = temp_ddf.set_index('orbit', sorted=True, drop=False)
    #temp_ddf.reset_index(drop=True)
    norbs = len(df["orbit"].unique())
    df = df.pivot_table(values=["abundance"], index=["orbit","alt", "species"]).unstack()
    df["N2/Ar"] = df["abundance"]["N2"] / df["abundance"]["Ar"]
    df = df["N2/Ar"].reset_index().dropna(subset=["alt", "N2/Ar"])
    try:
        fit = fit_log_alt(df, "N2/Ar")
    except ValueError:
        return {"hp_alt": np.nan, "fit_slope": np.nan, "fit_intercept": np.nan, "n_orbits": norbs}
    hp = hp_from_fit(1.25, fit.coef_[0], fit.intercept_)
    hp_res = {
        "hp_alt": hp, 
        "fit_slope": fit.coef_[0], 
        "fit_intercept": fit.intercept_, 
        "n_orbits": norbs, 
        "max_alt": max_alt,
        "score": get_r2(df, fit, "N2/Ar")
    }
    return hp_res

@dask.delayed()
def exo_files(files, max_alt):
    temp_ddf = dd.read_csv(
        files, 
        assume_missing=True, 
        usecols=list(META_COLS.keys()),
        dtype=META_COLS,
        na_values = NA_VALUES
    )
    temp_ddf = temp_ddf.map_partitions(IO_orb, meta=temp_ddf)
    temp_ddf = temp_ddf[(temp_ddf["abundance"] > 0.) & (temp_ddf["species"].isin(["Ar", "CO2"]))]
    df = temp_ddf.compute()
    norbs = len(df["orbit"].unique())
    df = df.pivot_table(values=["abundance"], index=["orbit", "alt", "species"]).unstack()
    df = df.dropna()
    df = df.droplevel("orbit")
    df = df.sort_index(ascending=False)
    Ar = df[("abundance", "Ar")]
    CO2 = df[("abundance", "CO2")]
    alt = np.array(df.index.tolist())
    exo = exo_Ar_int(CO2, Ar, alt, taufrange=[0,2])
    exo_res = {
        "exo_alt": exo[0], 
        "fit_slope": exo[1][0], 
        "fit_intercept": exo[1][1], 
        "n_orbits": norbs, 
    }
    return exo_res

@dask.delayed()
def H_files(files, max_alt):
    temp_ddf = dd.read_csv(
        files, 
        assume_missing=True, 
        usecols=list(META_COLS.keys()),
        dtype=META_COLS,
        na_values = NA_VALUES
    )
    temp_ddf = temp_ddf.map_partitions(IO_orb, meta=temp_ddf)
    temp_ddf = temp_ddf[
        (temp_ddf["abundance"] > 0.) & (temp_ddf["alt"] < max_alt) & (temp_ddf["species"].isin(["Ar", "N2", "CO2"]))
    ]
    df = temp_ddf.compute()
    norbs = len(df["orbit"].unique())
    df = df.pivot_table(values=["abundance"], index=["orbit", "alt", "species"]).unstack()
    df = df.reset_index().dropna()
    nan_dict = {
        "H_Ar": np.nan, 
        "fit_slope_Ar": np.nan, 
        "fit_intercept_Ar": np.nan, 
        "score_Ar": np.nan,
        "H_N2": np.nan, 
        "fit_slope_N2": np.nan, 
        "fit_intercept_N2": np.nan, 
        "score_N2": np.nan,
        "H_CO2": np.nan, 
        "fit_slope_CO2": np.nan, 
        "fit_intercept_CO2": np.nan, 
        "score_CO2": np.nan,
        "n_orbits": norbs,
        "max_alt": np.nan
    }
    try:
        fit_Ar = fit_log_alt(df, ("abundance", "Ar"))
    except ValueError:
        return nan_dict
    try:
        fit_N2 = fit_log_alt(df, ("abundance", "N2"))
    except ValueError:
        return nan_dict
    try:
        fit_CO2 = fit_log_alt(df, ("abundance", "CO2"))
    except ValueError:
        return nan_dict
    H_Ar = fit_Ar.coef_[0]**-1*-1
    H_N2 = fit_N2.coef_[0]**-1*-1
    H_CO2 = fit_CO2.coef_[0]**-1*-1
    H_res = {
        "H_Ar": H_Ar, 
        "fit_slope_Ar": fit_Ar.coef_[0], 
        "fit_intercept_Ar": fit_Ar.intercept_,
        "score_Ar": get_r2(df, fit_Ar, ("abundance", "Ar")),
        "H_N2": H_N2, 
        "fit_slope_N2": fit_N2.coef_[0], 
        "fit_intercept_N2": fit_N2.intercept_, 
        "score_N2": get_r2(df, fit_N2, ("abundance", "N2")),
        "H_CO2": H_CO2, 
        "fit_slope_CO2": fit_CO2.coef_[0], 
        "fit_intercept_CO2": fit_CO2.intercept_, 
        "score_CO2": get_r2(df, fit_CO2, ("abundance", "CO2")),
        "n_orbits": norbs,
        "max_alt": max_alt
    }
    return H_res

@click.command()
@click.argument(
    "hp_ex",
    type=click.Choice(["hp", "exo", "H"])
)
@click.option("--all-data", is_flag=True, help="Calculate homopause altitudes for entire data set")
@click.option(
    "--orbit_span", 
    type=int, 
    default=DEFAULT_ORBIT_SPAN,
    help="Number of orbits to use for homopause fit"
)
@click.option(
    "--max_alt", 
    type=float, 
    default=DEFAULT_MAX_ALT,
    help="Maximum altitude of data used to calculate homopause"
)
def main(hp_ex, all_data, orbit_span, max_alt):
    if hp_ex == "exo":
        max_alt = None
    if all_data:
        for year in DEFAULT_YEARS:
            print(f"Loading {year} data")
            # Get path to subset of data
            filelist = os.path.join(PATH_NGI_L2, f"{year}/*/*.csv")
            save_path_year = os.path.join(OUTPUT_DIR, f"{year}_{hp_ex}.csv")
            # Load chunk of data (only a few columns)
            data_in_range = dd.read_csv(
                filelist, 
                assume_missing=True, 
                usecols = META_COLS.keys(),
                include_path_column=True,
                dtype=META_COLS,
                na_values = NA_VALUES
            )
            print("Mapping orbits to filenames")
            # Map orbit numbers to all files within range of orbits
            orb_path_map = make_orbit_path_map(data_in_range, orbit_span)
            del data_in_range # no need to keep all that data in memory
            print("Calculating altitudes")
            results_subset = compute_results_subset(orb_path_map, max_alt, hp_ex=hp_ex)
            print(f"Saving results to {save_path_year}")
            results_subset.to_csv(save_path_year)

if __name__=="__main__":
    main()