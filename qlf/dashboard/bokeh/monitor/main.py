from bokeh.plotting import figure, output_file, curdoc
from bokeh.models import ColumnDataSource, LabelSet, Label
from bokeh.driving import count
from dashboard.bokeh.helper import get_last_process
from bokeh.models import CustomJS, Div
from bokeh.layouts import column, row
import configparser
import os
import logging


import Pyro4
QLF_DAEMON_URL='PYRO:{}@{}:{}'.format(
    os.environ.get('QLF_DAEMON_NS', 'qlf.daemon'),
    os.environ.get('QLF_DAEMON_HOST', 'localhost'),
    str(os.environ.get('QLF_DAEMON_PORT', 56005))
)
uri = QLF_DAEMON_URL
qlf = Pyro4.Proxy(uri)

logger = logging.getLogger(__name__)
INDICE = -1
qlf_root = os.getenv('QLF_ROOT')
cfg = configparser.ConfigParser()

try:
    cfg.read('%s/qlf/config/qlf.cfg' % qlf_root)
    scratch = cfg.get('namespace', 'scratch')
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
        cameras['stagez' + str(num)] = Label(x=50, y=num - .3, text='Initializing ', background_fill_color='white',
                                             background_fill_alpha=0.7)
        label_name.append('z' + str(num))
    elif 'r9' not in label_name:
        cameras['r' + str(num - 10)] = Label(x=-6.5, y=num - .3, text='r' + str(num - 10))
        cameras['stager' + str(num - 10)] = Label(x=50, y=num - .3, text='Initializing ',
                                                  background_fill_color='white', background_fill_alpha=0.7)
        label_name.append('r' + str(num - 10))
    elif 'b9' not in label_name:
        cameras['b' + str(num - 20)] = Label(x=-6.5, y=num - .3, text='b' + str(num - 20))
        cameras['stageg' + str(num - 20)] = Label(x=50, y=num - .3, text='Initializing ', render_mode='css',
                                                  background_fill_color='white', background_fill_alpha=0.7)
        label_name.append('b' + str(num - 20))

plot = figure(height=900, x_range=(-9, 120), tools="tap")

for cam in cameras:
    plot.add_layout(cameras[cam])

# AF: Move plot style configuration to theme.yaml
plot.xaxis.visible = False
plot.yaxis.visible = False

sourceBar = ColumnDataSource(dict(y=[1], right=[1], height=[1], color=['#0000FF']))

plot.hbar(y='y', right='right', height='height', color='color', source=sourceBar, name='hbar')


def callback(attr, old, new):
    global INDICE
    div.text = ''
    INDICE = new['1d']['indices'][0]


taptool = plot.select(dict(name='hbar'))

hbar = taptool[0].data_source
hbar.on_change('selected', callback)
div = Div(text='', height=340, width=700)

curdoc().add_root(column(plot, div))


@count()
def update(t):
    barsRight = list()
    global INDICE
    if len(str(INDICE)) == 1:
        INDICE = 'z' + str(INDICE)[0]
    if str(INDICE)[0] == '1':
        INDICE = 'r' + str(INDICE)[1]
    if str(INDICE)[0] == '2':
        INDICE = 'b' + str(INDICE)[1]

    for num in range(30):
        barsRight.append(50)

    proc_finished = False

    global PROCESS

    process = get_last_process()

    if process:
        process = process.pop()

        if PROCESS.get("id") != process.get("id"):
            proc_finished = True

        PROCESS = process
        exp_id = PROCESS.get("exposure")
        status = qlf.get_status()
        if status == True:
            plot.title.text = "Processing Exposure ID: %i" % exp_id
        elif status == False:
            plot.title.text = "Resuming Exposure ID: %i" % exp_id
        else:
            plot.title.text = "Exposure ID: %i" % exp_id

    # logger.info("Process: %s" % PROCESS)

    # AF: loop over cameras
    for cam in cameras:
        if cam[:5] != 'stage':
            cameralog = None
            log = str()

            try:
                for item in PROCESS.get("jobs", list()):
                    if cam == item.get("camera"):
                        cameralog = os.path.join(scratch, item.get('logname'))
                        break
                if cameralog:
                    arq = open(cameralog, 'r')
                    log = arq.readlines()

            except Exception as e:
                logger.warn(e)
            if cam == INDICE:
                if 'Pipeline completed' not in div.text and cameralog:
                    div.text = '<h2>Ouput log for \
                        camera %s:</h2><br><div style="max-height: 300px; overflow: auto;"> ' % cam
                    for line in log:
                        div.text += line + '<br>'
                    div.text += '</div><br>'
            if cam[:1] == 'z':
                barsRight[int(cam[1:])] = len(log)
            if cam[:1] == 'r':
                barsRight[int(cam[1:]) - 20] = len(log)
            if cam[:1] == 'b':
                barsRight[int(cam[1:]) - 10] = len(log)

            # AF: currrent line
            for line in log[::-1]:
                if 'Pipeline completed' in line:
                    cameras['stage' + cam].text = 'Pipeline completed'
                    break
                elif 'SkySub_QL' in line:
                    cameras['stage' + cam].text = 'Sky Subtraction'
                    break
                elif 'BoxcarExtract' in line:
                    cameras['stage' + cam].text = 'Boxcar Extraction'
                    break
                elif 'Preproc' in line:
                    cameras['stage' + cam].text = 'Preprocessing'
                    break
                elif 'Initialize' in line:
                    cameras['stage' + cam].text = 'Initializing'
                    break

    new_datat = dict(y=bars, right=barsRight, height=barsHeight, color=listColor)
    sourceBar.stream(new_datat, 30)


curdoc().add_periodic_callback(update, 300)
