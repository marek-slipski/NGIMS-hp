# NGIMS-hp
Plot density profiles and mixing ratios of NGIMS L2 abundances
Calculate homopause altitudes from N2 and Ar


## Config
Set `config.local` `data_path` to directory containing MAVEN data. L2 NGIMS data should be contained in `/maven/data/sci/ngi/l2/[YYYY]/[MM]/`. Set config `version` and `revision` to latest L2 files that have been downloaded.

# Find files

Use `python src/find_ngi_files.py` to create list of filenames within orbit or date range. List can be piped into other scripts or saved. `python src/find_ngi_files.py -h` for more details.

# Plot densities and mixing ratios
`python src/plot_profiles.py -h` for more details.

# Calculate homopause as function of altitude and CO2 density

`python src/hp_calc_bins.py`


