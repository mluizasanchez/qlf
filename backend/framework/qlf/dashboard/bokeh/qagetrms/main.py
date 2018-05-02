import sys

from bokeh.plotting import Figure
from bokeh.layouts import row, column, widgetbox, gridplot

from bokeh.io import curdoc
from bokeh.io import output_notebook, show, output_file

from bokeh.models.widgets import PreText, Div
from bokeh.models import HoverTool, ColumnDataSource, PrintfTickFormatter
from bokeh.models import (LinearColorMapper ,    ColorBar)


from bokeh.palettes import (RdYlBu, Colorblind, Viridis256)

from bokeh.io import output_notebook
import numpy as np

from dashboard.bokeh.helper import get_url_args, write_description, write_info, get_scalar_metrics

import numpy as np
import logging

logger = logging.getLogger(__name__)

# =============================================
# THIS comes from INTERFACE
#
args = get_url_args(curdoc)

try:
    selected_process_id = args['process_id']
    selected_arm = args['arm']
    selected_spectrograph = args['spectrograph']
except:
    sys.exit('Invalid args')

# ============================================
#  THIS READ yaml files
#

cam = selected_arm+str(selected_spectrograph)
try:
    lm = get_scalar_metrics(selected_process_id, cam)
    metrics, tests  = lm['results']['metrics'], lm['results']['tests']
except:
    sys.exit('Could not load metrics')

getrms    = metrics['getrms']
name = 'RMS_AMP'
metr = getrms

# Get Bias
dx = [0,1,0,1]
dy = [1,1,0,0]
dz = metr[name] #getbias['BIAS_AMP']
mapper = LinearColorMapper(palette= Viridis256, low=min(dz),high=max(dz) )


source = ColumnDataSource(
    data=dict(
        x=dx,
        y=dy,
        y_offset1 = [i+0.15 for i in dy],
        y_offset2 = [i-0.05 for i in dy],

        z = dz,
        amp = ['AMP %s'%i for i in range(1,5) ] ,
        ztext = ['{:3.2e}'.format(i) for i in dz]
    )
)

cmap_tooltip = """
    <div>
        <div>
            <span style="font-size: 12px; font-weight: bold; color: #303030;">counts: </span>
            <span style="font-size: 13px; color: #515151">@z</span>
        </div>
        <div>
            <span style="font-size: 12px; font-weight: bold; color: #303030;">AMP: </span>
            <span style="font-size: 13px; color: #515151;">@amp</span>
        </div>
    </div>
""".replace("counts:", name+":")

hover = HoverTool(tooltips=cmap_tooltip)


p = Figure(title=name, tools=[hover],
           x_range= list([-0.5,1.5]),           # length = 18
           y_range= list([-0.5,1.5]), #numeros romanos
           plot_width=450, plot_height=400
          )


p.grid.grid_line_color = None
p.outline_line_color = None
p.axis.clear

text_props = {
    "source": source,
    "angle": 0,
    "color": "black",
    "text_color":"black",
    "text_align": "center",
    "text_baseline": "middle"
}



p.rect("x", "y", .98, .98, 0, source=source,
       fill_color={'field': 'z', 'transform': mapper}, fill_alpha=0.9)#, color="color")
p.axis.minor_tick_line_color=None

p.text(x="x", y="y_offset2", text="ztext",
       text_font_style="bold", text_font_size="20pt", **text_props)
p.text(x="x", y="y_offset1", text="amp",
        text_font_size="18pt", **text_props)

formatter = PrintfTickFormatter(format='%2.1e')
color_bar = ColorBar(color_mapper=mapper,  major_label_text_align='left',
                major_label_text_font_size='10pt', label_standoff=2, location=(0, 0)
                   ,formatter=formatter, title="(ADU)", title_text_baseline="alphabetic" )

p.add_layout(color_bar, 'right')


p.xaxis.major_label_text_font_size = '0pt'  # turn off x-axis tick labels
p.yaxis.major_label_text_font_size = '0pt'  # turn off y-axis tick labels
p.xaxis.major_tick_line_color = None  # turn off x-axis major ticks
p.xaxis.minor_tick_line_color = None  # turn off x-axis minor ticks

p.yaxis.major_tick_line_color = None  # turn off y-axis major ticks
p.yaxis.minor_tick_line_color = None  # turn off y-axis minor ticks

#infos
info, nlines = write_info('getrms', tests['getrms'])
info= """<div> 
<body><p  style="text-align:left; color:#262626; font-size:20px;">
            <b>Get RMS</b> <br>Used to calculate RMS of region of 2D image, including overscan.</body></div>"""
nlines=2
txt = Div(text=info, width=p.plot_width)
info_col=Div(text=write_description('getrms'), width=p.plot_width)
ptxt = column(widgetbox(info_col),p)



# End of Bokeh Block
curdoc().add_root(ptxt)
curdoc().title="GETRMS"
