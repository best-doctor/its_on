FROM python:3.7

MAINTAINER Igor Perepilitsyn <i.perepelytsyn@bestdoctor.ru>

ARG USER_NAME=its_on
ARG UID=999

RUN useradd --uid=$UID --no-log-init -r $USER_NAME
RUN mkdir -p /var/www/its_on /var/log/gunicorn
WORKDIR /var/www/its_on
COPY ./requirements.txt /var/www/its_on
RUN pip install --no-cache-dir -r requirements.txt
COPY . /var/www/its_on
RUN chown -R $USER_NAME /var/www/its_on /var/log/gunicorn
USER $USER_NAME
VOLUME ["/var/log/gunicorn", "/var/www/its_on/its_on/static"]
EXPOSE 8081
ENTRYPOINT ["./entrypoint.sh"]
