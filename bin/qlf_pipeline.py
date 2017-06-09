import os
import sys
import logging
import subprocess
import datetime
import configparser
from multiprocessing import Manager
from threading import Thread

from qlf_models import (
    insert_process, insert_job,
    update_job, update_process
)

# Project main directory
qlf_root = os.getenv('QLF_ROOT')
cfg = configparser.ConfigParser()

try:
    cfg.read('%s/qlf/config/qlf.cfg' % qlf_root)
    scratch = cfg.get('namespace', 'scratch')
except Exception as error:
    print(error)
    print("Error reading  %s/qlf/config/qlf.cfg" % qlf_root)
    sys.exit(1)

logger = logging.getLogger(__name__)


class QLFProcess(object):
    """ Class responsible for managing Quick Look pipeline process. """

    def __init__(self, data):
        self.pipeline_name = 'Quick Look'
        self.data = data

    def start_process(self):
        """ Start pipeline. """

        logger.info('Started %s ...' % self.pipeline_name)
        logger.info('Night: %s' % self.data.get('night'))
        logger.info('Exposure: %s' % str(self.data.get('expid')))

        self.data['start'] = datetime.datetime.now().replace(microsecond=0)

        # create process in database and obtain the process id
        process = insert_process(
            self.data.get('expid'),
            self.data.get('night'),
            self.data.get('start'),
            self.pipeline_name
        )

        self.data['process_id'] = process.id
        self.data['status'] = process.status

        # TODO: ingest configuration file used, this should be done by process
        # insert_config(process.id)

        logger.info('Process ID: %i' % process.id)
        logger.info('Starting...')

        output_dir = os.path.join(
            'exposures',
            self.data.get('night'),
            self.data.get('zfill')
        )

        output_full_dir = os.path.join(scratch, output_dir)

        # Make sure output dir is created
        if not os.path.isdir(output_full_dir):
            os.makedirs(output_full_dir)

        logger.info('Output dir: %s' % output_dir)

        self.data['output_dir'] = output_dir

    def finish_process(self):
        """ Finish pipeline. """

        self.data['end'] = datetime.datetime.now().replace(microsecond=0)

        self.data['duration'] = str(self.data.get('end') - self.data.get('start'))

        logger.info("Process with expID {} completed in {}.".format(
            self.data.get('expid'),
            self.data.get('duration')
        ))

        update_process(
            process_id=self.data.get('process_id'),
            end=self.data.get('end'),
            process_dir=self.data.get('output_dir'),
            status=self.data.get('status')
        )


class Jobs(QLFProcess):

    def __init__(self, data):
        super().__init__(data)

    def start_jobs(self):
        """ Distributes the cameras for parallel processing. """

        procs = list()
        return_cameras = Manager().list()

        for camera in self.data.get('cameras'):
            camera['start'] = datetime.datetime.now().replace(
                microsecond=0
            )

            logname = os.path.join(
                self.data.get('output_dir'),
                "run-%s.log" % camera.get('name')
            )

            camera['logname'] = logname

            logger.info('Output log for camera %s: %s' % (
                camera.get('name'), camera.get('logname')
            ))

            job = insert_job(
                process_id=self.data.get('process_id'),
                camera=camera.get('name'),
                start=camera.get('start'),
                logname=camera.get('logname')
            )

            camera['job_id'] = job.id

            args = (
                self.data.get('night'),
                self.data.get('expid'),
                self.data.get('data_dir'),
                self.data.get('output_dir'),
                camera,
                return_cameras,
            )

            proc = Thread(target=self.start_parallel_job, args=args)
            proc.start()
            procs.append(proc)

        for proc in procs:
            proc.join()

        self.data['cameras'] = return_cameras

        logger.info('Begin ingestion of results...')
        start_ingestion = datetime.datetime.now().replace(microsecond=0)

        # TODO: refactor?
        camera_failed = 0

        for camera in self.data.get('cameras'):
            output_path = os.path.join(
                scratch,
                self.data.get('output_dir'),
                'ql-*-%s-%s.yaml' % (
                    camera.get('name'),
                    self.data.get('zfill')
                )
            )

            update_job(
                job_id=camera.get('job_id'),
                end=camera.get('end'),
                status=camera.get('status'),
                output_path=output_path
            )

            if not camera.get('status') == 0:
                camera_failed += 1

        status = 0

        if camera_failed > 0:
            status = 1

        self.data['status'] = status

        duration_ingestion = str(
            datetime.datetime.now().replace(microsecond=0) - start_ingestion
        )

        logger.info("Results ingestion complete in %s." % duration_ingestion)

    @staticmethod
    def start_parallel_job(night, expid, datadir, outputdir, camera, return_cameras):
        """ Execute QL Pipeline by camera """

        cmd = (
            'desi_quicklook -n {night} -c {camera} -e {exposure} '
            '-f dark --psfboot {psfboot} --fiberflat {fiberflat} '
            '--rawdata_dir {data_dir} --specprod_dir {scratch} '
            '--save qlconfig-{camera}-{exposure}'
        ).format(**{
            'night': night,
            'exposure': str(expid),
            'camera': camera.get('name'),
            'psfboot': camera.get('psfboot'),
            'fiberflat': camera.get('fiberflat'),
            'data_dir': datadir,
            'scratch': scratch
        })

        logger.info(
            "Started job %i on exposure %s and camera %s ... " % (
            camera.get('job_id'),
            expid,
            camera.get('name')
        ))

        log = open(os.path.join(
            scratch,
            camera.get('logname')
        ), 'wb')

        cwd = os.path.join(
            scratch,
            outputdir
        )

        with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              shell=True, cwd=cwd) as process:
            for line in iter(process.stdout.readline, bytes()):
                log.write(line)
                log.flush()

            for line in iter(process.stderr.readline, bytes()):
                log.write(line)
                log.flush()

            retcode = process.wait()

        log.close()

        camera['end'] = datetime.datetime.now().replace(microsecond=0)
        camera['status'] = 0
        camera['duration'] = str(
            camera.get('end') - camera.get('start')
        )

        if retcode < 0:
            camera['status'] = 1
            msg = (
                "Job on exposure %s and camera %s "
                "finished with code %i in %s"
            ) % (
                camera.get('name'),
                expid,
                retcode,
                camera.get('duration')
            )

            logger.error(msg)

        logger.info("Finished job %i in %s" % (
            camera.get('job_id'),
            camera.get('duration')
        ))

        return_cameras.append(camera)


