FROM python:2.7.15

WORKDIR /app/fathom-training-server/
RUN groupadd --gid 10001 app && useradd -g app --uid 10001 --shell /usr/sbin/nologin app
RUN chown app:app /app/
RUN mkdir /home/app/
RUN chown app:app /home/app/

# Update operating system
RUN apt-get update
# Install Firefox mainly for the deps
RUN apt-get install -y firefox-esr
RUN pip install -U 'pip>=8' && \
    pip install pipenv

USER app

# Install Python requirements
COPY ./Pipfile /app/fathom-training-server/Pipfile
COPY ./Pipfile.lock /app/fathom-training-server/Pipfile.lock
RUN pipenv install

# Fetch a copy of Firefox
RUN pipenv run mozdownload --version latest --destination /home/app/firefox.tar.bz2
RUN pipenv run mozinstall --destination /home/app /home/app/firefox.tar.bz2
ENV FIREFOX_BIN=/home/app/firefox/firefox

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

COPY . /app/fathom-training-server/
