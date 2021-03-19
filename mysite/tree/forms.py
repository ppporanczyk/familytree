from django import forms
from django.forms import Form, CharField

from .models import FamilyTree


class FamilyTreeForm(forms.ModelForm):
    class Meta:
        model = FamilyTree
        fields = ['name_tree', 'description', 'access']

    def save(self):
        family_tree = super(FamilyTreeForm, self).save(commit=False)
        # FamilyTree.objects.filter(id=family_tree.id).update(datetime_tree=timezone.now())
        family_tree.save()
        return family_tree

    def clean_name_tree(self, **kwargs):
        name_tree = self.cleaned_data['name_tree']
        if FamilyTree.objects.filter(name_tree=name_tree).exclude(id=self.instance.id).exists():
            raise forms.ValidationError("There is already a tree with that name.")
        return name_tree


class FilterForm(Form):
    FILTER_CHOICES = (
        ('first_name', 'first name'),
        ('last_name', 'last name'),
    )
    search = CharField(required=False)
