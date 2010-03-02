from fabric.api import *
from fabric.network import needs_host

@needs_host
def setup():
    '''
    Create all the required directories used by a deployment
    '''
    require("path")
    pass


def build_release():
    pass

@needs_host
def send_release(name=None):
    pass

@needs_host
def activate_release(release=None):
    pass
