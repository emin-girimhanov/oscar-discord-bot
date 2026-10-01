""" This module builds links into the OVGU LSF course catalogue."""

from urllib.parse import quote


LSF_SEARCH_BASE: str = "https://lsf.ovgu.de/qislsf/rds"


def lsf_search_url(module_title: str) -> str:
    """ Builds a link to the public LSF course search for a module title.

        The LSF has no stable id for a module of the FIN module database, so we search
        by title instead. The search view is public and needs no login.

        Parameters:
            module_title: The module title to search for.

        Returns:
            An absolute `https` url. Falls back to the empty search when the title is blank.
    """
    title: str = module_title.strip()
    return (
        f"{LSF_SEARCH_BASE}?state=wsearchv&search=1"
        f"&veranstaltung.dtxt={quote(title, safe='')}"
    )
