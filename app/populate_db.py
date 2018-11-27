from app import create_app, db
from app.models import Compartment, Enzyme, EvidenceLevel, Mechanism, Model, Organism, Reference, ReferenceType


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


# only for development
def add_enzymes():
    enzyme_list = [('Phosphofructokinase', 'PFK', 'PFK1', '1.2.3.33'),
                     ('Phosphofructokinase', 'PFK', 'PFK2', '1.2.3.33')]

    for name, acronym, isoenzyme, ec_number in enzyme_list:
        enzyme = Enzyme(name=name, acronym=acronym, isoenzyme=isoenzyme, ec_number=ec_number)
        db.session.add(enzyme)
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
def add_models():
    model_list = [('E. coli - iteration 1', 'E. coli', 'MG16555'),
                  ('E. coli - iteration 2', 'E. coli', 'MG16555')]

    for name, organism_name, strain in model_list:
        model = Model(name=name, organism_name=organism_name, strain=strain)
        db.session.add(model)
    db.session.commit()


if __name__ == '__main__':

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

