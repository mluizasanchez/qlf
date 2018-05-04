from qlf_models import QLFModels
from multiprocessing import Process, Event, Value
import configparser
import os
import datetime
from log import get_logger
from qlf_pipeline import QLFProcess
from clients import get_exposure_generator

qlf_root = os.getenv('QLF_ROOT')
cfg = configparser.ConfigParser()

cfg.read('%s/framework/config/qlf.cfg' % qlf_root)
logfile = cfg.get("main", "logfile")
loglevel = cfg.get("main", "loglevel")

logger = get_logger("main_logger", logfile, loglevel)


class Monitoring(Process):

    def __init__(self):
        super().__init__()
        self.processing = None
        self.exit = Event()
        self.allowed_delay = 20.0

        self.generator = get_exposure_generator()

        self.db_last_exposure = QLFModels().get_last_exposure()
        self.ics_last_exposure = {}

        self.process_id = Value('i', 0)

    def run(self):
        """ """
        while not self.exit.is_set():

            exposure = self.generator.last_exposure()

            if not exposure:
                logger.info('No exposure')
                continue

            if exposure.get('expid') == self.ics_last_exposure.get('expid', None):
                # logger Loop only to debug
                logger.debug('Loop')
                continue

            self.ics_last_exposure = exposure

            logger.info('Exposure ID {} was obtained'.format(exposure.get('expid')))

            if self.db_last_exposure.exposure_id == int(exposure.get('expid')):
                logger.info('Exposure ID {} has already been ingested.'.format(str(exposure.get('expid'))))
                continue

            # records exposure in database
            self.db_last_exposure = QLFModels().insert_exposure(
                exposure.get('expid'),
                exposure.get('night'),
                exposure.get('telra'),
                exposure.get('teldec'),
                exposure.get('tile'),
                exposure.get('dateobs'),
                exposure.get('flavor'),
                exposure.get('exptime')
            )

            if self.processing and self.processing.is_alive():
                logger.info('Exposure ID {} was not processed as there is active processing.'.format(
                    str(exposure.get('expid'))
                ))
                continue

            delay = datetime.datetime.utcnow() - exposure.get('time')
            delay = delay.total_seconds()

            if delay > self.allowed_delay:
                logger.info('The delay in the acquisition of the exposure went from {} seconds'.format(
                    str(self.allowed_delay)
                ))
                continue

            self.processing = QLFProcess(exposure)
            self.processing.start()

        logger.info("Bye!")


if __name__ == "__main__":
    print('Start Monitoring...')
    monitor = Monitoring()
    monitor.start()
