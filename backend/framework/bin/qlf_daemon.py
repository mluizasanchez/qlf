from dos_monitor import DOSmonitor
from qlf_models import QLFModels
from time import sleep
from multiprocessing import Process, Event, Value
import Pyro4
import configparser
import sys
import os
import errno
from socket import error as socket_error
from log import get_logger
from procutil import kill_proc_tree
from qlf_pipeline import Jobs as QLFPipeline
from scalar_metrics import LoadMetrics

qlf_root = os.getenv('QLF_ROOT')
cfg = configparser.ConfigParser()

cfg.read('%s/framework/config/qlf.cfg' % qlf_root)
logfile = cfg.get("main", "logfile")
logpipeline = cfg.get("main", "logpipeline")
loglevel = cfg.get("main", "loglevel")

logger = get_logger("icslogger", logfile, loglevel)
mainlogger = get_logger("main_logger", "main_daemon.log", loglevel)


class QLFAutoRun(Process):

    def __init__(self):
        super().__init__()
        self.running = Event()
        self.exit = Event()

        self.dos_monitor = DOSmonitor()

        self.last_night = None
        self.process_id = Value('i', 0)

        exposure = QLFModels().get_last_exposure()

        if exposure:
            self.last_night = exposure.night

    def run(self):

        while not self.get_exit():
            night = self.dos_monitor.get_last_night()

            if night == self.last_night:
                sleep(10)
                continue

            exposures = self.dos_monitor.get_exposures_by_night(night)

            if not exposures:
                sleep(10)
                continue

            for exposure in exposures:
                if self.get_exit():
                    break

                logger.info('Found expID {}'.format(exposure.get('expid')))
                self.running.set()

                try:
                    ql = QLFPipeline(exposure)
                    self.process_id.value = ql.start_process()
                    ql.start_jobs()
                    ql.finish_process()
                except socket_error as serr:
                    if serr.errno != errno.ECONNREFUSED:
                        mainlogger.exception('Daemon Error')
                        raise

            self.running.clear()
            self.process_id.value = 0
            self.last_night = night

    def get_current_process_id(self):
        """ """
        return self.process_id.value

    def set_exit(self, value=True):
        """ """
        if value:
            self.exit.set()
        else:
            self.exit.clear()

    def get_exit(self):
        """ """
        return self.exit.is_set()

# TODO: refactor QLFManualRun
class QLFManualRun(Process):

    def __init__(self, exposures):
        super().__init__()
        self.running = Event()
        self.exit = Event()
        self.current_exposure = None

        # TODO: improve the method for obtaining exposures
        dos_monitor = DOSmonitor()
        night = dos_monitor.get_last_night()
        self.exposures = list()

        for exposure in exposures:
            self.exposures.append(dos_monitor.get_exposure(night, exposure))

    def run(self):
        self.exit.clear()

        for exposure in self.exposures:
            if self.exit.is_set():
                mainlogger.info('Execution stopped')
                break

            self.running.set()
            self.current_exposure = exposure
            ql = QLFPipeline(self.current_exposure)
            mainlogger.info('Executing expid {}...'.format(exposure.get('expid')))
            ql.start_process()
            ql.start_jobs()
            ql.finish_process()

        self.running.clear()
        self.current_exposure = None

        logger.info("Bye!")
        self.shutdown()

    def clear(self):
        self.exit.clear()

    def shutdown(self):
        self.exit.set()

@Pyro4.expose
@Pyro4.behavior(instance_mode="single")
class QLFAutomatic(object):
    def __init__(self):
        self.process = False

    def start(self):
        if self.process and self.process.is_alive():
            self.process.set_exit(False)
            mainlogger.info("Monitor is already initialized (pid: %i)." % self.process.pid)
        else:
            self.process = QLFAutoRun()
            self.process.start()
            mainlogger.info("Starting pid %i..." % self.process.pid)

    def stop(self):
        if self.process and self.process.is_alive():
            self.process.set_exit()
            mainlogger.info("Stop pid %i" % self.process.pid)

            process_id = self.process.get_current_process_id()
            pid = self.process.pid

            kill_proc_tree(pid, include_parent=False)

            if process_id:
                model = QLFModels()
                model.delete_process(process_id)
        else:
            mainlogger.info("Monitor is not initialized.")

    def reset(self):
        self.stop()

        with open(logfile, 'r+') as ics:
            ics.truncate()

        with open(logpipeline, 'r+') as pipeline:
            pipeline.truncate()

        model = QLFModels()
        model.delete_all_cameras()
        model.delete_all_processes()
        model.delete_all_exposures()

    def get_status(self):
        status = False

        if self.process and not self.process.get_exit():
            status = True

        return status

    def is_running(self):
        running = False

        if self.process and self.process.running.is_set():
            running = True

        return running

    def qa_tests(self, process_id):
        qa_tests = list()
        for job in QLFModels().get_jobs_by_process_id(process_id):
            try:
                process = job.process
                exposure = process.exposure
                lm = LoadMetrics(job.camera_id, process.exposure_id, exposure.night)
                qa_tests.append({job.camera_id: lm.load_qa_tests()})
            except:
                mainlogger.error('qa_tests error camera %s' % job.camera)
        return qa_tests

# TODO: refactor QLFManual
@Pyro4.expose
@Pyro4.behavior(instance_mode="single")
class QLFManual(object):

    def __init__(self):
        self.process = False
        self.exposures = list()

    def start(self, exposures):
        if self.process and self.process.is_alive():
            self.process.clear()
            mainlogger.info("Monitor is already initialized (pid: %i)." % self.process.pid)
        else:
            self.process = QLFManualRun(exposures)
            self.process.start()
            mainlogger.info("Starting pid %i..." % self.process.pid)

    def stop(self):
        if self.process and self.process.is_alive():
            mainlogger.info("Stop pid %i" % self.process.pid)
            self.process.shutdown()
        else:
            mainlogger.info("Monitor is not initialized.")

    def get_status(self):
        status = False

        if self.process and not self.process.exit.is_set():
            status = True

        mainlogger.info("QLF Manual status: {}".format(status))
        return status

    def get_current_run(self):
        return self.process.current_exposure


def main():
    try:
        auto_mode = os.environ.get('QLF_DAEMON_NS', 'qlf.daemon')
        manual_mode = os.environ.get('QLF_MANUAL_NS', 'qlf.manual')
        host = os.environ.get('QLF_DAEMON_HOST', 'localhost')
        port = int(os.environ.get('QLF_DAEMON_PORT', '56005'))
    except Exception as err:
        logger.error(err)
        sys.exit(1)

    Pyro4.Daemon.serveSimple(
        {QLFAutomatic: auto_mode, QLFManual: manual_mode},
        host=host,
        port=port,
        ns=False
    )


if __name__ == "__main__":
    main()
