from invoke import task

from .vars import package_name, boilerplate_branch


@task
def setup_dev(c):
    c.run("APP_NAME={} " .format(package_name) +
          "DJANGO_PROJECT={} ".format("dev_project") +  # FIXME: is this dry?
          "HOST_IP={} ".format("0.0.0.0") +
          "APP_PORT={} ".format(6969) +
          "docker-compose up --build")  # -- build

@task
def clean(c):
    c.run("rm -{}/migrations/*".format(package_name))


@task
def update_boilerplate(c, drop=False):
    c.run("git fetch boilerplate")  # TODO: this knows the name of the remote
    c.run("git merge boilerplate/{} --no-edit".format(boilerplate_branch))
    if drop:
        c.run("rm -rf mydjangoapp")
        c.run("rm -rf mypackage")
