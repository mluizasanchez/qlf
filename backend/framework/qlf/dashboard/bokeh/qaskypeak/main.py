import sys

from bokeh.plotting import Figure
from bokeh.layouts import row, column, widgetbox, gridplot
from bokeh.layouts import Spacer

from bokeh.io import curdoc
from bokeh.io import output_notebook, show, output_file

from bokeh.models import HoverTool, ColumnDataSource
from bokeh.models import (LinearColorMapper, ColorBar)
from bokeh.models import TapTool, OpenURL
from bokeh.models.widgets import Select
from bokeh.models.widgets import PreText, Div
from bokeh.models import PrintfTickFormatter
from dashboard.bokeh.helper import write_info



from bokeh.palettes import (RdYlBu, Colorblind, Viridis256)

from bokeh.io import output_notebook
import numpy as np

from dashboard.bokeh.helper import get_url_args, write_description

import numpy as np
import logging

logger = logging.getLogger(__name__)

# =============================================
# THIS comes from INTERFACE
#
args = get_url_args(curdoc)


try:
    selected_exposure = args['exposure']
    selected_arm = args['arm']
    selected_spectrograph = args['spectrograph']
except:
    sys.exit('Invalid args')

# =============================================
# THIS comes from QLF.CFG
#
night = '20190101'

# ============================================
#  THIS READ yaml files
#
from dashboard.bokeh.utils.scalar_metrics import LoadMetrics

cam = selected_arm+str(selected_spectrograph)
exp = selected_exposure # intentionaly redundant
lm = LoadMetrics(cam, exp, night);
metrics, tests  = lm.metrics, lm.tests 

skypeak = metrics['skypeak']
par     = tests['skypeak']

# ============================================
# values to plot:
name = 'PEAKCOUNT'
metr = skypeak


# ============================================
# THIS: Given the set up in the block above, 
#       we have the bokeh plots

def palette(name_of_mpl_palette):
    """ Transforms a matplotlib palettes into a bokeh 
    palettes
    """
    from matplotlib.colors import rgb2hex
    import matplotlib.cm as cm
    colormap =cm.get_cmap(name_of_mpl_palette) #choose any matplotlib colormap here
    bokehpalette = [rgb2hex(m) for m in colormap(np.arange(colormap.N))]
    return bokehpalette

my_palette = palette("viridis")

peak_tooltip = """
    <div>
        <div>
            <span style="font-size: 12px; font-weight: bold; color: #303030;">PEAKCOUNT: </span>
            <span style="font-size: 13px; color: #515151">@peakcount</span>
        </div>
        <div>
            <span style="font-size: 12px; font-weight: bold; color: #303030;">RA: </span>
            <span style="font-size: 13px; color: #515151;">@x1</span>
        </div>
        <div>
            <span style="font-size: 12px; font-weight: bold; color: #303030;">DEC: </span>
            <span style="font-size: 13px; color: #515151;">@y1</span>
        </div>
        <div>
            <span style="font-size: 12px; font-weight: bold; color: #303030;">Obj Type: </span>
            <span style="font-size: 13px; color: #515151;">@OBJ_TYPE</span>
        </div>
    </div>
"""
url = "http://legacysurvey.org/viewer?ra=@ra&dec=@dec&zoom=16&layer=decals-dr5"

c1,c2 = int(selected_spectrograph)*500, (int(selected_spectrograph)+1)*500
qlf_fiberid = np.arange(0,5000)[c1:c2] 

# prevent to broke if the file was not generated by ql
try:
    snr = metrics['snr']
except:
    snr= {'ELG_FIBERID':[],'QSO_FIBERID':[],
          'LRG_FIBERID':[],'STAR_FIBERID':[]}
try:
    skycont = metrics['skycont']
except:
    skycont ={'SKYFIBERID':[]}
# marking type of objects:
obj_type=[]
for j in qlf_fiberid:
    i = j - c1
    if  i in snr['ELG_FIBERID']:
        obj_type.append('ELG')
    elif  i  in snr['QSO_FIBERID']:
        obj_type.append('QSO')
    elif  i  in snr['LRG_FIBERID']:
        obj_type.append('LRG')
    elif  i in snr['STAR_FIBERID']:
        obj_type.append('STAR')
    elif i in skycont['SKYFIBERID']:
        obj_type.append('SKY')
    else:
        obj_type.append('UNKNOWN')


peak_hover = HoverTool(tooltips=peak_tooltip)

