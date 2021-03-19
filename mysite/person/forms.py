import datetime
from django import forms
from django.forms import CharField, Form
from tempus_dominus.widgets import DatePicker
from django.core.validators import MaxValueValidator
from mysite import settings
from .models import Person, Relation
from django.utils import timezone


class PersonForm(forms.ModelForm):
    date_of_birth = forms.DateField(required=False, widget=DatePicker())
    date_of_death = forms.DateField(required=False, widget=DatePicker())

    class Meta:
        model = Person
        fields = ['first_name', 'last_name', 'maiden_name', 'sex', 'date_of_birth', 'date_of_death']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date_of_birth'].label = "Date of birth (use 'year-month-day' format)"
        self.fields['date_of_death'].label = "Date of death (use 'year-month-day' format)"


    def save(self):
        person = super(PersonForm, self).save(commit=False)
        person.save()
        return person

    def clean(self):
        super(PersonForm, self).clean()
        person_birth = self.cleaned_data['date_of_birth']
        person_death = self.cleaned_data['date_of_death']
        if person_birth and person_birth > datetime.date.today():
            raise forms.ValidationError("You cannot kill a person from the future.")
        if person_death and person_death > datetime.date.today():
            raise forms.ValidationError("You cannot create a person from the future.")
        if person_birth and person_death and person_birth > person_death:
            raise forms.ValidationError("Date of birth cannot be after death.")


# -------------------------------------------------------------------------
# -------------------------relation----------------------------------------
# -------------------------------------------------------------------------


def number_of_parents(child):
    return len(Relation.objects.filter(related_person=child, family_relation='A'))


def check_age_of_parent(relation, person_s, person_r):
    if person_s.date_of_birth is not None and person_r.date_of_birth is not None:
        if relation == 'D' and person_s.date_of_birth < person_r.date_of_birth:
            return f'{person_s} (child) cannot be older than {person_r} (parent)'
        if relation == 'A' and person_r.date_of_birth < person_s.date_of_birth:
            return f'{person_r} (child) cannot be older than {person_s} (parent)'

    if person_s.date_of_birth is not None and person_r.date_of_death is not None:
        if relation == 'D' and person_s.date_of_birth > person_r.date_of_death:
            return f'{person_s} (child) was born, when {person_r} (parent) was dead'
    if person_r.date_of_birth is not None and person_s.date_of_death is not None:
        if person_r.date_of_birth > person_s.date_of_death:
            return f'{person_r} (parent)) was born, when {person_s} (child) was dead'
    return 0


def check_age_of_partner(person_s, person_r):
    if person_s.date_of_death is not None and person_r.date_of_birth is not None:
        if person_s.date_of_death < person_r.date_of_birth:
            return f'{person_s} passed away before the birth of {person_r}'
    elif person_r.date_of_death is not None and person_s.date_of_birth is not None:
        if person_r.date_of_death < person_s.date_of_birth:
            return f'{person_r} passed away before the birth of {person_s}'
    return 0


