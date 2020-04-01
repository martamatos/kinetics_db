import pandas as pd


def get_model_name(file_path, sheet_name):
    """
    Return the model name, which is assumed to be in the first row, second column of the sheet_name.

    Args:
        file_path: path to file containing the model
        sheet_name: sheet_name: name of the excel sheet where the model name is, should be 'general'

    Returns:
        Model name
    """

    data_df = pd.read_excel(file_path, sheet_name=sheet_name)
    model_name = data_df.iloc[0, 1]

    return model_name


def get_model_stoichiometry(file_path, sheet_name):
    """
    Gets the reaction strings from the stoichiometry matrix defined in the GRASP input models.

    Args:
        file_path: path to file containing the model
        sheet_name: name of the excel sheet where the model stoichiometry is, should be 'stoic'

    Returns:
        mets list, rxns lists, rxn_strings list
    """

    data_df = pd.read_excel(file_path, sheet_name=sheet_name, index_col=0, header=0)
    data_df = data_df.fillna('')
    rxn_strings = []

    for row in data_df.index:

        subs_entries = data_df.loc[row][data_df.loc[row].lt(0)]
        sub_stoic_coeffs = subs_entries.values
        subs = subs_entries.index.values

        prod_entries = data_df.loc[row][data_df.loc[row].gt(0)]
        prod_stoic_coeffs = prod_entries.values
        prods = prod_entries.index.values

        subs_with_coeffs = [' '.join([str(abs(coef)), met]) for coef, met in zip(sub_stoic_coeffs, subs)]
        subs_part = ' + '.join(subs_with_coeffs)

        prods_with_coeffs = [' '.join([str(abs(coef)), met]) for coef, met in zip(prod_stoic_coeffs, prods)]
        prods_part = ' + '.join(prods_with_coeffs)

        rxn_string = ' <-> '.join([subs_part, prods_part])
        rxn_strings.append(rxn_string)

    mets = data_df.columns.values
    rxns = data_df.index.values

    return mets, rxns, rxn_strings


def get_model_enzymes(file_path, sheet_name):
    """
    Imports the list of enzymes associated to each reaction in the model

    Args:
        file_path: path to file containing the model
        sheet_name: name of the excel sheet where the model enzymes are, should be 'enzyme_reaction'

    Returns:
        enzyme list
    """

    data_df = pd.read_excel(file_path, sheet_name=sheet_name, index_col=None, header=0)
    data_df = data_df.fillna('')

    enzyme_list = []

    for row in data_df.index:
        enzyme_list.append(data_df.loc[row].to_dict())

    return enzyme_list


def get_model_subunits(file_path, sheet_name):
    """
    Gets the columns reaction ID and subunits and returns a tuple (reaction ID, subunits).

    Args:
        file_path: path to file containing the model
        sheet_name: name of the excel sheet where the enzyme subunits specification is, should be 'kinetics1'

    Returns:
        subunit_dict with the form {rxn: number_of_subunits}
    """

    data_df = pd.read_excel(file_path, sheet_name=sheet_name, index_col=None, header=0)
    data_df = data_df.fillna('')

    subunit_dict = dict((rxn, n_subunits) for rxn, n_subunits in zip(data_df['reaction ID'].values, data_df['subunits'].values))

    return subunit_dict


def get_model_mechanisms(file_path, sheet_name):
    """
    From the kinetics1 sheet, gets the kinetic mechanisms, respective substrate binding order and product release order,
    as well as references for each mechanism and returns a dictionary
     {rxn_id : (mechanism, [mech_order], [mech_references])}.  Entry i in mech_references contains all references
      for the mechanism, and mech_order contains the order of substrate binding and product release.

    Args:
        file_path: path to file containing the model
        sheet_name: name of the excel sheet where the reaction mechanism specification is, should be 'kinetics1'

    Returns:
        mechanisms_dict of the form:
         {rxn_id: [mechanism name, [substrates binding order], [products release order], [references]]}
    """

    data_df = pd.read_excel(file_path, sheet_name=sheet_name, index_col=None, header=0)
    data_df['mechanism_refs'] = data_df['mechanism_refs'].fillna('')

    model_mechanisms = data_df['kinetic mechanism'].values
    substrate_order = [mech_order.split(' ') if isinstance(mech_order, str) else [] for mech_order in data_df['substrate order'].values]
    product_order = [mech_order.split(' ') if isinstance(mech_order, str) else [] for mech_order in data_df['product order'].values]
    #model_mechanisms_refs = [mech_refs.split(' ') if isinstance(mech_refs, str) else [] for mech_refs in data_df['mechanisms_refs'].values]
    mechanisms_dict = dict([(rxn_id, mechs_and_ref) for rxn_id, mechs_and_ref in zip(data_df['reaction ID'].values, zip(model_mechanisms, substrate_order, product_order, data_df['mechanism_refs'].values))])

    return mechanisms_dict


def get_model_inhibitors(file_path, sheet_name):
    """
    Gets the inhibitors and respective references for each reaction on the kinetics1 sheet and returns a dictionary
     {rxn_id : ([inhibitor_list], [inhib_references])}.  Entry i in inhib_references contains all references as a string
      for inhibition i in inhibitor_list. If there are multiple references for the same inhibition these are still
      contained in the same string in entry i of inhib_references, where the reference strings are separated  by a space.


    Args:
        file_path: path to file containing the model
        sheet_name: name of the excel sheet where the reaction inhibitors specification is, should be 'kinetics1'

    Returns:
        inhibitors_dict of the form {rxn_id: [[inhibitors], [reference types], [references]]}
    """

    data_df = pd.read_excel(file_path, sheet_name=sheet_name, index_col=None, header=0)

    model_inhibitors = [inhib_list.split(' ') if isinstance(inhib_list, str) else [] for inhib_list in data_df['inhibitors'].values]
    model_inhibitors_refs_type = [inhib_refs_type.split(';') if isinstance(inhib_refs_type, str) else [] for inhib_refs_type in data_df['inhibitors_refs_type'].values]
    model_inhibitors_refs = [inhib_refs.split(';') if isinstance(inhib_refs, str) else [] for inhib_refs in data_df['inhibitors_refs'].values]
    inhibitors_dict = dict([(rxn_id, inhib_and_ref) for rxn_id, inhib_and_ref in zip(data_df['reaction ID'].values, zip(model_inhibitors, model_inhibitors_refs_type, model_inhibitors_refs))])

    return inhibitors_dict


