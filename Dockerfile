FROM python:3.8-slim AS builder

ARG APP_DIRECTORY=/its_on
ARG USER_NAME=its_on
ARG UID=800
ARG GID=800

RUN groupadd --gid=${GID} -r ${USER_NAME} && useradd --uid=${UID} --gid=${GID} --no-log-init -r ${USER_NAME}
RUN mkdir -p $APP_DIRECTORY
RUN python -m venv /opt/venv
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev
RUN pip install wheel==0.37.0 --no-cache-dir
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1
COPY ./requirements.txt /
RUN pip install -r /requirements.txt --no-cache-dir


FROM python:3.8-slim AS app

ARG APP_DIRECTORY=/its_on
ARG USER_NAME=its_on
ARG UID=800
ARG GID=800

RUN groupadd --gid=${GID} -r ${USER_NAME} && useradd --uid=${UID} --gid=${GID} --no-log-init -r ${USER_NAME}
RUN apt-get update && apt-get install -y --no-install-recommends \
    && apt-get clean && apt-get autoremove -y && rm -rf /var/lib/apt/lists/* /var/cache/apt
COPY --from=builder /opt/venv /opt/venv
RUN chown -R ${UID}:${GID} /opt/venv
COPY . ${APP_DIRECTORY}
RUN chown -R ${UID}:${GID} ${APP_DIRECTORY}
WORKDIR $APP_DIRECTORY
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
USER $USER_NAME
VOLUME ["/srv/www/its_on"]
EXPOSE 8081
ENTRYPOINT ["./entrypoint.sh"]
CMD ["run"]
