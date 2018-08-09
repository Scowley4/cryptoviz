import numpy as np
import pandas as pd
import re
import os
import sys
import contextlib
from bs4 import BeautifulSoup
import argparse

from bokeh.layouts import gridplot
import bokeh.plotting as bplot
from bokeh.models import HoverTool, ColumnDataSource, WheelZoomTool, NumeralTickFormatter
from bokeh.models import CategoricalTicker, Range1d
from bokeh.embed import components
from bokeh.transform import jitter
from bokeh.palettes import Spectral6

C_TITLE = '#4FB3B7'
C_TEXT = '#4FB3B7'
C_AXES = '#519397'
C_CHART_BG = '#111818'
C_LEGEND_BG = 'red'
C_BAR = '#355AA6'
C_BUY = '#117E1A'
C_SELL = '#7B1111'
C_MISSING = '#7B1111'
CHART_TITLE_SIZE = '16pt'
C_BAR_HOVER_LINE = None

#DATA_FOLDER = './data/new_data/Output/'
#DATA_FOLDER = './data/new_data2/Output/'

class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
    pass
parser=argparse.ArgumentParser(
    description='Cryptoviz: Generates visualizations from cryptodata',
    formatter_class=CustomFormatter)
parser.add_argument('datafolder', metavar='datafolder',
                    help='Path from current location to the folder output of analysis_script.py')
parser.add_argument('outfile', metavar='outfile',
                    help='Filename for output of this script (and folder if desired)')
#parser.add_argument('-c', '--clean', action='store_true')
args=parser.parse_args()



#DATA_FOLDER = './data/new_data/Output/'
DATA_FOLDER = './data/new_data2/Output/'
DATA_FOLDER = args.datafolder
OUTFILE = args.outfile

#os.makedirs(PAGES, exist_ok=True)
if os.path.dirname(OUTFILE):
    os.makedirs(os.path.dirname(OUTFILE), exist_ok=True)

def _apply_figure_styles(p, **kwargs):
    keys = ['xaxis.major_tick_line_color', 'yaxis.major_tick_line_color',
            'xaxis.minor_tick_line_color', 'yaxis.minor_tick_line_color',
            'xgrid.grid_line_color', 'ygrid.grid_line_color',
            'xaxis.major_label_text_color', 'yaxis.major_label_text_color',
            'xaxis.axis_label_text_color', 'yaxis.axis_label_text_color',
            'title.text_color', 'title.text_font_style', 'title.text_font_size',
            'background_fill_color', 'border_fill_color',]

    for key in kwargs:
        if key not in keys:
            print(f'key "{key}" not recognized')

    #p.legend.location='center_right'
    #p.legend.background_fill_color = 'darkgrey'
    p.xaxis.major_tick_line_color = kwargs.get('xaxis.major_tick_line_color', C_AXES)
    p.yaxis.major_tick_line_color = kwargs.get('yaxis.major_tick_line_color', C_AXES)

    p.xaxis.minor_tick_line_color = kwargs.get('xaxis.minor_tick_line_color', C_AXES)
    p.yaxis.minor_tick_line_color = kwargs.get('yaxis.minor_tick_line_color', C_AXES)

    p.xgrid.grid_line_color = kwargs.get('xgrid.grid_line_color', C_AXES)
    p.ygrid.grid_line_color = kwargs.get('ygrid.grid_line_color', C_AXES)

    p.xaxis.major_label_text_color = kwargs.get('xaxis.major_label_text_color', C_TEXT)
    p.yaxis.major_label_text_color = kwargs.get('yaxis.major_label_text_color', C_TEXT)

    p.xaxis.axis_label_text_color = kwargs.get('xaxis.axis_label_text_color', C_TEXT)
    p.yaxis.axis_label_text_color = kwargs.get('yaxis.axis_label_text_color', C_TEXT)

    p.title.text_color = kwargs.get('title.text_color', C_TITLE)
    p.title.text_font_style = kwargs.get('title.text_font_style', 'bold')
    p.title.text_font_size = kwargs.get('title.text_font_size', CHART_TITLE_SIZE)

    #p.background_fill_alpha = 0
    p.background_fill_color = kwargs.get('background_fill_color', C_CHART_BG)

    p.border_fill_color = kwargs.get('border_fill_color', C_CHART_BG)
    p.border_fill_alpha = 0

    # The border around the whole chart (the background behind the toolbar)
    #p.outline_line_width
    #p.outline_line_alpha
    p.outline_line_color = None




