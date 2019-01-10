import re

from app import db
from app.models import Compartment, EnzymeGeneOrganism, EnzymeOrganism, EnzymeStructure, \
    Gene, GibbsEnergy, GibbsEnergyReactionModel, Metabolite, Reference
from app.utils.parsers import ReactionParser, parse_input_list


def add_enzyme_organism(enzyme, organism_id, uniprot_id_list, number_of_active_sites):
    """
    If no enzyme_organism entry with the given uniprot_id exist, add it. Repeat for each uniprot_id in uniprot_id_list.

    :param enzyme: an enzyme object.
    :param organism_id: the id of the organism (in the DB).
    :param uniprot_id_list: a list of uniprot IDs.
    :param number_of_active_sites: the number of active sites in the enzyme.
    :return: None
    """
    for uniprot_id in uniprot_id_list:
        enzyme_organism_db = EnzymeOrganism.query.filter_by(uniprot_id=uniprot_id).first()
        if not enzyme_organism_db:
            enzyme_organism_db = EnzymeOrganism(enzyme_id=enzyme.id,
                                                organism_id=organism_id,
                                                uniprot_id=uniprot_id,
                                                n_active_sites=number_of_active_sites)
            db.session.add(enzyme_organism_db)
        enzyme.add_enzyme_organism(enzyme_organism_db)


"""
def modify_enzyme_organism(enzyme, organism_id, uniprot_id_list, number_of_active_sites):
    for uniprot_id in uniprot_id_list:
        enzyme_organism_db = EnzymeOrganism.query.filter_by(uniprot_id=uniprot_id).first()
        if not enzyme_organism_db:
            enzyme_organism_db = EnzymeOrganism(enzyme_id=enzyme.id,
                                                organism_id=organism_id,
                                                uniprot_id=uniprot_id,
                                                n_active_sites=number_of_active_sites)
            db.session.add(enzyme_organism_db)
        else:
            enzyme_organism_db.enzyme_id = enzyme.id
            enzyme_organism_db.organism_id = organism_id
            enzyme_organism_db.n_active_sites = number_of_active_sites
        enzyme.add_enzyme_organism(enzyme_organism_db)

    db.session.commit()
"""


def add_enzyme_genes(gene_names, enzyme, organism_id):
    """
    If gene doesn't exist in DB, adds it. Then adds the connection between gene, enzyme, and organism.

    :param gene_names: a list of gene names.
    :param enzyme: an enzyme object.
    :param organism_id: the id of the organism (in the DB).
    :return: None
    """
    # populate genes
    if gene_names:
        gene_bigg_ids_list = parse_input_list(gene_names)
        for gene_name in gene_bigg_ids_list:
            gene_db = Gene.query.filter_by(name=gene_name).first()
            if not gene_db:
                gene_db = Gene(name=gene_name)
                db.session.add(gene_db)
                db.session.commit()

            enzyme_gene_organism_db = EnzymeGeneOrganism.query.filter_by(gene_id=gene_db.id,
                                                                         enzyme_id=enzyme.id,
                                                                         organism_id=organism_id).first()
            if not enzyme_gene_organism_db:
                enzyme_gene_organism = EnzymeGeneOrganism(gene_id=gene_db.id,
                                                          enzyme_id=enzyme.id,
                                                          organism_id=organism_id)
                db.session.add(enzyme_gene_organism)


def add_enzyme_structures(enzyme, organism_id, pdb_id_list, strain_list):
    """
    If the enzyme structures don't exist, adds them.

    :param enzyme: an enzyme object.
    :param organism_id: the id of the organism (in the DB).
    :param pdb_id_list: a list of pdb ids.
    :param strain_list: a list of strains, either a single one or one per pdb_id.
    :return: None
    """

    if len(strain_list) == 1 and len(pdb_id_list) > 1:
        pdb_id_strain_list = zip(pdb_id_list, [strain_list[0] for i in range(len(pdb_id_list))])
    elif len(strain_list) == 0 and len(pdb_id_list) > 1:
        pdb_id_strain_list = zip(pdb_id_list, ['' for i in range(len(pdb_id_list))])
    elif len(strain_list) == len(pdb_id_list):
        pdb_id_strain_list = zip(pdb_id_list, strain_list)

    for pdb_id, pdb_id_strain in pdb_id_strain_list:
        enzyme_structure_db = EnzymeStructure.query.filter_by(pdb_id=pdb_id).first()
        if not enzyme_structure_db:
            enzyme_structure_db = EnzymeStructure(enzyme_id=enzyme.id,
                                                  pdb_id=pdb_id,
                                                  organism_id=organism_id,
                                                  strain=pdb_id_strain)
            db.session.add(enzyme_structure_db)


