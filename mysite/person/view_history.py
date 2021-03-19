import datetime
from dateutil.relativedelta import relativedelta
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.generic import DetailView

from person.models import Person, Relation
from tree.models import FamilyTree


class PersonDetailView(UserPassesTestMixin, DetailView):
    model = Person
    template_name = 'person/detail.html'

    def test_func(self):
        person = self.get_object()
        tree = person.family_tree
        if tree.access == 0:
            return True
        if self.request.user == tree.owner:
            return True
        return False

    def get_object(self):
        obj = get_object_or_404(Person, pk=self.kwargs.get('pk_per'))
        obj.datetime_person = timezone.now()
        obj.save()
        return obj

    def get_context_data(self, **kwargs):
        context = super(PersonDetailView, self).get_context_data(**kwargs)
        context["own"] = False
        id_tree = self.object.family_tree_id
        owner = FamilyTree.objects.get(id=id_tree).owner
        if self.request.user == owner:
            context["own"] = True
        context["age"] = self.get_age()
        context["parents"] = self.get_parents()
        context["partner"] = self.get_partner()
        context["children"] = self.get_children()
        context["story"] = self.get_story()
        return context

    def get_age(self):
        if self.object.date_of_death is not None:
            if self.object.date_of_birth is not None:
                return f'Passed away at the age of {relativedelta(self.object.date_of_death, self.object.date_of_birth).years}'
        else:
            if self.object.date_of_birth is not None:
                return f'{relativedelta(datetime.date.today(), self.object.date_of_birth).years}'

    def get_parents(self):
        parents = Relation.objects.filter(related_person=self.object.id, family_relation='A')
        message = []
        for parent in parents:
            data = {'alive': '', 'status': '', 'person': '', 'age': ''}
            parent = Person.objects.get(id=parent.source_person_id)
            if parent.sex == 0:
                data['status'] = 'Father'
            else:
                data['status'] = 'Mother'
            data['person'] = parent
            if parent.date_of_death is not None:
                data['alive'] = f'{parent.date_of_death}'
            if parent.date_of_birth is not None:
                data['age'] = f'passed away at age of {relativedelta(parent.date_of_death, parent.date_of_birth).years}' if parent.date_of_death else f'{relativedelta(datetime.date.today(), parent.date_of_birth).years}'
            message.append(data)
        return message

    def get_children(self):
        children = Relation.objects.filter(source_person=self.object.id, family_relation='A').order_by('date_beginning')
        message = []
        for child in children:
            data = {'alive': '', 'status': '', 'person': '', 'age': ''}
            child = Person.objects.get(id=child.related_person_id)
            if child.sex == 0:
                data['status'] = 'Son'
            else:
                data['status'] = 'Daughter'
            data['person'] = child
            if child.date_of_death is not None:
                data['alive'] = f'[+]{child.date_of_death}'
            if child.date_of_birth is not None:
                data['age'] = f'passed away at age of {relativedelta(child.date_of_death, child.date_of_birth).years}' if child.date_of_death else f'{relativedelta(datetime.date.today(), child.date_of_birth).years}'
            message.append(data)
        return message

    def get_partner(self):

        message = []

        rel_partners = Relation.objects.filter(source_person=self.object.id,
                                               family_relation='P') if self.object.sex == 0 \
            else Relation.objects.filter(related_person=self.object.id, family_relation='P')
        for rel_partner in rel_partners:
            data = {'alive': '', 'status': '', 'person': '', 'age': '', 'in_relation': '', 'breakup': ''}
            partner = Person.objects.get(id=rel_partner.related_person_id) if self.object.sex == 0 \
                else Person.objects.get(id=rel_partner.source_person_id)
            if partner.sex == 1:
                data['status'] = 'Wife'
            else:
                data['status'] = 'Husband'
            data['person'] = partner
            if partner.date_of_death is not None:
                data['alive'] = f'[+]{partner.date_of_death}'

            if partner.date_of_birth is not None:
                data['age'] = f'passed away at age of {relativedelta(partner.date_of_death, partner.date_of_birth).years}' if partner.date_of_death else f'{relativedelta(datetime.date.today(), partner.date_of_birth).years}'
            if rel_partner.date_beginning is not None:
                data['in_relation'] = f'{relativedelta(datetime.date.today() if rel_partner.date_end is None else rel_partner.date_end, rel_partner.date_beginning).years} years together [married in {rel_partner.date_beginning}] '
            if rel_partner.date_end is not None and rel_partner.date_end != partner.date_of_death and rel_partner.date_end != self.object.date_of_death:
                data['breakup'] = f'Divorce in {rel_partner.date_end}'
            message.append(data)

        return message

    def get_story(self):

        message = []
        data = {'event': '', 'status': '', 'rel_person': '', 'age': '', 'date': ''}

        if self.object.date_of_birth:
            data = {'event': '', 'status': '', 'rel_person': '', 'age': '', 'date': ''}

            data['event'] = 'The birth of'
            data['status'] = None
            data['rel_person'] = self.object
            data['age'] = 0
            data['date'] = self.object.date_of_birth
            message.append(data)

        if self.object.date_of_death:
            data = {'event': '', 'status': '', 'rel_person': '', 'age': '', 'date': ''}

            data['event'] = 'Death of'
            data['status'] = ''
            data['rel_person'] = self.object
            data['age'] = relativedelta(self.object.date_of_death,
                                        self.object.date_of_birth).years if self.object.date_of_birth else ''
            data['date'] = self.object.date_of_death
            message.append(data)

        rel_partners = Relation.objects.filter(source_person=self.object.id,
                                               family_relation='P') if self.object.sex == 0 \
            else Relation.objects.filter(related_person=self.object.id, family_relation='P')
        for rel_partner in rel_partners:
            if rel_partner.date_beginning:
                data = {'event': '', 'status': '', 'rel_person': '', 'age': '', 'date': ''}

                partner = Person.objects.get(id=rel_partner.related_person_id) if self.object.sex == 0 \
                    else Person.objects.get(id=rel_partner.source_person_id)
                data['event'] = 'Relationship with'
                data['status'] = ''
                data['rel_person'] = partner
                data['age'] = relativedelta(rel_partner.date_beginning,
                                            self.object.date_of_birth).years if self.object.date_of_birth else ''
                data['date'] = rel_partner.date_beginning
                message.append(data)

            if rel_partner.date_end is not None and rel_partner.date_end != self.object.date_of_death:

                partner = Person.objects.get(id=rel_partner.related_person_id) if self.object.sex == 0 \
                    else Person.objects.get(id=rel_partner.source_person_id)
                if rel_partner.date_end != partner.date_of_death:
                    data = {'event': '', 'status': '', 'rel_person': '', 'age': '', 'date': ''}

                    data['event'] = 'Divorce with'
                    data['status'] = ''
                    data['rel_person'] = partner
                    data['age'] = relativedelta(rel_partner.date_end,
                                                self.object.date_of_birth).years if self.object.date_of_birth else ''
                    data['date'] = rel_partner.date_end
                    message.append(data)
                elif self.object.date_of_death is None or self.object.date_of_death > partner.date_of_death:
                    data = {'event': '', 'status': '', 'rel_person': '', 'age': '', 'date': ''}

                    data['event'] = 'Death of'
                    data['status'] = 'wife' if partner.sex == 1 else 'husband'
                    data['rel_person'] = partner
                    data['age'] = relativedelta(rel_partner.date_end,
                                                self.object.date_of_birth).years if self.object.date_of_birth else ''
                    data['date'] = rel_partner.date_end
                    message.append(data)

        rel_parents = Relation.objects.filter(related_person=self.object.id, family_relation='A')
        for rel_parent in rel_parents:
            parent = Person.objects.get(id=rel_parent.source_person_id)
            if parent.date_of_death:
                if self.object.date_of_death is None or self.object.date_of_death > parent.date_of_death:
                    data = {'event': '', 'status': '', 'rel_person': '', 'age': '', 'date': ''}

                    data['event'] = 'Death of'
                    data['status'] = 'mother' if parent.sex == 1 else 'father'
                    data['rel_person'] = parent
                    data['age'] = relativedelta(parent.date_of_death,
                                                self.object.date_of_birth).years if self.object.date_of_birth else ''
                    data['date'] = parent.date_of_death
                    message.append(data)

        rel_children = Relation.objects.filter(source_person=self.object.id, family_relation='A').order_by(
            'date_beginning')
        for rel_child in rel_children:
            child = Person.objects.get(id=rel_child.related_person_id)

            if child.date_of_birth:
                data = {'event': '', 'status': '', 'rel_person': '', 'age': '', 'date': ''}

                data['event'] = 'The birth of'
                data['status'] = 'daughter' if child.sex == 1 else 'son'
                data['rel_person'] = child
                data['age'] = relativedelta(child.date_of_birth,
                                            self.object.date_of_birth).years if self.object.date_of_birth else ''
                data['date'] = child.date_of_birth
                message.append(data)
            if child.date_of_death:
                if self.object.date_of_death is None or self.object.date_of_death > child.date_of_death:
                    data = {'event': '', 'status': '', 'rel_person': '', 'age': '', 'date': ''}

                    data['event'] = 'Death of'
                    data['status'] = 'daughter' if child.sex == 1 else 'son'
                    data['rel_person'] = child
                    data['age'] = relativedelta(child.date_of_death,
                                                self.object.date_of_birth).years if self.object.date_of_birth else ''
                    data['date'] = child.date_of_death
                    message.append(data)

            if Relation.objects.filter(source_person=child.id, family_relation='P').exists or Relation.objects.filter(
                    related_person=child.id, family_relation='P').exists:
                rel_partners_child = Relation.objects.filter(source_person=child.id,
                                                             family_relation='P') if child.sex == 0 \
                    else Relation.objects.filter(related_person=child.id, family_relation='P')
                for rel_partner_child in rel_partners_child:
                    if rel_partner_child.date_beginning:
                        if self.object.date_of_death is None or self.object.date_of_death > rel_partner_child.date_beginning:
                            if rel_partner_child.date_beginning:
                                data = {'event': '', 'status': '', 'rel_person': '', 'age': '', 'date': ''}

                                partner = Person.objects.get(id=rel_partner_child.related_person_id) if child.sex == 0 \
                                    else Person.objects.get(id=rel_partner_child.source_person_id)
                                data[
                                    'event'] = f'Son relationship {child.first_name} {child.last_name} with' if child.sex == 0 else f'Daughter relationship {child.first_name} {child.last_name} with'
                                data['status'] = ''
                                data['rel_person'] = partner
                                data['age'] = relativedelta(rel_partner_child.date_beginning,
                                                            self.object.date_of_birth).years if self.object.date_of_birth else ''
                                data['date'] = rel_partner_child.date_beginning
                                message.append(data)

            rel_grandchildren = Relation.objects.filter(source_person=child.id, family_relation='A').order_by(
                'date_beginning')
            for rel_grandchild in rel_grandchildren:
                grandchild = Person.objects.get(id=rel_grandchild.related_person_id)

                if grandchild.date_of_birth:
                    if self.object.date_of_death is None or self.object.date_of_death > grandchild.date_of_birth:
                        data = {'event': '', 'status': '', 'rel_person': '', 'age': '', 'date': ''}

                        data['event'] = 'The birth of'
                        data['status'] = 'granddaughter' if grandchild.sex == 1 else 'grandson'
                        data['rel_person'] = grandchild
                        data['age'] = relativedelta(grandchild.date_of_birth,
                                                    self.object.date_of_birth).years if self.object.date_of_birth else ''
                        data['date'] = grandchild.date_of_birth
                        message.append(data)

        return message