class EveryOtherTicker(CategoricalTicker):
    __implementation__ = """
    import {CategoricalTicker} from "models/tickers/categorical_ticker"

    export class EveryOtherTicker extends CategoricalTicker
      type: "EveryOtherTicker"

      get_ticks: (start, end, range, cross_loc) ->
        ticks = super(start, end, range, cross_loc)

        # drops every other tick -- update to suit your specific needs
        ticks.major = ticks.major.filter((element, index) -> index % 2 == 0)

        return ticks
    """


def _parse_gap(line):
    if 'to' in line:
        split = line.split(' to ')
        return int(split[0]), int(split[1])
    else:
        return int(line), int(line)


def build_gaps_block(path, product_id, output_file=None, show=False):

    # Open and read the file into lines
    with open(path, 'r') as infile:
        lines = [line.strip() for line in infile.readlines()]

    # Get min and max from the range line
    line = lines[1][len('Range: ('):-1]
    split = line.split(', ')
    min_trade_id = int(split[0])
    max_trade_id = int(split[1])

    # Get gaps
    gaps = []
    for line in lines[3:]:
        gaps.append(_parse_gap(line))

    # Get assignment for each trade id (missing or not)
    trade_ids = []
    indicators = []
    missing = set(num for gap in gaps for num in range(gap[0], gap[1]+1))
    for i in range(min_trade_id, max_trade_id+1):
        trade_ids.append(i)
        indicators.append(i not in missing)

    # Group into missing and not missing
    quads = []
    cur_indicator = indicators[0]
    quad_left = trade_ids[0]
    quad_indicators = []
    i = 0
    while i < len(trade_ids):
        if indicators[i] == cur_indicator:
            quad_right = trade_ids[i]
        if indicators[i] != cur_indicator or i==len(trade_ids)-1:
            quad_indicators.append(cur_indicator)
            quads.append((quad_left, quad_right))
            quad_left = trade_ids[i]
            quad_right = trade_ids[i]
            cur_indicator = indicators[i]
        i += 1

    # Tools
    tools = 'save,xpan,box_zoom,xwheel_zoom,reset'

    # Set window range
    span = max_trade_id - min_trade_id
    space = span*.05
    left = min_trade_id-space
    right = max_trade_id+space
    top = 1.2
    bottom = -.2

    # Set window range (For some reason, y_range isn't working right)
    x_range = Range1d(start=left, end=right, bounds=(left,right))
    y_range = Range1d(start=bottom, end=top, bounds=(bottom,top))

    p = bplot.figure(title='Gaps in trade ids', tools=tools,
                plot_width=1000,
                plot_height=300,
                x_range=x_range,
               # y_range=y_range,
                active_scroll='xwheel_zoom',
                toolbar_location='above',
                background_fill_color=C_CHART_BG)
    #p.add_tools(WheelZoomTool(dimensions='width'))

    source = ColumnDataSource(data={
                'quad_left': [quad[0] for quad in quads],
                'quad_right': [quad[1]+1 for quad in quads],
                'top': [1 for x in quads],
                'bottom': [0 for x in quads],
                'range_left': [quad[0] for quad in quads],
                'range_right': [quad[1] for quad in quads],
                'fill': [C_BAR if x else C_MISSING for x in quad_indicators],
                'indicator': quad_indicators,
                'size': [quad[1]-quad[0]+1 for quad in quads],
                })

    p.quad(top='top', bottom='bottom', left='quad_left', right='quad_right',
           line_color=None, fill_color='fill',source=source)

    p.xaxis.axis_label = 'trade_id'
    p.yaxis.visible = False
    p.add_tools(HoverTool(tooltips=[('trade_ids', '@range_left - @range_right'),
                                    ('size', '@size'),
                                   ]))

    # Numbers formatted as ints on the x-axis
    p.xaxis[0].formatter = NumeralTickFormatter(format='0'*len(str(min_trade_id)))

    # Apply desired styles
    styles = {'ygrid.grid_line_color': None}
    _apply_figure_styles(p, **styles)

    if output_file:
        bplot.output_file(output_file)
        bplot.save(p)
    if show:
        bplot.show(p)
    return p

