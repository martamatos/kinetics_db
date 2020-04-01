""" This module implements methods to load initial values into the database.

Author: Marta Matos

"""

import re

import pandas as pd

from app import create_app, db
from app.load_data import COMPARTMENT_DATA_FILE, ECOLI_CORE_MODEL, METABOLITE_DATA_FILE, REACTION_DATA_FILE, \
    REACTION_EC_DATA_FILE, ENZYME_GENES_DATA_FILE
from app.load_data.load_sbml_models import load_sbml_model, Flavor
from app.models import Compartment, Enzyme, EnzymeGeneOrganism, Gene, Metabolite, Organism, Reaction, ReferenceType, \
    EnzymeReactionOrganism, EvidenceLevel, Model, Mechanism, EnzymeReactionInhibition, EnzymeReactionActivation, \
    EnzymeReactionMiscInfo, EnzymeReactionEffector, ModelAssumptions
from app.utils.misc import clear_data
from config import Config


def load_compartments():
    """
    Using a file based on Metanetx comp_xref.tsv, populate the Compartment table with the compartments found in BiGG.

    Returns:
        None
    """

    comp_data_df = pd.read_csv(COMPARTMENT_DATA_FILE, sep='\t', comment='#', header=None)
    col_names = ['bigg_id', 'metanetx_id', 'name']
    comp_data_df.columns = col_names

    for index in comp_data_df.index:
        bigg_id = re.findall('bigg:(\w+)', comp_data_df.loc[index, 'bigg_id'])
        compartment = Compartment(name=comp_data_df.loc[index, 'name'],
                                  bigg_id=bigg_id[0],
                                  metanetx_id=comp_data_df.loc[index, 'metanetx_id'])

        db.session.add(compartment)

    compartment = Compartment(name='imaginary',
                              bigg_id='z',
                              metanetx_id='')

    db.session.add(compartment)

    db.session.commit()


def load_enzymes():
    """
    Gets all enzymes names in enzymes_genes_data_file and adds them to the database.

    Returns:
        None
    """

    enzymes_df = pd.read_csv(ENZYME_GENES_DATA_FILE, sep=',')

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

    ex_enzyme = ('Fake enzyme for exchange reactions', 'EX_enz', 'EX_enz', None)
    enzyme = Enzyme(name=ex_enzyme[0],
                    acronym=ex_enzyme[1],
                    isoenzyme=ex_enzyme[2])

    db.session.add(enzyme)

    db.session.commit()


def load_genes():
    """
    Gets all gene names in enzymes_genes_data_file and adds them to the database.
    Afterwards it adds the gene associations to the enzymes and organism.

    Returns:
        None
    """

    genes_df = pd.read_csv(ENZYME_GENES_DATA_FILE, sep=',')

    organism = Organism.query.filter_by(name='E. coli').first()
    genes_df = genes_df.loc[genes_df['gene_name'].dropna().index, :]

    for row in genes_df.index:
        gene = Gene(name=genes_df.loc[row, 'gene_name'])
        db.session.add(gene)

        enzyme = Enzyme.query.filter_by(isoenzyme=genes_df.loc[row, 'isoenzyme']).first()
        enzyme_gene_organism = EnzymeGeneOrganism(gene_id=gene.id,
                                                  enzyme_id=enzyme.id,
                                                  organism_id=organism.id)

        db.session.add(enzyme_gene_organism)

    db.session.commit()


def _get_metabolites_from_core_ecoli():
    model = load_sbml_model(ECOLI_CORE_MODEL, kind='cb', flavor=Flavor.BIGG, exchange_detection_mode=None,
                            load_gprs=False)

    column_names = ['bigg_id', 'stuff0', 'name', 'compartment', 'stuff1', 'stuff2']
    metabolites_df = pd.DataFrame(model['metabolites'], columns=column_names)
    metabolites_df = metabolites_df[['bigg_id', 'name', 'compartment']]

    return metabolites_df


def _get_met_ids_from_metanetx(metabolites_df):
    met_bigg_ids = metabolites_df['bigg_id'].values

    met_data_df = pd.read_csv(METABOLITE_DATA_FILE, sep='\t', comment='#', header=None)
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

    Returns:
        None
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
    model = load_sbml_model(ECOLI_CORE_MODEL, kind='cb', flavor=Flavor.BIGG, exchange_detection_mode=None,
                            load_gprs=False)

    column_names = ['bigg_id', 'name', 'reversibility', 'stoichiometry', 'modifiers', 'exchange']
    reactions_df = pd.DataFrame(model['reactions'], columns=column_names)
    reactions_df = reactions_df[['bigg_id', 'name', 'stoichiometry', 'exchange']]

    return reactions_df


def _get_rxn_ids_from_metanetx(reactions_df):
    rxn_bigg_ids = reactions_df['bigg_id']

    met_data_df = pd.read_csv(REACTION_DATA_FILE, sep='\t', comment='#', header=None)
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
    rxn_ec_data_df = pd.read_csv(REACTION_EC_DATA_FILE, sep='\t', comment='#', header=None)
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

    Returns:
        None
    """

    organism_list = ['', 'E. coli', 'S. cerevisiae']

    for name in organism_list:
        organism = Organism(name=name)
        db.session.add(organism)
    db.session.commit()


def load_reactions():
    """
    Gets all reactions on the E. coli core model (see BiGG database), and then uses reac_xref.tsv from metanetx to
    get the metanetx ids, kegg ids, and metacyc ids and populate the Reaction table.

    It also gets the corresponding EC numbers from reac_prop.csv which will be used to populate the Enzyme table.

    Returns:
        None
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


