import unittest
from datetime import datetime, timedelta

from app import create_app, db
from app.models import User, Post, Enzyme, EnzymeOrganism, EnzymeStructure, Gene, Model, \
    Organism, EnzymeGeneOrganism
from app.utils.parsers import parse_input_list
from config import Config


class TestConfig(Config):
    TESTING = True
    #SQLALCHEMY_DATABASE_URI = 'sqlite://'
    POSTGRES_DB = 'kinetics_db_test'
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

        gene = Gene(name='b0001')
        db.session.add(gene)
        self.assertEqual(gene.query.count(), 1)

        # populate enzyme_structure
        if pdb_structure_ids:
            pdb_id_list = parse_input_list(pdb_structure_ids)
            strain_list = parse_input_list(pdb_structure_ids_strains)
            for pdb_id, pdb_id_strain in zip(pdb_id_list, strain_list):
                enzyme_structure_db = EnzymeStructure(enzyme_id=enzyme.id,
                                                      pdb_id=pdb_id,
                                                      organism_id=organism.id,
                                                      strain=pdb_id_strain)
                db.session.add(enzyme_structure_db)

        # populate enzyme_organism
        if uniprot_id_list:
            uniprot_id_list = parse_input_list(uniprot_id_list)

            for uniprot_id in uniprot_id_list:
                enzyme_organism_db = EnzymeOrganism.query.filter_by(uniprot_id=uniprot_id).first()
                if not enzyme_organism_db:
                    enzyme_organism_db = EnzymeOrganism(enzyme_id=enzyme.id,
                                                        organism_id=organism.id,
                                                        uniprot_id=uniprot_id,
                                                        n_active_sites=enzyme_number_of_active_sites)

                    db.session.add(enzyme_organism_db)

                enzyme.add_enzyme_organism(enzyme_organism_db)

                # populate genes
                if gene_bigg_ids:
                    gene_bigg_ids_list = parse_input_list(gene_bigg_ids)
                    for gene_name in gene_bigg_ids_list:
                        gene_db = Gene.query.filter_by(name=gene_name).first()
                        if not gene_db:
                            gene_db = Gene(name=gene_name)
                            db.session.add(gene_db)
                            db.session.commit()

                        enzyme_gene_organism_db = EnzymeGeneOrganism.query.filter_by(gene_id=gene_db.id,
                                                                                     enzyme_id=enzyme.id,
                                                                                     organism_id=organism.id).first()
                        if not enzyme_gene_organism_db:
                            enzyme_gene_organism = EnzymeGeneOrganism(gene_id=gene_db.id,
                                                                      enzyme_id=enzyme.id,
                                                                      organism_id=organism.id)
                            db.session.add(enzyme_gene_organism)

        db.session.commit()

        self.assertEqual(gene.query.count(), 2)

        self.assertEqual(Enzyme.query.first().enzyme_structures.count(), 2)
        self.assertEqual(Gene.query.all()[0].enzyme_gene_organisms.count(), 1)
        self.assertEqual(Gene.query.all()[1].enzyme_gene_organisms.count(), 1)

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
        self.assertEqual(EnzymeGeneOrganism.query.all()[0].gene.name, 'b0001')
        self.assertEqual(EnzymeGeneOrganism.query.all()[1].gene.name, 'b003')


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

        gene = Gene(name=gene_name)
        db.session.add(gene)
        db.session.commit()

        self.assertEqual(gene.query.first().name, gene_name)
        self.assertEqual(gene.query.first().enzyme_gene_organisms.count(), 0)


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


if __name__ == '__main__':
    unittest.main(verbosity=2)