def build_gaps_bar_graph(path, product_id, output_file=None, show=False):

    # Open and read the file into lines
    with open(path, 'r') as infile:
        lines = [line.strip() for line in infile.readlines()]

    # Get min and max from the range line
    line = lines[1][len('Range: ('):-1]
    split = line.split(', ')
    min_trade_id = int(split[0])
    max_trade_id = int(split[1])

    # Get gaps
    gaps = []
    for line in lines[3:]:
        gaps.append(_parse_gap(line))

    gap_sizes = sorted([gap[1]-gap[0]+1 for gap in gaps],reverse=True)

    # Tools
    tools = 'save,xpan,box_zoom,xwheel_zoom,reset'

    numbers = [str(i+1) for i in range(len(gap_sizes))]

    p = bplot.figure(title='Missing Trade Ids', tools=tools,
                x_range=numbers,
                plot_width=1000,
                plot_height=300,
                active_scroll='xwheel_zoom',
                toolbar_location='above',
                )

    source = ColumnDataSource(data={
                'xlabel': numbers,
                'size': gap_sizes,
                })


    p.vbar(x='xlabel', top='size', width=.8, legend=False, source=source,
    color=C_BAR)


    if len(numbers)>50:
        p.xaxis.ticker = EveryOtherTicker()

    p.xaxis.axis_label = 'Gap Count'
    p.add_tools(HoverTool(tooltips=[('Gap Size', '@size')]))

    # Apply desired styles
    styles = {'xgrid.grid_line_color': None}
    _apply_figure_styles(p, **styles)

    if output_file:
        bplot.output_file(output_file)
        bplot.save(p)
    if show:
        bplot.show(p)
    return p


def build_delays_histogram(path, product_id, output_file=None, show=False):

    with open(path, 'r') as infile:
        lines = infile.readlines()[1:]

    # Parse the delays
    delays = {int(line.split('+')[0].split(' ')[0]): int(line.split(': ')[1])
                for line in [l.strip() for l in lines if 'second' in l]}

    # Build hist edges and heights
    edges = np.arange(62)
    hist = np.array([delays.get(i, 0) for i in range(61)])

    centers = (edges[:-1]+edges[1:])/2
    width = abs(centers[0]-centers[1])

    tools = 'save,pan,box_zoom,wheel_zoom,reset'

    span = max(centers) - min(centers)
    space = span*.05
    left = max(min(centers)-space, 0)
    right = max(centers)+space
    top = max(hist)*1.2
    bottom = 0
    x_range = Range1d(start=left, end=right, bounds=(left,right))
    y_range = Range1d(start=bottom, end=top, bounds=(bottom,top))

    p = bplot.figure(title='Delay Duration Between Server and Exchange Datetime',
                tools=tools,
                width=1000,
                x_range=x_range,
                y_range=y_range,
                active_scroll='wheel_zoom',
                background_fill_color=C_CHART_BG)

    source = ColumnDataSource(data={
                'count': hist,
                'center': centers,
                'left': edges[:-1],
                'right': edges[1:],
                'label': [f'{int(edges[i])}-{int(edges[i+1])}' if i<60 else '60+'
                          for i in range(61)],
            })

    p.vbar(x='center', top='count', width=width, source=source,
           line_color=None, hover_line_color='grey')
    p.xaxis.axis_label = 'Delay Duration (sec)'
    p.yaxis.axis_label = 'Count'
    p.add_tools(HoverTool(tooltips=[#('Value', '$x{1.1111}'),
                                     ('Range', '@label'),
                                     ('Count', '@count'),
                                     ]))

    styles={}
    _apply_figure_styles(p, **styles)
    if output_file:
        bplot.output_file(output_file)
        bplot.save(p)
    if show:
        bplot.show(p)
    return p

