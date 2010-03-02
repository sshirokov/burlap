from fabric.api import *
from fabric.network import needs_host
from fabric.contrib.files import exists

def with_roles(*roles_then_funcs):
    def role_or_function(acc, i):
        if callable(i): acc[1].append(i)
        else: acc[0].append(i)
        return acc
    def bind_roles(roles_list, func):
        func.roles = roles_list
    required_roles, functions = reduce(role_or_function, roles_then_funcs, ([], []))
    map(lambda func: bind_roles(required_roles, func), functions)

def path_subdir(d):
    return "%s/%s" % (env.path, d)
    
@needs_host
def setup():
    '''
    Create all the required directories used by a deployment
    '''
    require("path")
    
    def add_path_subdir(d):
        run("mkdir -p %s" % path_subdir(d))
        return path_subdir(d)
    
    def is_missing_path_subdir(d):
        return not exists(path_subdir(d))
        
    created = map(add_path_subdir,
                  filter(is_missing_path_subdir, ["releases", "shared"]))
    if not created: print "All requirements seem to be met!"

def build_release():
    pass

@needs_host
def send_release(name=None):
    pass

@needs_host
def activate_release(release=None):
    pass
