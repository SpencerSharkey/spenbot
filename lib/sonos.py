import soco

from soco import SoCo

def get_devices(interface_addr=None):
    return soco.discovery.discover(timeout=5, interface_addr=interface_addr)