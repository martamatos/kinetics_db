from app import create_app, db
from app.models import Compartment, Enzyme, EvidenceLevel, Mechanism, Metabolite, Model, Organism, Reaction, Reference, ReferenceType,EnzymeReactionOrganism
from app.utils.parsers import ReactionParser
import re


def add_compartments():
    compartment_list = [('Cytosol', 'c'), ('Mitochondria', 'm')]

    for name, acronym in compartment_list:
        compartment = Compartment(name=name, acronym=acronym)
        db.session.add(compartment)
    db.session.commit()


def add_evidence_levels():
    evidence_list = [('Literature 1', 'Got it from papers for the given organism'),
                     ('Literature 2', 'Got it from papers of other organisms'),
                     ('Predicted', 'Predicted by some algorithm'),
                     ('Educated guess', '')]

    for name, description in evidence_list:
        evidence = EvidenceLevel(name=name, description=description)
        db.session.add(evidence)
    db.session.commit()


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




def add_references():
    reference = Reference(title='eQuilibrator', type_type='Online database')
    db.session.add(reference)
    db.session.commit()


def add_reference_types():
    reference_type_list = ['Article', 'Thesis', 'Online database', 'Book']

    for type in reference_type_list:
        reference_type = ReferenceType(type=type)
        db.session.add(reference_type)
    db.session.commit()

# only for development
def add_enzymes():
    enzyme_list = [('Phosphofructokinase', 'PFK', 'PFK1', '1.2.3.33'),
                     ('Phosphofructokinase', 'PFK', 'PFK2', '1.2.3.33')]

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


# only for development
def add_reactions():
        reaction_name = ' Phosphofructokinase'
        reaction_acronym = 'PFK'
        reaction_bigg_id = 'PFK'
        reaction_kegg_id = ''
        reaction_string = '1 pep_c + adp_c <-> 1.5 pyr_c + atp_c'

        compartment_name = 'Cytosol'

        reaction = Reaction(name=reaction_name,
                            acronym=reaction_acronym,
                            metanetx_id=reaction_bigg_id,
                            bigg_id=reaction_kegg_id,
                            kegg_id=reaction_kegg_id,
                            compartment_name=compartment_name)

        db.session.add(reaction)

        reversible, stoichiometry = ReactionParser().parse_reaction(reaction_string)
        for met, stoich_coef in stoichiometry.items():
            bigg_id = re.findall('(\w+)_(?:\S+)', met)[0]
            compartment_acronym = re.findall('(?:\S+)_(\w+)', met)[0]
            met_db = Metabolite(bigg_id=bigg_id,
                                grasp_id=bigg_id,
                                compartment_acronym=compartment_acronym)

            db.session.add(met_db)

            reaction.add_metabolite(met_db, stoich_coef)

def add_enzyme_reaction_organism():

    model = Model.query.filter_by(name='E. coli - iteration 1', organism_name='E. coli', strain='MG16555').first()

    grasp_id = 'PFK'
    subs_binding_order = 'adp_c, pep_c'
    prod_release_order = 'pyr_c, atp_c'
    enzyme_reaction_model = EnzymeReactionOrganism(enzyme_id=1,
                                                    reaction_id = 1,
                                                    organism_id=1,
                                                    mechanism_id= 1,
                                                    mech_evidence_level_id=1,
                                                    grasp_id=grasp_id,
                                                    subs_binding_order=subs_binding_order,
                                                    prod_release_order=prod_release_order)

    db.session.add(enzyme_reaction_model)
    enzyme_reaction_model.add_model(model)
    db.session.commit()

def main():
    app=create_app()
    app_context = app.app_context()
    app_context.push()

    add_organisms()
    add_compartments()
    add_enzymes()
    add_evidence_levels()
    add_mechanisms()
    add_models()

    add_reference_types()
    add_references()

    #add_reactions()
    #add_enzyme_reaction_model


#main()


