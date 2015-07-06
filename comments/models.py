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
from django.utils.encoding import python_2_unicode_compatible
from django.contrib.sites.models import Site
from fluo.db import models
from . import conf as settings


def get_current_site():
    # for a rationale of this helper
    # https://docs.djangoproject.com/en/dev/topics/migrations/#migration-serializing
    return Site.objects.get_current()


class CommentQuerySet(models.QuerySet):
    def roots(self):
        return self.filter(parent__isnull=True)

    def public(self):
        return self.filter(is_public=True)

    def moderated(self):
        return self.filter(is_public=False)

    def removed(self):
        return self.filter(is_removed=True)


class CommentManager(models.Manager.from_queryset(CommentQuerySet)):
    use_for_related_fields = True


@python_2_unicode_compatible
class CommentModel(models.TimestampModel):
    """
    A user comment about some object.
    """

    objects = CommentManager()

    site = models.ForeignKey(
        Site,
        default=get_current_site,
        related_name="comments",
        verbose_name=_("site"),
    )
    parent = models.ForeignKey(
        "self",
        blank=True,
        null=True,
        related_name="children",
        verbose_name=_("parent comment"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        related_name="%(class)s_comments",
        verbose_name=_("user"),
    )
    user_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("user's name"),
    )
    user_email = models.EmailField(
        max_length=255,
        blank=True,
        verbose_name=_("user's email address"),
    )
    user_url = models.URLField(
        blank=True,
        verbose_name=_("user's URL"),
    )

    comment = models.TextField(
        max_length=settings.MAX_LENGTH,
        verbose_name=_("comment"),
    )

    notify_by_email = models.BooleanField(
        default=True,
        verbose_name=_("notify by email for updates"),
    )

    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name=_("IP address"),
    )
    is_public = models.BooleanField(
        default=True,
        help_text=_("Uncheck this box to make the comment effectively disappear from the site."),
        verbose_name=_("is public"),
    )
    is_removed = models.BooleanField(
        default=False,
        help_text=_("Check this box if the comment is inappropriate. A \"This comment has been removed\" message will be displayed instead."),
        verbose_name=_("is removed"),
    )

    class Meta:
        abstract = True
        ordering = ["created_at"]
        permissions = [("can_moderate", "Can moderate comments")]
        verbose_name = _("comment")
        verbose_name_plural = _("comments")

    def __str__(self):
        return "{name}: {comment}...".format(
            name=self.name,
            comment=self.comment[:50],
        )

    @property
    def name(self):
        return self.userinfo["name"]

    @name.setter
    def name(self, val):
        if self.user_id:
            raise AttributeError(_("This comment was posted by an authenticated user and thus the name is read-only."))
        self.user_name = val

    @property
    def email(self):
        return self.userinfo["email"]

    @email.setter
    def email(self, val):
        if self.user_id:
            raise AttributeError(_("This comment was posted by an authenticated user and thus the email is read-only."))
        self.user_email = val

    @property
    def url(self):
        return self.userinfo["url"]

    @url.setter
    def url(self, val):
        self.user_url = val

    @property
    def userinfo(self):
        if not hasattr(self, "_userinfo"):
            userinfo = {
                "name": self.user_name,
                "email": self.user_email,
                "url": self.user_url
            }
            if self.user_id:
                u = self.user
                if u.email:
                    userinfo["email"] = u.email

                # If the user has a full name, use that for the user name.
                # However, a given user_name overrides the raw user.username,
                # so only use that if this comment has no associated name.
                if u.get_full_name():
                    userinfo["name"] = self.user.get_full_name()
                elif not self.user_name:
                    userinfo["name"] = u.get_username()
            self._userinfo = userinfo
        return self._userinfo
