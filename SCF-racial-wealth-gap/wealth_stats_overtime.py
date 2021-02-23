import os
import numpy as np
import pandas as pd
from tqdm.notebook import tqdm

import plotly.graph_objects as go
import chart_studio.plotly as py
import chart_studio.tools as tls


# Log into Chart studio for visual chart upload

tls.set_credentials_file(username='•••••••', api_key='••••••••')

# Custom function for pretty-printing a number with comma-separators and/or decimal vals 
def comma_num(x, dollars=0, dec=0):
    
    if dec: x = round(x, dec)
    elif dollars: x = round(x)
    minus = False
    x = str(x)
    if '-' in x:
        minus=True
        x = x.replace('-', '').strip()
    parts = [list(l) for l in x.split('.')]
    predec = parts[0]
    if len(parts)>1: postdec = parts[-1]
    else: postdec = None
    
    if len(predec)>3:
        for i in list(range(-3, -len(predec)-1, -4)):
            predec.insert(i, ',')

    if postdec: out = '.'.join([''.join(l) for l in [predec, postdec]])
    else: out = ''.join(predec)
    if minus: out = '-'+out
    if dollars: out = '$'+out
    
    return out




def load_df(year, filetype, datadir='data/'):
    
    """ Load pre-downloaded data for a given year into a pandas dataframe. If loading summary data,
        Households are ID'd with household_id and implicates are numbered using imputed_hh_id. The weight
        of each household is divided by five into 'hh_wgt' for multi-implicate averaging analysis.
       
           Parameters:
                year (int or str): Indicates the year to load data from.
                filetype ('summary' or 'raw'): Indicates the filetype to load.
                    (See SCF_load_data() documentation for details)
                datadir (str): Indicates the base data directory
            Returns:
                df (pd.df): This year's dataset as a pandas dataframe
       
       """
    
    
    fname = f'rscfp{year}.dta'
    

    # Define the target filename given the year
    fpath = os.path.join(datadir, str(year), fname)
    
    # Load the file into a pandas dataframe
    df =  pd.read_stata(fpath)
    
    # Return the raw dataset as-is if loading the raw version (encoded variables)
    if filetype=='raw': return df
    

    col_renames = {
        'yy1': 'household_id',
        'y1': 'imputed_hh_id',}
    df.rename(columns=col_renames, inplace=True)
    
    # decode races (convert to string) these are directly from the codebook
    race_map = {
        1: 'white non-Hispanic',
        2: 'black/African-American',
        3: 'Hispanic',
        4: 'Asian', # (only available in internal data set, see codebook)
        5: 'other' }
    df['race'] = df['race'].map(race_map)
    
    # Add Implicate Number
    df['implicate'] = [x - y*10 for x, y in zip(df['imputed_hh_id'], df['household_id'])]
    
    # weighting dividing by 5 for simple multi-imputation averages (ideal for regression)
    df['hh_wgt'] = [x*5 for x in df['wgt']]
                      
    return df



def display_group_avgs(df, var='networth', grouper='race',
                       avg_worth=False):
    """Prints information about each racial demographic for this year. Returns the proportion of households with
        zero or negative net wealth by default.
       
           Parameters:
                df (pd.df): Pandas dataframe of this year's [summary] dataset
                var (str): Indicates the target variable to track
                grouper (str): Indicates the variable to group over
                avg_worth (bool): If True, returns the average worth of race categeory households instead of the
                                    proportion of zero/negative net wealth households
            Returns:
                group_avgs (pd.df): Dictionary with target stat for each category this year
                                    (i.e. {[races]: [pct_neg_wealth]}
       
       """
    
    group_avgs = {} # 
    
    # iterate groups of each [grouper] (i.e. race)
    for gcat in df[grouper].value_counts().index:
        if str(gcat).lower()=='nan': continue
            
        # Isolate households in the given categeory (i.e. race)
        g_df = df[df[grouper]==gcat].copy()
        
        # apply weights to the 
        var_wgted =  g_df.wgt * g_df[var]
        var_avg = sum(var_wgted) / g_df.wgt.sum()
        
        # Isolate households with zero or negative net wealth
        nonetworth = g_df[g_df.networth<=0].wgt.sum()
        pct_nonetworth = round(100*(nonetworth / (g_df.wgt.sum())), 1)
            
        # Log details about this category's wealth stats this year
        print(f'> {gcat.upper()}')
        print(f'   > AVG {var.upper()}:', comma_num( var_avg, dollars=True))
        print(f'   >', comma_num( round(g_df.wgt.sum()) ), 'total PEUs')
        print(f'     >', comma_num( round(nonetworth) ),
                  f'HHs have ≤0 networth, ({pct_nonetworth}%)')
        
        # Save either the proportion of zero-wealth HHs or the avg. net worth of HHs
        if avg_worth: group_avgs[gcat] = var_avg
        else: group_avgs[gcat] = pct_nonetworth
        
    # print all groups total
    var_wgted =  df.wgt * df[var]
    var_avg = sum(var_wgted)/sum(df.wgt)
    print()
    print(f'Total average {var}:', comma_num( round(var_avg), dollars=True))
    
    # Return a dictionary with 'grouper' as keys and 'pct_nonetworth' or 'avg_worth' as values 
    return group_avgs
    
    
    
