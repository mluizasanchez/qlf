import sys

from bokeh.plotting import Figure
from bokeh.layouts import row, column, widgetbox, gridplot

from bokeh.io import curdoc
from bokeh.io import output_notebook, show, output_file

from bokeh.models import ColumnDataSource, HoverTool, Range1d, OpenURL
from bokeh.models import LinearColorMapper , ColorBar
from bokeh.models.widgets import Select, Slider
from dashboard.bokeh.helper import get_url_args, write_description, get_scalar_metrics
from bokeh.models import TapTool, OpenURL
from bokeh.models.widgets import PreText, Div

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

xwsigma   = metrics['xwsigma']
snr       = metrics['snr'] #RA and DEC info
skycont   = metrics['skycont']

def palette(name_of_mpl_palette):
    """ Transforms a matplotlib palettes into a bokeh 
    palettes
    """
    from matplotlib.colors import rgb2hex
    import matplotlib.cm as cm
    colormap =cm.get_cmap(name_of_mpl_palette) #choose any matplotlib colormap here
    bokehpalette = [rgb2hex(m) for m in colormap(np.arange(colormap.N))]
    return bokehpalette

#nipy_spectral)#Viridis256)#,RdYlBu11)#Viridis256)#, low=0, high=100)
my_palette = palette("viridis")


xsigma_tooltip = """
    <div>
        <div>
            <span style="font-size: 12px; font-weight: bold; color: #303030;">XSigma: </span>
            <span style="font-size: 13px; color: #515151">@xsigma</span>
        </div>
        <div>
            <span style="font-size: 12px; font-weight: bold; color: #303030;">Obj Type: </span>
            <span style="font-size: 13px; color: #515151;">@OBJ_TYPE</span>
        </div>
        <div>
            <span style="font-size: 12px; font-weight: bold; color: #303030;">RA: </span>
            <span style="font-size: 13px; color: #515151;">@x1</span>
        </div>
        <div>
            <span style="font-size: 12px; font-weight: bold; color: #303030;">DEC: </span>
            <span style="font-size: 13px; color: #515151;">@y1</span>
        </div>
    </div>
"""

wsigma_tooltip = """
    <div>
        <div>
            <span style="font-size: 12px; font-weight: bold; color: #303030;">WSigma: </span>
            <span style="font-size: 13px; color: #515151">@wsigma</span>
        </div>
        <div>
            <span style="font-size: 12px; font-weight: bold; color: #303030;">Obj Type: </span>
            <span style="font-size: 13px; color: #515151;">@OBJ_TYPE</span>
        </div>
        <div>
            <span style="font-size: 12px; font-weight: bold; color: #303030;">RA: </span>
            <span style="font-size: 13px; color: #515151;">@x1</span>
        </div>
        <div>
            <span style="font-size: 12px; font-weight: bold; color: #303030;">DEC: </span>
            <span style="font-size: 13px; color: #515151;">@y1</span>
        </div>
    </div>
"""

url = "http://legacysurvey.org/viewer?ra=@ra&dec=@dec&zoom=16&layer=decals-dr5"

# determining the position of selected cam fibers:
c1,c2 = int(selected_spectrograph)*500, (int(selected_spectrograph)+1)*500
# 171 qlf_fiberid = np.arange(0,5000)[c1:c2] 
qlf_fiberid = np.arange(0,5000)[c1:c2] 
# print (snr['ELG_FIBERID'][:10], '\nfiber:',qlf_fiberid[:10])
# marking type of objects:
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
# ---------------------------------


xsigma_hover = HoverTool(tooltips=xsigma_tooltip)
wsigma_hover = HoverTool(tooltips=wsigma_tooltip)

xsigma = xwsigma['XSIGMA']
wsigma = xwsigma['WSIGMA']

source = ColumnDataSource(data={
    'x1'     : xwsigma['RA'][c1:c2],
    'y1'     : xwsigma['DEC'][c1:c2],
    'xsigma' : xwsigma['XSIGMA'],
    'wsigma' : xwsigma['WSIGMA'],
    'QLF_FIBERID': qlf_fiberid,
    'OBJ_TYPE': obj_type
})

