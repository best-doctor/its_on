from enum import StrEnum


class Environment(StrEnum):
    dev = 'dev'
    test = 'test'
    staging = 'staging'
    prod = 'production'
