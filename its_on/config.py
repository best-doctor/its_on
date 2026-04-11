from dynaconf import Dynaconf

settings = Dynaconf(
    settings_files=['settings.yaml'],
    environments=True,
    envvar_prefix='DYNACONF',
    env_switcher='ENV_FOR_DYNACONF',
)
