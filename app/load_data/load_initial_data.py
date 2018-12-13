""" This module implements methods to load initial values in the database.

Author: Marta Matos

"""

import re

import pandas as pd

from app import db
from app.load_data import compartment_data_file, ecoli_core_model, metabolite_data_file, reaction_data_file, \
    reaction_ec_data_file, enzymes_genes_data_file
from app.load_data.load_sbml_models import load_sbml_model, Flavor
from app.models import Compartment, Enzyme, Gene, Metabolite, Organism, Reaction, ReferenceType


def load_compartments():
    """
    Using a file based on Metanetx comp_xref.tsv, populate the Compartment table with the compartments found in BiGG.

    :return: None
    """

    comp_data_df = pd.read_csv(compartment_data_file, sep='\t', comment='#', header=None)
    col_names = ['bigg_id', 'metanetx_id', 'name']
    comp_data_df.columns = col_names

    for index in comp_data_df.index:
        bigg_id = re.findall('bigg:(\w+)', comp_data_df.loc[index, 'bigg_id'])
        compartment = Compartment(name=comp_data_df.loc[index, 'name'],
                                  bigg_id=bigg_id[0],
                                  metanetx_id=comp_data_df.loc[index, 'metanetx_id'])

        db.session.add(compartment)

    db.session.commit()


def load_enzymes():
    """
    Gets all enzymes names in enzymes_genes_data_file and adds them to the database.

    :return: None
    """
    enzymes_df = pd.read_csv(enzymes_genes_data_file, sep=',')

    for row in enzymes_df.index:
        enzyme = Enzyme(name=enzymes_df.loc[row, 'enzyme_name'],
                        acronym=enzymes_df.loc[row, 'enzyme_acronym'],
                        isoenzyme=enzymes_df.loc[row, 'isoenzyme'],
                        ec_number=enzymes_df.loc[row, 'EC'])

        db.session.add(enzyme)

    sucoas_complex = Enzyme.query.filter_by(isoenzyme='SUCOAS_complex').first()
    sucoas_a = Enzyme.query.filter_by(isoenzyme='SUCOASa').first()
    sucoas_b = Enzyme.query.filter_by(isoenzyme='SUCOASb').first()

    if sucoas_complex and sucoas_a and sucoas_b:
        sucoas_complex.add_subunit(sucoas_a)
        sucoas_complex.add_subunit(sucoas_b)

    db.session.commit()


def load_genes():
    """
    Gets all gene names in enzymes_genes_data_file and adds them to the database.

    :return: None
    """
    genes_df = pd.read_csv(enzymes_genes_data_file, sep=',')

    for gene_name in genes_df['gene_name'].dropna().values:
        gene = Gene(name=gene_name)
        db.session.add(gene)

    db.session.commit()


def _get_metabolites_from_core_ecoli():
    model = load_sbml_model(ecoli_core_model, kind='cb', flavor=Flavor.BIGG, exchange_detection_mode=None,
                            load_gprs=False)

    column_names = ['bigg_id', 'stuff0', 'name', 'compartment', 'stuff1', 'stuff2']
    metabolites_df = pd.DataFrame(model['metabolites'], columns=column_names)
    metabolites_df = metabolites_df[['bigg_id', 'name', 'compartment']]

    return metabolites_df


def _get_met_ids_from_metanetx(metabolites_df):
    met_bigg_ids = metabolites_df['bigg_id'].values

    met_data_df = pd.read_csv(metabolite_data_file, sep='\t', comment='#', header=None)
    col_names = ['bigg_id', 'metanetx_id', 'evidence', 'name']
    met_data_df.columns = col_names

    bigg_data_df = met_data_df[met_data_df['bigg_id'].str.match('bigg:[^M]')]
    bigg_data_df['bigg_id'].replace(regex='bigg:', value='', inplace=True)
    bigg_data_df = bigg_data_df[bigg_data_df['bigg_id'].isin(met_bigg_ids)]

    assert len(set(met_bigg_ids).difference(set(bigg_data_df['bigg_id'].values))) == 0

    return bigg_data_df


def load_metabolites():
    """
    Gets all metabolites on the E. coli core model (see BiGG database), and then uses chem_xref.tsv from metanetx to
    get the metanetx ids and populate the Metabolite table.

    :return: None
    """

    metabolites_df = _get_metabolites_from_core_ecoli()
    bigg_data_df = _get_met_ids_from_metanetx(metabolites_df)

    for index in bigg_data_df.index:
        bigg_id = bigg_data_df.loc[index, 'bigg_id']

        metabolite = Metabolite(grasp_id=bigg_id,
                                name=bigg_data_df.loc[index, 'name'],
                                bigg_id=bigg_id,
                                metanetx_id=bigg_data_df.loc[index, 'metanetx_id'])

        db.session.add(metabolite)

        met_compartments = metabolites_df[metabolites_df['bigg_id'].str.match(bigg_id)]['compartment'].values
        for comp_acronym in met_compartments:
            compartment = Compartment.query.filter_by(bigg_id=comp_acronym).first()
            metabolite.add_compartment(compartment)

    db.session.commit()