def add_metabolites_to_reaction(reaction, reaction_string):
    reversible, stoichiometry = ReactionParser().parse_reaction(reaction_string)
    # (True, OrderedDict([('m_pep_c', -1.0), ('m_adp_c', -1.5), ('m_pyr_c', 1.0), ('m_atp_m', 2.0)]))

    for met, stoich_coef in stoichiometry.items():
        met_compartment = re.findall('(\w+)_(\w+)', met)[0]

        bigg_id = met_compartment[0]
        met_db = Metabolite.query.filter_by(bigg_id=bigg_id).first()

        compartment_acronym = met_compartment[1]

        if not met_db:
            met_db = Metabolite(bigg_id=bigg_id,
                                grasp_id=bigg_id)
            db.session.add(met_db)

        compartment_db = Compartment.query.filter_by(bigg_id=compartment_acronym).first()
        met_db.add_compartment(compartment_db)

        reaction.add_metabolite(met_db, stoich_coef, compartment_db)

    return reaction


def add_gibbs_energy(reaction_id, model_id, standard_dg, standard_dg_std, standard_dg_ph, standard_dg_is,
                     std_gibbs_energy_references):
    gibbs_energy_db = GibbsEnergy.query.filter_by(standard_dg=standard_dg,
                                                  standard_dg_std=standard_dg_std,
                                                  ph=standard_dg_ph,
                                                  ionic_strength=standard_dg_is).first()

    if gibbs_energy_db:
        gibbs_energy_reaction_model_db = GibbsEnergyReactionModel.query.filter_by(reaction_id=reaction_id,
                                                                                  model_id=model_id,
                                                                                  gibbs_energy_id=gibbs_energy_db.id).first()

        if not gibbs_energy_reaction_model_db:
            gibbs_energy_reaction_model_db = GibbsEnergyReactionModel(reaction_id=reaction_id,
                                                                      model_id=model_id,
                                                                      gibbs_energy_id=gibbs_energy_db.id)

            db.session.add(gibbs_energy_reaction_model_db)

    if not gibbs_energy_db:
        gibbs_energy_db = GibbsEnergy(standard_dg=standard_dg,
                                      standard_dg_std=standard_dg_std,
                                      ph=standard_dg_ph,
                                      ionic_strength=standard_dg_is)

        db.session.add(gibbs_energy_db)
        db.session.commit()

        gibbs_energy_reaction_model_db = GibbsEnergyReactionModel(reaction_id=reaction_id,
                                                                  model_id=model_id,
                                                                  gibbs_energy_id=gibbs_energy_db.id)

        db.session.add(gibbs_energy_reaction_model_db)

        db.session.commit()

    if std_gibbs_energy_references.lower().strip() != 'equilibrator':

        gibbs_references = parse_input_list(std_gibbs_energy_references)
        for ref_doi in gibbs_references:
            ref_db = Reference.query.filter(doi=ref_doi).first()
            if not ref_db:
                ref_db = Reference(doi=ref_doi)
                db.session.add(ref_db)
            gibbs_energy_db.add_reference(ref_db.id)

    if std_gibbs_energy_references.lower().strip() == 'equilibrator':
        ref_db = Reference.query.filter_by(title='eQuilibrator').first()
        gibbs_energy_db.add_reference(ref_db)


def add_mechanism_references(mechanism_references, enzyme_reaction_model):
    mech_references = parse_input_list(mechanism_references)

    for ref_doi in mech_references:
        ref_db = Reference.query.filter_by(doi=ref_doi).first()
        if not ref_db:
            ref_db = Reference(doi=ref_doi)
            db.session.add(ref_db)

        enzyme_reaction_model.add_mechanism_reference(ref_db)


def add_references(references):
    reference_list = parse_input_list(references)
    ref_db_list = []
    for reference in reference_list:
        ref_db = Reference.query.filter_by(doi=reference).first()
        if not ref_db:
            ref_db = Reference(doi=reference)
        ref_db_list.append(ref_db)

    return ref_db_list


def check_metabolite(bigg_id):
    met_db = Metabolite.query.filter_by(bigg_id=bigg_id).first()
    if not met_db:
        met_db = Metabolite(bigg_id=bigg_id,
                            grasp_id=bigg_id)
        db.session.add(met_db)

    return met_db
