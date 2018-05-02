from qlf_models import QLFModels
from qlf_interface import QLFInterface
from exposure_generator import ExposureGenerator
import Pyro4
import configparser
import sys
import os
from log import get_logger
from procutil import kill_proc_tree
from scalar_metrics import LoadMetrics

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

    process = False

    def start(self):
        if self.process and self.process.is_alive():
            self.process.set_exit(False)
            logger.info("Monitor is already initialized (pid: %i)." % self.process.pid)
        else:
            self.process = QLFInterface()
            self.process.start()
            logger.info("Starting pid %i..." % self.process.pid)

    def stop(self):
        if self.process and self.process.is_alive():
            self.process.set_exit()
            logger.info("Stop pid %i" % self.process.pid)

            process_id = self.process.get_current_process_id()
            pid = self.process.pid

            kill_proc_tree(pid, include_parent=False)

            if process_id:
                model = QLFModels()
                model.delete_process(process_id)
        else:
            logger.info("Monitor is not initialized.")

    def reset(self):
        self.stop()
        model = QLFModels()
        model.delete_all_cameras()
        model.delete_all_processes()
        model.delete_all_exposures()
        logger.info('Deleted all processes and exposures')

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

    def qa_tests(self):
        model = QLFModels()
        for camera in model.get_cameras():
            try:
                exposure = model.get_last_exposure()
                lm = LoadMetrics(camera.camera, exposure.exposure_id, exposure.night)
                lm.save_qa_tests()
            except:
                logger.error('qa_tests error camera %s' % (camera.camera))


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


def main():
    try:
        interface = os.environ.get('QLF_INTERFACE', 'qlf.interface')
        emulator = os.environ.get('EXPOSURE_EMULATOR', 'exposure.emulator')
        host = os.environ.get('PYROSERVER', 'localhost')
        port = int(os.environ.get('PYROPORT', '56005'))
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
