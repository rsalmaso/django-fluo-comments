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
import hashlib
from django.apps import apps
from django import template
from django.template import TemplateSyntaxError
from django.utils.six.moves.urllib.parse import urlencode
from django.utils.translation import ugettext as _
from fluo.shortcuts import render_to_string
from .. import settings

if apps.is_installed('django.contrib.staticfiles'):
    from django.contrib.staticfiles.templatetags.staticfiles import static as _static
else:
    from django.templatetags.static import static as _static

register = template.Library()

GRAVATAR_URL = "http://www.gravatar.com/"
GRAVATAR_SECURE_URL = "https://secure.gravatar.com/"

# These options can be used to change the default image if no gravatar is found
GRAVATAR_DEFAULT_IMAGE_404 = "404"
GRAVATAR_DEFAULT_IMAGE_MYSTERY_MAN = "mm"
GRAVATAR_DEFAULT_IMAGE_IDENTICON = "identicon"
GRAVATAR_DEFAULT_IMAGE_MONSTER = "monsterid"
GRAVATAR_DEFAULT_IMAGE_WAVATAR = "wavatar"
GRAVATAR_DEFAULT_IMAGE_RETRO = "retro"

# These options can be used to restrict gravatar content
GRAVATAR_RATING_G = "g"
GRAVATAR_RATING_PG = "pg"
GRAVATAR_RATING_R = "r"
GRAVATAR_RATING_X = "x"

# Get user defaults from settings.py
GRAVATAR_DEFAULT_SIZE = getattr(settings, "GRAVATAR_DEFAULT_SIZE", 80)
GRAVATAR_DEFAULT_IMAGE = getattr(settings, "GRAVATAR_DEFAULT_IMAGE", GRAVATAR_DEFAULT_IMAGE_MYSTERY_MAN)
GRAVATAR_DEFAULT_RATING = getattr(settings, "GRAVATAR_DEFAULT_RATING", GRAVATAR_RATING_G)
GRAVATAR_DEFAULT_SECURE = getattr(settings, "GRAVATAR_DEFAULT_SECURE", True)

GRAVATAR_BASE_URL = {
    True: GRAVATAR_SECURE_URL,
    False: GRAVATAR_URL,
}


def _get_default_avatar_image(request, query, is_secure=False):
    if settings.DEFAULT_IMAGE:
        query["d"] = request.build_absolute_uri(_static(settings.DEFAULT_IMAGE))


def _get_gravatar_image(request, comment, size, is_secure):
    base = GRAVATAR_BASE_URL[is_secure]
    hash = hashlib.md5(comment.email.encode("utf8")).hexdigest()
    query = {
        "s": str(size),
        "r": GRAVATAR_RATING_G,
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
        context[varname] = _get_gravatar_image(
            request=request,
            comment=comment,
            size=size,
            is_secure=is_secure,
        )
        return ""


@register.tag
def get_gravatar(parser, token):
    '''
    This tag is used for rendering an avatar icon, depending on user profile setting.

    Usage::
        {% get_avatar comment [size] as variable_name %}
        {% get_avatar comment 64 as icon %}
        {% get_avatar comment as icon %}

    Example::
        {% get_avatar user as avatar %}
        <img src="{{ avatar.src }}" width="{{ avatar.width }}" height="{{ avatar.height}}" alt=""/>
    '''
    bits = token.contents.split()
    if len(bits) < 4 or len(bits) > 5:
        raise TemplateSyntaxError(_("get_avatar takes exactly four or five arguments"))

    if len(bits) == 4 and bits[2] != "as":
        raise TemplateSyntaxError(_("second argument must be 'as'"))
    elif len(bits) == 5 and bits[3] != "as":
        raise TemplateSyntaxError(_("third argument must be 'as'"))

    kwargs = { "comment": bits[1], "size": str(GRAVATAR_DEFAULT_SIZE) }
    if len(bits) == 5:
        kwargs["size"] = bits[2]
        kwargs["varname"] = bits[4]
    elif len(bits) == 4:
        kwargs["varname"] = bits[3]

    return GravatarNode(**kwargs)


@register.inclusion_tag("comments/tags/gravatar.html", takes_context=True)
def get_gravatar_image(context, comment, size=GRAVATAR_DEFAULT_SIZE):
    """
    simple get_avatar shorcuts
    """
    context["comment"] = comment
    context["size"] = size
    return context


class CommentNode(template.Node):
    def __init__(self, comment, template_name=None):
        self.comment = template.Variable(comment)
        self.template = template.Variable(template_name) if template_name else None

    def render(self, context):
        request = context["request"]
        comment = self.comment.resolve(context)
        template = self.template.resolve(context) if self.template else "blog/comment.html"
        return render_to_string(template, request=request, comment=comment, form=context["form"])


@register.tag
def render_comment(parser, token, kwargs=None):
    """
    render_comment comment
    render_comment comment with 'template.html'
    """
    args = token.split_contents()[1:]
    template_name = None

    if len(args) < 1:
        raise TemplateSyntaxError("'%s' requires at least 'as variable' (got %r)" % (self.tag_name, args))
    comment = args[0]
    if args == 3 and args[1] == "with":
        template_name = args[2]
    return CommentNode(comment, template_name)
