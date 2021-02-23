# (loosely) adapted from Dan Valanzuela, "Linear Regressions for the New Survey of Consumer Finances"
# https://towardsdatascience.com/linear-regressions-for-the-survey-of-consumer-finances-ed2c10b2670c

import os
import sys
import importlib.util
import requests
import zipfile
import pandas as pd


# If TQDM is installed, generate a progress bar for the download process
TQDM_ON = True
try: from tqdm import tqdm
except: TQDM_ON = False


def URL_DL_ZIP(targetzip, targetdir, url):
    """Downloads and unzips zip file from url and return locations of extracted filed.
    
            Parameters:
                targetzip (str): String indicating where zip file is to be saved.
                targetdir (str): String indicating where files are to be extracted.
                url (str): URL where the zip exists.
            Returns:
                file_locs (list of str): Returns locations for all the extracted files.
    """
        
    # Save Zip from archived site
    r = requests.get(url)
    with open(targetzip,'wb') as f: 
        f.write(r.content)
            
    # Unzipping file
    with zipfile.ZipFile(targetzip, 'r') as zip_ref:
        zip_ref.extractall(targetdir)
        # Get list of files names in zip
        files = zip_ref.namelist()
        
    # Return list of locations of extracted files   
    file_locs = [] 
    for file in files:
        fpath = os.path.join(targetdir, file)
        file_locs.append(fpath)
        
    return file_locs


def SCF_load_data(datadir, year, filetype='summary', to_df=False):
    """Loads SCF data for a given year into pandas data frame. Limited to 1989 and on. 
    
            Parameters:
                targetdir (str): String indicating where you want files saved.
                year (str or int): Indicating the year of SCF wanted.
                filetype (str): Indicating the filetype to download.
                    - 'summary': 351 key named variables computed in the SCF codebook.
                       for more info see https://www.federalreserve.gov/econres/files/codebk2019.txt
                    - 'raw': 5333 original encoded variables for every survey question
                       decode with https://www.federalreserve.gov/econres/files/2019map.txt
                to_df (bool): Default False, set to True to load and return the file as a pandas dataframe
            Returns:
                SCF_data (pd.df): Data frame of imported SCF data with labels adjusted 
                according to labels_dict in dataloading.py
    """
    
    # Set/create target download directory for this year
    targetdir = os.path.join(datadir, str(year))
    if not os.path.exists(targetdir):
        os.makedirs(targetdir)
    
    # Set target zip file
    targetzip = os.path.join(targetdir, f'SCF{year}_data_public_{filetype}.zip')
    
    # Set file type to download
    if filetype=='summary': file_string = 'p'
    elif filetype=='raw': file_string = ''
    
    # Make year-specific URL alterations 
    panel_string = 'p' if ((int(year)%3) != 0) else ''
    
    #year = str(year)[-2:] if int(year) < 2002 else str(year)
    # (SCF UPDATED SO ALL YEARS ARE NOW STANDARD)
    
    # Compile target URL with params 
    url_params = file_string + str(year) + panel_string
    url = f'https://www.federalreserve.gov/econres/files/scf{url_params}s.zip'
        
    # Return list of locations of extracted files   
    SCF_file_locs = URL_DL_ZIP(targetzip, targetdir, url) 
      
    if to_df: # Option for loading as a pandas df
        SCF_data = pd.read_stata(SCF_file_locs[0])
        return SCF_data

    # Return path of unzipped .dta file 
    else: return SCF_file_locs[0]
    
def scrape_SCF(datadir='data', start=1989, until=2019, filetypes=['summary']):
    """Downloads a range of historic SCF data. Limited to 1989 and on. 
    
            Parameters:
                datadir: Indicating the base directory to create a sub-folders for each year
                start (int or str): Indicating the first year to begin scraping.
                until (int or str): Indicating the last year to scrape.
                filetypes (list): List of strings indicating types of files to download.
                                  (See SCF_load_data() documentation for details)
            Returns:
                paths (dict): Nested dictionary containing filepaths for all downloaded files
    """
    
    paths = {} # Compile all downloaded filepaths
    
    # Set/create the base target download directory
    if not os.path.exists:
        os.makedirs(datadir)
    
    # Set the range of years to scrape
    yrange = range(start, until+3, 3)
    
    # Apply a progress monitor if TQDM is installed
    if TQDM_ON: yrange = tqdm(yrange)
    
    # Iterate years (integers)
    for year in yrange:
        
        # Instantiate the sub-dictionary of filetype paths for this year
        paths[year] = {}
        
        # Iterate target filetypes by keyword ('summary' or 'raw')
        for filetype in filetypes:
            
            # Download and save the file location. Creates the year directory if needed
            paths[year][filetype] = SCF_load_data(datadir, year, filetype)
    
    # Log & return dictionary with all filepaths
    return paths