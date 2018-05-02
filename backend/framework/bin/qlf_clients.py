import logging
import Pyro4
import sys

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
sh = logging.StreamHandler(sys.stdout)
sh.setLevel(logging.DEBUG)
log.addHandler(sh)

name_servers = {'generator': 'PYRO:exposure.emulator@localhost:56005'}


def get_exposure_generator():
    """ """

    return Pyro4.Proxy(name_servers.get('generator'))
