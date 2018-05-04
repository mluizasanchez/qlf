from monitoring import Monitoring
from exposure_generator import ExposureGenerator
from qlf_models import QLFModels
import Pyro4
import configparser
import sys
import os
from log import get_logger
from procutil import kill_proc_tree
from scalar_metrics import LoadMetrics
from clients import get_exposure_generator

qlf_root = os.getenv('QLF_ROOT')
cfg = configparser.ConfigParser()

if not qlf_root:
    raise ValueError('QLF_ROOT not define.')

qlf_conf = os.path.join(qlf_root, "framework/config/qlf.cfg")

cfg.read(qlf_conf)
logfile = cfg.get("main", "logfile")
loglevel = cfg.get("main", "loglevel")

logger = get_logger("main_logger", logfile, loglevel)
gen_logger = get_logger(__name__, os.path.join(qlf_root, "exposure_generator.log"))


@Pyro4.expose
@Pyro4.behavior(instance_mode="single")
class QLFInterface(object):

    monitoring = False

    # TODO: is provisional while we do not have the ICS.
    generator = get_exposure_generator()

    def start(self):
        if self.monitoring and self.monitoring.is_alive():
            self.monitoring.set_exit(False)
            logger.info("Monitor is already initialized (pid: %i)." % self.monitoring.pid)
        else:
            self.monitoring = Monitoring()
            self.monitoring.start()
            logger.info("Starting pid %i..." % self.monitoring.pid)

        self.generator.start()

    def stop(self):
        if self.monitoring and self.monitoring.is_alive():
            self.monitoring.set_exit()
            logger.info("Stop pid %i" % self.monitoring.pid)

            self.monitoring.get_current_process_id()
            pid = self.monitoring.pid

            kill_proc_tree(pid, include_parent=False)
        else:
            logger.info("Monitor is not initialized.")

        self.generator.stop()

    def get_status(self):
        status = False

        if self.monitoring and not self.monitoring.get_exit():
            status = True

        return status

    def is_running(self):
        running = False

        if self.monitoring and self.monitoring.running.is_set():
            running = True

        return running

    @staticmethod
    def qa_tests():
        model = QLFModels()
        for camera in model.get_cameras():
            try:
                exposure = model.get_last_exposure()
                lm = LoadMetrics(camera.camera, exposure.exposure_id, exposure.night)
                lm.save_qa_tests()
            except:
                logger.error('qa_tests error camera %s' % camera.camera)


@Pyro4.expose
@Pyro4.behavior(instance_mode="single")
class ExposureEmulator(object):

    generator = False

    def start(self):
        if self.generator and self.generator.is_alive():
            gen_logger.info("Exposure generator is already initialized.")
        else:
            self.generator = ExposureGenerator()
            self.generator.start()

    def stop(self):
        if self.generator and self.generator.is_alive():
            gen_logger.info("Stop pid %i" % self.generator.pid)
            self.generator.terminate()
        else:
            gen_logger.info("Exposure generator is not initialized.")

    def last_exposure(self):
        if self.generator and self.generator.is_alive():
            return dict(self.generator.get_last_exposure())
        else:
            gen_logger.info("Exposure generator is not initialized.")
            return dict()

    # def get_exposure_summary(self, date_range=None, expid_range=None, require_data_written=True):
    #   # TODO
    #   return
    #
    # def get_exposure_files(self, expid, dest=None, file_class=['desi', 'fibermap'], overwrite=True):
    #   # TODO
    #   return


def main():
    try:
        interface = os.environ.get('QLF_DAEMON_NS', 'qlf.daemon')
        emulator = os.environ.get('EXPOSURE_EMULATOR', 'exposure.emulator')
        host = os.environ.get('QLF_DAEMON_HOST', 'localhost')
        port = int(os.environ.get('QLF_DAEMON_PORT', '56005'))
    except Exception as err:
        logger.error(err)
        sys.exit(1)

    Pyro4.Daemon.serveSimple(
        {QLFInterface: interface, ExposureEmulator: emulator},
        host=host,
        port=port,
        ns=False
    )


if __name__ == "__main__":
    main()
