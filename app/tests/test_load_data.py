import unittest

from app import create_app, db
from app.load_data.load_initial_data import load_compartments, load_enzymes, load_genes, load_metabolites, \
    load_organisms, load_reactions, load_reference_types, load_enzyme_reaction_relation
from app.models import Compartment, Enzyme, EnzymeGeneOrganism, Gene, Metabolite, Organism, Reaction, \
    ReactionMetabolite, ReferenceType, EnzymeReactionOrganism
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    LOGIN_DISABLED = True
    WTF_CSRF_ENABLED = False


class TestLoadCompartments(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_load_compartments(self):
        load_compartments()

        for compartment in Compartment.query.all():
            print(compartment)

        self.assertEqual(Compartment.query.count(), 15)


class TestLoadEnzymes(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_load_enzymes(self):
        load_enzymes()

        for enzyme in Enzyme.query.all():
            print(enzyme)

        succoas_complex = Enzyme.query.filter_by(isoenzyme='SUCOAS_complex').first()
        self.assertEqual(succoas_complex.enzyme_subunits.count(), 2)
        self.assertEqual(Enzyme.query.count(), 30)


class TestLoadGenes(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        load_enzymes()
        load_organisms()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_load_genes(self):
        load_genes()

        for gene in Gene.query.all():
            print(gene)

        self.assertEqual(Gene.query.count(), 29)
        self.assertEqual(EnzymeGeneOrganism.query.count(), 29)


class TestLoadMetabolites(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        load_compartments()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_load_metabolites(self):
        load_metabolites()

        for met in Metabolite.query.all():
            print(met)

        self.assertEqual(Metabolite.query.count(), 54)


class TestLoadOrganisms(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_load_organisms(self):
        load_organisms()
        self.assertEqual(Organism.query.count(), 3)


class TestLoadReactions(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        load_compartments()
        load_metabolites()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_load_reactions(self):
        load_reactions()

        for rxn in Reaction.query.all():
            print(rxn)
            for rxn_met in ReactionMetabolite.query.filter_by(reaction_id=rxn.id).all():
                print(rxn_met)
            print('---')

        self.assertEqual(Reaction.query.count(), 68)
        self.assertEqual(ReactionMetabolite.query.count(), 305)


class TestLoadReferenceTypes(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_load_reference_types(self):
        load_reference_types()
        self.assertEqual(ReferenceType.query.count(), 4)


class TestLoadEnzymeReactionRelation(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        load_organisms()
        load_enzymes()
        load_compartments()
        load_metabolites()
        load_reactions()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_load_enzyme_reaction_relation(self):
        load_enzyme_reaction_relation()
        self.assertEqual(EnzymeReactionOrganism.query.count(), 28)


if __name__ == '__main__':
    unittest.main(verbosity=2)
