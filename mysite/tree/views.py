from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from person.models import Person, Relation
from .forms import FamilyTreeForm, FilterForm
from .models import FamilyTree


class FamilyTreeAllListView(ListView):
    model = FamilyTree
    template_name = 'familytree/all.html'

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return FamilyTree.objects.filter(access='0').exclude(owner=self.request.user).order_by('-datetime_tree')
        else:
            return FamilyTree.objects.filter(access='0').order_by('-datetime_tree')


class FamilyTreeDetailView(UserPassesTestMixin, DetailView):
    model = FamilyTree
    template_name = 'familytree/detail.html'

    def get_object(self):
        obj = super(FamilyTreeDetailView, self).get_object()
        obj.datetime_tree = timezone.now()
        obj.save()
        return obj

    def get_context_data(self, **kwargs):
        context = super(FamilyTreeDetailView, self).get_context_data(**kwargs)
        context["own"] = False
        if self.request.user == self.object.owner:
            context["own"] = True
        context["form"] = FilterForm(initial={
            'search': self.request.GET.get('search', ''),
        })
        context["search"] = self.request.GET.get('search')
        context['object_list'] = self.get_data().order_by('-datetime_person')
        context["relation"] = False
        context["two_people"] = False
        for per in self.get_data():
            if len(self.get_data()) > 1:
                context["two_people"] = True
                if Relation.objects.filter(source_person=per) or Relation.objects.filter(related_person=per):
                    context["relation"] = True
                    break
        return context

    def get_data(self):
        query = self.request.GET.get('search')
        if query:
            return Person.objects.filter(family_tree_id=self.object.id).filter(
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(maiden_name__icontains=query)
            )
        else:
            return Person.objects.filter(family_tree_id=self.object.id)

    def test_func(self):
        tree = self.get_object()
        if tree.access == 0:
            return True
        if self.request.user == tree.owner:
            return True
        return False


class FamilyTreeCreateView(LoginRequiredMixin, CreateView):
    model = FamilyTree
    template_name = 'familytree/form.html'
    form_class = FamilyTreeForm

    def form_valid(self, form):
        messages.success(self.request, f'Registered {form.instance}')
        form.instance.owner = self.request.user
        form.save()
        return super(FamilyTreeCreateView, self).form_valid(form)

    def get_object(self):
        obj = super(FamilyTreeCreateView, self).get_object()
        obj.datetime_tree = timezone.now()
        obj.save()
        return obj


class FamilyTreeUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = FamilyTree
    template_name = 'familytree/update.html'
    form_class = FamilyTreeForm

    def form_valid(self, form):
        messages.success(self.request, f'Registered {form.instance}')
        form.instance.owner = self.request.user
        name_tree = form.cleaned_data['name_tree']
        form.save()
        return super(FamilyTreeUpdateView, self).form_valid(form)

    def test_func(self):
        tree = self.get_object()
        if self.request.user == tree.owner:
            return True
        return False

    def get_object(self):
        obj = super(FamilyTreeUpdateView, self).get_object()
        obj.datetime_tree = timezone.now()
        obj.save()
        return obj


class FamilyTreeDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = FamilyTree
    success_url = '/profile'
    template_name = 'familytree/confirm_delete.html'

    def test_func(self):
        tree = self.get_object()
        if self.request.user == tree.owner:
            return True
        return False
