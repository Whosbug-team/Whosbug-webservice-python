FROM python:3.8
ENV PYTHONUNBUFFERED 1

# Allows docker to cache installed dependencies between builds
COPY requirements.txt requirements.txt
RUN pip -V
RUN pip install -r requirements.txt

# Adds our application code to the image
COPY . code
WORKDIR code

EXPOSE 8081

# Run the production server
# CMD bash -c "python wait_for_postgres.py && python manage.py makemigrations && python manage.py migrate && python manage.py runserver 0.0.0.0:8080"
CMD bash -c "python wait_for_postgres.py && python manage.py runserver 0.0.0.0:8081 && python manage.py collectstatic"
