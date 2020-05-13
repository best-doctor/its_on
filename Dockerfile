FROM python:3.8.2

LABEL maintainer="i.perepelytsyn@bestdoctor.ru"

ARG USER_NAME=its_on
ARG UID=999
ARG APP_PATH=/its_on
ARG LOGS_PATH=/var/log/its_on

RUN useradd --uid=${UID} --no-log-init -r ${USER_NAME}
RUN mkdir -p ${APP_PATH} ${LOGS_PATH}
WORKDIR ${APP_PATH}
COPY ./requirements.txt ${APP_PATH}
RUN pip install --no-cache-dir -r requirements.txt
COPY . ${APP_PATH}
RUN chown -R ${USER_NAME}:${USER_NAME} ${APP_PATH} ${LOGS_PATH}
USER ${USER_NAME}
VOLUME ["${LOGS_PATH}", "/srv/www/its_on"]
EXPOSE 8081
ENTRYPOINT ["./entrypoint.sh"]
CMD ["run"]
