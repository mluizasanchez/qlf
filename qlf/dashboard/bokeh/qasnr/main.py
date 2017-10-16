import os

from bokeh.io import curdoc
from bokeh.models import ColumnDataSource, HoverTool, TapTool, OpenURL
from bokeh.models.widgets import Select, Slider
from bokeh.layouts import row, column, widgetbox, gridplot


from dashboard.bokeh.helper import get_data, get_exposure_ids, \
    init_xy_plot, get_url_args, get_arms_and_spectrographs

QLF_API_URL = os.environ.get(
    'QLF_API_URL',
    'http://localhost:8000/dashboard/api'
)

# Get url query args
args = get_url_args(curdoc)

selected_exposure = args['exposure']
selected_arm = args['arm']
selected_spectrograph = args['spectrograph']

data_model = {
    'bias': [],
#    'bias_amp_1':[],
#    'bias_amp_1_hist':[],
#    'bias_amp_2':[],
#    'bias_amp_2_hist':[],
#    'bias_amp_3':[],
#    'bias_amp_3_hist':[],
#    'bias_amp_4':[],
#    'bias_amp_4_hist':[],
#    'date_new':[],
    'date': []
}

bias = ColumnDataSource(data=data_model.copy())
bias_H = ColumnDataSource(data=data_model.copy())
bias_amp1 = ColumnDataSource(data=data_model.copy())
bias_amp2 = ColumnDataSource(data=data_model.copy())
bias_amp3 = ColumnDataSource(data=data_model.copy())
bias_amp4 = ColumnDataSource(data=data_model.copy())
bias_amp1_H = ColumnDataSource(data=data_model.copy())
bias_amp2_H = ColumnDataSource(data=data_model.copy())
bias_amp3_H = ColumnDataSource(data=data_model.copy())
bias_amp4_H = ColumnDataSource(data=data_model.copy())

params = [
    'BIAS', 'BIAS_AMP']#,
#    'DATA5SIG', 'DIFF1SIG',
#    'DIFF2SIG', 'DIFF3SIG',
#    'MEANBIAS_ROW'
#]

#HARDWIRE TO DEBUG:  
bias_hist = [0.14395, 0.14300000000000002, 0.14364, 0.14342, 0.14346, 0.14320999999999995,0.14347, 0.14297]

bias_amp_hist = [[0.14333, 0.14303999999999997, 0.14302, 0.14332, 0.14348, 0.14357, 0.14381, 0.14340000000000003],
	[0.14332999999999999, 0.14339999999999997, 0.14306, 0.14303000000000002, 0.14331999999999998,0.14324, 0.14272999999999997, 0.14329],
	[0.14317, 0.14313, 0.14336, 0.14364999999999997, 0.14357999999999999, 0.14340999999999998,0.14325, 0.1431],
	[0.14298, 0.14337, 0.14343999999999998, 0.14332, 0.14323, 0.14311, 0.14351, 0.14362000000000003]]


def update(arm, spectrograph, exposure_id):
    exp_zfill = str(exposure_id).zfill(8)

    # get the data ql-getbias-r0-00000003.yaml
    qa_bias = 'ql-getbias-{}-{}.yaml'.format(arm + spectrograph, exp_zfill)

    data = get_data(qa_bias, params)
    
    if not data.empty:

        bias_H.data['bias'] = bias_hist
        bias.data['bias'] = data.BIAS
        bias.data['date'] = [10.]   #HARDWIRE
        bias_H.data['date'] = [1.,2.,3.,4.,5.,6.,7.,8.]  #HARDWIRE
        
        bias_amp1.data['bias'] = [data.BIAS_AMP[0]]
        bias_amp1.data['date'] = [10.]  #HARDWIRE
        bias_amp1_H.data['bias'] = bias_amp_hist[0]
        bias_amp1_H.data['date'] = [1.,2.,3.,4.,5.,6.,7.,8.]  #HARDWIRE
        bias_amp2.data['bias'] = [data.BIAS_AMP[1]]
        bias_amp2.data['date'] = [10.]  #HARDWIRE
        bias_amp2_H.data['bias'] = bias_amp_hist[1]
        bias_amp2_H.data['date'] = [1.,2.,3.,4.,5.,6.,7.,8.]  #HARDWIRE
        bias_amp3.data['bias'] = [data.BIAS_AMP[2]]
        bias_amp3.data['date'] = [10.]  #HARDWIRE
        bias_amp3_H.data['bias'] = bias_amp_hist[2]
        bias_amp3_H.data['date'] = [1.,2.,3.,4.,5.,6.,7.,8.]  #HARDWIRE
        bias_amp4.data['bias'] = [data.BIAS_AMP[3]]
        bias_amp4.data['date'] = [10.]  #HARDWIRE
        bias_amp4_H.data['bias'] = bias_amp_hist[3]
        bias_amp4_H.data['date'] = [1.,2.,3.,4.,5.,6.,7.,8.]  #HARDWIRE



# configure bokeh widgets
exposure = get_exposure_ids()

print('exposures  ')
print(exposure)
print('termina exposures ')

if not exposure:
    exposure.append(int(selected_exposure))

exposure = sorted(exposure)

