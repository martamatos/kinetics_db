from datetime import datetime, timedelta
import unittest
from app import create_app, db
from app.main.forms import ModelForm
from app.main.routes import add_model
from app.models import User, Post, Compartment, Enzyme, EnzymeOrganism, EnzymeStructure, Gene, Metabolite, Model, \
    Organism, Reaction, ReactionMetabolite
from config import Config
from app.main.routes import add_metabolites_to_reaction, _add_enzyme_organism, _add_enzyme_structures
from app.utils.parsers import parse_input_list
import re


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    LOGIN_DISABLED = True
    WTF_CSRF_ENABLED = False


class UserModelCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_hashing(self):
        u = User(username='susan')
        u.set_password('cat')
        self.assertFalse(u.check_password('dog'))
        self.assertTrue(u.check_password('cat'))

    def test_avatar(self):
        u = User(username='john', email='john@example.com')
        self.assertEqual(u.avatar(128), ('https://www.gravatar.com/avatar/'
                                         'd4c74594d841139328695756648b6bd6'
                                         '?d=identicon&s=128'))

    def test_follow(self):
        u1 = User(username='john', email='john@example.com')
        u2 = User(username='susan', email='susan@example.com')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        self.assertEqual(u1.followed.all(), [])
        self.assertEqual(u1.followers.all(), [])

        u1.follow(u2)
        db.session.commit()
        self.assertTrue(u1.is_following(u2))
        self.assertEqual(u1.followed.count(), 1)
        self.assertEqual(u1.followed.first().username, 'susan')
        self.assertEqual(u2.followers.count(), 1)
        self.assertEqual(u2.followers.first().username, 'john')

        u1.unfollow(u2)
        db.session.commit()
        self.assertFalse(u1.is_following(u2))
        self.assertEqual(u1.followed.count(), 0)
        self.assertEqual(u2.followers.count(), 0)

    def test_follow_posts(self):
        # create four users
        u1 = User(username='john', email='john@example.com')
        u2 = User(username='susan', email='susan@example.com')
        u3 = User(username='mary', email='mary@example.com')
        u4 = User(username='david', email='david@example.com')
        db.session.add_all([u1, u2, u3, u4])

        # create four posts
        now = datetime.utcnow()
        p1 = Post(body="post from john", author=u1,
                  timestamp=now + timedelta(seconds=1))
        p2 = Post(body="post from susan", author=u2,
                  timestamp=now + timedelta(seconds=4))
        p3 = Post(body="post from mary", author=u3,
                  timestamp=now + timedelta(seconds=3))
        p4 = Post(body="post from david", author=u4,
                  timestamp=now + timedelta(seconds=2))
        db.session.add_all([p1, p2, p3, p4])
        db.session.commit()

        # setup the followers
        u1.follow(u2)  # john follows susan
        u1.follow(u4)  # john follows david
        u2.follow(u3)  # susan follows mary
        u3.follow(u4)  # mary follows david
        db.session.commit()

        # check the followed posts of each user
        f1 = u1.followed_posts().all()
        f2 = u2.followed_posts().all()
        f3 = u3.followed_posts().all()
        f4 = u4.followed_posts().all()
        self.assertEqual(f1, [p2, p4, p1])
        self.assertEqual(f2, [p2, p3])
        self.assertEqual(f3, [p3, p4])
        self.assertEqual(f4, [p4])


class EnzymeModelCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_add_enzyme(self):
        enzyme_name = 'PFK'
        enzyme_acronym = 'PFK'
        enzyme_isoenzyme = 'PFK1'
        enzyme_ec_number = '2.1.34.55'

        organism_name = 'E. coli'

        pdb_structure_ids = '3H8A, 1E9I'
        pdb_structure_ids_strains = 'WT, knockout'

        uniprot_id_list = 'PW12D, PE45Q'
        enzyme_number_of_active_sites = 4

        gene_bigg_ids = 'b0001, b003'

        enzyme = Enzyme(name=enzyme_name,
                        acronym=enzyme_acronym,
                        isoenzyme=enzyme_isoenzyme,
                        ec_number=enzyme_ec_number)
        db.session.add(enzyme)

        self.assertEqual(enzyme.query.first().name, enzyme_name)
        self.assertEqual(enzyme.query.first().acronym, enzyme_acronym)
        self.assertEqual(enzyme.query.first().isoenzyme, enzyme_isoenzyme)
        self.assertEqual(enzyme.query.first().ec_number, enzyme_ec_number)
        self.assertEqual(enzyme.query.first().enzyme_structures.count(), 0)

        organism = Organism(name=organism_name)
        db.session.add(organism)

        self.assertEqual(organism.query.first().name, organism_name)

        gene = Gene(name='b0001', bigg_id='b0001')
        db.session.add(gene)
        self.assertEqual(gene.query.count(), 1)

        # populate enzyme_structure
        if pdb_structure_ids:
            pdb_id_list = parse_input_list(pdb_structure_ids)
            strain_list = parse_input_list(pdb_structure_ids_strains)
            _add_enzyme_structures(enzyme, organism.id, pdb_id_list, strain_list)

        # populate enzyme_organism
        if uniprot_id_list:
            uniprot_id_list = parse_input_list(uniprot_id_list)
            _add_enzyme_organism(enzyme, organism.id, uniprot_id_list, gene_bigg_ids, enzyme_number_of_active_sites)


        db.session.commit()


        self.assertEqual(gene.query.count(), 2)

        self.assertEqual(Enzyme.query.first().enzyme_structures.count(), 2)
        self.assertEqual(Gene.query.all()[0].enzyme_organisms.count(), 2)
        self.assertEqual(Gene.query.all()[1].enzyme_organisms.count(), 2)

        self.assertEqual(EnzymeStructure.query.count(), 2)
        self.assertEqual(EnzymeStructure.query.all()[0].pdb_id, '3H8A')
        self.assertEqual(EnzymeStructure.query.all()[0].strain, 'WT')
        self.assertEqual(EnzymeStructure.query.all()[1].pdb_id, '1E9I')
        self.assertEqual(EnzymeStructure.query.all()[1].strain, 'knockout')
        self.assertEqual(EnzymeStructure.query.all()[0].organism.name, organism_name)
        self.assertEqual(EnzymeStructure.query.all()[1].organism.name, organism_name)
        self.assertEqual(EnzymeStructure.query.all()[0].enzyme.name, enzyme_name)
        self.assertEqual(EnzymeStructure.query.all()[1].enzyme.name, enzyme_name)


        self.assertEqual(EnzymeOrganism.query.all()[0].n_active_sites, enzyme_number_of_active_sites)
        self.assertEqual(EnzymeOrganism.query.all()[1].n_active_sites, enzyme_number_of_active_sites)
        self.assertEqual(EnzymeOrganism.query.all()[0].uniprot_id, 'PW12D')
        self.assertEqual(EnzymeOrganism.query.all()[1].uniprot_id, 'PE45Q')
        self.assertEqual(EnzymeOrganism.query.all()[0].organism.name, organism_name)
        self.assertEqual(EnzymeOrganism.query.all()[1].organism.name, organism_name)
        self.assertEqual(EnzymeOrganism.query.all()[0].enzyme.acronym, enzyme_acronym)
        self.assertEqual(EnzymeOrganism.query.all()[1].enzyme.acronym, enzyme_acronym)
        self.assertEqual(EnzymeOrganism.query.all()[0].genes[0].bigg_id, 'b0001')
        self.assertEqual(EnzymeOrganism.query.all()[0].genes[1].bigg_id, 'b003')
        self.assertEqual(EnzymeOrganism.query.all()[1].genes[0].bigg_id, 'b0001')
        self.assertEqual(EnzymeOrganism.query.all()[1].genes[1].bigg_id, 'b003')


class GeneModelCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_add_gene(self):
        gene_name = 'pfkA'
        gene_bigg_id = 'b0001'

        gene = Gene(name=gene_name, bigg_id=gene_bigg_id)
        db.session.add(gene)
        db.session.commit()

        self.assertEqual(gene.query.first().name, gene_name)
        self.assertEqual(gene.query.first().bigg_id, gene_bigg_id)
        self.assertEqual(gene.query.first().enzyme_organisms.count(), 0)


class ModelModelCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_add_model_and_create_organism(self):
        organism_name = 'E coli'
        model_name = 'E coli - test'
        model_strain = 'MG16555'
        model_comments = 'just testing'

        organism = Organism.query.filter_by(name=organism_name).first()
        if not organism:
            organism = Organism(name=organism_name)
            db.session.add(organism)

        model = Model(name=model_name,
                      organism_name=organism_name,
                      strain=model_strain,
                      comments=model_comments)

        db.session.add(model)
        organism.add_model(model)
        db.session.commit()

        self.assertEqual(organism.query.first().name, organism_name)
        self.assertEqual(organism.models.first().name, model_name)
        self.assertEqual(model.query.first().name, model_name)
        self.assertEqual(model.query.first().strain, model_strain)
        self.assertEqual(model.query.first().comments, model_comments)

    def test_add_model_for_existing_organism(self):
        organism_name = 'E coli'
        model_name = 'E coli - test'
        model_strain = 'MG16555'
        model_comments = 'just testing'

        organism = Organism(name=organism_name)
        db.session.add(organism)
        db.session.commit()

        self.assertEqual(organism.query.first().name, organism_name)
        self.assertEqual(organism.query.first().models.count(), 0)

        model = Model(name=model_name,
                      organism_name=organism_name,
                      strain=model_strain,
                      comments=model_comments)

        db.session.add(model)
        organism.add_model(model)
        db.session.commit()

        self.assertEqual(organism.query.first().models.count(), 1)
        self.assertEqual(organism.query.first().models[0].name, model_name)
        self.assertEqual(model.query.first().name, model_name)
        self.assertEqual(model.query.first().strain, model_strain)
        self.assertEqual(model.query.first().comments, model_comments)
        self.assertEqual(model.query.first().organism.name, organism_name)


class OrganismModelCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_add_organism(self):
        organism_name = 'E coli'

        organism = Organism(name=organism_name)
        db.session.add(organism)
        db.session.commit()

        self.assertEqual(organism.query.first().name, organism_name)

class TestFormsCase(unittest.TestCase):
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

    def test_main_page(self):
        #response = self.client.get('/', follow_redirects=True)
        #self.assertEqual(response.status_code, 200)

        response = self.client.post('/add_organism', data=dict(
                            name='E. coli'), follow_redirects=True)

        print(response.data)
        print(response.status_code)
        self.assertEqual(response.status_code, 200)

        response = self.client.post('/add_model', data=dict(
                                    name='E. coli - iteration 1',
        #organism_name='E. coli',
        strain='MG16555'), follow_redirects=True)

        print(response.data)
        print(response.status_code)
        form=ModelForm()
        print(Organism().query.all())
        print(Model().query.all())
        print(b'<h1>Add model</h1>' in response.data)
        self.assertEqual(response.status_code, 200)



"""
        form.name.data = 'E. coli - iteration 1'
        form.organism_name.data = 'E. coli'

        organism_name = 'E coli'

        organism = Organism(name=organism_name)
        db.session.add(organism)
        db.session.commit()

        self.assertEqual(organism.query.first().name, organism_name)"""
"""

  class ModelForm(FlaskForm):
    name = StringField('Model name (e.g. E coli - iteration 1) *', validators=[DataRequired()])
    organism_name = StringField('Organism name (eg. E coli) *', validators=[DataRequired()], id='organism_name')
    strain = StringField('Organism strain (e.g. MG1655)')
    comments = TextAreaField('Comments')

    submit = SubmitField('Submit')
"""

"""
class ReactionModelCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_add_reaction_without_existing_metabolites(self):
        organism_name = 'E coli'
        model_name = 'E coli - test'
        model_strain = 'MG16555'
        model_comments = 'just testing'

        organism = Organism(name=organism_name)
        db.session.add(organism)

        self.assertEqual(Organism.query.first().name, organism_name)

        model = Model(name=model_name,
                      organism_name=organism_name,
                      strain=model_strain,
                      comments=model_comments)
        db.session.add(model)

        self.assertEqual(Model.query.first().name, model_name)
        self.assertEqual(Model.query.first().organism_name, organism_name)
        self.assertEqual(Model.query.first().strain, model_strain)
        self.assertEqual(Model.query.first().comments, model_comments)

        compartment_name = 'cytoplasm'
        compartment_acronym = 'c'

        compartment = Compartment(name=compartment_name,
                                  acronym=compartment_acronym)
        db.session.add(compartment)

        self.assertEqual(Compartment.query.first().name, compartment_name)
        self.assertEqual(Compartment.query.first().acronym, compartment_acronym)

        reaction_name = 'pyruvate kinase'
        reaction_grasp_id = 'PYK'
        reaction_string = 'pep_c + 1.0 adp_c <-> pyr_c + 1 atp_c'
        met_list = ['pep_c', 'adp_c', 'pyr_c', 'atp_c']
        stoic_coef_list = [-1, -1, 1, 1]
        compartment_name = 'cytoplasm'

        reaction = Reaction(name=reaction_name,
                            grasp_id=reaction_grasp_id,
                            compartment_name=compartment_name)

        db.session.add(reaction)

        self.assertEqual(Reaction.query.first().name, reaction_name)
        self.assertEqual(Reaction.query.first().grasp_id, reaction_grasp_id)
        self.assertEqual(Reaction.query.first().compartment_name, compartment_name)

        add_metabolites_to_reaction(reaction, reaction_string)
        db.session.commit()

        for i, met in enumerate(Metabolite.query.all()):
            self.assertEqual(met.grasp_id, met_list[i])
            self.assertEqual(len(met.reactions.all()), 1)
            self.assertEqual(met.reactions.first().reaction.grasp_id, reaction_grasp_id)

        for i, rxn_met in enumerate(reaction.metabolites.all()):
            self.assertEqual(rxn_met.reaction.grasp_id, reaction_grasp_id)
            self.assertEqual(rxn_met.metabolite.grasp_id, met_list[i])
            self.assertEqual(rxn_met.stoich_coef, stoic_coef_list[i])

        for i, rxn_met in enumerate(ReactionMetabolite.query.all()):
            self.assertEqual(rxn_met.reaction.grasp_id, reaction_grasp_id)
            self.assertEqual(rxn_met.metabolite.grasp_id, met_list[i])
            self.assertEqual(rxn_met.stoich_coef, stoic_coef_list[i])

"""
if __name__ == '__main__':
    unittest.main(verbosity=2)