def load_enzyme_reaction_relation():
    """
    Gets all reaction and respective catalyzing enzymes and creates populates the table enzyme_reaction_organism for
     E. coli.
    Returns:
        None
    """

    data_df = pd.read_csv(ENZYME_GENES_DATA_FILE, sep=',')

    organism = Organism.query.filter_by(name='E. coli').first()

    id = 1
    for row in data_df.index:
        if data_df.loc[row, 'isoenzyme'] != 'SUCOASa' and data_df.loc[row, 'isoenzyme'] != 'SUCOASb':
            enzyme = Enzyme.query.filter_by(isoenzyme=data_df.loc[row, 'isoenzyme']).first()
            reaction = Reaction.query.filter_by(acronym=data_df.loc[row, 'reaction_acronym']).first()

            enzyme_reaction_organism = EnzymeReactionOrganism(id=id,
                                                              enzyme_id=enzyme.id,
                                                              reaction_id=reaction.id,
                                                              organism_id=organism.id)

            db.session.add(enzyme_reaction_organism)
            id += 1

    db.session.commit()


def load_reference_types():
    """
    Loads four types of references into database.

    Returns:
        None
    """

    reference_type_list = ['Article', 'Thesis', 'Online resource', 'Book']

    for type in reference_type_list:
        reference_type = ReferenceType(type=type)
        db.session.add(reference_type)
    db.session.commit()


def load_evidence_levels():
    """
    Adds evidence levels to the database.

    Returns:
        None
    """

    evidence_list = ['Solid, clear evidence found in one or more papers for this organism.',
                     'Evidence found in papers but for other organisms',
                     'Evidence found in papers for this organism but not very clear or conflicting.',
                     'Prediction by a method/algorithm.',
                     'Educated guess',
                     'No evidence.']

    for evidence_description in evidence_list:
        evidence_db = EvidenceLevel(description=evidence_description)
        db.session.add(evidence_db)

    db.session.commit()


def load_empty_model():
    """
    Adds empty model.

    Returns:
        None
    """

    model = Model(name='')
    db.session.add(model)
    db.session.commit()


def load_mechanisms():
    """
    Adds the most common mechanisms (from Cleland's paper) to the mechanism table.

    Returns:
        None
    """

    mechanism_list = [('UniUni', ''),

                      ('OrderedBiBi', 'Ordered_Bi_Bi'),
                      ('OrderedUniBi', 'Ordered_Uni_Bi'),
                      ('OrderedBiUni', ''),
                      ('OrderedTerBi', 'Ordered_Ter_Bi'),
                      ('OrderedTerTer', 'Ordered_Ter_Ter'),

                      ('RandomBiBi', 'Random_Bi_Bi'),
                      ('RandomUniBi', 'Random_Uni_Bi'),
                      ('RandomBiUni', ''),
                      ('RandomTerBi', ''),
                      ('RandomTerTer', ''),

                      ('PingPongBiBi', 'PingPong_Bi_Bi'),
                      ('PingPongBiUniUniUni', 'PingPong_Bi_Uni_Uni_Uni'),
                      ('PingPongUniUniBiUni', 'PingPong_Uni_Uni_Bi_Uni'),
                      ('PingPongBiUniUniBi', 'PingPong_Bi_Uni_Uni_Bi'),
                      ('PingPongBiBiUniUni', 'PingPong_Bi_Bi_Uni_Uni'),
                      ('PingPongUniBiBiUni', 'PingPong_Uni_Bi_Bi_Uni'),
                      ('PingPongUniUniBiBi', 'PingPong_Uni_Uni_Bi_Bi'),
                      ('PingPongHexaUni', 'PingPong_Hexa_Uni'),

                      ('Other', ''),
                      ('massAction', ''),
                      ('fixedExchange', ''),
                      ('freeExchange', ''),
                      ('Diffusion', '')]

    for mech_name, image_name in mechanism_list:
        mechanism = Mechanism(name=mech_name, image_name=image_name)
        db.session.add(mechanism)
    db.session.commit()


def load_empty_entries():
    enz_rxn_inhib = EnzymeReactionInhibition(comments='')
    db.session.add(enz_rxn_inhib)

    enz_rxn_activation = EnzymeReactionActivation(comments='')
    db.session.add(enz_rxn_activation)

    enz_rxn_effector = EnzymeReactionEffector(comments='')
    db.session.add(enz_rxn_effector)

    enz_rxn_misc_info = EnzymeReactionMiscInfo(topic='',
                                               description='',
                                               comments='')
    db.session.add(enz_rxn_misc_info)

    model_assumption = ModelAssumptions(assumption='',
                                        description='',
                                        comments='')
    db.session.add(model_assumption)

    db.session.commit()


# TODO add mechanisms, add empty field to all tables


class LoadDataConfig(Config):
    LOGIN_DISABLED = True
    WTF_CSRF_ENABLED = False


def main():
    app = create_app(LoadDataConfig)
    app_context = app.app_context()
    app_context.push()

    db.drop_all()
    #clear_data(db)
    db.create_all()

    load_organisms()

    load_compartments()

    load_metabolites()
    load_reactions()

    load_enzymes()

    load_genes()

    load_reference_types()

    load_enzyme_reaction_relation()

    load_evidence_levels()

    load_mechanisms()

    load_empty_entries()

main()

