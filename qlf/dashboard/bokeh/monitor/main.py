from bokeh.plotting import figure, output_file, curdoc
from bokeh.models import ColumnDataSource, LabelSet, Label
from bokeh.driving import count
from dashboard.bokeh.helper import get_last_process
from bokeh.models import RadioGroup, Div
from bokeh.layouts import widgetbox, row, column, gridplot
from bokeh.charts import Donut
import pandas as pd
from bokeh.charts.utils import df_from_json

import configparser
import os
import logging

logger = logging.getLogger(__name__)

qlf_root = os.getenv('QLF_ROOT')
cfg = configparser.ConfigParser()

try:
    cfg.read('%s/qlf/config/qlf.cfg' % qlf_root)
    desi_spectro_redux = cfg.get('namespace', 'desi_spectro_redux')
except Exception as error:
    logger.error(error)
    logger.error("Error reading  %s/qlf/config/qlf.cfg" % qlf_root)

PROCESS = dict()

bars = list()
label_name = list()
cameras = dict()
listColor = list()

# AF: height of the bars in the bokeh chart
barsHeight = list()

for num in range(30):
    # AF: add bars
    bars.append(num)
    listColor.append('#0000FF')
    barsHeight.append(0.5)
    # AF: add labels for cameras and processing steps

    if 'z9' not in label_name:
        cameras['z' + str(num)] = Label(x=-6.5, y=num - .3, text='z' + str(num))
        #cameras['stagez' + str(num)] = Label(x=50, y=num - .3, text='Initializing ', background_fill_color='white',
        #                                     background_fill_alpha=0.7)
        label_name.append('z' + str(num))
    elif 'r9' not in label_name:
        cameras['r' + str(num - 10)] = Label(x=-6.5, y=num - .3, text='r' + str(num - 10))
        #cameras['stager' + str(num - 10)] = Label(x=50, y=num - .3, text='Initializing ',
        #                                          background_fill_color='white', background_fill_alpha=0.7)
        label_name.append('r' + str(num - 10))
    elif 'b9' not in label_name:
        cameras['b' + str(num - 20)] = Label(x=-6.5, y=num - .3, text='b' + str(num - 20))
        #cameras['stageg' + str(num - 20)] = Label(x=50, y=num - .3, text='Initializing ', render_mode='css',
        #                                          background_fill_color='white', background_fill_alpha=0.7)
        label_name.append('b' + str(num - 20))

plot = figure(height=700, x_range=(-9, 120))
# plot.logo = None
plot.toolbar_location = None

for cam in cameras:
    plot.add_layout(cameras[cam])

sourceBar = ColumnDataSource(dict(y=[0], right=[0], height=[0], color=['#0000FF']))

plot.hbar(y='y', right='right', height='height', color='color', source=sourceBar)
# curdoc().add_root(plot)
reduct_mode = widgetbox(Div(text="<b>Reduction Mode:</b>"))

radio = RadioGroup(labels=['Manual', 'Automatic'], active=1)
column_mode = column(reduct_mode, widgetbox(radio))

exposure_label = widgetbox(Div(text="<b>Exposure Id:</b>"))
exposure = widgetbox(Div(text="999999999"))
column_exposure = column(exposure_label, exposure)

date_label = widgetbox(Div(text="<b>Date:</b>"))
date = widgetbox(Div(text="MM/DD/YYYYY"))
column_date = column(date_label, date)

time_label = widgetbox(Div(text="<b>Time:</b>"))
time = widgetbox(Div(text="HH:MM:SS"))
column_time = column(time_label, time)

curdoc().add_root(row(column_mode,column_exposure,column_date,column_time))

wedge = {'data': [{'0': 1, '1': 1, '2': 1, '3': 1, '4': 1, '5': 1, '6': 1, '7': 1, '8': 1, '9': 1 }]}

df = df_from_json(wedge)
df = pd.melt(df,
             value_vars=['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'],
             value_name='number', var_name='spectrograph')

circle_size =150

wedge_b = Donut(df, plot_height=circle_size, plot_width=circle_size, color=["green"] * 30)
wedge_r = Donut(df, plot_height=circle_size, plot_width=circle_size, color=["green"] * 30)
wedge_z = Donut(df, plot_height=circle_size, plot_width=circle_size, color=["green"] * 30)

wedge_b.toolbar_location = None
wedge_r.toolbar_location = None
wedge_z.toolbar_location = None