def _get_reactions_from_core_ecoli():
    model = load_sbml_model(ecoli_core_model, kind='cb', flavor=Flavor.BIGG, exchange_detection_mode=None,
                            load_gprs=False)

    column_names = ['bigg_id', 'name', 'reversibility', 'stoichiometry', 'modifiers', 'exchange']
    reactions_df = pd.DataFrame(model['reactions'], columns=column_names)
    reactions_df = reactions_df[['bigg_id', 'name', 'stoichiometry', 'exchange']]

    return reactions_df


def _get_rxn_ids_from_metanetx(reactions_df):
    rxn_bigg_ids = reactions_df['bigg_id']

    met_data_df = pd.read_csv(reaction_data_file, sep='\t', comment='#', header=None)
    col_names = ['XREF', 'metanetx_id', 'rxn']
    met_data_df.columns = col_names
    met_data_df = met_data_df[['XREF', 'metanetx_id']]

    # get bigg IDs
    bigg_data_df = met_data_df[met_data_df['XREF'].str.match('bigg:R')]
    bigg_data_df['XREF'].replace(regex='bigg:', value='', inplace=True)
    bigg_data_df = bigg_data_df[bigg_data_df['XREF'].isin(rxn_bigg_ids)]
    assert len(set(rxn_bigg_ids).difference(set(bigg_data_df['XREF'].values))) == 0

    # get kegg IDs
    kegg_data_df = met_data_df[met_data_df['XREF'].str.match('kegg:R')]
    kegg_data_df['XREF'].replace(regex='kegg:', value='', inplace=True)
    joined_rxn_data_df = bigg_data_df.join(kegg_data_df.set_index('metanetx_id'), rsuffix='_kegg', how='left',
                                           on='metanetx_id')

    # get EC numbers
    rxn_ec_data_df = pd.read_csv(reaction_ec_data_file, sep='\t', comment='#', header=None)
    col_names = ['metanetx_id', 'equation', 'description', 'balance', 'EC', 'source']
    rxn_ec_data_df.columns = col_names
    rxn_ec_data_df = rxn_ec_data_df[['metanetx_id', 'EC']]
    joined_rxn_data_df = joined_rxn_data_df.join(rxn_ec_data_df.set_index('metanetx_id'), how='left', on='metanetx_id')

    # rename columns
    col_names = ['bigg_id', 'metanetx_id', 'kegg_id', 'ec_number']
    joined_rxn_data_df.columns = col_names

    return joined_rxn_data_df


def load_organisms():
    """
    Loads E. coli and S. cerevisiae into the database.

    :return: None
    """
    organism_list = ['E. coli', 'S. cerevisiae']

    for name in organism_list:
        organism = Organism(name=name)
        db.session.add(organism)
    db.session.commit()


def load_reactions():
    """
    Gets all reactions on the E. coli core model (see BiGG database), and then uses reac_xref.tsv from metanetx to
    get the metanetx ids, kegg ids, and metacyc ids and populate the Reaction table.

    It also gets the corresponding EC numbers from reac_prop.csv which will be used to populate the Enzyme table.

    :return:
    """

    reactions_df = _get_reactions_from_core_ecoli()
    metanetx_data_df = _get_rxn_ids_from_metanetx(reactions_df)

    reactions_df = reactions_df.join(metanetx_data_df.set_index('bigg_id'), how='left', on='bigg_id')
    reactions_df['bigg_id'].replace(regex='R_', value='', inplace=True)

    for index in reactions_df.index:
        if not reactions_df.loc[index, 'bigg_id'].endswith('t') and not reactions_df.loc[index, 'bigg_id'].startswith(
                'EX') \
                and not reactions_df.loc[index, 'bigg_id'].startswith('BIOMASS'):

            reaction = Reaction(name=reactions_df.loc[index, 'name'],
                                acronym=reactions_df.loc[index, 'bigg_id'],
                                metanetx_id=reactions_df.loc[index, 'metanetx_id'],
                                bigg_id=reactions_df.loc[index, 'bigg_id'],
                                kegg_id=reactions_df.loc[index, 'kegg_id'])

            db.session.add(reaction)

            compartment_list = []
            for met, stoich_coef in reactions_df.loc[index, 'stoichiometry'].items():
                met_compartment = re.findall('M_(\w+)_(\w+)', met)[0]

                bigg_id = met_compartment[0]
                met_db = Metabolite.query.filter_by(bigg_id=bigg_id).first()

                compartment_acronym = met_compartment[1]
                compartment_list.append(compartment_acronym)

                if not met_db:
                    met_db = Metabolite(bigg_id=bigg_id,
                                        grasp_id=bigg_id)

                    db.session.add(met_db)

                compartment_db = Compartment.query.filter_by(bigg_id=compartment_acronym).first()
                met_db.add_compartment(compartment_db)

                reaction.add_metabolite(met_db, stoich_coef, compartment_db)

            if len(set(compartment_list)) == 1:
                compartment_db.add_reaction(reaction)

    db.session.commit()


def load_reference_types():
    """
    Loads four types of references into database.

    :return: None
    """
    reference_type_list = ['Article', 'Thesis', 'Online resource', 'Book']

    for type in reference_type_list:
        reference_type = ReferenceType(type=type)
        db.session.add(reference_type)
    db.session.commit()


# TODO add evidence levels and mechanisms
