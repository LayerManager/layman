from . import IS_PUBLICATION_COMPLETE_AND_CONSISTENT
from ... import util


def is_publication_valid_and_complete(publication):
    for action in IS_PUBLICATION_COMPLETE_AND_CONSISTENT[publication.type]:
        util.run_action(publication, action)