def get_distribution_histograms(path, product_id, output_file=None, show=False):
    df = pd.read_csv(path, index_col=None,
                     parse_dates=['Start_exchange_datetime',
                                  'End_exchange_datetime'])
    distributions = []
    for i, col in enumerate(df.columns):
        if (df[col].dtype == 'float64'
           # and all(df[col]>=0)
           # and all(df[col]<=1)
            and (not (col[0].isnumeric()) or col[:2]=='01')
            and not ('Vol_Slope' in col)
            and not ('Area' in col)):


            #distributions[col] = build_distribution_histogram(df[col],
            #            output_file='testdist.html', show=Truek
            distributions.append((f'{i}~~{col}', build_distribution_histogram(df[col])))
        elif (col in ['Buy_Area_01', 'Sell_Area_01',
               'Buy_Vol_Slope_0001', 'Sell_Vol_Slope_0001',
               'Buy_Vol_Slope_0102', 'Sell_Vol_Slope_0102']):

            distributions.append((f'{i}~~{col}', build_distribution_histogram(df[col])))
    return distributions

def build_distribution_histogram(data, output_file=None, show=False):
    BINS=50

    hist, edges = np.histogram(data.dropna(), bins=BINS)

    tools = 'save,pan,box_zoom,wheel_zoom,reset'
    p = bplot.figure(title=data.name, tools=tools,
                     toolbar_location='above',
                     plot_width=500,
                     plot_height=200,
                     active_scroll='wheel_zoom',
                     background_fill_color=C_CHART_BG)

    centers = (edges[:-1]+edges[1:])/2
    width = abs(centers[0]-centers[1])

    # p.quad(top=hist, bottom=0, left=edges[:-1], right=edges[1:],
    #         fill_color='#036564', line_color='#033649')
    source = ColumnDataSource(data={
                'count':hist,
                'centers':centers,
                'label': [f'{round(edges[i], 3)}-{round(edges[i+1], 3)}' for i in range(BINS)],
                })

    p.vbar(x='centers', top='count',
           width=width, source=source,
           hover_line_color='grey')
    p.legend.location='center_right'
    p.legend.background_fill_color = 'darkgrey'
    #p.xaxis.axis_label = 'x'
    #p.yaxis.axis_label = 'P(x)'
    p.add_tools(HoverTool(tooltips=[('Range', '@label'), ('Count', '@count')]))

    styles={}
    _apply_figure_styles(p, **styles)
    if output_file:
        bplot.output_file(output_file)
        bplot.save(p)
    if show:
        bplot.show(p)
    return p

def build_trade_scatter(path, product_id, output_file=None, show=False):
    product_df = pd.read_csv(path, index_col=None,
                             parse_dates=['server_datetime',
                                          'exchange_datetime'])

    # Get the weekday and time
    product_df['weekday_name'] = product_df['exchange_datetime'].dt.weekday_name
    product_df['time'] = product_df['exchange_datetime'].dt.time

    # Setting color based on buy/sell
    color_map = {'sell': C_SELL, 'buy': C_BUY}
    product_df['color'] = [color_map[entry] for entry in product_df['side']]


    # Days reversed so they will be in order top to bottom
    days = ['Sunday', 'Saturday', 'Friday',
            'Thursday', 'Wednesday', 'Tuesday',
            'Monday']

    source = ColumnDataSource(product_df)

    tools = 'save,pan,box_zoom,xwheel_zoom,reset'
    p = bplot.figure(title='Trades Over Time', tools=tools,
               plot_width=800,
               plot_height=300,
               y_range=days,
               active_scroll='xwheel_zoom',
               x_axis_type='datetime',
               background_fill_color=C_CHART_BG
               )

    p.circle(x='time', y=jitter('weekday_name', width=0.6, range=p.y_range),
             source=source, alpha=0.6, fill_color='color', line_color=None)

    p.xaxis[0].formatter.days = ['%Hh']

    p.x_range.range_padding = 0

    styles={}
    _apply_figure_styles(p, **styles)
    if output_file:
        bplot.output_file(output_file)
        bplot.save(p)
    if show:
        bplot.show(p)
    return p