class JobsParallelIngestion(QLFProcess):
    """ """

    def __init__(self, data):
        super().__init__(data)

    def start_jobs(self):
        """ Distributes the cameras for parallel processing. """

        procs = list()
        return_cameras = Manager().list()

        for camera in self.data.get('cameras'):
            args = (
                self.data.get('process_id'),
                self.data.get('night'),
                self.data.get('expid'),
                self.data.get('data_dir'),
                self.data.get('output_dir'),
                self.data.get('zfill'),
                camera,
                return_cameras,
            )

            proc = Thread(target=self.start_parallel_job, args=args)
            proc.start()
            procs.append(proc)

        for proc in procs:
            proc.join()

        self.data['cameras'] = return_cameras

        # TODO: refactor?
        camera_failed = 0

        for camera in self.data.get('cameras'):
            logger.info("Finished ingestion of pipeline results.")

            if not camera.get('status') == 0:
                camera_failed += 1

        status = 0

        if camera_failed > 0:
            status = 1

        self.data['status'] = status

    @staticmethod
    def start_parallel_job(process_id, night, expid, datadir, outputdir, zfill, camera, return_cameras):
        """ Execute QL Pipeline by camera """

        camera['start'] = datetime.datetime.now().replace(
            microsecond=0
        )

        camera['logname'] = os.path.join(
            outputdir,
            "run-%s.log" % camera.get('name')
        )

        log_path = os.path.join(scratch, camera.get('logname'))

        logger.info('Output log for camera %s: %s' % (
            camera.get('name'), log_path
        ))

        job = insert_job(
            process_id=process_id,
            camera=camera.get('name'),
            start=camera.get('start'),
            logname=camera.get('logname')
        )

        camera['job_id'] = job.id

        cmd = (
            'desi_quicklook -n {night} -c {camera} -e {exposure} '
            '-f dark --psfboot {psfboot} --fiberflat {fiberflat} '
            '--rawdata_dir {data_dir} --specprod_dir {scratch} '
            '--save qlconfig-{camera}-{exposure}'
        ).format(**{
            'night': night,
            'exposure': str(expid),
            'camera': camera.get('name'),
            'psfboot': camera.get('psfboot'),
            'fiberflat': camera.get('fiberflat'),
            'data_dir': datadir,
            'scratch': scratch
        })

        logger.info(
            "Started job %i on exposure %s and camera %s ... " % (
            camera.get('job_id'),
            expid,
            camera.get('name')
        ))

        log = open(log_path, 'wb')

        cwd = os.path.join(
            scratch,
            outputdir
        )

        with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              shell=True, cwd=cwd) as process:
            for line in iter(process.stdout.readline, bytes()):
                log.write(line)
                log.flush()

            for line in iter(process.stderr.readline, bytes()):
                log.write(line)
                log.flush()

            retcode = process.wait()

        log.close()

        camera['end'] = datetime.datetime.now().replace(microsecond=0)
        camera['status'] = 0
        camera['duration'] = str(
            camera.get('end') - camera.get('start')
        )

        if retcode > 0:
            camera['status'] = 1
            msg = (
                "Job on exposure %s and camera %s "
                "finished with code %i in %s"
            ) % (
                camera.get('name'),
                expid,
                retcode,
                camera.get('duration')
            )

            logger.error(msg)

        logger.info("Finished job %i in %s" % (
            camera.get('job_id'),
            camera.get('duration')
        ))

        output_path = os.path.join(
            scratch,
            outputdir,
            'ql-*-%s-%s.yaml' % (
                camera.get('name'),
                zfill
            )
        )

        update_job(
            job_id=camera.get('job_id'),
            end=camera.get('end'),
            status=camera.get('status'),
            output_path=output_path
        )

        return_cameras.append(camera)


if __name__ == "__main__":
    exposure = {
        'night': '20170428',
        'expid': '3',
        'zfill': '00000003',
        'data_dir': '/home/singulani/raw_data',
        'cameras': [
          {
            'name': 'r8',
            'psfboot': '/home/singulani/raw_data/20170428/psfboot-r8.fits',
            'fiberflat': '/home/singulani/raw_data/20170428/fiberflat-r8-00000003.fits'
          },
          {
            'name': 'r9',
            'psfboot': '/home/singulani/raw_data/20170428/psfboot-r9.fits',
            'fiberflat': '/home/singulani/raw_data/20170428/fiberflat-r9-00000003.fits'
          }
        ]
    }

    qlp = JobsParallelIngestion(exposure)
    qlp.start_process()
    qlp.start_jobs()
    qlp.finish_process()