wedge_b_spectra = Donut(df, plot_height=circle_size, plot_width=circle_size, color=["green"] * 30)
wedge_r_spectra = Donut(df, plot_height=circle_size, plot_width=circle_size, color=["green"] * 30)
wedge_z_spectra = Donut(df, plot_height=circle_size, plot_width=circle_size, color=["green"] * 30)

wedge_b_spectra.toolbar_location = None
wedge_r_spectra.toolbar_location = None
wedge_z_spectra.toolbar_location = None

wedge_b_fiber = Donut(df, plot_height=circle_size, plot_width=circle_size, color=["green"] * 30)
wedge_r_fiber = Donut(df, plot_height=circle_size, plot_width=circle_size, color=["green"] * 30)
wedge_z_fiber = Donut(df, plot_height=circle_size, plot_width=circle_size, color=["green"] * 30)

wedge_b_fiber.toolbar_location = None
wedge_r_fiber.toolbar_location = None
wedge_z_fiber.toolbar_location = None

wedge_b_sky = Donut(df, plot_height=circle_size, plot_width=circle_size, color=["green"] * 30)
wedge_r_sky = Donut(df, plot_height=circle_size, plot_width=circle_size, color=["green"] * 30)
wedge_z_sky = Donut(df, plot_height=circle_size, plot_width=circle_size, color=["green"] * 30)

wedge_b_sky.toolbar_location = None
wedge_r_sky.toolbar_location = None
wedge_z_sky.toolbar_location = None

pre_proc = widgetbox(Div(text="<b>Pre Processing:</b>"))
layout_1 = row(wedge_b, wedge_r, wedge_z)
group_1 = column(pre_proc, layout_1)
spec_proc = widgetbox(Div(text="<b>Spectra Extraction:</b>"))
layout_2 = row(wedge_b_spectra, wedge_r_spectra, wedge_z_spectra)
group_2 = column(spec_proc, layout_2)

fiber_proc = widgetbox(Div(text="<b>Fiber Flattening:</b>"))
layout_3 = row(wedge_b_fiber, wedge_r_fiber, wedge_z_fiber)
group_3 = column(fiber_proc, layout_3)

sky_proc = widgetbox(Div(text="<b>Sky Subtraction:</b>"))
layout_4 = row(wedge_b_sky, wedge_r_sky, wedge_z_sky)
group_4 = column(sky_proc, layout_4)

curdoc().add_root(row(group_1, group_2))
curdoc().add_root(row(group_3, group_4))

@count()
def update(t):
    barsRight = list()

    for num in range(30):
        barsRight.append(0)

    proc_finished = False

    global PROCESS

    process = get_last_process()

    if process:
        process = process.pop()

        if PROCESS.get("id") != process.get("id"):
            proc_finished = True

        PROCESS = process
        exp_id = PROCESS.get("exposure")
        plot.title.text = "Exposure ID: %i" % exp_id

    for cam in cameras:
        if cam[:5] != 'stage':

            cameralog = None
            log = str()

            try:
                for item in PROCESS.get("jobs", list()):
                    if cam == item.get("camera"):
                        cameralog = os.path.join(desi_spectro_redux, item.get('logname'))
                        break
                if cameralog:
                    arq = open(cameralog, 'r')
                    log = arq.readlines()

            except Exception as e:
                logger.warn(e)

            if cam[:1] == 'z':
                barsRight[int(cam[1:])] = len(log)
            if cam[:1] == 'r':
                barsRight[int(cam[1:]) - 20] = len(log)
            if cam[:1] == 'b':
                barsRight[int(cam[1:]) - 10] = len(log)

            # AF: This is not working properly

            #for line in log[::-1]:
            #    if 'Pipeline completed' in line:
            #        cameras['stage' + cam].text = 'Pipeline completed'
            #        break
            #    elif 'SkySub_QL' in line:
            #        cameras['stage' + cam].text = 'Sky Subtraction'
            #        break
            #    elif 'BoxcarExtract' in line:
            #        cameras['stage' + cam].text = 'Boxcar Extraction'
            #        break
            #    elif 'Preproc' in line:
            #        cameras['stage' + cam].text = 'Preprocessing'
            #        break
            #    elif 'Initialize' in line:
            #        cameras['stage' + cam].text = 'Initializing'
            #        break

    new_datat = dict(y=bars, right=barsRight, height=barsHeight, color=listColor)
    sourceBar.stream(new_datat, 30)

curdoc().add_periodic_callback(update, 300)
