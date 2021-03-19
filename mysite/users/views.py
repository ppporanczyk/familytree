from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import UpdateView, DeleteView

from tree.models import FamilyTree
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Your account has been created {username}')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form})


@login_required
def profile(request):
    list_tree = FamilyTree.objects.filter(owner=request.user.id).order_by('-datetime_tree')
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=request.user)

        if form.is_valid():
            form.save()
            messages.success(request, f'Your account has been updated!')
            return redirect('profile')
    else:
        form = UserUpdateForm(instance=request.user)
    context = {'form': form, 'list_tree': list_tree}

    return render(request, 'users/profile.html', context)


def start(request):
    return render(request, 'users/start.html')


class UserUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = User
    template_name = 'users/update.html'
    success_url = reverse_lazy('profile')
    form_class = UserUpdateForm

    def get_object(self, queryset=None):
        return self.request.user

    def test_func(self):
        user = self.get_object()
        if self.request.user == user:
            return True
        return False


class UserDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = User
    success_url = reverse_lazy('start')
    template_name = 'users/delete.html'

    def get_object(self, queryset=None):
        return self.request.user

    def test_func(self):
        user = self.get_object()
        if self.request.user == user:
            return True
        return False
