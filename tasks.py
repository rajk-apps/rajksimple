import toml
from invoke import task
import io
import os
import importlib

from invoke_commands.docs import build_docs

pytom = toml.load("pyproject.toml")
package_name = pytom["project"]["name"]
author_name = " - ".join(pytom["project"]["authors"])

doc_dir_name = "docs"
doc_notebooks_dir = "notebooks"

mymodule = importlib.import_module(package_name)


@task
def lint(c):
    c.run("black {}".format(package_name))
    c.run("flake8 {}".format(package_name))


@task
def clean(c, docs=False, build=False, bytecode=False, test=False, sonar=False, all=False):
    patterns = []
    if docs or all:
        patterns.append("docs")
    if build or all:
        patterns += ["build", "{}.egg-info".format(package_name)]
    if bytecode or all:
        patterns.append("**/*.pyc")
    if sonar or all:
        patterns += [
            "{}/.sonar".format(package_name),
            "{}/.scannerwork".format(package_name),
            "{}/sonar-project.properties".format(package_name),
        ]
    if test or all:
        patterns += [
            ".pytest_cache",
            ".coverage",
            "**/.coverage",
            "htmlcov",
            "**/coverage.xml",
        ]

    for pattern in patterns:
        c.run("rm -rf {}".format(pattern))


@task
def build(c, docs=False):

    c.run("python setup.py build")
    if docs:
        c.run("sphinx-build docs docs/_build")


@task
def test(c, option="", html=False, xml=False):

    comm = "python -m pytest --cov={}".format(package_name)
    if option:
        comm += " --{}".format(option)
    if html:
        comm += " --cov-report=html"
    elif xml:
        comm += " --cov-report=xml:{}/coverage.xml".format(package_name)

    c.run(comm)


@task
def new_release(c):

    version = mymodule.__version__

    f = io.StringIO()
    c.run("git branch", out_stream=f)
    branch = f.getvalue().strip()
    f.close()

    if branch.endswith("master"):
        tag_version = "v{}".format(version)
        f2 = io.StringIO()
        c.run("git tag", out_stream=f2)
        tags = f2.getvalue().split()
        print(tags)
        if tag_version not in tags:
            with open("docs_config/current_release.rst") as fp:
                notes = fp.read()
            # TODO: remove this file, moce to rlease_notes, and add to the end of main.rst
            c.run("git tag -a {} -m {}".format(tag_version, notes))
            c.run("python setup.py sdist")
            c.run("twine check dist/*")
            c.run("twine upload dist/*{}.tar.gz".format(version))
        else:
            print("{} version already tagged".format(tag_version))
    else:
        print("only master branch can be tagged")


@task
def sonarqube(c):
    c.run("docker run -d --name sonarqube -p 9000:9000 -p 9092:9092 sonarqube")


@task
def sonar_scanner(c):

    with open(os.path.join(package_name, "sonar-project.properties"), "w") as fp:
        fp.write(
            "sonar.projectKey={}\n"
            "sonar.python.coverage.reportPaths=coverage.xml\n"
            "sonar.scm.disabled=true".format(package_name)
        )

    c.run(
        "docker run -e SONAR_HOST_URL={} "
        '--user="$(id -u):$(id -g)" '
        '-t -v "{}/{}:/usr/src" sonarsource/sonar-scanner-cli'.format(
            "http://172.17.0.2:9000", os.getcwd(), package_name
        )
    )


@task
def kill_sonar(c):
    c.run("docker kill sonarqube")
    c.run("docker container rm sonarqube")
