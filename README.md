### to setup dev env:

- install dev dependencies:

`pip install -r requirements-init.txt -r requirements.txt`

- lauch dev container:

`inv django.setup-dev`

> app should be available at http://localhost:6969/rajksimple

> admin page is available at http://0.0.0.0:6969/admin with user fing///fing

- tear down:

`inv django.clean`

### try build locally:

- ...