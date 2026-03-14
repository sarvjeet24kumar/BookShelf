from .base import *

DEBUG = env("DEBUG")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["*"])
DATABASES = {"default": env.db()}
