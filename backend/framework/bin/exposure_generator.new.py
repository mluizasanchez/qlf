import astropy.io.fits
import configparser
import datetime
from log import get_logger
import os
import random
import re
import shutil
import sys
import time
import Pyro4
from multiprocessing import Process, Manager

qlf_root = os.getenv("QLF_ROOT")

if not qlf_root:
    raise ValueError('QLF_ROOT not define.')

log = get_logger(__name__, os.path.join(qlf_root, "exposure_generator.log"))
qlf_conf = os.path.join(qlf_root, "framework/config/qlf.cfg")


class ExposureGenerator(Process):

    def __init__(self):
        super().__init__()

        self.min_interval = 2
        self.max_interval = 5

        cfg = configparser.ConfigParser()

        try:
            cfg.read(qlf_conf)

            self.spectro_path = os.path.normpath(
                cfg.get("namespace", "desi_spectro_data"))
            self.spectro_redux = os.path.normpath(
                cfg.get("namespace", "desi_spectro_redux"))

            self.fiberflat_path = os.path.join(self.spectro_redux, "calib2d")
            self.psfboot_path = os.path.join(self.fiberflat_path, "psf")

            self.base_night = cfg.get("data", "night").split(",")[0]
            self.base_exposure = str(cfg.get("data", "exposures").split(",")[0]).zfill(8)
        except Exception as error:
            log.error(error)
            log.error("Error reading config file %s" % qlf_conf)
            sys.exit(1)

        arms = cfg.get('data', 'arms').split(',')
        spectrographs = cfg.get('data', 'spectrographs').split(',')

        self.__last_exposure = Manager().dict()
        self.cameras = list()

        for arm in arms:
            for spec in spectrographs:
                try:
                    self.cameras.append(arm + spec)
                except Exception as error:
                    log.error(error)

        self.__print_vars()

    def run(self):
        while True:
            log.info("Starting generation of new exposure...")
            last_exposure = self.generate_exposure()
            log.info(
                "Exposure id '%s' generated at '%s' as night '%s'."
                % (last_exposure['expid'], last_exposure['date-obs'], last_exposure['night'])
            )
            self.__last_exposure.update(last_exposure)
            rand = random.randint(self.min_interval, self.max_interval)
            log.info("Next generation in %s minutes..." % rand)
            time.sleep(rand*60)
            # time.sleep(60)

    def get_last_exposure(self):
        return Manager().dict(self.__last_exposure)

    def generate_exposure(self):
        gen_time = datetime.datetime.now()
        exp_id = self.__gen_new_expid()
        exp_id_zfill = str(exp_id).zfill(8)
        self.__gen_desi_file(exp_id_zfill, gen_time)
        self.__gen_fibermap_file(exp_id_zfill, gen_time)
        self.__gen_fiberflat_folder(gen_time)
        self.__gen_psfboot_folder(gen_time)

        exponame = "desi-{}.fits.fz".format(exp_id_zfill)
        night = self.__night_to_generate(gen_time)
        filepath = os.path.join(self.spectro_path, night, exponame)

        try:
            hdr = astropy.io.fits.getheader(filepath)
        except Exception as error:
            log.error("error to load fits file: %s" % error)
            return {}

        return {
            "expid": exp_id,
            "date-obs": self.__date_obs(gen_time),
            "night": night,
            "zfill": exp_id_zfill,
            "desi_spectro_data": self.spectro_path,
            "desi_spectro_redux": self.spectro_redux,
            "cameras": self.cameras,
            'telra': hdr.get('telra', None),
            'teldec': hdr.get('teldec', None),
            'tile': hdr.get('tileid', None),
            'flavor': hdr.get('flavor', None),
            'exptime': hdr.get('exptime', None)
        }

    def __gen_new_expid(self):
        last_id = self.__get_last_expid()

        return int(last_id) + 1

    def __get_last_expid(self):
        # spectro 'desi-X.fits.fz' is mandatory,
        # so should be fine to use it to detect the last exp_id

        last_night = self.__get_last_night()

        listdir = os.listdir(os.path.join(self.spectro_path, last_night))
        regex = re.compile("^desi-\d+.fits.fz$")
        last_exp_file = sorted(list(filter(regex.match, listdir)))[-1]

        return re.findall("^desi-(\d+).fits.fz$", last_exp_file)[0]

    def __get_last_night(self):
        listdir = os.listdir(self.spectro_path)
        regex = re.compile("^\d+$")
        regex_match = list(filter(regex.match, listdir))

        # last night can not be detected, because the 'demo' night
        # is dated on 2019, so it will be the last night until 2019 comes
        if len(regex_match) > 1 and regex_match.count("20190101"):
            regex_match.remove("20190101")

        return sorted(regex_match)[-1]

    def __gen_desi_file(self, exp_id, gen_time):
        src = os.path.join(self.spectro_path, self.base_night)
        dest = os.path.join(
            self.spectro_path, self.__night_to_generate(gen_time))
        self.__ensure_dir(dest)
        src_file = os.path.join(
            src, ("desi-{}.fits.fz".format(self.base_exposure)))
        dest_file = os.path.join(dest, ("desi-{}.fits.fz".format(exp_id)))
        shutil.copy(src_file, dest_file)
        self.__update_fitsfile_metadata(dest_file, exp_id, gen_time)

    def __update_fitsfile_metadata(self, exp_file, exp_id, gen_time):
        hdulist = astropy.io.fits.open(exp_file, mode="update")
        for hduid in range(0, len(hdulist)):
            if "EXPID" in hdulist[hduid].header:
                hdulist[hduid].header["EXPID"] = (
                    int(exp_id))
            if "DATE-OBS" in hdulist[hduid].header:
                hdulist[hduid].header["DATE-OBS"] = (
                    self.__date_obs(gen_time))
            if "NIGHT" in hdulist[hduid].header:
                hdulist[hduid].header["NIGHT"] = (
                    self.__night_to_generate(gen_time))
            if "ARCNIGHT" in hdulist[hduid].header:
                hdulist[hduid].header["ARCNIGHT"] = (
                    self.__night_to_generate(gen_time))
            if "FLANIGHT" in hdulist[hduid].header:
                hdulist[hduid].header["FLANIGHT"] = (
                    self.__night_to_generate(gen_time))
        hdulist.flush()
        hdulist.close()

    def __gen_fibermap_file(self, exp_id, gen_time):
        src = os.path.join(self.spectro_path, self.base_night)
        dest = os.path.join(
            self.spectro_path, self.__night_to_generate(gen_time))
        self.__ensure_dir(dest)
        src_file = os.path.join(
            src, ("fibermap-{}.fits".format(self.base_exposure)))
        dest_file = os.path.join(dest, ("fibermap-{}.fits".format(exp_id)))
        shutil.copy(src_file, dest_file)
        self.__update_fitsfile_metadata(dest_file, exp_id, gen_time)

    def __gen_fiberflat_folder(self, gen_time):
        src = os.path.join(self.fiberflat_path, self.base_night)
        dest = os.path.join(
            self.fiberflat_path, self.__night_to_generate(gen_time))

        self.__ensure_dir(dest)

        if not os.listdir(dest):
            for filename in os.listdir(src):
                if not filename.endswith(".fits"):
                    continue

                src_file = os.path.join(src, filename)
                dest_file = os.path.join(dest, filename)
                shutil.copy(src_file, dest_file)

    def __gen_psfboot_folder(self, gen_time):
        # it is fine to just copy the path
        src = os.path.join(self.psfboot_path, self.base_night)
        dest = os.path.join(
            self.psfboot_path, self.__night_to_generate(gen_time))

        if not os.path.exists(dest):
            shutil.copytree(src, dest)

    @staticmethod
    def __night_to_generate(gen_time):
        return (gen_time - datetime.timedelta(hours=12)).strftime("%Y%m%d")

    @staticmethod
    def __date_obs(gen_time):
        return gen_time.strftime("%Y-%m-%dT%H:%M:%S")

    @staticmethod
    def __ensure_dir(path):
        if not os.path.exists(path):
            os.makedirs(path)

    def __print_vars(self):
        log.info("min_interval:      {}".format(self.min_interval))
        log.info("max_interval:      {}".format(self.max_interval))
        log.info("spectro_path:      {}".format(self.spectro_path))
        log.info("fiberflat_path:    {}".format(self.fiberflat_path))
        log.info("psfboot_path:      {}".format(self.psfboot_path))
        log.info("base_night:        {}".format(self.base_night))
        log.info("base_exposure:     {}".format(self.base_exposure))
        log.info("cameras:           {}".format(",".join(self.cameras)))


