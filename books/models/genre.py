from django.db import models
from common.models import BaseModel
from common.constants import MAX_GENRE_NAME_LENGTH


class Genre(BaseModel):
    name = models.CharField(max_length=MAX_GENRE_NAME_LENGTH, unique=True)
    description = models.TextField(blank=True, default="")

    class Meta:
        db_table = "genres"
        ordering = ["name"]

    def __str__(self):
        return self.name
