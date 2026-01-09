from .base import *

DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")
DATABASES = {"default": env.db()}