source_comp = ColumnDataSource(
    data = {
    'x1': xwsigma['RA'][:c1] + xwsigma['RA'][c2:],
    'y1': xwsigma['DEC'][:c1] + xwsigma['DEC'][c2:],
    'xsigma': ['']*4500,
    'wsigma': ['']*4500
})

# axes limit
xmin, xmax = [min(xwsigma['RA'][:]), max(xwsigma['RA'][:])]
ymin, ymax = [min(xwsigma['DEC'][:]), max(xwsigma['DEC'][:])]
xfac, yfac  = [(xmax-xmin)*0.06, (ymax-ymin)*0.06]
left, right = xmin -xfac, xmax+xfac
bottom, top = ymin-yfac, ymax+yfac

xmapper = LinearColorMapper(palette= my_palette,
                           low=0.98*np.min(xsigma), 
                           high=1.02*np.max(xsigma))

wmapper = LinearColorMapper(palette= my_palette,
                           low=0.99*np.min(wsigma), 
                           high=1.01*np.max(wsigma))

# ======
# XSIGMA

radius = 0.015
radius_hover = 0.0165

px = Figure( title = 'XSIGMA', x_axis_label='RA', y_axis_label='DEC'
           , plot_width=700, plot_height=600
           , x_range=Range1d(left, right), y_range=Range1d(bottom, top)
           , tools= [xsigma_hover, "pan,box_zoom,reset,crosshair, tap"])

# Color Map
px.circle('x1','y1', source = source, name="data", radius = radius,
        fill_color={'field': 'xsigma', 'transform': xmapper}, 
         line_color='black', line_width=0.1,
         hover_line_color='red')

# marking the Hover point
px.circle('x1','y1', source = source, name="data", radius = radius_hover
          , hover_fill_color={'field': 'xsigma', 'transform': xmapper}
          , fill_color=None, line_color=None
          , line_width=3, hover_line_color='red')

px.circle('x1','y1', source = source_comp, radius = radius_hover,
         fill_color = 'lightgray', line_color='black', line_width=0.3)

taptool = px.select(type=TapTool)
taptool.callback = OpenURL(url=url)


# bokeh.pydata.org/en/latest/docs/reference/models/annotations.html
xcolor_bar = ColorBar(color_mapper= xmapper, label_standoff=-13,
                     major_label_text_font_style="bold", padding = 26,
                     major_label_text_align='right',
                     major_label_text_font_size="10pt",
                     location=(0, 0))

px.add_layout(xcolor_bar, 'left')



# ======
# WSIGMA
pw = Figure( title = 'WSIGMA', x_axis_label='RA', y_axis_label='DEC'
           , plot_width=700, plot_height=600
           , x_range=Range1d(left, right), y_range=Range1d(bottom, top)
           , tools= [wsigma_hover, "pan,box_zoom,reset,crosshair,tap"])

# Color Map
pw.circle('x1','y1', source = source, name="data", radius = radius,
        fill_color={'field': 'wsigma', 'transform': wmapper}, 
         line_color='black', line_width=0.1,
         hover_line_color='red')

# marking the Hover point
pw.circle('x1','y1', source = source, name="data", radius = radius_hover
          , hover_fill_color={'field': 'wsigma', 'transform': wmapper}
          , fill_color=None, line_color=None
          , line_width=3, hover_line_color='red')

pw.circle('x1','y1', source = source_comp, radius = 0.015,
         fill_color = 'lightgray', line_color='black', line_width=0.3)

taptool = pw.select(type=TapTool)
taptool.callback = OpenURL(url=url)


# bokeh.pydata.org/en/latest/docs/reference/models/annotations.html
wcolor_bar = ColorBar(color_mapper= wmapper, label_standoff=-13,
                     major_label_text_font_style="bold", padding = 26,
                     major_label_text_align='right',
                     major_label_text_font_size="10pt",
                     location=(0, 0))

pw.add_layout(wcolor_bar, 'left')


# ================================
# histogram

