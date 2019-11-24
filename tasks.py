import toml
from invoke import task
import glob
import io
import os
import importlib

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
def build_docs(c):

    clean(c, docs=True)

    c.run(
        'sphinx-quickstart {} -p {} -a "{}" -q --ext-autodoc'.format(
            doc_dir_name, package_name, author_name
        )
    )

    doc_notebooks = sorted(glob.glob("{}/*.ipynb".format(doc_notebooks_dir)))
    c.run(
        "jupyter nbconvert --to rst {} --output-dir={}/notebooks".format(
            " ".join(doc_notebooks), doc_dir_name
        )
    )
    toc_nbs = [
        "   notebooks/{}".format(np.split("/")[-1].split(".")[0])
        for np in doc_notebooks
    ]

    index_rst = """
Welcome to {}'s documentation!
=====================================================================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   autosumm
{}
   {}

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
""".format(
        package_name, "\n".join(toc_nbs), "release_notes/main"
    )

    autosumm_rst = """

API
===

.. automodapi:: {}

""".format(
        package_name
    )

    with open(os.path.join(doc_dir_name, "index.rst"), "w") as fp:
        fp.write(index_rst)

    with open(os.path.join(doc_dir_name, "autosumm.rst"), "w") as fp:
        fp.write(autosumm_rst)

    c.run("cp -r docs_config/* docs/")
    c.run("pip install -r docs/requirements.txt")
    c.run("sphinx-build docs docs/_build")


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
