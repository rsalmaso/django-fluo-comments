# Copyright (C) 2007-2018, Raffaele Salmaso <raffaele@salmaso.org>
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

from .version import get_version

VERSION = (0, 1, 0, "alpha", 0)

__version__  = get_version(VERSION)
__author__  = "Raffaele Salmaso"
__email__ = "raffaele@salmaso.org"


default_app_config = "comments.apps.CommentsConfig"


def get_comment_model():
    from django.conf import settings
    from django.apps import apps

    app_label, model_name = settings.COMMENTS_SETTINGS['COMMENT_MODEL'].split('.')
    comment_model = apps.get_model(app_label=app_label, model_name=model_name)
    if comment_model is None:
        raise
    return comment_model
