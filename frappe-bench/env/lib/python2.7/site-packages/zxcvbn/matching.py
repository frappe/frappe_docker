from itertools import groupby
import pkg_resources
import re

try:
    import simplejson as json
    json # silences pyflakes :<
except ImportError:
    import json


GRAPHS = {}
DICTIONARY_MATCHERS = []


def translate(string, chr_map):
    out = ''
    for char in string:
        out += chr_map[char] if char in chr_map else char
    return out

#-------------------------------------------------------------------------------
# dictionary match (common passwords, english, last names, etc) ----------------
#-------------------------------------------------------------------------------

def dictionary_match(password, ranked_dict):
    result = []
    length = len(password)

    pw_lower = password.lower()

    for i in xrange(0, length):
        for j in xrange(i, length):
            word = pw_lower[i:j+1]
            if word in ranked_dict:
                rank = ranked_dict[word]
                result.append( {'pattern':'dictionary',
                                'i' : i,
                                'j' : j,
                                'token' : password[i:j+1],
                                'matched_word' : word,
                                'rank': rank,
                               })
    return result


def _build_dict_matcher(dict_name, ranked_dict):
    def func(password):
        matches = dictionary_match(password, ranked_dict)
        for match in matches:
            match['dictionary_name'] = dict_name
        return matches
    return func


def _build_ranked_dict(unranked_list):
    result = {}
    i = 1
    for word in unranked_list:
        result[word] = i
        i += 1
    return result


def _load_frequency_lists():
    data = pkg_resources.resource_string(__name__, 'generated/frequency_lists.json')
    dicts = json.loads(data)
    for name, wordlist in dicts.items():
        DICTIONARY_MATCHERS.append(_build_dict_matcher(name, _build_ranked_dict(wordlist)))


def _load_adjacency_graphs():
    global GRAPHS
    data = pkg_resources.resource_string(__name__, 'generated/adjacency_graphs.json')
    GRAPHS = json.loads(data)


# on qwerty, 'g' has degree 6, being adjacent to 'ftyhbv'. '\' has degree 1.
# this calculates the average over all keys.
def _calc_average_degree(graph):
    average = 0.0
    for neighbors in graph.values():
        average += len([n for n in neighbors if n is not None])

    average /= len(graph)
    return average


_load_frequency_lists()
_load_adjacency_graphs()

KEYBOARD_AVERAGE_DEGREE = _calc_average_degree(GRAPHS[u'qwerty'])

# slightly different for keypad/mac keypad, but close enough
KEYPAD_AVERAGE_DEGREE = _calc_average_degree(GRAPHS[u'keypad'])

KEYBOARD_STARTING_POSITIONS = len(GRAPHS[u'qwerty'])
KEYPAD_STARTING_POSITIONS = len(GRAPHS[u'keypad'])


#-------------------------------------------------------------------------------
# dictionary match with common l33t substitutions ------------------------------
#-------------------------------------------------------------------------------

L33T_TABLE = {
  'a': ['4', '@'],
  'b': ['8'],
  'c': ['(', '{', '[', '<'],
  'e': ['3'],
  'g': ['6', '9'],
  'i': ['1', '!', '|'],
  'l': ['1', '|', '7'],
  'o': ['0'],
  's': ['$', '5'],
  't': ['+', '7'],
  'x': ['%'],
  'z': ['2'],
}

# makes a pruned copy of L33T_TABLE that only includes password's possible substitutions
def relevant_l33t_subtable(password):
    password_chars = set(password)

    filtered = {}
    for letter, subs in L33T_TABLE.items():
        relevent_subs = [sub for sub in subs if sub in password_chars]
        if len(relevent_subs) > 0:
            filtered[letter] = relevent_subs
    return filtered

# returns the list of possible 1337 replacement dictionaries for a given password

