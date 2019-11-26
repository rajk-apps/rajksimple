

"""
GITHUB_CLIENT_ID=yourclientid GITHUB_CLIENT_SECRET=yourclientsecret docker-compose up --build

#!/usr/bin/env bash
PATH=/$DJANGO_PROJECT:$PATH
python $DJANGO_PROJECT/manage.py makemigrations
python $DJANGO_PROJECT/manage.py migrate
python $DJANGO_PROJECT/manage.py loaddata $INIT_DATA
jupyter contrib nbextensions install
#jupyter nbextension install /notebook_extension/
#jupyter nbextension enable notebook_extension/main
#cp /jupyter_extensions/jupyter_notebook_config.py /root/.jupyter/jupyter_notebook_config.py
jupyter-notebook --ip=0.0.0.0 --allow-root &
bash
"""