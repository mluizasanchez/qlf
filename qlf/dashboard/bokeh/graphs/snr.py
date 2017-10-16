import os

from bokeh.io import curdoc
from bokeh.models import ColumnDataSource, HoverTool, TapTool, OpenURL
from bokeh.models.widgets import Select, Slider
from bokeh.layouts import row, column, widgetbox, gridplot

from dashboard.bokeh.helper import get_data, get_exposure_ids, \
    init_xy_plot, get_url_args, get_arms_and_spectrographs

import numpy as np

class SNR:
    def get_snr(selected_exposure, arm_select, spectrograph_select):
        data_model = {
            'x': [],
            'y': [],
            'fiber_id': [],
            'ra': [],
            'dec': []
        }

        data_fit = {'xfit': [], 'yfit': []}

        elg = ColumnDataSource(data=data_model.copy())
        lrg = ColumnDataSource(data=data_model.copy())
        qso = ColumnDataSource(data=data_model.copy())
        star = ColumnDataSource(data=data_model.copy())

        elg_fit = ColumnDataSource(data = data_fit.copy() )
        lrg_fit = ColumnDataSource(data = data_fit.copy() )
        qso_fit = ColumnDataSource(data = data_fit.copy() )
        star_fit = ColumnDataSource(data = data_fit.copy() )

        params = [
            'ELG_SNR_MAG', 'ELG_FIBERID',
            'LRG_SNR_MAG', 'LRG_FIBERID',
            'QSO_SNR_MAG', 'QSO_FIBERID',
            'STAR_SNR_MAG', 'STAR_FIBERID',
            'RA', 'DEC'
        ]

        params_fit = ['ELG_FITRESULTS', 'LRG_FITRESULTS', 'QSO_FITRESULTS', 'STAR_FITRESULTS']

        def update(arm, spectrograph, exposure_id):
            exp_zfill = str(exposure_id).zfill(8)

            # get the data
            qa_snr = 'ql-snr-{}-{}.yaml'.format(arm + spectrograph, exp_zfill)

            data = get_data(qa_snr, params)

            data2 = get_data(qa_snr, params_fit)
            if not data2.empty:
                a_elg, b_elg,   c_elg  = data2['ELG_FITRESULTS'][0]
                a_lrg, b_lrg,   c_lrg  = data2['LRG_FITRESULTS'][0]
                a_qso, b_qso,   c_qso  = data2['QSO_FITRESULTS'][0]
                a_star, b_star, c_star = data2['STAR_FITRESULTS'][0]
            

            if not data.empty:
                # drop rows that have ELG_FIBERID null
                elg_data = data[data.ELG_FIBERID.notnull()]

                # create the bokeh column data sources
                elg.data['x'] = elg_data.ELG_SNR_MAG[1]
                elg.data['y'] = elg_data.ELG_SNR_MAG[0]
                elg.data['fiber_id'] = elg_data.ELG_FIBERID.tolist()
                elg.data['ra'] = elg_data.RA.tolist()
                elg.data['dec'] = elg_data.DEC.tolist()

                fitx          = elg_data.ELG_SNR_MAG[1]
                fitx          = sorted(fitx)
                fity          = [ c_elg* x**2 + b_elg *x + a_elg for x in fitx] #PIPELINE FIT
                a,b,c        = np.polyfit(elg_data.ELG_SNR_MAG[1],elg_data.ELG_SNR_MAG[0],2) #numpy FIT
                fity          = [ a* x**2 + b*x + c for x in fitx]                           #numpy FIT
                print( '\n\n\nFits\t\na: {}, b: {}, c: {}'.format(a_elg, b_elg, c_elg) )
                print( 'Fits npy \na: {}, b: {}, c: {}'.format(c, b, a) )
                #print('\n\n\nfitx\n', len(fitx),'\n\n', len(fity) )
                elg_fit.data['xfit'] = fitx 
                elg_fit.data['yfit'] = fity 
                elg.stream(elg.data, 30)

                # drop rows that have ELG_FIBERID null
                lrg_data = data[data.LRG_FIBERID.notnull()]

                lrg.data['x'] = lrg_data.LRG_SNR_MAG[1]
                lrg.data['y'] = lrg_data.LRG_SNR_MAG[0]
                lrg.data['fiber_id'] = lrg_data.LRG_FIBERID.dropna().tolist()
                lrg.data['ra'] = lrg_data.RA.dropna().tolist()
                lrg.data['dec'] = lrg_data.DEC.dropna().tolist()
                fitx                 = lrg_data.LRG_SNR_MAG[1]
                lrg_fit.data['xfit'] = sorted(fitx)
                lrg_fit.data['yfit'] =  [ c_lrg* x**2 + b_lrg *x + a_lrg for x in sorted(fitx)]  
                a,b,c                 = np.polyfit(lrg_data.LRG_SNR_MAG[1], lrg_data.LRG_SNR_MAG[0],2) #numpy FIT
                lrg_fit.data['xfit']  = np.linspace(np.min(fitx), np.max(fitx), 200)                   #numpy FIT
                lrg_fit.data['yfit']  = [ a* x**2 + b*x + c for x in lrg_fit.data['xfit']]             #numpy FIT
            
                lrg.stream(lrg.data, 30)

                # drop rows that have QSO_FIBERID null
                qso_data = data[data.QSO_FIBERID.notnull()]

                qso.data['x'] = qso_data.QSO_SNR_MAG[1]
                qso.data['y'] = qso_data.QSO_SNR_MAG[0]
                qso.data['fiber_id'] = qso_data.QSO_FIBERID.dropna().tolist()
                qso.data['ra'] = qso_data.RA.dropna().tolist()
                qso.data['dec'] = qso_data.DEC.dropna().tolist()
                fitx                 = qso_data.QSO_SNR_MAG[1]
                qso_fit.data['xfit'] = sorted(fitx)
                qso_fit.data['yfit'] =  [ c_qso* x**2 + b_qso *x + a_qso for x in sorted(fitx)]
                a,b,c                 = np.polyfit(qso_data.QSO_SNR_MAG[1], qso_data.QSO_SNR_MAG[0],2) #numpy FIT
                qso_fit.data['xfit']  = np.linspace(np.min(fitx), np.max(fitx), 200)                   #numpy FIT
                qso_fit.data['yfit']  = [ a* x**2 + b*x + c for x in qso_fit.data['xfit']]             #numpy FIT


                qso.stream(qso.data, 30)

                # drop rows that have STAR_FIBERID null
                star_data = data[data.STAR_FIBERID.notnull()]

                star.data['x'] = star_data.STAR_SNR_MAG[1]
                star.data['y'] = star_data.STAR_SNR_MAG[0]
                star.data['fiber_id'] = star_data.STAR_FIBERID.dropna().tolist()
                star.data['ra'] = star_data.RA.dropna().tolist()
                star.data['dec'] = star_data.DEC.dropna().tolist()
                fitx                  = star_data.STAR_SNR_MAG[1]
                star_fit.data['xfit'] = sorted(fitx)
                star_fit.data['yfit'] =  [ c_star* x**2 + b_star *x + a_star for x in sorted(fitx)]
                a,b,c                 = np.polyfit(star_data.STAR_SNR_MAG[1], star_data.STAR_SNR_MAG[0],2) #numpy FIT
                star_fit.data['xfit']  = np.linspace(np.min(fitx), np.max(fitx), 200)                   #numpy FIT
                star_fit.data['yfit']  = [ a* x**2 + b*x + c for x in star_fit.data['xfit']]             #numpy FIT

                star.stream(star.data, 30)


        # configure bokeh widgets
        exposure = get_exposure_ids()

        if not exposure:
            exposure.append(int(selected_exposure))

        exposure = sorted(exposure)

        exp_slider = Slider(
            start=int(exposure[0]), end=int(exposure[-1]),
            value=int(selected_exposure), step=1,
            title="Exposure ID")

        # cameras = get_arms_and_spectrographs()

        # if not cameras["spectrographs"]:
        #     cameras["spectrographs"].append(selected_spectrograph)

        # if not cameras["arms"]:
        #     cameras["arms"].append(selected_arm)

        # # we can filter by spectrograph
        # spectrograph_select = Select(
        #     title="Spectrograph:",
        #     value=selected_spectrograph,
        #     options=cameras["spectrographs"],
        #     width=100)

        # # and arm
        # arm_select = Select(
        #     title="Arm:",
        #     options=cameras['arms'],
        #     value=selected_arm,
        #     width=100)

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
                    <span style="font-size: 12px; font-weight: bold; color: #303030;">SNR: </span>
                    <span style="font-size: 13px; color: #515151;">@y</span>
                </div>
                <div>
                    <span style="font-size: 12px; font-weight: bold; color: #303030;">DECAM_R: </span>
                    <span style="font-size: 13px; color: #515151;">@x</span>
                </div>
                <div>
                    <span style="font-size: 12px; font-weight: bold; color: #303030;">Fiber ID: </span>
                    <span style="font-size: 13px; color: #515151;">@fiber_id</span>
                </div>
                <div>
                    <span style="font-size: 12px; font-weight: bold; color: #303030;">RA: </span>
                    <span style="font-size: 13px; color: #515151;">@ra</span>
                </div>
                <div>
                    <span style="font-size: 12px; font-weight: bold; color: #303030;">Dec: </span>
                    <span style="font-size: 13px; color: #515151">@dec</span>
                </div>
            </div>
        """

        url = "http://legacysurvey.org/viewer?ra=@ra&dec=@dec&zoom=16&layer=decals-dr3"


        from bokeh.plotting import Figure

        hover = HoverTool(tooltips=html_tooltip, names=["data"]) #names=['data'] in order to not show hover in line
        elg_plot = init_xy_plot(hover=hover)
        elg_plot.circle(x='x', y='y', source=elg, name = "data",color="blue", size=5)
        elg_plot.xaxis.axis_label = "DECAM_R"
        elg_plot.yaxis.axis_label = "SNR"
        elg_plot.title.text = "ELG"
        elg_plot.line(x='xfit', y='yfit', source = elg_fit)

        taptool = elg_plot.select(type=TapTool)
        taptool.callback = OpenURL(url=url)

        hover = HoverTool(tooltips=html_tooltip, names=["data"])
        lrg_plot = init_xy_plot(hover=hover)
        lrg_plot.circle(x='x', y='y', source=lrg, name = "data", color="red", size=5)
        lrg_plot.xaxis.axis_label = "DECAM_R"
        lrg_plot.yaxis.axis_label = "SNR"
        lrg_plot.title.text = "LRG"
        lrg_plot.line(x='xfit', y='yfit', source = lrg_fit)

        taptool = lrg_plot.select(type=TapTool)
        taptool.callback = OpenURL(url=url)

        hover = HoverTool(tooltips=html_tooltip, names=["data"])
        qso_plot = init_xy_plot(hover=hover)
        qso_plot.circle(x='x', y='y', source=qso, name = "data", color="green", size=5)
        qso_plot.xaxis.axis_label = "DECAM_R"
        qso_plot.yaxis.axis_label = "SNR"
        qso_plot.title.text = "QSO"
        qso_plot.line(x='xfit', y='yfit', source = qso_fit)

        taptool = qso_plot.select(type=TapTool)
        taptool.callback = OpenURL(url=url)

        hover = HoverTool(tooltips=html_tooltip, names=["data"])
        star_plot = init_xy_plot(hover=hover)
        star_plot.circle(x='x', y='y', source=star, name = "data", color="black", size=5)
        star_plot.xaxis.axis_label = "DECAM_R"
        star_plot.yaxis.axis_label = "SNR"
        star_plot.title.text = "STAR"
        star_plot.line(x='xfit', y='yfit', source = star_fit)

        taptool = star_plot.select(type=TapTool)
        taptool.callback = OpenURL(url=url)

        update(arm_select.value, spectrograph_select.value, selected_exposure)

        plot = gridplot([[elg_plot, lrg_plot], [qso_plot, star_plot]])

        # and create the final layout
        # layout = column(widgetbox(exp_slider, width=130, responsive=True),
        #                 row(widgetbox(arm_select, width=130),
        #                     widgetbox(spectrograph_select, width=130)),
        #                 plot, responsive=True)

        layout = column(plot, responsive=True)

        return layout