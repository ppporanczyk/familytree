from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render

from person.models import Person, Relation
from .forms import RelationCheck


@login_required
def relation_check(request, pk):
    context = {}
    form = RelationCheck()
    context['form'] = form
    context['text'] = "There is no relation"

    if not request.user.is_authenticated:
        return HttpResponseForbidden()

    if request.POST.get('source_person') and request.POST.get('related_person'):
        s_person = request.POST.get('source_person')
        r_person = request.POST.get('related_person')
        s_person = Person.objects.get(id=s_person)
        r_person = Person.objects.get(id=r_person)
        context['text'] = family_relation_control(s_person, r_person)

    return render(request, 'relation/check.html', {'context': context})


def get_code_dict(code_list, s_person, r_person):
    get_level = {1: 'first', 2: 'second', 3: 'third', 4: 'fourth', 5: 'fifth', 6: 'sixth', 7: 'seventh', 8: 'eighth',
                 9: 'ninth', 10: 'tenth'}
    get_times = {1: 'once', 2: 'twice', 3: 'thrice', 4: 'four times', 5: 'five times', 6: 'six times', 7: 'seven times',
                 8: 'eight times',
                 9: 'nine times', 10: 'ten times'}

    r = code_list.count('R')
    d = code_list.count('D')
    p = code_list.count('P')
    code = ''
    code_list = ''.join(code_list)
    if p > 0:
        if code_list == 'PR':
            code = 'mother in-law' if r_person.sex == 1 else 'father in-law'
        elif code_list == 'DP':
            code = 'daughter in-law' if r_person.sex == 1 else 'son in-law'
        elif code_list == 'PRR':
            code = 'grandmother in-law' if r_person.sex == 1 else 'grandfather in-law'
        elif code_list == 'DDP':
            code = 'granddaughter in-law' if r_person.sex == 1 else 'grandson in-law'
        elif code_list == 'RDP' or code_list == 'PRD':
            code = 'sister in-law' if r_person.sex == 1 else 'brother in-law'
        elif code_list == 'P':
            return f'{r_person} and {s_person} are in relationship'
    elif r > 0 and d > 0 and p == 0:
        if r == d:
            if r == 1:
                code = 'sister' if r_person.sex == 1 else 'brother'
            else:
                r = r - 1
                code = get_level[r] + ' ' + 'cousin'
        elif r > 1 and d == 1:
            if r == 2:
                code = 'aunt' if r_person.sex == 1 else 'uncle'
            else:
                r = r - 3
                great = 'great ' * r if r > 0 else ''
                code = great + 'grand-aunt' if r_person.sex == 1 else great + 'grand-uncle'
        elif r == 1 and d > 1:
            if d == 2:
                code = 'niece' if r_person.sex == 1 else 'nephew'
            else:
                d = d - 3
                great = 'great ' * d if d > 0 else ''
                code = great + 'grandniece' if r_person.sex == 1 else great + 'grandnephew'
        elif d > 1 and r > 1:
            d = r - d if r > d else d - r
            r = r - 1
            code = get_level[r] + ' ' + 'cousin' + ' ' + get_times[d] + ' removed'
    elif r > 0 and p == 0:
        if r == 1:
            code = 'mother' if r_person.sex == 1 else 'father'
        else:
            r = r - 2
            great = 'great ' * r if r > 0 else ''
            code = great + 'grandmother' if r_person.sex == 1 else great + 'grandfather'

    elif d > 0 and p == 0:
        if d == 1:
            code = 'daughter' if r_person.sex == 1 else 'son'
        else:
            d = d - 2
            great = 'great ' * d if d > 0 else ''
            code = great + 'granddaughter' if r_person.sex == 1 else great + 'grandson'

    if code:
        return f'{r_person} is a {code} of {s_person}'
    return f'There is no relation'


def path_child(start_person, destiny_person, code):
    list_rel_child = Relation.objects.filter(family_relation='A', source_person=start_person)
    if list_rel_child is not None:
        for rel_child in list_rel_child:
            child = Person.objects.get(id=rel_child.related_person_id)
            code.append('D')
            if 0 < code.count('D') < 3:
                if child.sex == 1 and Relation.objects.filter(related_person=child, family_relation='P').exists():
                    rel_child = Relation.objects.get(related_person=child, family_relation='P').source_person_id
                    partner_of_child = Person.objects.get(id=rel_child)
                    if partner_of_child == destiny_person:
                        code.append('P')
                        return code
                elif child.sex == 0 and Relation.objects.filter(source_person=child, family_relation='P').exists():
                    rel_child = Relation.objects.get(source_person=child, family_relation='P').related_person_id
                    partner_of_child = Person.objects.get(id=rel_child)
                    if partner_of_child == destiny_person:
                        code.append('P')
                        return code
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
            if ''.join(code) == 'RD':
                if child.sex == 1 and Relation.objects.filter(related_person=child, family_relation='P').exists():
                    rel_child = Relation.objects.get(related_person=child, family_relation='P').source_person_id
                    partner_of_child = Person.objects.get(id=rel_child)
                    if partner_of_child == destiny_person:
                        code.append('P')
                        return code
                elif child.sex == 0 and Relation.objects.filter(source_person=child, family_relation='P').exists():
                    rel_child = Relation.objects.get(source_person=child, family_relation='P').related_person_id
                    partner_of_child = Person.objects.get(id=rel_child)
                    if partner_of_child == destiny_person:
                        code.append('P')
                        return code
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


def path_partner(start_person, destiny_person, code):
    if start_person.sex == 1 and Relation.objects.filter(related_person=start_person, family_relation='P').exists():
        rel = Relation.objects.get(related_person=start_person, family_relation='P').source_person_id
        partner = Person.objects.get(id=rel)
        code.append('P')
        if partner == destiny_person:
            return code
        else:
            return path_parent(partner, destiny_person, code)
    elif start_person.sex == 0 and Relation.objects.filter(source_person=start_person, family_relation='P').exists():
        rel = Relation.objects.get(source_person=start_person, family_relation='P').related_person_id
        partner = Person.objects.get(id=rel)
        code.append('P')
        if partner == destiny_person:
            return code
        else:
            return path_parent(partner, destiny_person, code)


def family_relation_control(s_person, r_person):
    code = []
    if s_person == r_person:
        return "That is the same person"

    code = path_partner(s_person, r_person, code)
    if code is None:
        code = []
        code = path_child(s_person, r_person, code)
    if code is None:
        code = []
        code = path_parent(s_person, r_person, code)
    if code is not None:
        return get_code_dict(code, s_person, r_person)
    return f'No relation between {r_person} and {s_person}'
