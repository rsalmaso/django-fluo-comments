# -*- coding: utf-8 -*-

# Copyright (C) 2007-2015, Raffaele Salmaso <raffaele@salmaso.org>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from __future__ import absolute_import, division, print_function, unicode_literals
from django.utils.translation import ugettext_lazy as _
from fluo import forms


class Type(object):
    HANDLE = "handle"
    MODERATE = "moderate"
    COMMENT = "comment"


class BaseForm(forms.Form):
    type = forms.CharField(
        required=False,
        widget=forms.HiddenInput,
        label=_("Type"),
    )


class HandleForm(BaseForm):
    def save(self, request, post, commit=True):
        post.can_comment = not post.can_comment
        if commit:
            post.save()
        return post


class ModerateForm(BaseForm):
    pk = forms.CharField(
        required=True,
        widget=forms.HiddenInput,
        label=_("Comment pk"),
    )
    moderate = forms.CharField(
        required=False,
        widget=forms.HiddenInput,
        label=_("Moderate"),
    )

    def save(self, request, post, commit=True):
        from . import get_comment_model
        Comment = get_comment_model()
        comment = Comment.objects.get(pk=self.cleaned_data.get("pk"))
        comment.is_removed = not comment.is_removed
        if commit:
            comment.save()
        return comment


class CommentForm(BaseForm):
    parent = forms.CharField(
        required=False,
        widget=forms.HiddenInput,
    )
    name = forms.CharField(
        required=True,
        max_length=255,
        label=_("Your name:"),
    )
    email = forms.CharField(
        required=True,
        max_length=255,
        label=_("Your email (will not show):"),
    )
    message = forms.CharField(
        required=True,
        widget=forms.Textarea,
        label=_("Your message:"),
    )

    def __init__(self, data=None, user=None, *args, **kwargs):
        super(CommentForm, self).__init__(data, *args, **kwargs)
        self.fields["name"].required = False
        self.fields["email"].required = False
        self.user = user

    def save(self, request, post, commit=True):
        from . import get_comment_model
        Comment = get_comment_model()
        comment = Comment()
        pk = self.cleaned_data.get("parent", None)
        if pk:
            comment.parent = Comment.objects.get(pk=pk)
        comment.post = post
        comment.comment = self.cleaned_data.get("message")
        if self.user.is_authenticated():
            comment.name = self.user.username
            comment.email = self.user.email
            comment.user = self.user
        else:
            comment.name = self.cleaned_data.get("name")
            comment.email = self.cleaned_data.get("email")
        if commit:
            comment.save()
        return comment
