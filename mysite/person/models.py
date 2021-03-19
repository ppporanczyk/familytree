from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from mysite import settings
from tree.models import FamilyTree


# YEARS = [tuple([x, x]) for x in range(timezone.now().year,1902,-1)]


class Person(models.Model):
    class Sex(models.IntegerChoices):
        MALE = 0, _('Male')
        FEMALE = 1, _('Female')

    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    maiden_name = models.CharField(max_length=30, null=True, blank=True)
    sex = models.IntegerField(choices=Sex.choices, default=0)
    date_of_birth = models.DateField(default=None, null=True, blank=True)
    date_of_death = models.DateField(default=None, null=True, blank=True)
    datetime_person = models.DateTimeField(default=timezone.now)
    family_tree = models.ForeignKey(FamilyTree, on_delete=models.CASCADE, related_name='family_tree')

    def __str__(self):
        if self.maiden_name is not None:
            return "%s %s (%s) %s" % (self.first_name, self.last_name, self.maiden_name, self.get_age())
        return "%s %s %s" % (self.first_name, self.last_name, self.get_age())

    def get_absolute_url(self):
        return reverse('person-detail', kwargs={'pk': self.family_tree_id, 'pk_per': self.id})

    def get_age(self):
        living = self.date_of_birth.__format__('%d/%m/%Y') if self.date_of_birth is not None else '-'
        death = self.date_of_death.__format__('%d/%m/%Y') if self.date_of_death is not None else '-'
        if living == '-' and death == '-':
            return ''
        return f'[{living} - {death}]'


class Relation(models.Model):
    class FamilyRelation(models.TextChoices):
        ANCESTOR = 'A', _('Ancestor')
        PARTNER = 'P', _('Partner')
        DESCENDANT = 'D', _('Descendant')

    source_person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='source_person')
    related_person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='related_person')
    datetime_relation = models.DateTimeField(default=timezone.now)
    family_relation = models.CharField(max_length=10, choices=FamilyRelation.choices, default='D')
    date_beginning = models.DateField(default=None, null=True, blank=True)
    date_end = models.DateField(default=None, null=True, blank=True)

    def get_absolute_url(self):
        return reverse('tree-detail', kwargs={'pk': Person.objects.get(id=self.source_person_id).family_tree_id})