def enumerate_l33t_subs(table):
    subs = [[]]

    def dedup(subs):
        deduped = []
        members = set()
        for sub in subs:
            key = str(sorted(sub))
            if key not in members:
                deduped.append(sub)
        return deduped

    keys = table.keys()
    while len(keys) > 0:
        first_key = keys[0]
        rest_keys = keys[1:]
        next_subs = []
        for l33t_chr in table[first_key]:
            for sub in subs:
                dup_l33t_index = -1
                for i in range(0, len(sub)):
                    if sub[i][0] == l33t_chr:
                        dup_l33t_index = i
                        break
                if dup_l33t_index == -1:
                    sub_extension = list(sub)
                    sub_extension.append((l33t_chr, first_key))
                    next_subs.append(sub_extension)
                else:
                    sub_alternative = list(sub)
                    sub_alternative.pop(dup_l33t_index)
                    sub_alternative.append((l33t_chr, first_key))
                    next_subs.append(sub)
                    next_subs.append(sub_alternative)
        subs = dedup(next_subs)
        keys = rest_keys
    return map(dict, subs)


def l33t_match(password):
    matches = []

    for sub in enumerate_l33t_subs(relevant_l33t_subtable(password)):
        if len(sub) == 0:
            break
        subbed_password = translate(password, sub)
        for matcher in DICTIONARY_MATCHERS:
            for match in matcher(subbed_password):
                token = password[match['i']:match['j'] + 1]
                if token.lower() == match['matched_word']:
                    continue
                match_sub = {}
                for subbed_chr, char in sub.items():
                    if token.find(subbed_chr) != -1:
                        match_sub[subbed_chr] = char
                match['l33t'] = True
                match['token'] = token
                match['sub'] = match_sub
                match['sub_display'] = ', '.join([("%s -> %s" % (k, v)) for k, v in match_sub.items()])
                matches.append(match)
    return matches

# ------------------------------------------------------------------------------
# spatial match (qwerty/dvorak/keypad) -----------------------------------------
# ------------------------------------------------------------------------------

def spatial_match(password):
    matches = []
    for graph_name, graph in GRAPHS.items():
        matches.extend(spatial_match_helper(password, graph, graph_name))
    return matches


def spatial_match_helper(password, graph, graph_name):
    result = []
    i = 0
    while i < len(password) - 1:
        j = i + 1
        last_direction = None
        turns = 0
        shifted_count = 0
        while True:
            prev_char = password[j-1]
            found = False
            found_direction = -1
            cur_direction = -1
            adjacents = graph[prev_char] if prev_char in graph else []
            # consider growing pattern by one character if j hasn't gone over the edge.
            if j < len(password):
                cur_char = password[j]
                for adj in adjacents:
                    cur_direction += 1
                    if adj and adj.find(cur_char) != -1:
                        found = True
                        found_direction = cur_direction
                        if adj.find(cur_char) == 1:
                            # index 1 in the adjacency means the key is shifted, 0 means unshifted: A vs a, % vs 5, etc.
                            # for example, 'q' is adjacent to the entry '2@'. @ is shifted w/ index 1, 2 is unshifted.
                            shifted_count += 1
                        if last_direction != found_direction:
                            # adding a turn is correct even in the initial case when last_direction is null:
                            # every spatial pattern starts with a turn.
                            turns += 1
                            last_direction = found_direction
                        break
            # if the current pattern continued, extend j and try to grow again
            if found:
                j += 1
            # otherwise push the pattern discovered so far, if any...
            else:
                if j - i > 2: # don't consider length 1 or 2 chains.
                    result.append({
                        'pattern': 'spatial',
                        'i': i,
                        'j': j-1,
                        'token': password[i:j],
                        'graph': graph_name,
                        'turns': turns,
                        'shifted_count': shifted_count,
                    })
                # ...and then start a new search for the rest of the password.
                i = j
                break
    return result

#-------------------------------------------------------------------------------
# repeats (aaa) and sequences (abcdef) -----------------------------------------
#-------------------------------------------------------------------------------

def repeat_match(password):
    result = []
    repeats = groupby(password)
    i = 0
    for char, group in repeats:
        length = len(list(group))
        if length > 2:
            j = i + length - 1
            result.append({
                'pattern': 'repeat',
                'i': i,
                'j': j,
                'token': password[i:j+1],
                'repeated_char': char,
            })
        i += length
    return result