def check_another_relation_date(person_s, person_r, date_beg, date_end):
    person_1 = Relation.objects.filter(source_person=person_s, family_relation='P').exclude(related_person=person_r)
    if person_1 is not None:
        for rel in person_1:
            lover = Person.objects.get(id=rel.related_person_id)
            if date_beg is not None and date_end is not None:
                if rel.date_beginning is not None and rel.date_end is not None:
                    if date_beg < rel.date_end or date_end > rel.date_beginning:
                        return f'{person_s} was in another relation that time'
                elif rel.date_beginning is not None:
                    if date_end > rel.date_beginning:
                        return f'{person_s} was in another relation that time'
                elif rel.date_end is not None:
                    if date_beg < rel.date_end:
                        return f'{person_s} was in another relation that time'
            elif date_beg is not None:
                if rel.date_beginning is not None and rel.date_end is not None:
                    if date_beg < rel.date_end:
                        return f'{person_s} was in another relation that time'
                elif rel.date_end is not None:
                    if date_beg < rel.date_end:
                        return f'{person_s} was in another relation that time'
            if date_end is not None:
                if rel.date_beginning is not None and rel.date_end is not None:
                    if date_end > rel.date_beginning:
                        return f'{person_s} was in another relation that time'
                elif rel.date_beginning is not None:
                    if date_end > rel.date_beginning:
                        return f'{person_s} was in another relation that time'
    person_2 = Relation.objects.filter(related_person=person_s, family_relation='P').exclude(source_person=person_r)
    if person_2 is not None:
        for rel in person_2:
            lover = Person.objects.get(id=rel.related_person_id)
            if date_beg is not None and date_end is not None:
                if rel.date_beginning is not None and rel.date_end is not None:
                    if date_beg < rel.date_end or date_end > rel.date_beginning:
                        return f'{person_s} was in another relation that time'
                elif rel.date_beginning is not None:
                    if date_end > rel.date_beginning:
                        return f'{person_s} was in another relation that time'
                elif rel.date_end is not None:
                    if date_beg < rel.date_end:
                        return f'{person_s} was in another relation that time'
            elif date_beg is not None:
                if rel.date_beginning is not None and rel.date_end is not None:
                    if date_beg < rel.date_end:
                        return f'{person_s} was in another relation that time'
                elif rel.date_end is not None:
                    if date_beg < rel.date_end:
                        return f'{person_s} was in another relation that time'
            if date_end is not None:
                if rel.date_beginning is not None and rel.date_end is not None:
                    if date_end > rel.date_beg:
                        return f'{person_s} was in another relation that time'
                elif rel.date_beg is not None:
                    if date_end > rel.date_beginning:
                        return f'{person_s} was in another relation that time'


def get_code_dict(code_list, s_person, r_person, relation):
    r = code_list.count('R')
    d = code_list.count('D')
    code = ''
    if r == 1 and d == 1:
        code = 'RD'
    elif r > 0:
        code = 'R'
    elif d < 0:
        code = 'D'

    code_dict_p = {'R': f'{r_person} is a ancestor of {s_person}',
                   'D': f'{r_person} is a descendant of {s_person}',
                   'RD': f'{r_person} is a brother/sister of {s_person}',
                   }

    return code_dict_p[code]


def path_child(start_person, destiny_person, code):
    list_rel_child = Relation.objects.filter(family_relation='A', source_person=start_person)
    if list_rel_child is not None:
        for rel_child in list_rel_child:
            child = Person.objects.get(id=rel_child.related_person_id)
            code.append('D')
            if child == destiny_person:
                return code
            check = path_child(child, destiny_person, code)
            if check is not None:
                return code
            code.pop(-1)
    else:
        return None


def path_parent(start_person, destiny_person, code):
    list_rel_parent = Relation.objects.filter(family_relation='A', related_person=start_person)

    if list_rel_parent is not None:
        set_children = set()
        parent_list = []
        for rel_parent in list_rel_parent:
            parent = Person.objects.get(id=rel_parent.source_person_id)
            if parent == destiny_person:
                code.append('R')
                return code
            else:
                parent_list.append(parent)
            list_children = Relation.objects.filter(family_relation='A', source_person=parent)
            for children in list_children:
                child = Person.objects.get(id=children.related_person_id)
                set_children.add(child)
        for child in list(set_children):
            code.append('R')
            if child == start_person:
                code.pop(-1)
                continue
            code.append('D')
            if child == destiny_person:
                return code
            check = path_child(child, destiny_person, code)
            if check is not None:
                return code
            else:
                code.pop(-1)
            code.pop(-1)
        for parent in parent_list:
            code.append('R')
            check = path_parent(parent, destiny_person, code)
            if check is not None:
                return code
            code.pop(-1)
    else:
        return None


def family_relation_control(s_person, r_person, relation):
    code = []
    if s_person == r_person:
        return "This is the same person"
    if Relation.objects.filter(source_person=s_person, related_person=r_person, family_relation='P').exists() or \
            Relation.objects.filter(source_person=r_person, related_person=s_person,
                                    family_relation='P').exists():  # wielokrotne zwiazki!
        code.append('P')
        return f'{s_person} and {r_person} are in a relationship',
    code = path_child(s_person, r_person, code)
    if code is None:
        code = []
        code = path_parent(s_person, r_person, code)
    if code is not None:
        return get_code_dict(code, s_person, r_person, relation)


