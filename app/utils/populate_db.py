from app import create_app, db
from app.models import Compartment, Enzyme, EvidenceLevel, Mechanism, Metabolite, Model, Organism, Reaction, Reference, \
    ReferenceType, EnzymeReactionOrganism, EnzymeReactionActivation, EnzymeReactionEffector, EnzymeReactionMiscInfo, \
    EnzymeReactionInhibition, ModelAssumptions
from app.utils.parsers import ReactionParser
import re
from config import Config


def add_compartments():

    compartment_list = [('Cytosol', 'c'), ('Mitochondria', 'm')]

    for name, acronym in compartment_list:
        compartment = Compartment(name=name, bigg_id=acronym)
        db.session.add(compartment)

    db.session.commit()


def add_evidence_levels():
    evidence_list = [('Got it from papers for the given organism'),
                     ('Got it from papers of other organisms'),
                     ('Predicted by some algorithm'),
                     ('Educated guess')]

    for description in evidence_list:
        evidence = EvidenceLevel(description=description)
        db.session.add(evidence)
    db.session.commit()


def add_metabolite(client):
    grasp_id = '2pg'
    name = '2-phosphoglycerate'
    bigg_id = '2pg'
    metanetx_id = 'MNXM23'

    compartments = ['1', '2']
    chebi_ids = 'CHEBI:86354, CHEBI:8685'
    inchis = 'InChI=1S/C3H4O3/c1-2(4)3(5)6/h4H,1H2,(H,5,6), InChI=1S/C3H4O4/c1-2(4)3(5)6/h4H,1H2,(H,5,6)'

    response = client.post('/add_metabolite', data=dict(
                           grasp_id=grasp_id,
                           name=name,
                           bigg_id=bigg_id,
                           metanetx_id=metanetx_id,
                           compartments=compartments,
                           chebi_ids=chebi_ids,
                           inchis=inchis), follow_redirects=True)

    assert response.status_code == 200


def add_mechanisms():
    mechanism_list = ['UniUni', 'OrderedBiBi']

    for name in mechanism_list:
        mechanism = Mechanism(name=name)
        db.session.add(mechanism)
    db.session.commit()


def add_organisms():
    organism_list = ['E. coli', 'S. cerevisiae']

    for name in organism_list:
        organism = Organism(name=name)
        db.session.add(organism)
    db.session.commit()


def add_reference_types():
    reference_type_list = ['Article', 'Thesis', 'Online database', 'Book']

    for type in reference_type_list:
        reference_type = ReferenceType(type=type)
        db.session.add(reference_type)
    db.session.commit()


def add_references():
    ref_type = ReferenceType.query.filter_by(type='Online database').first()
    reference = Reference(title='eQuilibrator', type=ref_type)
    db.session.add(reference)
    db.session.commit()


# only for development
def add_enzymes(client):

    enzyme_name = 'Phosphofructokinase'
    enzyme_acronym = 'PFK'
    isoenzyme = 'PFK1'
    ec_number = '1.2.1.31'

    organism_name = 'E. coli'
    number_of_active_sites = 4
    gene_bigg_ids = 'b001, b003'
    uniprot_ids = 'PC3W1, P34D'
    pdb_structure_ids = '3H8A, 1E9I'
    strain = 'WT'

    response = client.post('/add_enzyme', data=dict(
                                name=enzyme_name,
                                acronym=enzyme_acronym,
                                isoenzyme=isoenzyme,
                                ec_number=ec_number,
                                organism_name='1',  # querySelectField
                                number_of_active_sites=number_of_active_sites,
                                gene_names=gene_bigg_ids,
                                uniprot_id_list=uniprot_ids,
                                pdb_structure_ids=pdb_structure_ids,
                                strain=strain), follow_redirects=True)

    assert response.status_code == 200

    enzyme_list = [('Phosphofructokinase', 'PFK', 'PFK2', '1.2.3.33')]

    for name, acronym, isoenzyme, ec_number in enzyme_list:
        enzyme = Enzyme(name=name, acronym=acronym, isoenzyme=isoenzyme, ec_number=ec_number)
        db.session.add(enzyme)
    db.session.commit()



# only for development
def add_models():
    model_list = [('E. coli - iteration 1', 'E. coli', 'MG16555'),
                  ('E. coli - iteration 2', 'E. coli', 'MG16555')]

    for name, organism_name, strain in model_list:
        model = Model(name=name, organism_name=organism_name, strain=strain)
        db.session.add(model)
    db.session.commit()