peakcount = metr['PEAKCOUNT']

source = ColumnDataSource(data={
    'x1'     : metr['RA'][c1:c2],
    'y1'     : metr['DEC'][c1:c2],
    'peakcount' : peakcount,
    'QLF_FIBERID': qlf_fiberid,
    'OBJ_TYPE' : obj_type,
    
})

mapper = LinearColorMapper(palette= my_palette,
                           low=0.98*np.min(peakcount), 
                           high=1.02*np.max(peakcount))

radius = 0.012
radius_hover = 0.0135

p = Figure( title = 'PEAKCOUNT: sum of counts in peak regions ', x_axis_label='RA', y_axis_label='DEC'
           , plot_width=770, plot_height=700
           # , x_range=Range1d(left, right), y_range=Range1d(bottom, top)
           , tools= [peak_hover, "pan,box_zoom,reset,crosshair, tap"])

# Color Map
p.circle('x1','y1', source = source, name="data", radius = radius,
        fill_color={'field': 'peakcount', 'transform': mapper}, 
         line_color='black', line_width=0.1,
         hover_line_color='red')

# marking the Hover point
p.circle('x1','y1', source = source, name="data", radius = radius_hover
          , hover_fill_color={'field': 'peakcount', 'transform': mapper}
          , fill_color=None, line_color=None
          , line_width=3, hover_line_color='red')

taptool = p.select(type=TapTool)
taptool.callback = OpenURL(url=url)

# bokeh.pydata.org/en/latest/docs/reference/models/annotations.html
xcolor_bar = ColorBar(color_mapper= mapper, label_standoff=-13,
                     title= "PEAKCOUNT",
                     major_label_text_font_style="bold", padding = 26,
                     major_label_text_align='right',
                     major_label_text_font_size="10pt",
                     location=(0, 0))

p.add_layout(xcolor_bar, 'left')

info, nlines = write_info('skypeak', tests['skypeak'])
txt = PreText(text=info, height=nlines*20, width= int(1.5*p.plot_width) )
info_col=Div(text=write_description('skypeak'), width=p.plot_width)


# ================================
# histogram
hist_tooltip = """
    <div>
        <div>
            <span style="font-size: 12px; font-weight: bold; color: #303030;">Frequency: </span>
            <span style="font-size: 13px; color: #515151">@hist</span>
        </div>
        <div>
            <span style="font-size: 12px; font-weight: bold; color: #303030;">Peakcount: </span>
            <span style="font-size: 13px; color: #515151;">[@left, @right]</span>
        </div>
    </div>
"""

Nbins=40
hist, edges = np.histogram(peakcount, bins = Nbins)

source_hist = ColumnDataSource(data={
    'hist': hist,
    'histplusone':hist+1,
    'bottom':[0] *len(hist),
    'bottomplusone':[1]*len(hist),
    'left':edges[:-1],
    'right':edges[1:]
})


hover = HoverTool(tooltips=hist_tooltip)

p_hist = Figure(title='',tools=[hover,"pan,wheel_zoom,box_zoom,reset"],
           y_axis_label='Frequency + 1', x_axis_label='PEAKCOUNT', background_fill_color="white"
        , plot_width=700, plot_height=500
        , x_axis_type="auto",    y_axis_type="log"
        , y_range=(1, 11**(int(np.log10(max(hist)))+1) ) )

p_hist.quad(top='histplusone', bottom='bottomplusone', left='left', right='right',
       source=source_hist, 
        fill_color="dodgerblue", line_color="black", alpha=0.8,
       hover_fill_color='blue', hover_line_color='black', hover_alpha=0.8)

from bokeh.models import Span


logger.info(par['PEAKCOUNT_WARN_RANGE'])
spans = Span(location= par['PEAKCOUNT_WARN_RANGE'][0] , dimension='height', line_color='yellow',
                          line_dash='dashed', line_width=3)

p_hist.add_layout(spans)

"""for i in par['PEAKCOUNT_WARN_RANGE']:
    spans = Span(location= i, dimension='height', line_color='red',
                          line_dash='dashed', line_width=3)
    p_hist.add_layout(spans)
"""
row1 = row(p, column(Spacer(height=180), p_hist) )
p2txt = column(widgetbox(info_col),row1)
layout = gridplot([[p2txt]]) 

#logger.info("widths", p.plot_width, p_hist.plot_width)
# End of Bokeh Block
curdoc().add_root(layout)
curdoc().title= "SKYPEAK"
