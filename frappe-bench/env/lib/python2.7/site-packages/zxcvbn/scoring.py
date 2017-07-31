import math
import re

from zxcvbn.matching import (KEYBOARD_STARTING_POSITIONS, KEYBOARD_AVERAGE_DEGREE,
                             KEYPAD_STARTING_POSITIONS, KEYPAD_AVERAGE_DEGREE)

def binom(n, k):
    """
    Returns binomial coefficient (n choose k).
    """
    # http://blog.plover.com/math/choose.html
    if k > n:
        return 0
    if k == 0:
        return 1
    result = 1
    for denom in range(1, k + 1):
        result *= n
        result /= denom
        n -= 1
    return result


def lg(n):
    """
    Returns logarithm of n in base 2.
    """
    return math.log(n, 2)

# ------------------------------------------------------------------------------
# minimum entropy search -------------------------------------------------------
# ------------------------------------------------------------------------------
#
# takes a list of overlapping matches, returns the non-overlapping sublist with
# minimum entropy. O(nm) dp alg for length-n password with m candidate matches.
# ------------------------------------------------------------------------------
def get(a, i):
    if i < 0 or i >= len(a):
        return 0
    return a[i]


def minimum_entropy_match_sequence(password, matches):
    """
    Returns minimum entropy

    Takes a list of overlapping matches, returns the non-overlapping sublist with
    minimum entropy. O(nm) dp alg for length-n password with m candidate matches.
    """
    bruteforce_cardinality = calc_bruteforce_cardinality(password) # e.g. 26 for lowercase
    up_to_k = [0] * len(password) # minimum entropy up to k.
    # for the optimal sequence of matches up to k, holds the final match (match['j'] == k). null means the sequence ends
    # without a brute-force character.
    backpointers = []
    for k in range(0, len(password)):
        # starting scenario to try and beat: adding a brute-force character to the minimum entropy sequence at k-1.
        up_to_k[k] = get(up_to_k, k-1) + lg(bruteforce_cardinality)
        backpointers.append(None)
        for match in matches:
            if match['j'] != k:
                continue
            i, j = match['i'], match['j']
            # see if best entropy up to i-1 + entropy of this match is less than the current minimum at j.
            up_to = get(up_to_k, i-1)
            candidate_entropy = up_to + calc_entropy(match)
            if candidate_entropy < up_to_k[j]:
                #print "New minimum: using " + str(match)
                #print "Entropy: " + str(candidate_entropy)
                up_to_k[j] = candidate_entropy
                backpointers[j] = match

    # walk backwards and decode the best sequence
    match_sequence = []
    k = len(password) - 1
    while k >= 0:
        match = backpointers[k]
        if match:
            match_sequence.append(match)
            k = match['i'] - 1
        else:
            k -= 1
    match_sequence.reverse()

    # fill in the blanks between pattern matches with bruteforce "matches"
    # that way the match sequence fully covers the password: match1.j == match2.i - 1 for every adjacent match1, match2.
    def make_bruteforce_match(i, j):
        return {
            'pattern': 'bruteforce',
            'i': i,
            'j': j,
            'token': password[i:j+1],
            'entropy': lg(math.pow(bruteforce_cardinality, j - i + 1)),
            'cardinality': bruteforce_cardinality,
        }
    k = 0
    match_sequence_copy = []
    for match in match_sequence:
        i, j = match['i'], match['j']
        if i - k > 0:
            match_sequence_copy.append(make_bruteforce_match(k, i - 1))
        k = j + 1
        match_sequence_copy.append(match)

    if k < len(password):
        match_sequence_copy.append(make_bruteforce_match(k, len(password) - 1))
    match_sequence = match_sequence_copy

    min_entropy = 0 if len(password) == 0 else up_to_k[len(password) - 1] # corner case is for an empty password ''
    crack_time = entropy_to_crack_time(min_entropy)

    # final result object
    return {
        'password': password,
        'entropy': round_to_x_digits(min_entropy, 3),
        'match_sequence': match_sequence,
        'crack_time': round_to_x_digits(crack_time, 3),
        'crack_time_display': display_time(crack_time),
        'score': crack_time_to_score(crack_time),
    }


