# -*- coding: utf-8 -*-
#
# Copyright © 2012 - 2020 Michal Čihař <michal@cihar.com>
#
# This file is part of Weblate <https://weblate.org/>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#


from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.encoding import force_str
from django.utils.translation import gettext as _
from django.views.generic.base import TemplateView

from weblate.memory.forms import DeleteForm, ImportForm, UploadForm
from weblate.memory.storage import MemoryImportError, TranslationMemory
from weblate.memory.tasks import import_memory
from weblate.utils import messages
from weblate.utils.views import ErrorFormView, get_project
from weblate.wladmin.views import MENU

CD_TEMPLATE = 'attachment; filename="weblate-memory.{}"'


def get_objects(request, kwargs):
    if 'project' in kwargs:
        return {'project': get_project(request, kwargs['project'])}
    if 'manage' in kwargs:
        return {'use_file': True}
    return {'user': request.user}


def check_perm(user, permission, objects):
    if 'project' in objects:
        return user.has_perm(permission, objects['project'])
    if 'user' in objects:
        # User can edit own translation memory
        return True
    if 'use_file' in objects:
        return user.has_perm('memory.edit')
    return False


@method_decorator(login_required, name='dispatch')
class MemoryFormView(ErrorFormView):
    def get_success_url(self):
        return reverse('memory', kwargs=self.kwargs)

    def dispatch(self, request, *args, **kwargs):
        self.objects = get_objects(request, kwargs)
        return super().dispatch(request, *args, **kwargs)


class DeleteView(MemoryFormView):

    form_class = DeleteForm

    def form_valid(self, form):
        if not check_perm(self.request.user, 'memory.delete', self.objects):
            raise PermissionDenied()
        memory = TranslationMemory()
        memory.delete(**self.objects)
        messages.success(self.request, _('Entries deleted.'))
        return super().form_valid(form)


class ImportView(MemoryFormView):

    form_class = ImportForm

    def form_valid(self, form):
        if not check_perm(self.request.user, 'memory.edit', self.objects):
            raise PermissionDenied()
        import_memory.delay(self.objects['project'].pk)

        messages.success(self.request, _('Import of strings scheduled.'))
        return super().form_valid(form)


class UploadView(MemoryFormView):
    form_class = UploadForm

    def form_valid(self, form):
        if not check_perm(self.request.user, 'memory.edit', self.objects):
            raise PermissionDenied()
        try:
            TranslationMemory.import_file(
                self.request, form.cleaned_data['file'], **self.objects
            )
            messages.success(
                self.request, _('File processed, the entries will appear shortly.')
            )
        except MemoryImportError as error:
            messages.error(self.request, force_str(error))
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class MemoryView(TemplateView):
    template_name = 'memory/index.html'

    def dispatch(self, request, *args, **kwargs):
        self.objects = get_objects(request, kwargs)
        return super().dispatch(request, *args, **kwargs)

    def get_url(self, name):
        return reverse(name, kwargs=self.kwargs)

    def get_context_data(self, **kwargs):
        memory = TranslationMemory()
        context = super().get_context_data(**kwargs)
        context.update(self.objects)
        entries = memory.list_documents(**self.objects)
        context['num_entries'] = len(entries)
        context['total_entries'] = memory.doc_count()
        context['delete_url'] = self.get_url('memory-delete')
        context['upload_url'] = self.get_url('memory-upload')
        context['download_url'] = self.get_url('memory-download')
        user = self.request.user
        if check_perm(user, 'memory.delete', self.objects):
            context['delete_form'] = DeleteForm()
        if check_perm(user, 'memory.edit', self.objects):
            context['upload_form'] = UploadForm()
            if 'project' in self.objects:
                context['import_form'] = ImportForm()
                context['import_url'] = self.get_url('memory-import')
        if 'use_file' in self.objects:
            context['menu_items'] = MENU
            context['menu_page'] = 'memory'
        if 'use_file' in self.objects or (
            'project' in self.objects and self.objects['project'].use_shared_tm
        ):
            context['shared_entries'] = len(memory.list_documents(use_shared=True))
        return context


class DownloadView(MemoryView):
    def get(self, request, *args, **kwargs):
        memory = TranslationMemory()
        fmt = request.GET.get('format', 'json')
        data = [dict(x) for x in memory.list_documents(**self.objects)]
        if fmt == 'tmx':
            response = render(
                request,
                'memory/dump.tmx',
                {'data': data},
                content_type='application/x-tmx',
            )
        else:
            fmt = 'json'
            response = JsonResponse(data, safe=False)
        response['Content-Disposition'] = CD_TEMPLATE.format(fmt)
        return response
