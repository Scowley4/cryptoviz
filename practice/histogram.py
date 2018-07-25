import numpy as np
from bokeh.layouts import gridplot
from bokeh.plotting import figure, show, output_file

TOOLS = 'save,pan,box_zoom,wheel_zoom'
p1 = figure(title='Normal Dist', tools=TOOLS, background_fill_color='#E8DDCB')

mu, sigma = 0, .5
samples = np.random.normal(mu, sigma, 1000)
hist, edges = np.histogram(samples, density=False, bins=50)
p1.quad(top=hist, bottom=0, left=edges[:-1], right=edges[1:],
        fill_color='#036564', line_color='#033649')
p1.legend.location='center_right'
p1.legend.background_fill_color = 'darkgrey'
p1.xaxis.axis_label = 'x'
p1.yaxis.axis_label = 'P(x)'

output_file('single_histogram.html', title='histogram example')
show(p1)
