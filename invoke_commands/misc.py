from invoke import task
from .vars import package_name, boilerplate_branch


@task
def lint(c):
    c.run("black {}".format(package_name))
    c.run("flake8 {}".format(package_name))


@task
def update_boilerplate(c):
    c.run("git fetch boilerplate")  # TODO: this knows the name of the remote
    c.run("git merge boilerplate/{} --no-edit".format(boilerplate_branch))


@task
def notebook(c):
    from jupyter_client.kernelspec import KernelSpecManager
    from notebook.notebookapp import main

    class MyManager(KernelSpecManager):

        def get_kernel_spec(self, kernel_name):
            init_resp = super().get_kernel_spec(kernel_name)
            init_resp.argv = [*init_resp.argv, """--IPKernelApp.exec_lines=['import sys', 'sys.path.append("..")']"""]
            return init_resp

    main(kernel_spec_manager_class=MyManager)