def add_reaction(client):
    reaction_name = 'phosphofructokinase'
    reaction_acronym = 'PFK'
    reaction_grasp_id = 'PFK1'
    reaction_string = '1 pep_c + 1.5 adp_c <-> pyr_c + 2.0 atp_c'
    metanetx_id = ''
    bigg_id = ''
    kegg_id = ''

    compartment = '1'
    organism = '1'
    models = ['1', '2']
    enzymes = ['1','2']
    mechanism = '1'
    mechanism_references = 'https://doi.org/10.1093/bioinformatics/bty942, https://doi.org/10.1093/bioinformatics/bty943'
    mechanism_evidence_level = '1'
    subs_binding_order = 'adp_c, pep_c'
    prod_release_order = 'pyr_c, atp_c'
    std_gibbs_energy = 2.1
    std_gibbs_energy_std = 0.2
    std_gibbs_energy_ph = 7
    std_gibbs_energy_ionic_strength = 0.2
    std_gibbs_energy_references = 'equilibrator'
    comments = ''

    response = client.post('/add_reaction', data=dict(
                                name=reaction_name,
                                acronym=reaction_acronym,
                                grasp_id=reaction_grasp_id,
                                reaction_string=reaction_string,
                                bigg_id=bigg_id,
                                kegg_id=kegg_id,
                                metanetx_id=metanetx_id,
                                compartment=compartment,
                                organism=organism,
                                models=models,
                                enzymes=enzymes,
                                mechanism=mechanism,
                                mechanism_references=mechanism_references,
                                mechanism_evidence_level=mechanism_evidence_level,
                                subs_binding_order=subs_binding_order,
                                prod_release_order=prod_release_order,
                                std_gibbs_energy=std_gibbs_energy,
                                std_gibbs_energy_std=std_gibbs_energy_std,
                                std_gibbs_energy_ph=std_gibbs_energy_ph,
                                std_gibbs_energy_ionic_strength=std_gibbs_energy_ionic_strength,
                                std_gibbs_energy_references=std_gibbs_energy_references,
                                comments=comments), follow_redirects=True)

    assert response.status_code == 200

    met_db = Metabolite.query.filter_by(bigg_id='atp').first()
    compartment_db = Compartment.query.filter_by(bigg_id='m').first()

    met_db.add_compartment(compartment_db)

    db.session.commit()

    
def add_inhibitions(client):

    enzyme = '1'
    reaction = '1'
    organism = '1'
    models = '1'
    inhibitor_met = 'adp'
    affected_met = 'atp'
    inhibition_type = 'Competitive'
    inhibition_constant = 1.3*10**-4

    evidence_level = '1'
    references = 'https://doi.org/10.1093/bioinformatics/bty942, https://doi.org/10.1093/bioinformatics/bty943'
    comments = ''

    response = client.post('/add_enzyme_inhibition', data=dict(
                                 enzyme=enzyme,
                                 reaction=reaction,
                                 organism=organism,
                                 models=models,
                                 inhibitor_met=inhibitor_met,
                                 affected_met=affected_met,
                                 inhibition_type=inhibition_type,
                                 inhibition_constant=inhibition_constant,
                                 inhibition_evidence_level=evidence_level,
                                 references=references,
                                 comments=comments), follow_redirects=True)

    assert response.status_code == 200

    inhibitor_met = 'nad'
    affected_met = 'nadh'
    inhibition_type = 'Competitive'
    inhibition_constant = 1.3*10**-4

    evidence_level = '1'
    references = 'https://doi.org/10.1093/bioinformatics/bty942, https://doi.org/10.1093/bioinformatics/bty943'
    comments = ''

    response = client.post('/add_enzyme_inhibition', data=dict(
                                 enzyme=enzyme,
                                 reaction=reaction,
                                 organism=organism,
                                 models=models,
                                 inhibitor_met=inhibitor_met,
                                 affected_met=affected_met,
                                 inhibition_type=inhibition_type,
                                 inhibition_constant=inhibition_constant,
                                 inhibition_evidence_level=evidence_level,
                                 references=references,
                                 comments=comments), follow_redirects=True)

    assert response.status_code == 200


def add_activations(client):
    enzyme = '1'
    reaction = '1'
    organism = '1'
    models = '1'
    activator_met = 'adp'
    activation_constant = 1.3*10**-4

    evidence_level = '1'
    references = 'https://doi.org/10.1093/bioinformatics/bty942, https://doi.org/10.1093/bioinformatics/bty943'
    comments = ''

    response = client.post('/add_enzyme_activation', data=dict(
                                 enzyme=enzyme,
                                 reaction=reaction,
                                 organism=organism,
                                 models=models,
                                 activator_met=activator_met,
                                 activation_constant=activation_constant,
                                 activation_evidence_level=evidence_level,
                                 references=references,
                                 comments=comments), follow_redirects=True)

    assert response.status_code == 200


    activator_met = 'nad'
    activation_constant = 1.3*10**-4

    evidence_level = '1'
    references = 'https://doi.org/10.1093/bioinformatics/bty942, https://doi.org/10.1093/bioinformatics/bty943'
    comments = ''

    response = client.post('/add_enzyme_activation', data=dict(
                                 enzyme=enzyme,
                                 reaction=reaction,
                                 organism=organism,
                                 models=models,
                                 activator_met=activator_met,
                                 activation_constant=activation_constant,
                                 activation_evidence_level=evidence_level,
                                 references=references,
                                 comments=comments), follow_redirects=True)

    assert response.status_code == 200
    
        
