""" This module contains various globaly used (custom) enums"""

from enum import IntEnum
from typing import Self, override



# Defined by the tables api specifications °-°
class LanguageCode(IntEnum):
    """ Defines the supported languages (as its language code)

        See [ISO 639](https://en.wikipedia.org/wiki/List_of_ISO_639_language_codes) (Set 1)
    """
    EN = 0
    DE = 1

    @property
    @override
    # pylint: disable=E0102,W0236 # (function-redefined, invalid-overridden-method)
    # needed as languagecodes are always in lowercase, but enums should always be uppercase
    def name(self) -> str:
        """ The name of the Enum member (as lowercase)."""
        return super().name.lower()

    @classmethod
    def values(cls) -> list[int]:
        """ List of all valid enum values"""
        return [
            member.value for member in cls
        ]

    @classmethod
    def from_language_code(cls, language_code: str) -> Self:
        """ Creates a new enum based on the provided (ISO 639) language code"""
        return cls[language_code.upper()]

    @classmethod
    def valid_languages(cls) -> list[str]:
        """ Returns a list of all valid language codes"""
        return [
            name.lower() for name in cls.__members__
        ]

# Defined by the tables api specifications °-°
class ModuleLanguage(IntEnum):
    """ Defines the languages a module can be taught in (as stored in `Modulsprache`)

        A module can also be taught in both languages at once, which `LanguageCode`
        can not express, as the bot itself always speaks either english or german.
    """
    EN = 0
    DE = 1
    EN_DE = 2

    @property
    @override
    # pylint: disable=E0102,W0236 # (function-redefined, invalid-overridden-method)
    # needed as languagecodes are always in lowercase, but enums should always be uppercase
    def name(self) -> str:
        """ The name of the Enum member (as lowercase)."""
        return super().name.lower()

    @classmethod
    def values(cls) -> list[int]:
        """ List of all valid enum values"""
        return [
            member.value for member in cls
        ]

    @classmethod
    def from_language_code(cls, language_code: str) -> Self:
        """ Creates a new enum based on the provided language code"""
        return cls[language_code.upper()]

    @classmethod
    def valid_languages(cls) -> list[str]:
        """ Returns a list of all valid language codes"""
        return [
            name.lower() for name in cls.__members__
        ]

class StudyCourse(IntEnum):
    """ Defines all valid courses of study"""

    BSC_INF = 0             # B.Sc INF                   - Informatik
    BSC_CV = 1              # B.Sc CV                    - Computervisualistik
    BSC_INGINF = 2          # B.Sc INGINF                - Ingenieurinformatik
    BSC_WIF = 3             # B.Sc WIF                   - Wirtschaftsinformatik
    BSC_INF_BILINGUAL = 4   # B.Sc INF (bilingual)       - Informatik (bilingual)
    MSC_INF = 5             # M.Sc INF                   - --- " ----
    MSC_INGINF = 6          # M.Sc INGINF                - --------- " ---------
    MSC_WIF = 7             # M.Sc WIF                   - -------- " --------
    MSC_DKE = 8             # M.Sc DKE                   - Data and Knowledge Engineering
    MSC_DE = 9              # M.Sc DE                    - Digital Engineering
    MSC_VC = 10             # M.Sc VC                    - Visual Computing

    @classmethod
    def from_str(cls, course_str: str) -> Self:
        """ Creates a new enum based on the provided course of study string"""
        if course_str.upper() not in cls.__members__:
            raise ValueError(f"Invalid study course string: '{course_str}'")
        return cls[course_str.upper()]

    @classmethod
    def values(cls) -> list[int]:
        """ List of all valid enum values"""
        return [
            member.value for member in cls
        ]
class PO(IntEnum):
    """ Defines all valid courses of study"""

    PO_2015 = 0
    PO_2016 = 1
    PO_2017 = 2
    PO_2023 = 3
    PO_2024 = 4
    PO_2020 = 5
    PO_2021 = 6

    @classmethod
    def from_str(cls, course_str: str) -> Self:
        """ Creates a new enum based on the provided course of study string"""
        if course_str.upper() not in cls.__members__:
            raise ValueError(f"Invalid study course string: '{course_str}'")
        return cls[course_str.upper()]

    @classmethod
    def values(cls) -> list[int]:
        """ List of all valid enum values"""
        return [
            member.value for member in cls
        ]