def calc_zero_networth_races_overtime(
    group_black_hispanic=False,
    subtract_car_value=False,
    start=1992,
    until=2020):

    """Generates simple CSVs tracking the proportion of households with zero or negative wealth
       for each racial demographic indicated in the SCF data over time. Only works for 1992 and on
       
           Parameters:
                group_black_hispanic (bool): Whether to group black and brown households into a combined category
                subtract_car_value (bool): Whether to remove the value of cars (consumer durable) from net worth
                start/until (str or int): Indicates the 
            Returns:
                data (pd.df): Returns locations for all the extracted files.
       
       """

    ot_data = {} # to compile all overtime data
    
    # Iterate years
    for year in range(start, until, 3):
        
        df = load_df(year, 'summary')

        # Remove cars value from net worth (consumer durables skew the race gap)
        if subtract_car_value:
            df['networth_withcar'] = df.networth.copy()
            df.networth -= df.vehic

        # Group black and hispanic households into a one category
        if group_black_hispanic:
            df.race = df.race.replace('Hispanic', 'black & hispanic')
            df.race = df.race.replace('black/African-American', 'black & hispanic')

        # Run function to print and save this year's racial wealth stats
        print('\n\n'+str(year), '—'*60)
        ot_data[year] = display_group_avgs(df, # re-iterating defaults:
                                           'networth', # variable to track overtime
                                           'race' # variable to group over
                                          )

    # Save all overtime results as a csv
    data = pd.DataFrame(ot_data)
    fname = 'pct_neg_wealth'

    # Save the CSV into the negative_wealth folder with parameters indicated in the filename
    if subtract_car_value: fname += '_vehics_removed'
    if group_black_hispanic: fname+= '_blackhisp_grouped'
    if not os.path.exists('negative_wealth'):
        os.makedirs('negative_wealth')
    data.to_csv('negative_wealth'+'/'+fname+'.csv')
    
    return data




def plot_negative_wealth_overtime(data):
    """ Create a plotly chart of negative wealth among racial demographics overtime
    
        Parameters:
                data (pd.df): Proportions of races overtime
                    (output from calc_zero_networth_races_overtime())
        Returns:
            Launches a new browser window with the plotly chart
    
    
       
       """
    # ADAPTED FROM PLOTLY DOCUMENTATION: https://plotly.com/python/line-charts/

    title = 'Households with Zero or Negative Net Wealth'

    labels = list(data.index)
    # abbreviate these for space:
    labels[0] = 'white'
    labels[1] = 'Black'

    colors = ['rgb(67,67,67)', 'rgb(115,115,115)', 'rgb(49,130,189)', 'rgb(189,189,189)']

    mode_size = [10, 10, 10, 10]
    line_size = [4, 4, 4, 4]

    x_data = np.vstack((np.arange(1992, 2020, 3),)*4)

    y_data = data.values

    fig = go.Figure()

    for i in range(0, len(labels)):
        fig.add_trace(go.Scatter(x=x_data[i], y=y_data[i], mode='lines',
            name=labels[i],
            line=dict(color=colors[i], width=line_size[i]),
            connectgaps=True,
        ))

        # endpoints
        fig.add_trace(go.Scatter(
            x=[x_data[i][0], x_data[i][-1]],
            y=[y_data[i][0], y_data[i][-1]],
            mode='markers',
            marker=dict(color=colors[i], size=mode_size[i])
        ))


    fig.update_layout(
        xaxis=dict(
            showline=True,
            showgrid=False,
            showticklabels=True,
            linecolor='rgb(204, 204, 204)',
            linewidth=2,
            ticks='outside',
            tickfont=dict(
                family='Arial',
                size=12,
                color='rgb(82, 82, 82)',
            ),
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=False,
            showticklabels=False,
        ),
        autosize=False,
        margin=dict(
            autoexpand=False,
            l=100,
            r=20,
            t=110,
        ),
        showlegend=False,
        plot_bgcolor='white'
    )

    annotations = []

    # Adding labels
    for y_trace, label, color in zip(y_data, labels, colors):
        # labeling the left_side of the plot
        annotations.append(dict(xref='paper', x=0.05, y=y_trace[0],
                                      xanchor='right', yanchor='middle',
                                      text=label + ' {}%'.format(y_trace[0]),
                                      font=dict(family='Arial',
                                                size=16),
                                      showarrow=False))
        # labeling the right_side of the plot
        if all(y_trace==y_data[-1]): continue
        annotations.append(dict(xref='paper', x=0.95, y=y_trace[-1],
                                      xanchor='left', yanchor='middle',
                                      text='{}%'.format(y_trace[-1]),
                                      font=dict(family='Arial',
                                                size=16),
                                      showarrow=False))
    # Title
    annotations.append(dict(xref='paper', yref='paper', x=0.0, y=1.07,
                                  xanchor='left', yanchor='bottom',
                                  text=title,
                                  font=dict(family='Arial',
                                            size=22,
                                            color='rgb(37,37,37)'),
                                  showarrow=False))
    # subtitle
    annotations.append(dict(xref='paper', yref='paper', x=0.0, y=1.0,
                                  xanchor='left', yanchor='bottom',
                                  text='Estimated percentage of households by SCF racial demographics (1992–2019)',
                                  font=dict(family='Arial',
                                            size=14,
                                            color='rgb(37,37,37)'),
                                  showarrow=False))

    # Source
    annotations.append(dict(xref='paper', yref='paper', x=0.5, y=-0.1,
                                  xanchor='center', yanchor='top',
                                  text='Source: Survey of Consumer Finances & ' +
                                       'Institute for Policy Studies',
                                  font=dict(family='Arial',
                                            size=12,
                                            color='rgb(150,150,150)'),
                                  showarrow=False))

    # Methodology
    annotations.append(dict(xref='paper', yref='paper', x=0.5, y=-0.16,
                                  xanchor='center', yanchor='top',
                                  text='Federal Reserve net wealth calculated with consumer durables removed',
                                  font=dict(family='Arial',
                                            size=12,
                                            color='rgb(150,150,150)'),
                                  showarrow=False))

    fig.update_layout(annotations=annotations)

    fig.show()


    py.plot(fig, filename = 'neg_wealth_gap', auto_open=True)
    
    return