class RelationForm(forms.ModelForm):
    date_beginning = forms.DateField(required=False, widget=DatePicker())
    date_end = forms.DateField(required=False, widget=DatePicker())
    merge_child_father = forms.BooleanField(required=False)
    merge_child_mother = forms.BooleanField(required=False)

    class Meta:
        model = Relation
        fields = ['source_person', 'family_relation', 'related_person', 'date_beginning', 'date_end',
                  'merge_child_father', 'merge_child_mother']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['merge_child_father'].default = 'off'
        self.fields['merge_child_mother'].default = 'off'
        self.fields['family_relation'].label = "Type of relation"
        self.fields['date_beginning'].label = "The beginning of the relationship (use 'year-month-day' format or a calendar)"
        self.fields['date_end'].label = "Endof the relationship (use 'year-month-day' format or a calendar)"
        self.fields['merge_child_mother'].label = "Join the mother's children (mother's children, they will also belong to the father)"
        self.fields['merge_child_father'].label = "Join the father's children (father's children, they will also belong to the mother)"

        # if 'family' in self.data:
        try:
            family_id = int(self.data.get('family'))
            self.fields['source_person'].queryset = Person.objects.filter(family_tree_id=family_id).order_by(
                'first_name')
            self.fields['related_person'].queryset = Person.objects.filter(family_tree_id=family_id).order_by(
                'first_name')
        except (ValueError, TypeError):
            pass  # invalid input from the client; ignore and fallback to empty City queryset
        # elif self.instance.pk:
        #     self.fields['source_person'].queryset = self.instance.family_person.source_person_set.order_by(
        #         '-datetime_person')
        #     self.fields['related_person'].queryset = self.instance.family_person.related_person_se.order_by(
        #         '-datetime_person')

    def save(self):
        relation = super(RelationForm, self).save(commit=False)
        relation.save()
        return relation

    def clean(self):
        super(RelationForm, self).clean()
        person_s = self.cleaned_data['source_person']
        person_r = self.cleaned_data['related_person']
        relation = self.cleaned_data['family_relation']
        date_beg = self.cleaned_data['date_beginning']
        date_end = self.cleaned_data['date_end']
        if date_beg and date_beg > datetime.date.today():
            raise forms.ValidationError("You cannot end a relation from the future.")
        if date_end and date_end > datetime.date.today():
            raise forms.ValidationError("You cannot create a relation from the future.")
        if date_beg is not None and date_end is not None and date_end < date_beg:
            raise forms.ValidationError("Incorrect relation time period")

        if relation == 'P':
            check_age = check_age_of_partner(person_s, person_r)
            if check_age:
                raise forms.ValidationError(check_age)
            check_lovers_1 = check_another_relation_date(person_s, person_r, date_beg, date_end)
            if check_lovers_1:
                raise forms.ValidationError(check_lovers_1)
            check_lovers_2 = check_another_relation_date(person_s, person_r, date_beg, date_end)
            if check_lovers_2:
                raise forms.ValidationError(check_lovers_2)
        else:
            if relation == 'D' and number_of_parents(person_s) > 1:
                raise forms.ValidationError(f"{person_s} cannot have more than two parents.")
            elif relation == 'A' and number_of_parents(person_r) > 1:
                raise forms.ValidationError(f"{person_r} cannot have more than two parents.")
            check_age = check_age_of_parent(relation, person_s, person_r)
            if check_age:
                raise forms.ValidationError(check_age)

        info = family_relation_control(person_s, person_r, relation)
        if info:
            raise forms.ValidationError(info)



class RelationCheck(forms.ModelForm):
    class Meta:
        model = Relation
        fields = ['source_person', 'related_person']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["source_person"].required = True
        self.fields["related_person"].required = True

    def save(self):
        relation = super(RelationCheck, self).save(commit=False)
        relation.save()
        return relation


class FilterForm(Form):
    FILTER_CHOICES = (
        ('source_person__first_name', 'source person'),
        ('related_person__first_name', 'related person'),
    )
    search = CharField(required=False)
