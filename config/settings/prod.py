from .base import *

DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOST")
DATABASES = {"default": env.db()}
