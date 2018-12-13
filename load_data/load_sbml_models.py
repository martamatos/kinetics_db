""" This module implements methods for reading and writing SBML files.

Author: Daniel Machado

"""

import os
import re
import warnings
from builtins import object
from builtins import range
from collections import OrderedDict

from libsbml import SBMLReader

DEFAULT_SBML_LEVEL = 3
DEFAULT_SBML_VERSION = 1

CB_MODEL = 'cb'
ODE_MODEL = 'ode'

LB_TAG = 'LOWER_BOUND'
UB_TAG = 'UPPER_BOUND'
OBJ_TAG = 'OBJECTIVE_COEFFICIENT'
GPR_TAG = 'GENE_ASSOCIATION'

DEFAULT_LOWER_BOUND_ID = 'cobra_default_lb'
DEFAULT_UPPER_BOUND_ID = 'cobra_default_ub'
DEFAULT_ZERO_BOUND_ID = 'cobra_0_bound'

DEFAULT_LOWER_BOUND = -1000
DEFAULT_UPPER_BOUND = 1000

ACTIVATOR_TAG = 'SBO:0000459'
INHIBITOR_TAG = 'SBO:0000020'

non_alphanum = re.compile('\W+')
re_type = type(non_alphanum)


class Flavor(object):
    """ Enumeration of available model flavors. """

    COBRA = 'cobra'  # UCSD models in the old cobra toolbox format
    COBRA_OTHER = 'cobra:other'  # other models using the old cobra toolbox format
    SEED = 'seed'  # modelSEED format
    BIGG = 'bigg'  # BiGG database format (uses sbml-fbc2)
    FBC2 = 'fbc2'  # other models in sbml-fbc2 format


def load_sbml_model(filename, kind=None, flavor=None, exchange_detection_mode=None,
                    load_gprs=True, load_metadata=True):
    """ Loads a metabolic model from a file.

    Arguments:
        filename (str): SBML file path
        kind (str): define kind of model to load ('cb' or 'ode', optional)
        flavor (str): adapt to different modeling conventions (optional, see Notes)
        exchange_detection_mode (str): detect exchange reactions (optional, see Notes)

    Returns:
        Model: Simple model or respective subclass

    Notes:
        Currently supported flavors:
            * 'cobra': UCSD models in the old cobra toolbox format
            * 'cobra:other': other models using the old cobra toolbox format
            * 'seed': modelSEED format
            * 'bigg': BiGG database format (uses sbml-fbc2)
            * 'fbc2': other models using sbml-fbc2

        Supported exchange detection modes:
            * 'unbalanced': Exchange reactions is the one that have either only reactants or products
            * 'boundary': Exchange reaction is the one that have single boundary metabolite on one side
            * <regular expression pattern>: Regular expression which is executed against reaction ID

        Note that some flavors (cobra, bigg) have their own exchange detection mode.

    """
    if not os.path.exists(filename):
        raise IOError("Model file was not found")

    reader = SBMLReader()
    document = reader.readSBML(str(filename))
    sbml_model = document.getModel()

    if sbml_model is None:
        document.printErrors()
        raise IOError('Failed to load model {}.'.format(filename))

    if kind and kind.lower() == CB_MODEL:
        model = _load_cbmodel(sbml_model, flavor, exchange_detection_mode=exchange_detection_mode,
                              load_gprs=load_gprs, load_metadata=load_metadata)
    else:
        model = _load_stoichiometric_model(sbml_model)

    return model


def _load_stoichiometric_model(sbml_model):
    model = {'metabolites': [], 'reactions': [], 'genes': [], 'compartments': [], 'gpr': []}
    _load_compartments(sbml_model, model)
    _load_metabolites(sbml_model, model)
    _load_reactions(sbml_model, model)
    return model


def _load_compartments(sbml_model, model, load_metadata=True):
    for compartment in sbml_model.getListOfCompartments():
        model['compartments'].append(_load_compartment(compartment, load_metadata=load_metadata))


def _load_compartment(compartment, load_metadata=True):
    comp = (compartment.getId(), compartment.getName(), compartment.getSize())

    return comp


