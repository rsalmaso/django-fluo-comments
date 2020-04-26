# Copyright (C) 2007-2020, Raffaele Salmaso <raffaele@salmaso.org>
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

import hashlib

from django import template
from django.apps import apps
from django.template import TemplateSyntaxError
from django.template.loader import render_to_string
from django.utils.http import urlencode
from django.utils.translation import gettext as _

from ..conf import settings

if apps.is_installed("django.contrib.staticfiles"):
    from django.contrib.staticfiles.templatetags.staticfiles import static as _static
else:
    from django.templatetags.static import static as _static

register = template.Library()
GRAVATAR = settings.GRAVATAR


GRAVATAR_BASE_URL = {
    True: GRAVATAR.SECURE_URL,
    False: GRAVATAR.URL,
}


def _get_default_avatar_image(request, query, is_secure=False):
    if settings.DEFAULT_IMAGE:
        query["d"] = request.build_absolute_uri(_static(settings.DEFAULT_IMAGE))


def _get_gravatar_image(request, comment, size, is_secure):
    base = GRAVATAR_BASE_URL[is_secure]
    hash = hashlib.md5(comment.email.encode("utf8")).hexdigest()
    query = {
        "s": str(size),
        "r": GRAVATAR.RATING_G,
    }
    _get_default_avatar_image(request=request, query=query, is_secure=is_secure)
    url = "%(base)savatar/%(hash)s.png?%(query)s" % {
        "base": base,
        "hash": hash,
        "query": urlencode(query),
    }

    return {
        "url": url,
        "width": size,
        "height": size,
        "alt": comment.name,
    }


class GravatarNode(template.Node):
    def __init__(self, comment, size, varname):
        self.comment = template.Variable(comment)
        self.size = template.Variable(size)
        self.varname = template.Variable(varname)

    def render(self, context):
        request = context["request"]
        comment = self.comment.resolve(context)
        size = self.size.resolve(context)
        varname = self.varname.resolve(context)
        is_secure = request.META.get("wsgi.url_scheme") == "https"
        context[varname] = _get_gravatar_image(request=request, comment=comment, size=size, is_secure=is_secure)
        return ""


@register.tag
def get_gravatar(parser, token):
    """
    This tag is used for rendering an avatar icon, depending on user profile setting.

    Usage::
        {% get_avatar comment [size] as variable_name %}
        {% get_avatar comment 64 as icon %}
        {% get_avatar comment as icon %}

    Example::
        {% get_avatar user as avatar %}
        <img src="{{ avatar.src }}" width="{{ avatar.width }}" height="{{ avatar.height}}" alt=""/>
    """
    bits = token.contents.split()
    if len(bits) < 4 or len(bits) > 5:
        raise TemplateSyntaxError(_("get_avatar takes exactly four or five arguments"))

    if len(bits) == 4 and bits[2] != "as":
        raise TemplateSyntaxError(_("second argument must be 'as'"))
    elif len(bits) == 5 and bits[3] != "as":
        raise TemplateSyntaxError(_("third argument must be 'as'"))

    kwargs = {"comment": bits[1], "size": str(GRAVATAR.DEFAULT_SIZE)}
    if len(bits) == 5:
        kwargs["size"] = bits[2]
        kwargs["varname"] = bits[4]
    elif len(bits) == 4:
        kwargs["varname"] = bits[3]

    return GravatarNode(**kwargs)


@register.inclusion_tag("comments/tags/gravatar.html", takes_context=True)
def get_gravatar_image(context, comment, size=GRAVATAR.DEFAULT_SIZE):
    """
    simple get_avatar shorcuts
    """
    context["comment"] = comment
    context["size"] = size
    return context


class CommentNode(template.Node):
    def __init__(self, comment, template_name=None):
        self.comment = template.Variable(comment)
        self.template_name = template.Variable(template_name) if template_name else None

    def render(self, context):
        from ..forms import Type

        context["HANDLE"] = Type.HANDLE
        context["MODERATE"] = Type.MODERATE
        context["COMMENT"] = Type.COMMENT
        request = context["request"]
        comment = self.comment.resolve(context)
        template_name = self.template_name.resolve(context) if self.template_name else "blog/comment.html"
        return render_to_string(template_name, request=request, context={"comment": comment, "form": context["form"]})


@register.tag
def render_comment(parser, token, kwargs=None):
    """
    render_comment comment
    render_comment comment with 'template.html'
    """
    tag_name, *args = token.split_contents()
    template_name = None

    if len(args) < 1:
        raise TemplateSyntaxError("'%s' requires at least 'as variable' (got %r)" % (tag_name, args))
    comment = args[0]
    if args == 3 and args[1] == "with":
        template_name = args[2]
    return CommentNode(comment, template_name)