exp_slider = Slider(
    start=int(exposure[0]), end=int(exposure[-1]),
    value=int(selected_exposure), step=1,
    title="Exposure ID")

cameras = get_arms_and_spectrographs()

if not cameras["spectrographs"]:
    cameras["spectrographs"].append(selected_spectrograph)

if not cameras["arms"]:
    cameras["arms"].append(selected_arm)

# we can filter by spectrograph
spectrograph_select = Select(
    title="Spectrograph:",
    value=selected_spectrograph,
    options=cameras["spectrographs"],
    width=100)

# and arm
arm_select = Select(
    title="Arm:",
    options=cameras['arms'],
    value=selected_arm,
    width=100)

def arm_handler(attr, old, value):
    update(value, spectrograph_select.value, exp_slider.value)

def spectrograph_handler(attr, old, value):
    update(arm_select.value, value, exp_slider.value)

def exposure_handler(attr, old, value):
    update(arm_select.value, spectrograph_select.value, value)

arm_select.on_change("value", arm_handler)
spectrograph_select.on_change("value", spectrograph_handler)
exp_slider.on_change("value", exposure_handler)

# here we make the plots
html_tooltip = """
    <div>
        <div>
            <span style="font-size: 12px; font-weight: bold; color: #303030;">TIME: </span>
            <span style="font-size: 13px; color: #515151;">@date</span>
        </div>
        <div>
            <span style="font-size: 12px; font-weight: bold; color: #303030;">BIAS: </span>
            <span style="font-size: 13px; color: #515151;">@bias</span>
        </div>

    </div>
"""


hover = HoverTool(tooltips=html_tooltip)
bias_plot = init_xy_plot(hover=hover)

bias_plot.circle(x='date', y='bias', source=bias_H, color="blue", size=5)  #CHANGE color if alarm
bias_plot.circle(x='date', y='bias', source=bias, color="green", size=6)  #CHANGE color if alarm
bias_plot.xaxis.axis_label = "TIME"
bias_plot.yaxis.axis_label = "BIAS"

bias_plot.plot_height=150

hover = HoverTool(tooltips=html_tooltip)

bias_amp1_plot = init_xy_plot(hover=hover)
bias_amp1_plot.circle(x='date', y='bias', source=bias_amp1, color="blue", size=5)  #CHANGE color if alarm
bias_amp1_plot.circle(x='date', y='bias', source=bias_amp1_H, color="green", size=6)  #CHANGE color if alarm
bias_amp1_plot.xaxis.axis_label = "TIME"
bias_amp1_plot.yaxis.axis_label = "BIAS"
bias_amp1_plot.title.text = 'AMP 1'

bias_amp1_plot.plot_height=150
hover = HoverTool(tooltips=html_tooltip)

bias_amp2_plot = init_xy_plot(hover=hover)
bias_amp2_plot.circle(x='date', y='bias', source=bias_amp2, color="blue", size=5)  #CHANGE color if alarm
bias_amp2_plot.circle(x='date', y='bias', source=bias_amp2_H, color="green", size=6)  #CHANGE color if alarm
bias_amp2_plot.xaxis.axis_label = "TIME"
bias_amp2_plot.yaxis.axis_label = "BIAS"
bias_amp2_plot.title.text = 'AMP 2'

bias_amp2_plot.plot_height=150
hover = HoverTool(tooltips=html_tooltip)

bias_amp3_plot = init_xy_plot(hover=hover)
bias_amp3_plot.circle(x='date', y='bias', source=bias_amp3, color="blue", size=5)  #CHANGE color if alarm
bias_amp3_plot.circle(x='date', y='bias', source=bias_amp3_H, color="green", size=6)  #CHANGE color if alarm
bias_amp3_plot.xaxis.axis_label = "TIME"
bias_amp3_plot.yaxis.axis_label = "BIAS"
bias_amp3_plot.title.text = 'AMP 3'

bias_amp3_plot.plot_height=150
hover = HoverTool(tooltips=html_tooltip)

bias_amp4_plot = init_xy_plot(hover=hover)
bias_amp4_plot.circle(x='date', y='bias', source=bias_amp4, color="blue", size=5)  #CHANGE color if alarm
bias_amp4_plot.circle(x='date', y='bias', source=bias_amp4_H, color="green", size=6)  #CHANGE color if alarm
bias_amp4_plot.xaxis.axis_label = "TIME"
bias_amp4_plot.yaxis.axis_label = "BIAS"
bias_amp4_plot.title.text = 'AMP 4'

bias_amp4_plot.plot_height=150

import logging
logger = logging.getLogger(__name__)

logger.error(selected_exposure)
update(selected_arm, selected_spectrograph, selected_exposure)

#plot = gridplot([[bias_plot]], responsive=True)
amp_plot = gridplot([[bias_amp1_plot,bias_amp2_plot],[bias_amp3_plot,bias_amp4_plot]], responsive=True)

# and create the final layout
layout = column(widgetbox(exp_slider, responsive=True),
                row(widgetbox(arm_select, width=130),
                    widgetbox(spectrograph_select, width=130)),
                bias_plot, amp_plot, responsive=True)

curdoc().add_root(layout)
curdoc().title = "BIAS"