def round_to_x_digits(number, digits):
    """
    Returns 'number' rounded to 'digits' digits.
    """
    return round(number * math.pow(10, digits)) / math.pow(10, digits)

# ------------------------------------------------------------------------------
# threat model -- stolen hash catastrophe scenario -----------------------------
# ------------------------------------------------------------------------------
#
# assumes:
# * passwords are stored as salted hashes, different random salt per user.
#   (making rainbow attacks infeasable.)
# * hashes and salts were stolen. attacker is guessing passwords at max rate.
# * attacker has several CPUs at their disposal.
# ------------------------------------------------------------------------------

# for a hash function like bcrypt/scrypt/PBKDF2, 10ms per guess is a safe lower bound.
# (usually a guess would take longer -- this assumes fast hardware and a small work factor.)
# adjust for your site accordingly if you use another hash function, possibly by
# several orders of magnitude!
SINGLE_GUESS = .010
NUM_ATTACKERS = 100 # number of cores guessing in parallel.

SECONDS_PER_GUESS = SINGLE_GUESS / NUM_ATTACKERS


def entropy_to_crack_time(entropy):
    return (0.5 * math.pow(2, entropy)) * SECONDS_PER_GUESS # average, not total


def crack_time_to_score(seconds):
    if seconds < math.pow(10, 2):
        return 0
    if seconds < math.pow(10, 4):
        return 1
    if seconds < math.pow(10, 6):
        return 2
    if seconds < math.pow(10, 8):
        return 3
    return 4

# ------------------------------------------------------------------------------
# entropy calcs -- one function per match pattern ------------------------------
# ------------------------------------------------------------------------------

def calc_entropy(match):
    if 'entropy' in match: return match['entropy']

    if match['pattern'] == 'repeat':
        entropy_func = repeat_entropy
    elif match['pattern'] == 'sequence':
        entropy_func = sequence_entropy
    elif match['pattern'] == 'digits':
        entropy_func = digits_entropy
    elif match['pattern'] == 'year':
        entropy_func = year_entropy
    elif match['pattern'] == 'date':
        entropy_func = date_entropy
    elif match['pattern'] == 'spatial':
        entropy_func = spatial_entropy
    elif match['pattern'] == 'dictionary':
        entropy_func = dictionary_entropy
    match['entropy'] = entropy_func(match)
    return match['entropy']


def repeat_entropy(match):
    cardinality = calc_bruteforce_cardinality(match['token'])
    return lg(cardinality * len(match['token']))


def sequence_entropy(match):
    first_chr = match['token'][0]
    if first_chr in ['a', '1']:
        base_entropy = 1
    else:
        if first_chr.isdigit():
            base_entropy = lg(10) # digits
        elif first_chr.isalpha():
            base_entropy = lg(26) # lower
        else:
            base_entropy = lg(26) + 1 # extra bit for uppercase
    if not match['ascending']:
        base_entropy += 1 # extra bit for descending instead of ascending
    return base_entropy + lg(len(match['token']))


def digits_entropy(match):
    return lg(math.pow(10, len(match['token'])))


NUM_YEARS = 119 # years match against 1900 - 2019
NUM_MONTHS = 12
NUM_DAYS = 31


def year_entropy(match):
    return lg(NUM_YEARS)


def date_entropy(match):
    if match['year'] < 100:
        entropy = lg(NUM_DAYS * NUM_MONTHS * 100) # two-digit year
    else:
        entropy = lg(NUM_DAYS * NUM_MONTHS * NUM_YEARS) # four-digit year

    if match['separator']:
        entropy += 2 # add two bits for separator selection [/,-,.,etc]
    return entropy