def bundle_files(soup, css_files, js_files, write_filename=None):
    """Bundle all files into one"""
    for filename in css_files:
        tag = soup.new_tag('style')
        with open(filename, 'r') as infile:
            tag.append(infile.read())
        soup.head.append(tag)

    for filename in js_files:
        tag = soup.new_tag('script')
        with open(filename, 'r') as infile:
            tag.append(infile.read())
        soup.body.insert_after(tag)

    if filename:
        print(f'Writing to {write_filename}')
        with open(write_filename, 'w') as outfile:
            outfile.write(soup.prettify())



datafiles = os.listdir(DATA_FOLDER)

# Get all the product ids
product_ids = []
pattern = re.compile(r'^[A-Z_]+\.csv$')
for filename in datafiles:
    if pattern.match(filename):
        product_ids.append(filename[:-4])

product_figures = {}

for product_id in product_ids:

    if True:
        # gaps_block
        full_filepath = os.path.join(DATA_FOLDER, f'02_{product_id}_TRADE_ID_GAPS.txt')
        p = build_gaps_block(full_filepath, product_id,)
                            #output_file='test.html', show=True)
        product_figures[f'{product_id}~~gaps_block'] = p
    if True:
        # gaps bar graph
        full_filepath = os.path.join(DATA_FOLDER, f'02_{product_id}_TRADE_ID_GAPS.txt')
        p = build_gaps_bar_graph(full_filepath, product_id,)
                                # output_file='test_bars.html', show=True)
        product_figures[f'{product_id}~~gaps_bar_graph'] = p
    if True:
        # Distributions
        for filename in os.listdir(DATA_FOLDER):
            if filename.startswith(f'08_{product_id}'):
                full_filepath = os.path.join(DATA_FOLDER, filename)
                break
        distributions = get_distribution_histograms(full_filepath, product_id)

        for key, val in distributions:
            product_figures[f'{product_id}~~disthist~~{key}']=val
    if True:
        # Delays histogram
        full_filepath = os.path.join(DATA_FOLDER, f'03_{product_id}_TIME_DELAY.txt')
        p = build_delays_histogram(full_filepath, product_id,)
                                  # output_file='test_delays.html', show=True)
        product_figures[f'{product_id}~~delays_histogram'] = p
    if False:
        # Delays scatter plot
        full_filepath = os.path.join(DATA_FOLDER, product_id+'.csv')
        p = build_delay_scatter(full_filepath, product_id,)
                               # output_file='scatter.html', show=True)
        product_figures[f'{product_id}~~trade_scatter'] = p
    if True:
        # Trade scatter plot
        full_filepath = os.path.join(DATA_FOLDER, product_id+'.csv')
        p = build_trade_scatter(full_filepath, product_id,)
                               # output_file='scatter.html', show=True)
        product_figures[f'{product_id}~~trade_scatter'] = p



script, divs = components(product_figures)
#script, divs = components({'graph': product_figures['USDT_BTC~~gaps_block']})

# Split up the divs into products
product_divs = {product_id: {} for product_id in product_ids}
for name, div in divs.items():
    product_id, fig_name = name.split('~~', 1)
    product_divs[product_id][fig_name] = BeautifulSoup(div, 'html.parser')

subtabs = (('Gaps', ['gaps_block', 'gaps_bar_graph']),
           ('Distributions', ['disthist']),
           ('Delays', ['delays_histogram']),
           ('Trades', ['trade_scatter']),
          )

template = './templates/final_frame.html'
with open(template) as infile:
    soup = BeautifulSoup(infile.read(), 'html.parser')