def get_model_activators(file_path, sheet_name):
    """
    Gets the activators and respective references for each reaction on the kinetics1 sheet and returns a dictionary
     {rxn_id : ([activator_list], [activ_references])}.  Entry i in activ_references contains all references as a string
      for activation i in activator_list. If there are multiple references for the same activation these are still
      contained in the same string in entry i of activ_references, where the reference strings are separated  by a space.

    Args:
        file_path: path to file containing the model
        sheet_name: name of the excel sheet where the reaction activators specification is, should be 'kinetics1'

    Returns:
        activators_dict of the form {rxn_id: [[activators], [reference types], [references]]}
    """

    data_df = pd.read_excel(file_path, sheet_name=sheet_name, index_col=None, header=0)

    model_activators = [activ_list.split(' ') if isinstance(activ_list, str) else [] for activ_list in data_df['activators'].values]
    model_activators_refs_type = [activ_refs_type.split(';') if isinstance(activ_refs_type, str) else [] for activ_refs_type in data_df['activators_refs_type'].values]
    model_activators_refs = [activ_refs.split(';') if isinstance(activ_refs, str) else [] for activ_refs in data_df['activators_refs'].values]
    activators_dict = dict([(rxn_id, activ_and_ref) for rxn_id, activ_and_ref in zip(data_df['reaction ID'].values, zip(model_activators, model_activators_refs_type, model_activators_refs))])

    return activators_dict


def get_model_effectors(file_path, sheet_name):
    """
    Gets the effectors and respective references for each reaction on the kinetics1 sheet and returns a dictionary
     {rxn_id : ([effector_list], [effector_references])}.  Entry i in effector_references contains all references as a
      string for effector i in effector_list. If there are multiple references for the same effector these are
      still contained in the same string in entry i of effector_references, where the reference strings are separated
      by a space.
      In the end two different dictionaries are returned, one for positive effectors and another for negative effectors.

    Args:
        file_path: path to file containing the model
        sheet_name: name of the excel sheet where the reaction effectors specification is, should be 'kinetics1'

    Returns:
        neg_effectors_dict and pos_effectors_dict of the form: {rxn_id: [[effectors], [reference types], [references]]}
    """

    data_df = pd.read_excel(file_path, sheet_name=sheet_name, index_col=None, header=0)

    model_neg_effectors = [neg_effectors_list.split(' ') if isinstance(neg_effectors_list, str) else [] for neg_effectors_list in data_df['negative effectors'].values]
    model_neg_eff_refs_type = [neg_eff_refs_type.split(';') if isinstance(neg_eff_refs_type, str) else [] for neg_eff_refs_type in data_df['negative_effectors_refs_type'].values]
    model_neg_eff_refs = [neg_eff_refs.split(';') if isinstance(neg_eff_refs, str) else [] for neg_eff_refs in data_df['negative_effectors_refs'].values]
    neg_effectors_dict = dict([(rxn_id, neg_eff_and_ref) for rxn_id, neg_eff_and_ref in zip(data_df['reaction ID'].values, zip(model_neg_effectors, model_neg_eff_refs_type, model_neg_eff_refs))])

    model_pos_effectors = [pos_effectors_list.split(' ') if isinstance(pos_effectors_list, str) else [] for pos_effectors_list in data_df['positive effectors'].values]
    model_pos_eff_refs_type = [pos_eff_refs_type.split(';') if isinstance(pos_eff_refs_type, str) else [] for pos_eff_refs_type in data_df['positive_effectors_refs_type'].values]
    model_pos_eff_refs = [pos_eff_refs.split(';') if isinstance(pos_eff_refs, str) else [] for pos_eff_refs in data_df['positive_effectors_refs'].values]
    pos_effectors_dict = dict([(rxn_id, pos_eff_and_ref) for rxn_id, pos_eff_and_ref in zip(data_df['reaction ID'].values, zip(model_pos_effectors, model_pos_eff_refs_type, model_pos_eff_refs))])

    return neg_effectors_dict, pos_effectors_dict


def get_model_gibbs_energies(file_path, sheet_name):
    """
    Given the GRASP input excel file, extracts the gibbs energies (mean and respective std) for each reaction
    from the thermoRxns sheet.

    Args:
        file_path: path to file containing the model
        sheet_name: name of the excel sheet where the reaction effectors specification is, should be 'thermoRxns'

    Returns:
        dG_dict of the form {rxn_id: (dG_mean, dG_std, references)}
    """

    data_df = pd.read_excel(file_path, sheet_name=sheet_name, index_col=0, header=0)
    data_df = data_df.fillna('')

    dG_min = data_df['∆Gr\'_min (kJ/mol)']
    dG_max = data_df['∆Gr\'_max (kJ/mol)']
    dG_mean = (dG_max + dG_min) / 2
    dG_std = dG_max - dG_mean

    dG_dict = dict((rxn, (round(dG_mean[i], 2), round(dG_std[i], 2), data_df['refs'][i]))
                   for i, rxn in enumerate(data_df.index.values))

    return dG_dict
