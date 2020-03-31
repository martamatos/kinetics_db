import re

from app import db
from app.models import Compartment, EnzymeGeneOrganism, EnzymeOrganism, EnzymeStructure, \
    Gene, GibbsEnergy, GibbsEnergyReactionModel, Metabolite, Reference, EnzymeReactionEffector, ReactionMetabolite
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
                                                n_active_sites=int(number_of_active_sites))
            db.session.add(enzyme_organism_db)
        enzyme.add_enzyme_organism(enzyme_organism_db)


def add_enzyme_organism_subunits_only(enzyme, organism_id, number_of_active_sites):
    """
    If no enzyme_organism for the given enzyme and organism exist, add it with the given number of active_sites.

    :param enzyme: an enzyme object.
    :param organism_id: the id of the organism (in the DB).
    :param uniprot_id_list: a list of uniprot IDs.
    :param number_of_active_sites: the number of active sites in the enzyme.
    :return: None
    """
    enz_org_db = EnzymeOrganism.query.filter_by(organism_id=organism_id,
                                                enzyme=enzyme).first()
    if not enz_org_db:
        enz_org_db = EnzymeOrganism(organism_id=organism_id,
                                    enzyme=enzyme,
                                    n_active_sites=int(number_of_active_sites))
        db.session.add(enz_org_db)

    enzyme.add_enzyme_organism(enz_org_db)


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

        enzyme.add_structure(enzyme_structure_db)


def add_metabolites_to_reaction(reaction, reaction_string):
    """
    Takes in a reaction string, checks if the metabolites involved exist in the database, if not adds them, and then
    associates the metabolites with the reaction.

    :param reaction: DB instance of reaction
    :param reaction_string: reaction string in the format A_c + B_c <-> P_c
    :return:
    """
    reversible, stoichiometry = ReactionParser().parse_reaction(reaction_string)
    # (True, OrderedDict([('m_pep_c', -1.0), ('m_adp_c', -1.5), ('m_pyr_c', 1.0), ('m_atp_m', 2.0)]))

    for met, stoich_coef in stoichiometry.items():
        met_compartment = re.findall('(\w+)_(\w+)', met)[0]

        bigg_id = met_compartment[0]
        compartment_acronym = met_compartment[1]

        met_db = check_metabolite(bigg_id)

        compartment_db = Compartment.query.filter_by(bigg_id=compartment_acronym).first()
        met_db.add_compartment(compartment_db)

        reaction.add_metabolite(met_db, stoich_coef, compartment_db)

    return reaction


def add_gibbs_energy(reaction_id, model_id, standard_dg, standard_dg_std, standard_dg_ph, standard_dg_is,
                     std_gibbs_energy_references):
    """
    Adds the standard Gibbs energies to a reaction. First check if these exist already, if not creates it. Then adds the
    references.

    :param reaction_id: id of the reaction to which the Gibbs energy is going to be associated with
    :param model_id: id of model that the reaction is part of
    :param standard_dg: value of the standard Gibbs energy in kJ/mol
    :param standard_dg_std: value of the standard deviation of the standard Gibbs energy, in kJ/mol
    :param standard_dg_ph: pH for the standard Gibbs energy
    :param standard_dg_is: ionic strength for the standard Gibbs energy
    :param std_gibbs_energy_references:  list of references for the given standard Gibbs energy
    :return:
    """

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
    """
    Takes in a list of doi and adds them as references to the database. Then adds them as mechanism references.

    :param mechanism_references: a list of references for a mechanism
    :param enzyme_reaction_model: enzyme_reaction_model that has the given mechanism refs
    :return: None
    """

    mech_references = parse_input_list(mechanism_references)

    for ref_doi in mech_references:
        ref_db = Reference.query.filter_by(doi=ref_doi).first()
        if not ref_db:
            ref_db = Reference(doi=ref_doi)
            db.session.add(ref_db)

        enzyme_reaction_model.add_mechanism_reference(ref_db)


def add_references(references, obj, mechanism_ref=False):
    """
    Takes in a list of doi and adds them as references to the database. Returns a list of the DB instances of the
    references inserted.

    :param references: a list of references
    :param obj: DB object to which the references will be added
    :param mechanism_ref: boolean specifying whether or not the reference is for a mechanism
    :return: None
    """

    if type(references) is not list:
        reference_list = parse_input_list(references)
    else:
        reference_list = references

    for reference in reference_list:
        ref_db = Reference.query.filter_by(doi=reference).first()

        if not ref_db:
            ref_db = Reference(doi=reference)
            db.session.add(ref_db)

        if mechanism_ref:
            obj.add_mechanism_reference(ref_db)
        else:
            obj.add_reference(ref_db)


def check_metabolite(bigg_id):
    """
    Check if metabolite is part of the database and if it isn't add it and return the instance.

    :param bigg_id: bigg_id for the metabolite.
    :return: met_db
    """

    if bigg_id.find('_') != -1:
        met_compartment = re.findall('(\w+)_(\w*)', bigg_id)[0]
        bigg_id = met_compartment[0]

    met_db = Metabolite.query.filter_by(bigg_id=bigg_id).first()

    if not met_db:
        met_db = Metabolite(bigg_id=bigg_id,
                            grasp_id=bigg_id)
        db.session.add(met_db)

    return met_db


def set_binding_release_order(rxn, rxn_string, enz_rxn_org, mechanisms_dict):
    """

    :param rxn_string:
    :param enz_rxn_org:
    :param mechanisms_dict:
    :return:
    """
    rev, stoic = ReactionParser().parse_reaction(rxn_string)

    binding_ind = []
    release_ind = []
    for met, coeff in stoic.items():
        if coeff < 0:
            binding_ind.append(mechanisms_dict[rxn][1].index(met))
        else:
            release_ind.append(mechanisms_dict[rxn][2].index(met))

    binding_ind.sort()
    release_ind.sort()
    binding_order = ' '.join([mechanisms_dict[rxn][1][ind] for ind in binding_ind])
    release_order = ' '.join([mechanisms_dict[rxn][2][ind] for ind in release_ind])

    enz_rxn_org.subs_binding_order = binding_order
    enz_rxn_org.prod_release_order = release_order

    return binding_order, release_order


def add_effector(effector_dic, rxn, effector_type, model, enz_rxn_org):
    """

    :param effector_dic:
    :param rxn:
    :param effector_type:
    :param model:
    :return:
    """
    for effector_i, effector in enumerate(effector_dic[rxn][0]):
        effector_met_db = check_metabolite(effector)

        enz_effector_db = EnzymeReactionEffector.query.filter_by(effector_met=effector_met_db,
                                                                 effector_type=effector_type).first()

        if not enz_effector_db:
            enz_effector_db = EnzymeReactionEffector(effector_met=effector_met_db,
                                                     effector_type=effector_type)
            db.session.add(enz_effector_db)

        enz_effector_db.add_model(model)
        enz_rxn_org.add_enzyme_reaction_effector(enz_effector_db)

        if effector_dic[rxn][1]:
            try:
                if len(effector_dic[rxn][1]) > 1:
                    add_references(effector_dic[rxn][1][effector_i], enz_effector_db)
                else:
                    add_references(effector_dic[rxn][1][0], enz_effector_db)
            except IndexError:
                print(f'Number of references is wrong for effector {effector} from reaction {rxn}. '
                      f'These references won\'t be added.'
                      f'There should be either a single reference for all effectors, or one for each.')
