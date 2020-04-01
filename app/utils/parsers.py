from builtins import object
from re import compile
from collections import OrderedDict


class ReactionParser(object):
    """
    ReactionParser class, whose goal is to parse a reaction string in the format: A_c + B_c <-> P_c

    """

    def __init__(self):
        id_re = '[a-zA-Z]\w*'
        pos_float_re = '\d+(?:\.\d+)?(?:e[+-]?\d+)?'
        float_re = '-?\d+(?:\.\d+)?(?:e[+-]?\d+)?'

        compound = '(?:' + pos_float_re + '\s+)?' + id_re
        expression = compound + '(?:\s*\+\s*' + compound + ')*'
        bounds = '\[\s*(?P<lb>' + float_re + ')?\s*,\s*(?P<ub>' + float_re + ')?\s*\]'
        objective = '@' + float_re
        reaction ='\s*(?P<substrates>' + expression + ')?' + \
                   '\s*(?P<direction>-->|<->)' + \
                   '\s*(?P<products>' + expression + ')?' + \
                   '\s*(?P<bounds>' + bounds + ')?' + \
                   '\s*(?P<objective>' + objective + ')?$'

        self.regex_compound = compile('(?P<coeff>' + pos_float_re + '\s+)?(?P<met_id>' + id_re + ')')
        self.regex_bounds = compile(bounds)
        self.regex_reaction = compile(reaction)

    def parse_reaction(self, reaction_str):
        """
        Given a reaction string in the form A_c + B_c <-> P_c, parses it to retrieve its reversibility (True or False)
        and stoichiometry in the form of a dictionary {metabolite_id : stoichoimetric_coefficient}.

        Args:
            reaction_str: a reaction string in the form A_c + B_c <-> P_c

        Returns:
            reaction reverisibility (True or False), and stoichiometry dictionary
        """

        match = self.regex_reaction.match(reaction_str)

        if not match:
            raise SyntaxError('Unable to parse: ' + reaction_str)

        reversible = match.group('direction') == '<->'
        substrates = match.group('substrates')
        products = match.group('products')

        stoichiometry = OrderedDict()

        if substrates:
            left_coeffs = self.parse_coefficients(substrates, sense=-1.0)
            stoichiometry.update(left_coeffs)

        if products:
            right_coeffs = self.parse_coefficients(products, sense=1.0)
            for m_id, val in right_coeffs:
                if m_id in stoichiometry:
                    new_val = val + stoichiometry[m_id]
                    stoichiometry[m_id] = new_val
                else:
                    stoichiometry[m_id] = val

            return reversible, stoichiometry

    def parse_coefficients(self, expression, sense):
        """
        Parses the stoichiometric coefficients from expression.
        Expression has the form  2.0 metabolite_id.

        Args:
            expression: metabolite with respective stoichiometric coefficient, "2.0 metabolite_id"
            sense: whether the metabolite is consumed (-1) or produced (1)

        Returns:
            The stoichiometric coefficients
        """

        coefficients = []
        terms = expression.split('+')

        for term in terms:
            match = self.regex_compound.match(term.strip())
            coeff = sense * float(match.group('coeff')) if match.group('coeff') else sense
            m_id = match.group('met_id')
            coefficients.append((m_id, coeff))

        return coefficients


def parse_input_list(input_list, flag=True):
    """
    Given a string with several elements, converts them into a list by splitting the string by ' ', ', ', or ','.

    Args:
        input_list: a string with multiple elements separated by a space, a comma or a comma+space
        flag:

    Returns:
        list with the elements from the input.
    """

    input_list = input_list.strip()

    if input_list.find(', ') != -1:
        parsed_list = input_list.split(', ')
    elif input_list.find('; ') != -1:
        parsed_list = input_list.split('; ')
    elif input_list.find(' ') != -1:
        parsed_list = input_list.split(' ')
    elif input_list.find(',') != -1 and flag:
        parsed_list = input_list.split(',')
    elif input_list.find(';') != -1:
        parsed_list = input_list.split(';')
    else:
        parsed_list = [input_list]

    return parsed_list