def _load_metabolites(sbml_model, model, flavor=None, load_metadata=True):
    for species in sbml_model.getListOfSpecies():
        model['metabolites'].append(_load_metabolite(species, flavor, load_metadata=load_metadata))


def load_sbml_metabolites(sbml_model, model, flavor=None, load_metadata=True):
    for species in sbml_model.getListOfSpecies():
        model.append(_load_metabolite(species, flavor, load_metadata=load_metadata))


def _load_metabolite(species, flavor=None, load_metadata=True):
    met_id = re.findall('M_(\w+)_', species.getId())
    metabolite = [met_id[0], species.getId(), species.getName(), species.getCompartment(),
                  species.getBoundaryCondition(), species.getConstant()]

    return metabolite


def _load_reactions(sbml_model, model, exchange_detection_mode=None, load_metadata=True):
    for reaction in sbml_model.getListOfReactions():
        r = _load_reaction(reaction, sbml_model=sbml_model, exchange_detection_mode=exchange_detection_mode,
                           load_metadata=load_metadata)
        model['reactions'].append(r)


def _load_reaction(reaction, sbml_model, exchange_detection_mode=None, load_metadata=True):
    """
    Args:
        reaction: <SBMLReaction> object
        exchange_detection_mode: Argument describing how to detect exchange reaction (possible values
            'unbalanced' - Exchange reactions is the one that have either only reactants or products
            'boundary' - Exchange reaction is the one that have single boundary metabolite on one side
            Regex object - Regular expression which is executed against reaction ID
            None - All reactions are NOT exchange reactions

    Returns:

    """

    stoichiometry = OrderedDict()
    modifiers = OrderedDict()

    for reactant in reaction.getListOfReactants():
        m_id = reactant.getSpecies()
        coeff = -reactant.getStoichiometry()
        if m_id not in stoichiometry:
            stoichiometry[m_id] = coeff
        else:
            stoichiometry[m_id] += coeff

    for product in reaction.getListOfProducts():
        m_id = product.getSpecies()
        coeff = product.getStoichiometry()
        if m_id not in stoichiometry:
            stoichiometry[m_id] = coeff
        else:
            stoichiometry[m_id] += coeff
        if stoichiometry[m_id] == 0.0:
            del stoichiometry[m_id]

    for modifier in reaction.getListOfModifiers():
        m_id = modifier.getSpecies()
        kind = '?'
        sboterm = modifier.getSBOTermID()
        if sboterm == ACTIVATOR_TAG:
            kind = '+'
        if sboterm == INHIBITOR_TAG:
            kind = '-'
        modifiers[m_id] = kind

    is_exchange = False
    if exchange_detection_mode == "unbalanced":
        sign = None
        is_exchange = True
        for m_id, c in stoichiometry.items():
            if sign is None:
                sign = c > 0
            else:
                if sign != c > 0:
                    is_exchange = False
    elif exchange_detection_mode == "boundary":
        products = {m_id for m_id, c in stoichiometry.items() if c > 0}
        reactants = {m_id for m_id, c in stoichiometry.items() if c < 0}
        boundary_products = {m_id for m_id in products if sbml_model.getSpecies(m_id).getBoundaryCondition()}
        is_exchange = (boundary_products and not (products - boundary_products))
        if not is_exchange:
            boundary_reactants = {m_id for m_id in products if sbml_model.getSpecies(m_id).getBoundaryCondition()}
            is_exchange = (boundary_reactants and not (reactants - boundary_reactants))
    elif exchange_detection_mode is None:
        pass
    else:
        is_exchange = exchange_detection_mode.match(reaction.getId()) is not None

    rxn = (reaction.getId(), reaction.getName(), reaction.getReversible(), stoichiometry, modifiers, is_exchange)

    return rxn


