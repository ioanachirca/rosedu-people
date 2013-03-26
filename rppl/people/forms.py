from django import forms
from models import Person, Project, Edition, Role, Link, PersonRole
from django.core.exceptions import ValidationError

class ProjectRoleWidget(forms.MultiWidget):
    def __init__(self, editions, roles, *args, **kwargs):
        widgets = (
            forms.Select(choices = [(e, e) for e in editions]),
            forms.Select(choices = [(r, r) for r in roles])
        )
        super(ProjectRoleWidget, self).__init__(widgets, *args, **kwargs)

    def decompress(self, value):
        if value:
            return value.split('|')
        return ['', '']

class ProjectRoleField(forms.MultiValueField):
    def __init__(self, editions, roles, *args, **kwargs):
        self.widget = ProjectRoleWidget(editions, roles)
        fields = (
            forms.ChoiceField(choices=[(e, e) for e in editions]),
            forms.ChoiceField(choices=[(r, r) for r in roles])
        )
        super(ProjectRoleField, self).__init__(fields, *args, **kwargs)

    def compress(self, data_list):
        if data_list:
            return '|'.join(data_list)
        return None

class LinkSetForm(forms.Form):
    person = None

    max_links = 6

    def __init__(self, *args, **kwargs):
        self.person = kwargs.pop('instance')
        super(LinkSetForm, self).__init__(*args, **kwargs)

        if len(args) > 0:
            self.get_extra(args[0])
            return

        links = Link.objects.filter(person=self.person)

        for i in xrange(len(links)):
            self.fields['link%d' % (i + 1)] = forms.CharField(
                    max_length=100,
                    initial = links[i],
                    required = False)

    def get_extra(self, post):
        field_names = post.keys()
        for f in field_names:
            if f.startswith('link'):
                self.fields[f] = forms.CharField(max_length=100, required = False)

    def clean(self):
        return self.cleaned_data

    def save(self):
        links = self.cleaned_data.values()

class ProjectRoleForm(forms.Form):
    person = None
    project = None

    def __init__(self, *args, **kwargs):
        self.person = kwargs.pop('instance')
        self.project = kwargs.pop('project')

        super(ProjectRoleForm, self).__init__(*args, **kwargs)

        if len(args) > 0:
            self.get_extra(args[0])
            return

        roles = Role.objects.all()
        editions = Edition.objects.filter(project=self.project)

        person_roles = filter(lambda role: role.edition.project == self.project, self.person.person_roles)

        for i in xrange(len(person_roles)):
            role = person_roles[i]
            field = ProjectRoleField(
                    editions, roles,
                    initial = '|'.join([str(role.edition), str(role.role)]))

            self.fields['%d_role%d' % (self.project.id, i)] = field

    def get_extra(self, post):
        field_names = post.keys()

        roles = Role.objects.all()
        editions = Edition.objects.filter(project=self.project)

        for f in field_names:
            if f.startswith('%d_role' % self.project.id):
                # Truncate the name so the field is correctly named
                self.fields[f[:-2]] = ProjectRoleField(editions, roles)

    def save(self):
        pass


class ProfileSetForm(forms.ModelForm):
    class Meta:
        model = Person
        exclude = ('user', 'organisations')

    def clean(self):
        if len(self.cleaned_data['description'].split(' ')) > 200:
            raise ValidationError("Too many words")
        else:
            return self.cleaned_data

