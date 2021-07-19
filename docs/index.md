# whosbug-web

[![Build Status](https://travis-ci.org/f1ed/whosbug-web.svg?branch=master)](https://travis-ci.org/f1ed/whosbug-web)
[![Built with](https://img.shields.io/badge/Built_with-Cookiecutter_Django_Rest-F7B633.svg)](https://github.com/agconti/cookiecutter-django-rest)

WhosBug-A. Check out the project's [documentation](http://f1ed.github.io/whosbug-web/).

# Prerequisites

- [Docker](https://docs.docker.com/docker-for-mac/install/)

# Initialize the project

Start the dev server for local development:

```bash
docker-compose up
```

Create a superuser to login to the admin:

```bash
docker-compose run --rm web python ./manage.py createsuperuser
```
