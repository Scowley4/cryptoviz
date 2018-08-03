import numpy as np
import pandas as pd
import re
import os
import sys
import contextlib
from bs4 import BeautifulSoup

from bokeh.layouts import gridplot
import bokeh.plotting as bplot
from bokeh.models import HoverTool, ColumnDataSource, WheelZoomTool, NumeralTickFormatter
from bokeh.embed import components
from bokeh.models import Range1d

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

DATA_FOLDER = './data/new_data/Output/'

PAGES = './pages'

os.makedirs(PAGES, exist_ok=True)

def _apply_figure_styles(p, **kwargs):
    keys = ['xaxis.major_tick_line_color', 'yaxis.major_tick_line_color',
            'xaxis.minor_tick_line_color', 'yaxis.minor_tick_line_color',
            'xgrid.grid_line_color', 'ygrid.grid_line_color',
            'xaxis.major_label_text_color', 'yaxis.major_label_text_color',
            'xaxis.axis_label_text_color', 'yaxis.axis_label_text_color',
            'title.text_color', 'title.text_font_style', 'title.text_font_size', ]
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


def delay_histogram(filename):
    full_filename = os.path.join(OUTPUTDATA_FOLDER, filename)
    bins = 10

    with open(full_filename, 'r') as infile:
        lines = infile.readlines()[2:]

    def parse_delay(line):
        if 'second' in line:
            number = line.split('+')[0].split(' ')[0]
            count = line.split(': ')[1]
            return {int(number):int(count)}

    def get_delays_hist(delays):
        hist = []
        edges = []
        for i in range(61):
            edges.append(i)
            hist.append(delays.get(i, 0))
        edges.append(61)
        return np.array(hist), np.array(edges)

    delays = {}
    for line in lines:
        delays.update(parse_delay(line))

    hist, edges = get_delays_hist(delays)

    #hist, edges = np.histogram(gap_sizes, bins=bins)


    centers = (edges[:-1]+edges[1:])/2
    width = abs(centers[0]-centers[1])

    TOOLS = 'save,pan,box_zoom,wheel_zoom,reset'

    left = min(centers)*.75
    right = max(centers)*1.2
    top = max(hist)*1.2
    bottom = 0
    x_range = Range1d(start=left, end=right, bounds=(left,right))
    y_range = Range1d(start=bottom, end=top, bounds=(bottom,top))

    p = bplot.figure(title=filename, tools=TOOLS,
                width=1000,
                x_range=x_range,
                y_range=y_range,
                active_scroll='wheel_zoom', background_fill_color=C_CHART_BG)

    source = ColumnDataSource(data={
                'count': hist,
                'center': centers,
                'left': edges[:-1],
                'right': edges[1:]})

    p.vbar(x='center', top='count', width=width, source=source,
           line_color='white', fill_color='black', hover_line_color='grey')
    p.legend.location='center_right'
    p.legend.background_fill_color = 'darkgrey'
    p.xaxis.axis_label = 'Delay time'
    p.yaxis.axis_label = 'Count'
    p.add_tools(HoverTool(tooltips=[#('Value', '$x{1.1111}'),
                                     ('Range', '@left{1.1}-@right{1.1}'),
                                     ('Count', '@count'),
                                     ]))

    bplot.output_file('delay_test.html')

    bplot.show(p)



def build_gaps_bar(path, product_id, output_file=None, show=False):
    #df = pd.read_csv(path, index_col=None,
    #                 parse_dates=['server_datetime',
    #                              'exchange_datetime'])
    #return df

    with open(path, 'r') as infile:
        lines = [line.strip() for line in infile.readlines()]

    def parse_gap(line):
        if 'to' in line:
            split = line.split(' to ')
            return int(split[0]), int(split[1])
        else:
            return int(line), int(line)
    def parse_range(line):
        line = line[len('Range: ('):-1]
        split = line.split(', ')
        return int(split[0]), int(split[1])

    def get_gap_sizes(gaps):
        return [gap[1]-gap[0]+1 for gap in gaps]

    min_trade_id, max_trade_id = parse_range(lines[1])

    gaps = []
    for line in lines[3:]:
        gaps.append(parse_gap(line))

    trade_ids = []
    indicators = []
    missing = set(num for gap in gaps for num in range(gap[0], gap[1]+1))
    for i in range(min_trade_id, max_trade_id+1):
        trade_ids.append(i)
        indicators.append(i not in missing)

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
    TOOLS = 'save,xpan,box_zoom,xwheel_zoom,reset'

    span = max_trade_id - min_trade_id
    space = span*.05
    left = min_trade_id-space
    right = max_trade_id+space
    top = 1.2
    bottom = -.2
    x_range = Range1d(start=left, end=right, bounds=(left,right))
    y_range = Range1d(start=bottom, end=top, bounds=(bottom,top))

# C_TITLE = '#4FB3B7'
# C_TEXT = '#4FB3B7'
# C_AXES = '#519397'
# C_CHART_BG = '#111818'
# C_LEGEND_BG = 'red'
# C_BAR = '#355AA6'
# C_BUY = '#117E1A'
# C_SELL = '#7B1111'
# C_MISSING = '#7B1111'

    p = bplot.figure(title=filename, tools=TOOLS,
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
                'indicator': quad_indicators
                })

    p.quad(top='top', bottom='bottom', left='quad_left', right='quad_right',
           line_color=None, fill_color='fill',source=source)

    p.xaxis.axis_label = 'trade_id'
    p.yaxis.visible = False
    p.add_tools(HoverTool(tooltips=[('trade_ids', '@range_left - @range_right')]))

    p.xaxis[0].formatter = NumeralTickFormatter(format='0'*len(str(min_trade_id)))

    styles = {'ygrid.grid_line_color': None}

    _apply_figure_styles(p, **styles)
    if output_file:
        bplot.output_file(output_file)
        bplot.save(p)
    if show:
        bplot.show(p)
    return p



def bundle_files(soup, css_files, js_files, write=False):
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

    if write:
        with open('outfile.html', 'w') as outfile:
            outfile.write(soup.prettify())



datafiles = os.listdir(DATA_FOLDER)

# Get all the product ids
product_ids = []
pattern = re.compile(r'^[A-Z_]+\.csv$')
for filename in datafiles:
    if pattern.match(filename):
        product_ids.append(filename[:-4])

for product_id in product_ids:
    full_filepath = os.path.join(DATA_FOLDER, '02_'+product_id+'_TRADE_ID_GAPS.txt')
    p = build_gaps_bar(full_filepath, product_id, output_file='test.html', show=True)





filename = './practice/sub_tab_test/test_plots.html'
with open(filename) as infile:
    html = infile.read()

soup = BeautifulSoup(html, 'html.parser')

css_files = ['./practice/sub_tab_test/bokehjs/bokeh-0.13.0.min.css',
'./practice/sub_tab_test/styles.css']
js_files = ['./practice/sub_tab_test/bokehjs/bokeh-0.13.0.min.js']
#bundle_files(soup, css_files, js_files, write=True)



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

