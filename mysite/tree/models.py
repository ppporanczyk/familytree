from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.urls import reverse


class FamilyTree(models.Model):
    class Access(models.IntegerChoices):
        PUBLIC = 0, _('public')
        PRIVATE = 1, _('private')

    name_tree = models.CharField(max_length=30)
    description = models.TextField(null=True, blank=True, max_length=300)
    datetime_tree = models.DateTimeField(default=timezone.now)
    access = models.IntegerField(choices=Access.choices)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name_tree

    def save(self, *args, **kwargs):
        super(FamilyTree, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('tree-detail', kwargs={'pk': self.pk})