# @Pyro4.expose
# @Pyro4.behavior(instance_mode="single")
# class ICSInterface(object):
#
#     generator = False
#
#     def start(self):
#         if self.generator and self.generator.is_alive():
#             log.info("Exposure generator is already initialized.")
#         else:
#             self.generator = ExposureGenerator()
#             self.generator.start()
#
#     def stop(self):
#         if self.generator and self.generator.is_alive():
#             log.info("Stop pid %i" % self.generator.pid)
#             self.generator.terminate()
#         else:
#             log.info("Exposure generator is not initialized.")
#
#     def last_exposure(self):
#         if self.generator and self.generator.is_alive():
#             return dict(self.generator.get_last_exposure())
#         else:
#             log.info("Exposure generator is not initialized.")
#             return dict()
#
#     def get_exposure_summary(self, date_range=None, expid_range=None, require_data_written=True):
#         # TODO
#         return
#
#     def get_exposure_files(self, expid, dest=None, file_class=['desi', 'fibermap'], overwrite=True):
#         # TODO
#         return
#
#
# def main():
#     try:
#         generator = 'exposure.generator'
#         host = 'localhost'
#         port = 56006
#     except Exception as err:
#         log.error(err)
#         sys.exit(1)
#
#     Pyro4.Daemon.serveSimple(
#         {ICSInterface: generator},
#         host=host,
#         port=port,
#         ns=False
#     )
#
#
# if __name__ == "__main__":
#     main()