def histpar(yscale, hist):
    if yscale == 'log':
        ylabel = "Frequency + 1"
        yrange = (1, 11**(int(np.log10(max(hist)))+1) )
        bottomval = 'bottomplusone'
        histval = 'histplusone'
    else:
        ylabel = "Frequency"
        yrange = (0, 1.1*max(hist))
        bottomval = 'bottom'
        histval = 'hist'
    return [ylabel,yrange,bottomval,histval]


xhistlabel= "XSIGMA"
yscale = "auto"#"auto" or "log"



hist_tooltip_x = """
    <div>
        <div>
            <span style="font-size: 12px; font-weight: bold; color: #303030;">Frequency: </span>
            <span style="font-size: 13px; color: #515151">@hist</span>
        </div>
        <div>
            <span style="font-size: 12px; font-weight: bold; color: #303030;">XSIGMA: </span>
            <span style="font-size: 13px; color: #515151;">[@left, @right]</span>
        </div>
    </div>
"""


hist, edges = np.histogram(xwsigma['XSIGMA'],'auto')# auto: Maximum of the ‘sturges’ and ‘fd’ estimators.

source_hist = ColumnDataSource(data={
    'hist': hist,
    'histplusone':hist+1,
    'bottom':[0] *len(hist),
    'bottomplusone':[1]*len(hist),
    'left':edges[:-1],
    'right':edges[1:]
})

hover = HoverTool(tooltips=hist_tooltip_x)

ylabel,yrange,bottomval,histval = histpar(yscale, hist)

p_hist_x = Figure(title='',tools=[hover,"pan,wheel_zoom,box_zoom,reset"],
           y_axis_label= ylabel, x_axis_label=xhistlabel, background_fill_color="white"
        , plot_width=700, plot_height=500
        , x_axis_type="auto",    y_axis_type=yscale
        , y_range=yrange)#, y_range=(1, 11**(int(np.log10(max(hist)))+1) ) )

p_hist_x.quad(top=histval, bottom=bottomval, left='left', right='right',
       source=source_hist, 
        fill_color="dodgerblue", line_color="black", alpha=0.8,
       hover_fill_color='blue', hover_line_color='black', hover_alpha=0.8)

# Histogram 2
# histogram
xhistlabel= "WSIGMA"
hist_tooltip_w = """
    <div>
        <div>
            <span style="font-size: 12px; font-weight: bold; color: #303030;">Frequency: </span>
            <span style="font-size: 13px; color: #515151">@hist</span>
        </div>
        <div>
            <span style="font-size: 12px; font-weight: bold; color: #303030;">WSIGMA: </span>
            <span style="font-size: 13px; color: #515151;">[@left, @right]</span>
        </div>
    </div>
"""


hist, edges = np.histogram(xwsigma['WSIGMA'], 'auto') # Freedman Diaconis Estimator

source_hist = ColumnDataSource(data={
    'hist': hist,
    'histplusone':hist+1,
    'bottom':[0] *len(hist),
    'bottomplusone':[1]*len(hist),
    'left':edges[:-1],
    'right':edges[1:]
})

hover = HoverTool(tooltips=hist_tooltip_w)

ylabel,yrange,bottomval,histval = histpar(yscale, hist)

p_hist_w = Figure(title='',tools=[hover,"pan,wheel_zoom,box_zoom,reset"],
           y_axis_label=ylabel, x_axis_label=xhistlabel, background_fill_color="white"
        , plot_width=700, plot_height=500
        , x_axis_type="auto",    y_axis_type=yscale
        ,y_range=yrange)#, y_range=(1, 11**(int(np.log10(max(hist)))+1) ) )

p_hist_w.quad(top= histval, bottom=bottomval, left='left', right='right',
       source=source_hist, 
        fill_color="dodgerblue", line_color="black", alpha=0.8,
       hover_fill_color='blue', hover_line_color='black', hover_alpha=0.8)

# -------------------------------------------------------------------------
from bokeh.models import Spacer

info_col=Div(text=write_description('xwsigma'), width=2*pw.plot_width)
pxh = column(px,p_hist_x)
pwh = column(pw,p_hist_w)
layoutplot= row([pxh, Spacer(width=80),pwh], responsive=False)#, sizing_mode='scale_width')
layout = column(widgetbox(info_col),layoutplot)

curdoc().add_root(layout)
curdoc().title = "XWSIGMA"
