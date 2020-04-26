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

from django.conf import settings as djsettings


class Setting(dict):
    """ from http://stackoverflow.com/questions/3031219/python-recursively-access-dict-via-attributes-as-well-as-index-access """

    marker = object()

    def __init__(self, value=None):
        if value is None:
            pass
        elif isinstance(value, dict):
            for key in value:
                self.__setitem__(key, value[key])
        else:
            raise TypeError("expected dict")

    def __setitem__(self, key, value):
        if isinstance(value, dict) and not isinstance(value, Setting):
            value = Setting(value)
        super(Setting, self).__setitem__(key, value)

    def __getitem__(self, key):
        found = self.get(key, Setting.marker)
        if found is Setting.marker:
            found = Setting()
            super(Setting, self).__setitem__(key, found)
        return found

    __setattr__ = __setitem__
    __getattr__ = __getitem__


settings = Setting(getattr(djsettings, "COMMENTS_SETTINGS", {}))
settings.setdefault("MAX_LENGTH", 3000)
settings.setdefault("ENABLE_CAPTCHA", True)
settings.setdefault("DEFAULT_AVATAR", None)
if not settings.COMMENT_MODEL:
    from django.core.exceptions import ImproperlyConfigured

    raise ImproperlyConfigured("COMMENTS_SETTINGS does not have a COMMENT_MODEL field.")

settings.setdefault("AUTH_USER_MODEL", getattr(djsettings, "AUTH_USER_MODEL"))
settings.setdefault("SECRET_KEY", getattr(djsettings, "SECRET_KEY"))

gravatar = getattr(settings, "GRAVATAR", Setting())

gravatar.setdefault("URL", "http://www.gravatar.com/")
gravatar.setdefault("SECURE_URL", "https://secure.gravatar.com/")

# These options can be used to change the default image if no gravatar is found
gravatar.setdefault("DEFAULT_IMAGE_404", "404")
gravatar.setdefault("DEFAULT_IMAGE_MYSTERY_MAN", "mm")
gravatar.setdefault("DEFAULT_IMAGE_IDENTICON", "identicon")
gravatar.setdefault("DEFAULT_IMAGE_MONSTER", "monsterid")
gravatar.setdefault("DEFAULT_IMAGE_WAVATAR", "wavatar")
gravatar.setdefault("DEFAULT_IMAGE_RETRO", "retro")

# These options can be used to restrict gravatar content
gravatar.setdefault("RATING_G", "g")
gravatar.setdefault("RATING_PG", "pg")
gravatar.setdefault("RATING_R", "r")
gravatar.setdefault("RATING_X", "x")

gravatar.setdefault("DEFAULT_SIZE", 80)
gravatar.setdefault("DEFAULT_IMAGE", gravatar.DEFAULT_IMAGE_MYSTERY_MAN)
gravatar.setdefault("DEFAULT_RATING", gravatar.RATING_G)
gravatar.setdefault("DEFAULT_SECURE", True)

settings.GRAVATAR = gravatar
