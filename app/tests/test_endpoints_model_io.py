import re
import unittest
import os
from app import create_app, db
from app.models import Compartment, Enzyme, EnzymeOrganism, EnzymeReactionOrganism, EnzymeStructure, \
    EvidenceLevel, Gene, GibbsEnergy, GibbsEnergyReactionModel, Mechanism, Metabolite, Model, Organism, Reaction, \
    ReactionMetabolite, Reference, EnzymeGeneOrganism, Reference,\
    ReferenceType, EnzymeReactionInhibition, EnzymeReactionActivation, EnzymeReactionEffector, EnzymeReactionMiscInfo, \
    ModelAssumptions
from app.utils.parsers import parse_input_list, ReactionParser
from app.utils.populate_db import add_models, add_mechanisms, add_reaction, add_reference_types, add_enzymes, \
    add_compartments, add_evidence_levels, add_organisms, add_references, add_ex_enzyme
from config import Config
from werkzeug.datastructures import FileStorage


class TestConfig(Config):
    TESTING = True
    #SQLALCHEMY_DATABASE_URI = 'sqlite://'
    POSTGRES_DB = 'kinetics_db_test'
    LOGIN_DISABLED = True
    WTF_CSRF_ENABLED = False
    UPLOAD_FOLDER = '../../uploaded_models'
    DOWNLOAD_FOLDER = '../static/models'


def populate_db(test_case, client=None):

    if test_case == 'upload_model':
        add_compartments()
        add_evidence_levels()
        add_mechanisms()
        add_organisms()
        add_ex_enzyme()
        #add_models()
        add_reference_types()
        add_references()
        #add_reaction(client)
    """
    else:
        add_compartments()
        add_evidence_levels()
        add_mechanisms()
        add_organisms()
        add_enzymes(client)
        add_models()
        add_reference_types()
        add_references()
        add_reaction(client)"""


class TestUploadModel(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.drop_all()
        db.create_all()

        populate_db('upload_model', self.client)

        this_dir, this_filename = os.path.split(__file__)
        self.test_folder = os.path.join(this_dir, 'test_files', 'test_import_grasp_model')
        self.model_file = os.path.join(self.test_folder, 'HMP1489_r1_t0.xlsx')
        self.model_file = FileStorage(open(self.model_file, 'rb'))

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_upload_model(self):

        organism = '1'
        response = self.client.post('/upload_model', data=dict(
                                    organism=organism,
                                    model=self.model_file), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See models - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your model is now live!' in response.data)

        print(Metabolite.query.all())
        print(Enzyme.query.all())

        self.assertEqual(Organism.query.count(), 2)
        self.assertEqual(Model.query.count(), 1)
        self.assertEqual(Metabolite.query.count(), 21)
        self.assertEqual(Compartment.query.count(), 4)
        self.assertEqual(Enzyme.query.count(), 5)
        self.assertEqual(Reaction.query.count(), 10)
        self.assertEqual(ReactionMetabolite.query.count(), 28)
        self.assertEqual(EnzymeReactionOrganism.query.count(), 10)
        self.assertEqual(EnzymeReactionInhibition.query.count(), 6)
        self.assertEqual(EnzymeReactionActivation.query.count(), 2)
        self.assertEqual(EnzymeReactionEffector.query.count(), 6)
        self.assertEqual(EnzymeOrganism.query.count(), 5)
        self.assertEqual(EnzymeStructure.query.count(), 2)
        self.assertEqual(Reference.query.count(), 12)

        subunit_list = [1, 4, 2, 1, 2, 2]
        uniprot_id_list =['3CV8K', 'H12KP']
        pdb_id_list = ['1UCW', '1E9I']

        for i, enz in enumerate(Enzyme.query.all()):
            enz_org_list = EnzymeOrganism.query.filter_by(enzyme_id=enz.id, organism_id=1).all()

            for enz_org in enz_org_list:
                self.assertEqual(enz_org.n_active_sites, subunit_list[i])

            if enz.isoenzyme == 'DDC':
                for j, enz_org in enumerate(enz_org_list):
                    self.assertEqual(enz_org.uniprot_id, uniprot_id_list[j])

        enz_struct_list = EnzymeStructure.query.filter_by(enzyme_id=3, organism_id=1).all()
        for i, enz_struct in enz_struct_list:
            self.assertEqual(enz_struct.pdb_id, pdb_id_list[i])

        mechanism_list = [('substrateInhibOrderedBiBi', 'OrderedBiBi'), ('UniUniPromiscuous', 'UniUni'),
                          ('OrderedBiBiCompInhibPromiscuousIndep', 'OrderedBiBi'), ('randomBiBICompInhib', 'RandomBiBi'),
                          ('UniUniPromiscuous', 'UniUni'), ('OrderedBiBiCompInhibPromiscuousIndep', 'OrderedBiBi'),
                          ('massAction', 'massAction'), ('massAction', 'massAction'), ('massAction', 'massAction'),
                          ('massAction', 'massAction')]

        for i, enz_rxn_org in enumerate(EnzymeReactionOrganism.query.all()):
            self.assertEqual(enz_rxn_org.mechanism.grasp_name.lower(), mechanism_list[i][0].lower())
            self.assertEqual(enz_rxn_org.mechanism.name.lower(), mechanism_list[i][1].lower())


class TestDownloadModel(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.drop_all()
        db.create_all()
        populate_db('upload_model', self.client)

        this_dir, this_filename = os.path.split(__file__)
        self.test_folder = os.path.join(this_dir, 'test_files', 'test_import_grasp_model')
        self.model_file = os.path.join(self.test_folder, 'HMP1489_r1_t0.xlsx')
        self.model_file = FileStorage(open(self.model_file, 'rb'))

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_download_model(self):

        organism = '1'
        response = self.client.post('/upload_model', data=dict(
                                    organism=organism,
                                    model=self.model_file), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See models - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your model is now live!' in response.data)

        model_name = 'HMP1489_r1_t0'
        response = self.client.post('/download_model/' + model_name, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(os.path.isfile(os.path.join(self.app.download_path, model_name + '.xlsx')))


if __name__ == '__main__':
    unittest.main(verbosity=2)
