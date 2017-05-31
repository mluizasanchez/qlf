from dos_monitor import DOSmonitor
from qlf_pipeline import QLFPipeline
from qlf_models import QLFModels
from time import sleep
from multiprocessing import Process, Event
# from dashboard.bokeh.helper import get_last_exposures_by_night

import Pyro4
import configparser
import sys
import os
import logging

qlf_root = os.getenv('QLF_ROOT')
cfg = configparser.ConfigParser()

try:
    cfg.read('%s/qlf/config/qlf.cfg' % qlf_root)
    logfile = cfg.get("main", "logfile")
    loglevel = cfg.get("main", "loglevel")
except Exception as error:
    print(error)
    print("Error reading  %s/qlf/config/qlf.cfg" % qlf_root)
    sys.exit(1)

logging.basicConfig(
    format="%(asctime)s [%(levelname)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename=logfile,
    level=eval("logging.%s" % loglevel)
)

logger = logging.getLogger(__name__)

class QLFRun(Process):

    def __init__(self):
        Process.__init__(self)
        self.exit = Event()
        self.dos_monitor = DOSmonitor()
        self.last_night = str()
        self.running = Event()

        # TODO: get last night from db (improve)
        models = QLFModels()
        exposure = models.get_last_exposure()

        if exposure:
            self.last_night = exposure.night

    def run(self):
        self.clear()
        while not self.exit.is_set():
            night = self.dos_monitor.get_last_night()

            if night == self.last_night:
                logger.info("The night %s has already been processed" % night)
                sleep(5)
                continue

            exposures = self.dos_monitor.get_exposures_by_night(night)

            for exposure in exposures:
                if self.exit.is_set():
                    logger.info('Execution stopped')
                    break

                self.running.set()
                ql = QLFPipeline(exposure)
                ql.start_process()
                logger.info('Executing expid %s...' % exposure.get('expid'))

            self.running.clear()
            self.last_night = night

        logger.info("Bye!")

    def clear(self):
        self.exit.clear()

    def shutdown(self):
        self.exit.set()


@Pyro4.expose
@Pyro4.behavior(instance_mode="single")
class QLFDaemon(object):
    def __init__(self):
        self.process = False

    def start(self):
        if self.process and self.process.is_alive():
            self.process.clear()
            logger.info("Monitor is already initialized (pid: %i)." % self.process.pid)
        else:
            self.process = QLFRun()
            self.process.start()
            logger.info("Starting pid %i..." % self.process.pid)

    def stop(self):
        if self.process and self.process.is_alive():
            logger.info("Stop pid %i" % self.process.pid)
            self.process.shutdown()
        else:
            logger.info("Monitor is not initialized.")

    def restart(self):
        self.stop()
        logger.info("Restarting...")
        sleep(5)
        self.start()

    def get_status(self):
        status = False

        if self.process and not self.process.exit.is_set():
            status = True

        logger.info("QLF Daemon status: {}".format(status))
        return status

    def is_running(self):
        running = False

        if self.process and self.process.running.is_set():
            running = True

        logger.info("Running? {}".format(running))
        return running

def main():
    try:
        nameserver = os.environ.get('QLF_DAEMON_NS', 'qlf.daemon')
        host = os.environ.get('QLF_DAEMON_HOST', 'localhost')
        port = int(os.environ.get('QLF_DAEMON_PORT', '56005'))
    except Exception as err:
        logger.error(err)
        sys.exit(1)

    Pyro4.Daemon.serveSimple(
        {QLFDaemon: nameserver},
        host=host,
        port=port,
        ns=False
    )

if __name__ == "__main__":
    main()