SEQUENCES = {
    'lower': 'abcdefghijklmnopqrstuvwxyz',
    'upper': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
   'digits': '01234567890',
}


def sequence_match(password):
    result = []
    i = 0
    while i < len(password):
        j = i + 1
        seq = None           # either lower, upper, or digits
        seq_name = None
        seq_direction = None # 1 for ascending seq abcd, -1 for dcba
        for seq_candidate_name, seq_candidate in SEQUENCES.items():
            i_n = seq_candidate.find(password[i])
            j_n = seq_candidate.find(password[j]) if j < len(password) else -1

            if i_n > -1 and j_n > -1:
                direction = j_n - i_n
                if direction in [1, -1]:
                    seq = seq_candidate
                    seq_name = seq_candidate_name
                    seq_direction = direction
                    break
        if seq:
            while True:
                if j <  len(password):
                    prev_char, cur_char = password[j-1], password[j]
                    prev_n, cur_n = seq_candidate.find(prev_char), seq_candidate.find(cur_char)
                if j == len(password) or cur_n - prev_n != seq_direction:
                    if j - i > 2: # don't consider length 1 or 2 chains.
                        result.append({
                            'pattern': 'sequence',
                            'i': i,
                            'j': j-1,
                            'token': password[i:j],
                            'sequence_name': seq_name,
                            'sequence_space': len(seq),
                            'ascending': seq_direction    == 1,
                        })
                    break
                else:
                    j += 1
        i = j
    return result

#-------------------------------------------------------------------------------
# digits, years, dates ---------------------------------------------------------
#-------------------------------------------------------------------------------

def match_all(password, pattern_name, regex):
    out = []
    for match in regex.finditer(password):
        i = match.start()
        j = match.end()
        out.append({
            'pattern' : pattern_name,
            'i' : i,
            'j' : j,
            'token' : password[i:j+1]
        })
    return out


DIGITS_MATCH = re.compile(r'\d{3,}')
def digits_match(password):
    return match_all(password, 'digits', DIGITS_MATCH)


YEAR_MATCH = re.compile(r'19\d\d|200\d|201\d')
def year_match(password):
    return match_all(password, 'year', YEAR_MATCH)


def date_match(password):
    l = date_without_sep_match(password)
    l.extend(date_sep_match(password))
    return l


DATE_WITHOUT_SEP_MATCH = re.compile(r'\d{4,8}')
def date_without_sep_match(password):
    date_matches = []
    for digit_match in DATE_WITHOUT_SEP_MATCH.finditer(password):
        i, j = digit_match.start(), digit_match.end()
        token = password[i:j+1]
        end = len(token)
        candidates_round_1 = [] # parse year alternatives
        if len(token) <= 6:
            # 2-digit year prefix
            candidates_round_1.append({
                'daymonth': token[2:],
                'year': token[0:2],
                'i': i,
                'j': j,
            })

            # 2-digit year suffix
            candidates_round_1.append({
                'daymonth': token[0:end-2],
                'year': token[end-2:],
                'i': i,
                'j': j,
            })
        if len(token) >= 6:
            # 4-digit year prefix
            candidates_round_1.append({
                'daymonth': token[4:],
                'year': token[0:4],
                'i': i,
                'j': j,
            })
            # 4-digit year suffix
            candidates_round_1.append({
                'daymonth': token[0:end-4],
                'year': token[end-4:],
                'i': i,
                'j': j,
            })
        candidates_round_2 = [] # parse day/month alternatives
        for candidate in candidates_round_1:
            if len(candidate['daymonth']) == 2: # ex. 1 1 97
                candidates_round_2.append({
                    'day': candidate['daymonth'][0],
                    'month': candidate['daymonth'][1],
                    'year': candidate['year'],
                    'i': candidate['i'],
                    'j': candidate['j'],
                })
            elif len(candidate['daymonth']) == 3: # ex. 11 1 97 or 1 11 97
                candidates_round_2.append({
                    'day': candidate['daymonth'][0:2],
                    'month': candidate['daymonth'][2],
                    'year': candidate['year'],
                    'i': candidate['i'],
                    'j': candidate['j'],
                })
                candidates_round_2.append({
                    'day': candidate['daymonth'][0],
                    'month': candidate['daymonth'][1:3],
                    'year': candidate['year'],
                    'i': candidate['i'],
                    'j': candidate['j'],
                })
            elif len(candidate['daymonth']) == 4: # ex. 11 11 97
                candidates_round_2.append({
                    'day': candidate['daymonth'][0:2],
                    'month': candidate['daymonth'][2:4],
                    'year': candidate['year'],
                    'i': candidate['i'],
                    'j': candidate['j'],
                })
        # final loop: reject invalid dates
        for candidate in candidates_round_2:
            try:
                day = int(candidate['day'])
                month = int(candidate['month'])
                year = int(candidate['year'])
            except ValueError:
                continue
            valid, (day, month, year) = check_date(day, month, year)
            if not valid:
                continue
            date_matches.append( {
                'pattern': 'date',
                'i': candidate['i'],
                'j': candidate['j'],
                'token': password[i:j+1],
                'separator': '',
                'day': day,
                'month': month,
                'year': year,
            })
    return date_matches