def spatial_entropy(match):
    if match['graph'] in ['qwerty', 'dvorak']:
        s = KEYBOARD_STARTING_POSITIONS
        d = KEYBOARD_AVERAGE_DEGREE
    else:
        s = KEYPAD_STARTING_POSITIONS
        d = KEYPAD_AVERAGE_DEGREE
    possibilities = 0
    L = len(match['token'])
    t = match['turns']
    # estimate the number of possible patterns w/ length L or less with t turns or less.
    for i in range(2, L + 1):
        possible_turns = min(t, i - 1)
        for j in range(1, possible_turns+1):
            x =  binom(i - 1, j - 1) * s * math.pow(d, j)
            possibilities += x
    entropy = lg(possibilities)
    # add extra entropy for shifted keys. (% instead of 5, A instead of a.)
    # math is similar to extra entropy from uppercase letters in dictionary matches.
    if 'shifted_count' in match:
        S = match['shifted_count']
        U = L - S # unshifted count
        possibilities = sum(binom(S + U, i) for i in xrange(0, min(S, U) + 1))
        entropy += lg(possibilities)
    return entropy


def dictionary_entropy(match):
    match['base_entropy'] = lg(match['rank']) # keep these as properties for display purposes
    match['uppercase_entropy'] = extra_uppercase_entropy(match)
    match['l33t_entropy'] = extra_l33t_entropy(match)
    ret = match['base_entropy'] + match['uppercase_entropy'] + match['l33t_entropy']
    return ret


START_UPPER = re.compile('^[A-Z][^A-Z]+$')
END_UPPER = re.compile('^[^A-Z]+[A-Z]$')
ALL_UPPER = re.compile('^[A-Z]+$')


def extra_uppercase_entropy(match):
    word = match['token']
    if word.islower():
        return 0
    # a capitalized word is the most common capitalization scheme,
    # so it only doubles the search space (uncapitalized + capitalized): 1 extra bit of entropy.
    # allcaps and end-capitalized are common enough too, underestimate as 1 extra bit to be safe.
    for regex in [START_UPPER, END_UPPER, ALL_UPPER]:
        if regex.match(word):
            return 1
    # Otherwise calculate the number of ways to capitalize U+L uppercase+lowercase letters with U uppercase letters or
    # less. Or, if there's more uppercase than lower (for e.g. PASSwORD), the number of ways to lowercase U+L letters
    # with L lowercase letters or less.
    upp_len = len([x for x in word if x.isupper()])
    low_len = len([x for x in word if x.islower()])
    possibilities = sum(binom(upp_len + low_len, i) for i in range(0, min(upp_len, low_len) + 1))
    return lg(possibilities)


def extra_l33t_entropy(match):
    if 'l33t' not in match or not match['l33t']:
        return 0
    possibilities = 0
    for subbed, unsubbed in match['sub'].items():
        sub_len = len([x for x in match['token'] if x == subbed])
        unsub_len = len([x for x in match['token'] if x == unsubbed])
        possibilities += sum(binom(unsub_len + sub_len, i) for i in range(0, min(unsub_len, sub_len) + 1))
    # corner: return 1 bit for single-letter subs, like 4pple -> apple, instead of 0.
    if possibilities <= 1:
        return 1
    return lg(possibilities)

# utilities --------------------------------------------------------------------

def calc_bruteforce_cardinality(password):
    lower, upper, digits, symbols = False, False, False, False
    for char in password:
        if char.islower():
            lower = True
        elif char.isdigit():
            digits = True
        elif char.isupper():
            upper = True
        else:
            symbols = True
    cardinality = 0
    if digits:
        cardinality += 10
    if upper:
        cardinality += 26
    if lower:
        cardinality += 26
    if symbols:
        cardinality += 33
    return cardinality


def display_time(seconds):
    minute = 60
    hour = minute * 60
    day = hour * 24
    month = day * 31
    year = month * 12
    century = year * 100
    if seconds < minute:
        return 'instant'
    elif seconds < hour:
        return str(1 + math.ceil(seconds / minute)) + " minutes"
    elif seconds < day:
        return str(1 + math.ceil(seconds / hour)) + " hours"
    elif seconds < month:
        return str(1 + math.ceil(seconds / day)) + " days"
    elif seconds < year:
        return str(1 + math.ceil(seconds / month)) + " months"
    elif seconds < century:
        return str(1 + math.ceil(seconds / year)) + " years"
    else:
        return 'centuries'