def add_effectors(client):
    
    enzyme = '1'
    reaction = '1'
    organism = '1'
    models = '1'
    effector_met = 'adp'
    effector_type = 'Inhibiting'

    evidence_level = '1'
    references = 'https://doi.org/10.1093/bioinformatics/bty942, https://doi.org/10.1093/bioinformatics/bty943'
    comments = ''

    response = client.post('/add_enzyme_effector', data=dict(
                                 enzyme=enzyme,
                                 reaction=reaction,
                                 organism=organism,
                                 models=models,
                                 effector_met=effector_met,
                                 effector_type=effector_type,
                                 effector_evidence_level=evidence_level,
                                 references=references,
                                 comments=comments), follow_redirects=True)

    assert response.status_code == 200


    effector_met = 'nad'
    effector_type = 'Activating'

    evidence_level = '1'
    references = 'https://doi.org/10.1093/bioinformatics/bty942, https://doi.org/10.1093/bioinformatics/bty943'
    comments = ''

    response = client.post('/add_enzyme_effector', data=dict(
                                 enzyme=enzyme,
                                 reaction=reaction,
                                 organism=organism,
                                 models=models,
                                 effector_met=effector_met,
                                 effector_type=effector_type,
                                 effector_evidence_level=evidence_level,
                                 references=references,
                                 comments=comments), follow_redirects=True)

    assert response.status_code == 200

    
def add_misc_infos(client):
    enzyme = '1'
    reaction = '1'
    organism = '1'
    models = '1'
    topic = 'allostery'
    description = 'looks like this met is an allosteric inhibitor for that enzyme'

    evidence_level = '1'
    references = 'https://doi.org/10.1093/bioinformatics/bty942, https://doi.org/10.1093/bioinformatics/bty943'
    comments = ''

    response = client.post('/add_enzyme_misc_info', data=dict(
                                 enzyme=enzyme,
                                 reaction=reaction,
                                 organism=organism,
                                 models=models,
                                 topic=topic,
                                 description=description,
                                 evidence_level=evidence_level,
                                 references=references,
                                 comments=comments), follow_redirects=True)

    assert response.status_code == 200

    topic = 'blurb'
    description = 'looks like this met is an allosteric inhibitor for that enzyme'

    evidence_level = '1'
    references = 'https://doi.org/10.1093/bioinformatics/bty942, https://doi.org/10.1093/bioinformatics/bty943'
    comments = ''

    response = client.post('/add_enzyme_misc_info', data=dict(
                                 enzyme=enzyme,
                                 reaction=reaction,
                                 organism=organism,
                                 models=models,
                                 topic=topic,
                                 description=description,
                                 evidence_level=evidence_level,
                                 references=references,
                                 comments=comments), follow_redirects=True)

    assert response.status_code == 200


def add_model_assumptions(client):

    model = '1'
    assumption = 'allostery sucks'
    description = 'looks like this met is an allosteric inhibitor for that enzyme'
    included_in_model = 'True'
    evidence_level = '1'
    references = 'https://doi.org/10.1093/bioinformatics/bty942, https://doi.org/10.1093/bioinformatics/bty943'
    comments = ''

    response = client.post('/add_model_assumption', data=dict(
                            model=model,
                            assumption=assumption,
                            description=description,
                            evidence_level=evidence_level,
                            included_in_model=included_in_model,
                            references=references,
                            comments=comments), follow_redirects=True)

    assert response.status_code == 200

    model = '1'
    assumption = 'inhibition also sucks'
    description = 'blerb'
    included_in_model = 'True'
    evidence_level = '1'
    references = 'https://doi.org/10.1093/bioinformatics/bty942, https://doi.org/10.1093/bioinformatics/bty943'
    comments = ''

    response = client.post('/add_model_assumption', data=dict(
                            model=model,
                            assumption=assumption,
                            description=description,
                            evidence_level=evidence_level,
                            included_in_model=included_in_model,
                            references=references,
                            comments=comments), follow_redirects=True)

    assert response.status_code == 200


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


class LoadDataConfig(Config):
    LOGIN_DISABLED = True
    WTF_CSRF_ENABLED = False


def main():
    app = create_app(LoadDataConfig)
    app_context = app.app_context()
    app_context.push()
    client = app.test_client()

    #add_models()
    #add_references()
    #add_activations(client)
    add_inhibitions(client)
    add_effectors(client)
    add_misc_infos(client)
    add_model_assumptions(client)

#main()