DATE_RX_YEAR_SUFFIX = re.compile(r"(\d{1,2})(\s|-|/|\\|_|\.)(\d{1,2})\2(19\d{2}|200\d|201\d|\d{2})")
#DATE_RX_YEAR_SUFFIX = "(\d{1,2})(\s|-|/|\\|_|\.)"
DATE_RX_YEAR_PREFIX = re.compile(r"(19\d{2}|200\d|201\d|\d{2})(\s|-|/|\\|_|\.)(\d{1,2})\2(\d{1,2})")


def date_sep_match(password):
    matches = []
    for match in DATE_RX_YEAR_SUFFIX.finditer(password):
        day, month, year = tuple(int(match.group(x)) for x in [1, 3, 4])
        matches.append( {
            'day' : day,
            'month' : month,
            'year' : year,
            'sep' : match.group(2),
            'i' : match.start(),
            'j' : match.end()
        })
    for match in DATE_RX_YEAR_PREFIX.finditer(password):
        day, month, year = tuple(int(match.group(x)) for x in [4, 3, 1])
        matches.append( {
            'day' : day,
            'month' : month,
            'year' : year,
            'sep' : match.group(2),
            'i' : match.start(),
            'j' : match.end()
        })
    out = []
    for match in matches:
        valid, (day, month, year) = check_date(match['day'], match['month'], match['year'])
        if not valid:
            continue
        out.append({
            'pattern': 'date',
            'i': match['i'],
            'j': match['j']-1,
            'token': password[match['i']:match['j']],
            'separator': match['sep'],
            'day': day,
            'month': month,
            'year': year,
        })
    return out


def check_date(day, month, year):
    if 12 <= month <= 31 and day <= 12: # tolerate both day-month and month-day order
        day, month = month, day

    if day > 31 or month > 12:
        return (False, (0, 0, 0))

    if not (1900 <= year <= 2019):
        return (False, (0, 0, 0))

    return (True, (day, month, year))


MATCHERS = list(DICTIONARY_MATCHERS)
MATCHERS.extend([
    l33t_match,
    digits_match, year_match, date_match,
    repeat_match, sequence_match,
    spatial_match
])


def omnimatch(password, user_inputs=None):
    ranked_user_inputs_dict = {}
    for i, user_input in enumerate(user_inputs or []):
        ranked_user_inputs_dict[user_input] = i+1
    user_input_matcher = _build_dict_matcher('user_inputs', ranked_user_inputs_dict)
    matches = user_input_matcher(password)
    for matcher in MATCHERS:
        matches.extend(matcher(password))
    matches.sort(key=lambda x : (x['i'], x['j']))
    return matches
