from datetime import datetime
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

def path_subdir(*d):
    return "%s/%s" % (env.path, "/".join(d))

def add_path_subdir(*d):
    run("mkdir -p %s" % path_subdir(*d))
    return path_subdir(*d)
    
@needs_host
@runs_once
def setup():
    '''
    Create all the required directories used by a deployment
    '''
    require("path")
    
    def is_missing_path_subdir(d):
        return not exists(path_subdir(d))
        
    created = map(add_path_subdir,
                  filter(is_missing_path_subdir, ["releases", "shared"]))
    if not created: print "All requirements seem to be met!"

@needs_host
def deploy(release=None):
    '''
    Deploy the current snapshot
    '''
    setup()
    build_release(release)
    send_release(release)
    unpack_release(release)
    activate_release(release)
    clean_release(release)
    

@runs_once
def build_release(release=None):
    '''
    Build a release on the local side
    '''
    env.last_release = release or ("fab.release.%s" % (datetime.utcnow().strftime("%Y_%m_%d_%H-%M-%S")))
    tgz = "/tmp/%s.tgz" % env.last_release
    local("tar czf %s ." % tgz, capture=False)

@needs_host
def send_release(release=None):
    if not release:
        require("last_release", provided_by=["build_release"])
        release = env.last_release
    put("/tmp/%s.tgz" % release, "/tmp/%s.tgz" % release)
    env.last_sent_release = release
    clean_release(release)

@needs_host
def unpack_release(release=None):
    setup() #Assure we have somewhere to unpack
    if not release:
        require("last_sent_release", provided_by=["send_release"])
        release = env.pop('last_sent_release')
    add_path_subdir("releases", release)
    with cd(path_subdir("releases", release)):
        run("tar zxf /tmp/%s.tgz" % release)
        clean_remote_release(release)
    env.last_remote_release = release


def clean_release(release=None):
    if not release:
        require("last_release", provided_by=["build_release"])
        release = env.pop('last_release')
    
    with settings(warn_only=True):
        with hide("warnings"): local("rm /tmp/%s.tgz" % release)

@needs_host
def clean_remote_release(release=None):
    if not release:
        require("last_sent_release", provided_by=["send_release"])
        release = env.pop('last_sent_release')
    with hide("warnings"): run("rm /tmp/%s.tgz" % release)

@needs_host
def activate_release(release=None):
    '''
    Activate the last, or the given release
    '''
    if not release:
        require("last_remote_release", provided_by=["send_release"])
        release = env.last_remote_release

    with cd(env.path):
        run("rm -f current_stage")
        run("ln -s releases/%s current_stage" % release)
        run("mv -T current_stage current")
    with cd(path_subdir("shared")):
        run("echo -n %s > current.txt" % release)
activate = activate_release

@needs_host
def available_releases():
    with hide("everything"): r = run("ls -c1 %s" % path_subdir("releases"))
    return r.split("\n")

@needs_host
def current_release():
    with hide("everything"): r = run("cat %s" % path_subdir("shared", "current.txt"))
    return r

@needs_host
def rollback(n=1):
    '''
    Rollback to the previous deployment
    '''
    current = current_release()
    available =  available_releases()
    previous = available[available.index(current) + 1:]
    if previous:
        previous = previous[0]
        activate_release(previous)
    else: abort("No previous release available!")
