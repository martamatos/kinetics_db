import unittest

from app import create_app, db
from app.utils.populate_db import add_models, add_mechanisms, add_reaction, add_reference_types, add_enzymes, \
    add_compartments, add_evidence_levels, add_organisms, add_references, add_activations, add_effectors, \
    add_inhibitions, add_misc_infos, add_model_assumptions
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    LOGIN_DISABLED = True
    WTF_CSRF_ENABLED = False


def populate_db(test_case, client=None):
    if test_case == 'reaction':
        add_compartments()
        add_evidence_levels()
        add_mechanisms()
        add_organisms()
        add_enzymes(client)
        add_models()
        add_reference_types()
        add_references()

    else:
        add_compartments()
        add_evidence_levels()
        add_mechanisms()
        add_organisms()
        add_enzymes(client)
        add_models()
        add_reference_types()
        add_references()
        add_reaction(client)
        add_activations(client)
        add_inhibitions(client)
        add_effectors(client)
        add_misc_infos(client)
        add_model_assumptions(client)


class TestSeeEnzyme(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        populate_db('see_enzyme', self.client)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_see_enzyme_list(self):
        response = self.client.get('/see_enzyme_list', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See enzymes - Kinetics DB \n</title>' in response.data)

    def test_see_enzyme(self):
        response = self.client.get('/see_enzyme/PFK1', follow_redirects=True)

        self.assertEqual(response.status_code, 200)


class TestSeeEnzymeInhibitor(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        populate_db('see_enzyme_inhibitor', self.client)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_see_enzyme_inhibitors_list(self):
        response = self.client.get('/see_enzyme_inhibitors_list', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See enzyme inhibitors - Kinetics DB \n</title>' in response.data)

    def test_see_enzyme_inhibitor(self):
        response = self.client.get('/see_enzyme_inhibitor/1', follow_redirects=True)

        self.assertEqual(response.status_code, 200)


class TestSeeEnzymeActivator(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        populate_db('see_enzyme_activator', self.client)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_see_enzyme_activators_list(self):
        response = self.client.get('/see_enzyme_activators_list', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See enzyme activators - Kinetics DB \n</title>' in response.data)

    def test_see_enzyme_activator(self):
        response = self.client.get('/see_enzyme_activator/1', follow_redirects=True)

        self.assertEqual(response.status_code, 200)


class TestSeeEnzymeEffector(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        populate_db('see_enzyme_effector', self.client)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_see_enzyme_effectors_list(self):
        response = self.client.get('/see_enzyme_effectors_list', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See enzyme effectors - Kinetics DB \n</title>' in response.data)

    def test_see_enzyme_effector(self):
        response = self.client.get('/see_enzyme_effector/1', follow_redirects=True)

        self.assertEqual(response.status_code, 200)


class TestSeeEnzymeMiscInfo(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        populate_db('see_enzyme_misc_info', self.client)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_see_enzyme_misc_info_list(self):
        response = self.client.get('/see_enzyme_misc_info_list', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See enzyme misc info - Kinetics DB \n</title>' in response.data)

    def test_see_enzyme_misc_info(self):
        response = self.client.get('/see_enzyme_misc_info/1', follow_redirects=True)

        self.assertEqual(response.status_code, 200)


class TestSeeMechanism(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        populate_db('see_metabolite', self.client)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_see_mechanim_list(self):
        response = self.client.get('/see_mechanism_list', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See mechanisms - Kinetics DB \n</title>' in response.data)


class TestSeeMetabolite(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        populate_db('see_metabolite', self.client)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_see_metabolite_list(self):
        response = self.client.get('/see_metabolite_list', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See metabolites - Kinetics DB \n</title>' in response.data)

    def test_see_metabolite(self):
        response = self.client.get('/see_metabolite/atp', follow_redirects=True)

        self.assertEqual(response.status_code, 200)


class TestSeeModel(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        populate_db('see_model', self.client)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_see_model_list(self):
        response = self.client.get('/see_model_list', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See models - Kinetics DB \n</title>' in response.data)

    def test_see_model(self):
        response = self.client.get('/see_model/E. coli - iteration 2', follow_redirects=True)

        self.assertEqual(response.status_code, 200)


class TestSeeModelAssumption(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        populate_db('see_model_assumption', self.client)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_see_model_assumption_list(self):
        response = self.client.get('/see_model_assumptions_list', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See model assumptions - Kinetics DB \n</title>' in response.data)

    def test_see_model_assumption(self):
        response = self.client.get('/see_model_assumption/1', follow_redirects=True)

        self.assertEqual(response.status_code, 200)


class TestSeeOrganism(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        populate_db('see_organism', self.client)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_see_organism_list(self):
        response = self.client.get('/see_organism_list', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See organisms - Kinetics DB \n</title>' in response.data)

    def test_see_organism(self):
        response = self.client.get('/see_organism/E. coli', follow_redirects=True)

        self.assertEqual(response.status_code, 200)


class TestSeeReaction(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        populate_db('see_organism', self.client)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_see_reaction_list(self):
        response = self.client.get('/see_reaction_list', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See reactions - Kinetics DB \n</title>' in response.data)

    def test_see_reaction(self):
        response = self.client.get('/see_reaction/PFK', follow_redirects=True)

        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main(verbosity=2)