def _load_cbmodel(sbml_model, flavor, exchange_detection_mode=None, load_gprs=True, load_metadata=True):
    if exchange_detection_mode and exchange_detection_mode not in {None, 'unbalanced', 'boundary'}:
        try:
            exchange_detection_mode = re.compile(exchange_detection_mode)
        except:
            raise RuntimeError(
                "Exchange detection mode must be: 'unbalanced', 'boundary', or a valid regular expression.")

    if exchange_detection_mode is None:
        if flavor in {Flavor.COBRA, Flavor.BIGG}:
            exchange_detection_mode = re.compile('^R_EX')
        elif flavor in {Flavor.SEED}:
            exchange_detection_mode = re.compile('^EX_cpd')
        elif flavor in {Flavor.COBRA_OTHER}:
            exchange_detection_mode = 'boundary'
        elif flavor in {Flavor.FBC2}:
            exchange_detection_mode = 'unbalanced'

    model = {'metabolites': [], 'reactions': [], 'genes': [], 'compartments': [], 'gpr': []}
    _load_compartments(sbml_model, model, load_metadata=load_metadata)
    _load_metabolites(sbml_model, model, flavor, load_metadata=load_metadata)
    _load_reactions(sbml_model, model, exchange_detection_mode=exchange_detection_mode, load_metadata=load_metadata)

    if flavor in {Flavor.BIGG, Flavor.FBC2}:
        if load_gprs:
            _load_fbc2_gpr(sbml_model, model)
    else:
        raise TypeError("Unsupported SBML flavor: {}".format(flavor))

    return model


def _load_fbc2_gpr(sbml_model, model):
    fbcmodel = sbml_model.getPlugin('fbc')

    for gene in fbcmodel.getListOfGeneProducts():
        model['genes'].append((gene.getId(), gene.getName()))

    for reaction in sbml_model.getListOfReactions():
        fbcrxn = reaction.getPlugin('fbc')
        gpr_assoc = fbcrxn.getGeneProductAssociation()
        if gpr_assoc:
            gpr = _parse_fbc_association(gpr_assoc.getAssociation(), reaction.getId())
            model['gpr'].append((reaction.getId(), gpr))
        else:
            model['gpr'].append((reaction.getId(), None))


def _parse_fbc_association(gpr_assoc, reaction_id):
    parsing_error = False
    if gpr_assoc.isFbcOr():
        gpr = ['or']
        for item in gpr_assoc.getListOfAssociations():
            protein = []
            if item.isFbcAnd():
                for subitem in item.getListOfAssociations():
                    if subitem.isGeneProductRef():
                        protein.append(subitem.getGeneProduct())
                    else:
                        w = "Gene association for reaction '{}' is not DNF".format(reaction_id)
                        warnings.warn(w, SyntaxWarning)
                        parsing_error = True
            elif item.isGeneProductRef():
                protein.append(item.getGeneProduct())
            else:
                w = "Gene association for reaction '{}' is not DNF".format(reaction_id)
                warnings.warn(w, SyntaxWarning)
                parsing_error = True
            gpr.append(protein)

    elif gpr_assoc.isFbcAnd():
        gpr = ['and']
        protein = []
        for item in gpr_assoc.getListOfAssociations():
            if item.isGeneProductRef():
                protein.append(item.getGeneProduct())
            else:
                w = "Gene association for reaction '{}' is not DNF".format(reaction_id)
                warnings.warn(w, SyntaxWarning)
                parsing_error = True
        gpr.append(protein)

    elif gpr_assoc.isGeneProductRef():
        gpr = ['gpref']
        protein = [gpr_assoc.getGeneProduct()]
        gpr.append(protein)
    else:
        w = "Gene association for reaction '{}' is not DNF".format(reaction_id)
        warnings.warn(w, SyntaxWarning)
        parsing_error = True

    if not parsing_error:
        return gpr


def _load_metadata(sbml_elem, elem):
    notes = sbml_elem.getNotes()

    if notes:
        _recursive_node_parser(notes, elem.metadata)


def _recursive_node_parser(node, cache):
    node_data = node.getCharacters()
    if ':' in node_data:
        key, value = node_data.split(':', 1)
        cache[key.strip()] = value.strip()

    for i in range(node.getNumChildren()):
        _recursive_node_parser(node.getChild(i), cache)
