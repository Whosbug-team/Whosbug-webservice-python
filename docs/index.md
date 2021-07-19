# whosbug-web

[![Build Status](https://travis-ci.org/f1ed/whosbug-web.svg?branch=master)](https://travis-ci.org/f1ed/whosbug-web)
[![Built with](https://img.shields.io/badge/Built_with-Cookiecutter_Django_Rest-F7B633.svg)](https://github.com/agconti/cookiecutter-django-rest)

WhosBug Check out the project's [documentation](https://f1ed.coding.net/p/whosbug-uestc/d/whosbug-webservice/git).

# Prerequisites

- [Docker](https://docs.docker.com/docker-for-mac/install/)

# Initialize the project

Start the dev server for local development:

```bash
docker-compose up -d
```

Create a superuser to login to the admin:

```bash
docker-compose run --rm web python ./manage.py createsuperuser
```

# API doc

visit `127.0.0.1:8081/swagger/`