for product_id, figs in product_divs.items():
    # Add the tab for product_id
    li_tag = soup.new_tag('li')
    a_tag = soup.new_tag('a', onclick=f"openTab(event, '{product_id}')",
                        **{'class': 'tab-link'})
    a_tag.append(product_id)
    li_tag.append(a_tag)
    soup.find(id='tabs').append(li_tag)

    # tab = BeautifulSoup(f"""<li><a onclick="openTab(event, '{product_id}')"
    #     class="tab-link">{product_id}</a></li>""", 'html.parser')
    # soup.find(id='tabs').append(tab)

    # Get the tabcontent
    tab_content = soup.new_tag('div', id=product_id,
                    **{'class': 'tab-content'})
    for subtab_title, subtab_names in subtabs:
        subtab_content = soup.new_tag('div',
                      **{'class': f'subtab-content {subtab_title}'})
        # subtab_div = BeautifulSoup(f"""<div class="subtab-content
        # {subtab_title}"></div>""", 'html.parser')
        divs = []
        for name, div in figs.items():
            for subtab_name in subtab_names:
                if subtab_name in name:
                    divs.append(div)
        # sys.exit()
        # divs = [BeautifulSoup(div, 'html.parser') for name, div in figs.items()
        #         if any(subtab_name in name for subtab_name in subtab_names)]
        for div in divs:
            subtab_content.append(div)
        tab_content.append(subtab_content)

    # tab_content = BeautifulSoup(f"""<div id={product_id}
    #     class="tab-content"></div>""", 'html.parser')
    #tab_content.append(subtab_div)

    soup.find(id='main-content').append(tab_content)

for subtab_title, _ in subtabs:
    li_tag = soup.new_tag('li')
    a_tag = soup.new_tag('a', onclick=f"openSubtab(event, '{subtab_title}')",
                        **{'class': 'subtab-link'})
    a_tag.append(subtab_title)
    li_tag.append(a_tag)
    soup.find(id='subtabs').append(li_tag)

soup.html.append(BeautifulSoup(script, 'html.parser'))

css_files = ['./templates/bokehjs/bokeh-0.13.0.min.css',
'templates/styles.css']
js_files = ['./templates/bokehjs/bokeh-0.13.0.min.js']
bundle_files(soup, css_files, js_files, write_filename=OUTFILE)


sys.exit()

    # Add tab and tabcontent to soup

#EARLY TESTING

# template = 'templates/frame.html'
# template = './templates/empty_test.html'
# with open(template) as infile:
#     soup = BeautifulSoup(infile.read(), 'html.parser')

#
# soup.html.append(BeautifulSoup(script, 'html.parser'))
#
# for name, div in divs.items():
#     soup.find(class_='content').append(BeautifulSoup(div, 'html.parser'))
#
#
# css_files = ['./practice/sub_tab_test/bokehjs/bokeh-0.13.0.min.css',
# './practice/sub_tab_test/styles.css']
# js_files = ['./practice/sub_tab_test/bokehjs/bokeh-0.13.0.min.js']
# bundle_files(soup, css_files, js_files, write=True)


#EARLY TESTING

# sys.exit()
# filename = './practice/sub_tab_test/test_plots.html'
# with open(filename) as infile:
#     html = infile.read()
#
# soup = BeautifulSoup(html, 'html.parser')
#
# css_files = ['./practice/sub_tab_test/bokehjs/bokeh-0.13.0.min.css',
# './practice/sub_tab_test/styles.css']
# js_files = ['./practice/sub_tab_test/bokehjs/bokeh-0.13.0.min.js']
# #bundle_files(soup, css_files, js_files, write=True)



"""
Gaps
    1 Histogram showing length of gaps
        -CHANGED to xaxis is just count of gaps (organized largest gap to
         smallest), y is length of gap
    2 Countiuous bar representing all the trade_ids over time
        -Whole number on xaxis

Distributions
    1 Histograms for all the calculated values

Delays
    1 Histogram showing distribution of delays
        -Title "Delay Duration Between Server and Exchange Datetime"
        -xaxis label "Delay Duration (seconds)"
        -cut x off at 61
    2 How delays relate to time of day

Time Series Analysis
    1 When trades happen most frequently
        -Scatter plot
        -Title "Trades Over Time"
"""




def main():
    pass
    # Build visualizations and plug into files

    # Gaps

    # Distributions

    # Delays

    # Time Series

if __name__ == '__main__':
    main()

