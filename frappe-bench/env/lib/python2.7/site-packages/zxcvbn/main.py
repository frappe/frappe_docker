import time

from zxcvbn.matching import omnimatch
from zxcvbn.scoring import minimum_entropy_match_sequence


def password_strength(password, user_inputs=None):
    start = time.time()
    matches = omnimatch(password, user_inputs)
    result = minimum_entropy_match_sequence(password, matches)
    result['calc_time'] = time.time() - start
    return result
