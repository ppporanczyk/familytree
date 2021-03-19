import datetime
import random

from dateutil.relativedelta import relativedelta
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import render
from django.views.generic import View
from rest_framework.response import Response
from rest_framework.views import APIView

from person.models import Person, Relation
from tree.models import FamilyTree


class HomeView(UserPassesTestMixin, View):
    def get(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        tree = FamilyTree.objects.get(id=pk)
        oldest_person, oldest_person_age = self.get_higest_age(tree)
        youngest_person, youngest_person_age = self.get_lowest_age(tree)
        longest_rel_p, interval = self.longest_rel_p(tree)
        grandmother_num, num_grandchildren = self.grandma_num(tree)
        context = {'pk': pk, 'tree': tree, 'oldest_person': oldest_person, 'oldest_person_age': oldest_person_age,
                   'longest_p': longest_rel_p, 'interval_p': interval,
                   'grandmother_num': grandmother_num, 'num_grandchildren': num_grandchildren,
                   'youngest_person': youngest_person, 'youngest_person_age': youngest_person_age}
        return render(request, 'familytree/charts.html', context)

    def test_func(self):
        tree = self.kwargs['pk']
        tree = FamilyTree.objects.get(id=tree)
        if tree.access == 0:
            return True
        if self.request.user == tree.owner:
            return True
        return False

    def get_higest_age(self, tree):
        people = Person.objects.filter(family_tree=tree)
        oldest = None
        for person in people:
            if person.date_of_birth and person.date_of_death is None:
                if oldest is None:
                    oldest = person
                if oldest.date_of_birth > person.date_of_birth:
                    oldest = person
        age = None
        if oldest:
            age = f'{relativedelta(datetime.date.today(), oldest.date_of_birth).years}'

        return oldest, age

    def longest_rel_p(self, tree):
        people = Person.objects.filter(family_tree=tree)
        longest = None
        for person in people:
            if person.sex == 0:
                if Relation.objects.filter(family_relation='P', source_person=person, date_end=None).exists():
                    rel = Relation.objects.get(family_relation='P', source_person=person, date_end=None)
                    if rel.date_beginning:
                        if longest is None:
                            longest = rel
                        if longest.date_beginning > rel.date_beginning:
                            longest = rel

        interval = None
        if longest:
            interval = f'{relativedelta(datetime.date.today(), longest.date_beginning).years}'
        return longest, interval

    def grandma_num(self, tree):
        people = Person.objects.filter(family_tree=tree, sex=1)
        grandma = None
        num_grandma = None
        for person in people:
            if person.date_of_death is None:
                temp_grand = 0
                children_rel = Relation.objects.filter(family_relation='A', source_person=person)
                for child_rel in children_rel:
                    child = Person.objects.get(id=child_rel.related_person.id)
                    num = Relation.objects.filter(family_relation='A', source_person=child).count()
                    temp_grand += num
                if grandma is None:
                    grandma = person
                    num_grandma = temp_grand
                if num_grandma == temp_grand:
                    if person.date_of_birth and grandma.date_of_birth:
                        if person.date_of_birth < grandma.date_of_birth:
                            grandma = person
                elif num_grandma < temp_grand:
                    grandma = person
                    num_grandma = temp_grand
        if num_grandma==0:
            grandma = None
            num_grandma = None

        return grandma, num_grandma

    def get_lowest_age(self, tree):
        people = Person.objects.filter(family_tree=tree)
        youngest = None
        for person in people:
            if person.date_of_birth and person.date_of_death is None:
                if youngest is None:
                    youngest = person
                if youngest.date_of_birth < person.date_of_birth:
                    youngest = person
        age = None
        if youngest:
            age = f'{relativedelta(datetime.date.today(), youngest.date_of_birth).years} y.o.'
            if relativedelta(datetime.date.today(), youngest.date_of_birth).years == 0:
                age = f'{relativedelta(datetime.date.today(), youngest.date_of_birth).months} months'

        return youngest, age


class ChartData(UserPassesTestMixin, APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, pk, format=None):
        man = Person.objects.filter(family_tree_id=self.kwargs['pk'], sex=0).count()
        woman = Person.objects.filter(family_tree_id=self.kwargs['pk'], sex=1).count()

        labels = ['men', 'women']
        default_items = [man, woman]
        data = {
            "labels": labels,
            "default": default_items,
        }
        return Response(data)

    def test_func(self):
        tree = self.kwargs['pk']
        tree = FamilyTree.objects.get(id=tree)
        if tree.access== 1 and self.request.user == tree.owner:
            return True
        elif tree.access==0:
            return True
        return False


class ChartDataAge(UserPassesTestMixin, APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, pk, format=None):
        range_age = {'under_20': 0, 'under_40': 0, 'under_60': 0, 'under_80': 0, 'above_80': 0, 'unknown': 0}
        family = Person.objects.filter(family_tree=pk)
        for person in family:
            if person.date_of_birth:
                age = relativedelta(datetime.date.today(), person.date_of_birth).years
                if age in range(0, 21):
                    range_age['under_20'] += 1
                elif age in range(21, 41):
                    range_age['under_40'] += 1
                elif age in range(41, 61):
                    range_age['under_60'] += 1
                elif age in range(61, 81):
                    range_age['under_80'] += 1
                elif age in range(81, ):
                    range_age['above_80'] += 1

            else:
                range_age['unknown'] += 1

        labels = ['0-20 y.o.', '20-40 y.o.', '40-60 y.o.', '60-80 y.o.', '+80 y.o.', 'unknown age']
        default = [range_age['under_20'], range_age['under_40'], range_age['under_60'], range_age['under_80'],
                   range_age['above_80'], range_age['unknown']]
        data = {
            "labels": labels,
            "default": default,
        }
        return Response(data)

    def test_func(self):
        tree = self.kwargs['pk']
        tree = FamilyTree.objects.get(id=tree)
        if tree.access== 1 and self.request.user == tree.owner:
            return True
        elif tree.access==0:
            return True
        return False


class ChartDataName(UserPassesTestMixin, APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, pk, format=None):
        names = set()

        people = Person.objects.filter(family_tree=pk)
        for person in people:
            names.add(person.last_name)

        names = list(names)
        list_names = list()
        for name in names:
            num = Person.objects.filter(family_tree=pk, last_name=name).count()
            list_names.append((name, num))

        list_names.sort(key=lambda tup: tup[1], reverse=True)
        labels = []
        default = []
        background = []
        for key, val in list_names:
            labels.append(key)
            default.append(val)

        for x in range(0, len(labels)):
            r = lambda: random.randint(0, 255)
            g = lambda: random.randint(0, 255)
            b = lambda: random.randint(0, 255)
            background.append('rgb(%d,%d,%d)' % (r(), g(), b()))

        data = {
            "labels": labels,
            "default": default,
            "background": background,
        }
        return Response(data)

    def test_func(self):
        tree = self.kwargs['pk']
        tree = FamilyTree.objects.get(id=tree)
        if tree.access== 1 and self.request.user == tree.owner:
            return True
        elif tree.access==0:
            return True
        return False
