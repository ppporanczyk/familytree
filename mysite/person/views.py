from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, UpdateView, DeleteView, ListView

from person.models import Person, Relation
from tree.models import FamilyTree
from .forms import PersonForm, RelationForm, FilterForm


class PersonCreateView(UserPassesTestMixin, LoginRequiredMixin, CreateView):
    model = Person
    template_name = 'person/form.html'
    form_class = PersonForm

    def form_valid(self, form):
        person = form.instance
        tree = FamilyTree(owner=self.request.user, id=self.kwargs['pk'])
        person.family_tree = tree
        person.save()
        return super(PersonCreateView, self).form_valid(form)

    def get_object(self):
        obj = get_object_or_404(Person, pk=self.kwargs.get('pk_per'))
        # obj = super(PersonCreateView, self).get_object()
        obj.datetime_person = timezone.now()
        obj.save()
        return obj

    def test_func(self):
        tree = self.kwargs['pk']
        tree = FamilyTree.objects.get(id=tree)
        if self.request.user == tree.owner:
            return True
        return False


class PersonUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Person
    template_name = 'person/update.html'
    form_class = PersonForm

    def form_valid(self, form):
        person = form.instance
        tree = FamilyTree(owner=self.request.user, id=self.kwargs['pk'])
        person.family_tree = tree
        person.save()
        return super(PersonUpdateView, self).form_valid(form)

    def test_func(self):
        person = self.get_object()
        tree = person.family_tree
        if self.request.user == tree.owner:
            return True
        return False

    def get_object(self, *args, **kwargs):
        obj = get_object_or_404(Person, pk=self.kwargs.get('pk_per'))
        # obj = Person.objects.get(id=self.kwargs.get('pk_per'))
        obj.datetime_person = timezone.now()
        obj.save()
        return obj


class PersonDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Person
    template_name = 'person/confirm_delete.html'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        return HttpResponseRedirect(success_url)

    def get_success_url(self):
        return reverse_lazy('tree-detail', kwargs={'pk': self.object.family_tree_id})

    def test_func(self):
        person = self.get_object()
        tree = person.family_tree
        if self.request.user == tree.owner:
            return True
        return False

    def get_object(self, *args, **kwargs):
        obj = get_object_or_404(Person, pk=self.kwargs.get('pk_per'))
        obj.datetime_person = timezone.now()
        obj.save()
        return obj


class RelationCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Relation
    template_name = 'relation/form.html'
    form_class = RelationForm

    def form_valid(self, form):
        relation = form.instance

        if relation.family_relation == 'D':
            swap = relation.source_person
            relation.source_person = relation.related_person
            relation.related_person = swap
            relation.family_relation = 'A'

        sex_per = Person.objects.get(id=relation.source_person_id).sex
        if relation.family_relation == 'P' and sex_per == 1:
            swap = relation.source_person
            relation.source_person = relation.related_person
            relation.related_person = swap

        if relation.date_end is None:
            if relation.related_person.date_of_death is not None and relation.source_person.date_of_death is not None:
                relation.date_end = relation.source_person.date_of_death if relation.source_person.date_of_death < relation.related_person.date_of_death else relation.related_person.date_of_death
            elif relation.source_person.date_of_death is not None:
                relation.date_end = relation.source_person.date_of_death
            elif relation.related_person.date_of_death is not None:
                relation.date_end = relation.related_person.date_of_death

        if relation.family_relation == 'A':
            birth_date = relation.related_person.date_of_birth
            if birth_date is not None:
                relation.date_beginning = birth_date

        if form.cleaned_data['merge_child_father']:
            children_rel = Relation.objects.filter(source_person=relation.source_person, family_relation='A')

            for child_rel in children_rel:
                child = child_rel.related_person
                if relation.related_person.date_of_birth and child.date_of_birth and relation.related_person.date_of_birth >= child.date_of_birth:
                    continue
                elif relation.related_person.date_of_death and child.date_of_birth and relation.related_person.date_of_death < child.date_of_birth:
                    continue
                elif Relation.objects.filter(source_person=relation.related_person, related_person=child,
                                             family_relation='A').exists():
                    continue
                child_rel.id = None
                child_rel.source_person = relation.related_person
                child_rel.save()
        if form.cleaned_data['merge_child_mother']:
            children_rel = Relation.objects.filter(source_person=relation.related_person, family_relation='A')

            for child_rel in children_rel:
                child = child_rel.related_person
                if relation.source_person.date_of_birth and child.date_of_birth and relation.source_person.date_of_birth >= child.date_of_birth:
                    continue
                elif relation.source_person.date_of_death and child.date_of_birth and relation.source_person.date_of_death < child.date_of_birth:
                    continue
                elif Relation.objects.filter(source_person=relation.source_person, related_person=child,
                                             family_relation='A').exists():
                    continue
                child_rel.id = None
                child_rel.source_person = relation.source_person
                child_rel.save()
        relation.save()

        return super(RelationCreateView, self).form_valid(form)

    def get_object(self):
        obj = get_object_or_404(Person, pk=self.kwargs.get('pk_per'))
        obj.datetime_relation = timezone.now()
        obj.save()
        return obj

    def test_func(self):
        tree = self.kwargs['pk']
        tree = FamilyTree.objects.get(id=tree)
        if self.request.user == tree.owner:
            return True
        return False


class RelationListView(UserPassesTestMixin, ListView):
    model = Relation
    template_name = 'relation/list.html'

    def get_queryset(self):
        id_tree = self.kwargs.get('pk')
        list_person = Person.objects.filter(family_tree_id=id_tree)
        matches = Relation.objects.none()
        for person in list_person:
            matches = matches | Relation.objects.filter(source_person=person)
        query = self.request.GET.get('search')
        if query:
            return matches.filter(
                Q(source_person__first_name__icontains=query) |
                Q(related_person__first_name__icontains=query) |
                Q(source_person__last_name__icontains=query) |
                Q(related_person__last_name__icontains=query) |
                Q(source_person__maiden_name__icontains=query) |
                Q(related_person__maiden_name__icontains=query)
            ).order_by('-datetime_relation')
        else:
            return matches.order_by('-datetime_relation')

    def get_context_data(self, **kwargs):
        context = super(RelationListView, self).get_context_data(**kwargs)
        if self.object_list:
            per = self.object_list.first().source_person
            tree_id = Person.objects.get(id=per.id).family_tree_id
            context['tree'] = FamilyTree.objects.get(id=tree_id)
        context["form"] = FilterForm(initial={
            'search': self.request.GET.get('search', ''),
        })
        context["search"] = self.request.GET.get('search')
        return context

    def test_func(self):
        tree = self.kwargs['pk']
        tree = FamilyTree.objects.get(id=tree)
        if tree.access == 0:
            return True
        if self.request.user == tree.owner:
            return True
        return False


class RelationDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Relation
    template_name = 'relation/delete.html'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        return HttpResponseRedirect(success_url)

    def get_success_url(self):
        return reverse_lazy('relation-list', kwargs={'pk': self.object.source_person.family_tree_id})

    def get_object(self, *args, **kwargs):
        obj = get_object_or_404(Relation, pk=self.kwargs.get('pk_rel'))
        obj.datetime_relation = timezone.now()
        obj.save()
        return obj

    def test_func(self):
        relation = self.get_object()
        id_person = relation.source_person_id
        tree = Person.objects.get(id=id_person).family_tree
        if self.request.user == tree.owner:
            return True
        return False


def load_person(request):
    family = request.GET.get('family')
    people = Person.objects.filter(family_tree_id=family).order_by('first_name')
    return render(request, 'relation/person_dropdown_list_options.html', {'people': people})
