import re
import unittest

from app import create_app, db
from app.models import Compartment, Enzyme, EnzymeOrganism, EnzymeReactionOrganism, EnzymeStructure, \
    EvidenceLevel, Gene, GibbsEnergy, GibbsEnergyReactionModel, Mechanism, Metabolite, Model, Organism, Reaction, \
    ReactionMetabolite, Reference, EnzymeGeneOrganism, \
    ReferenceType, EnzymeReactionInhibition, EnzymeReactionActivation, EnzymeReactionEffector, EnzymeReactionMiscInfo, \
    ModelAssumptions
from app.utils.parsers import parse_input_list, ReactionParser
from app.utils.populate_db import add_models, add_mechanisms, add_reaction, add_reference_types, add_enzymes, \
    add_compartments, add_evidence_levels, add_organisms, add_references
from config import Config
from werkzeug.datastructures import FileStorage


class TestConfig(Config):
    TESTING = True
    #SQLALCHEMY_DATABASE_URI = 'sqlite://'
    POSTGRES_DB = 'kinetics_db_test'
    LOGIN_DISABLED = True
    WTF_CSRF_ENABLED = False
    UPLOAD_FOLDER = '../../uploaded_models'


def populate_db(test_case, client=None):
    if test_case == 'upload_model':
        add_compartments()
        add_evidence_levels()
        add_mechanisms()
        add_organisms()
        add_enzymes(client)
        add_models()
        add_reference_types()
        add_references()
        add_reaction(client)

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


class TestUploadModel(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        populate_db('upload_model', self.client)

        self.file_name = 'HMP1489_r1_t0.xlsx'
        self.file = FileStorage(open(self.file_name, 'rb'))

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_upload_model(self):

        organism = '1'
        response = self.client.post('/upload_model', data=dict(
                                    organism=organism,
                                    model=self.file), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See models - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your model is now live!' in response.data)


    """
            self.assertEqual(Enzyme.query.count(), 2)
            self.assertEqual(GibbsEnergy.query.count(), 1)
            self.assertEqual(EnzymeReactionOrganism.query.count(), 1)
            self.assertEqual(Mechanism.query.count(), 2)
            self.assertEqual(Reference.query.count(), 2)
            self.assertEqual(Model.query.count(), 2)
            self.assertEqual(Organism.query.count(), 2)
            self.assertEqual(Model.query.first().enzyme_reaction_organisms.count(), 1)

            self.assertEqual(Reaction.query.count(), 1)
            self.assertEqual(Reaction.query.first().name, self.reaction_name)
            self.assertEqual(Reaction.query.first().compartment_name, Compartment.query.first().name)

            self.assertEqual(EnzymeReactionOrganism.query.first().enzyme_id, 1)
            self.assertEqual(EnzymeReactionOrganism.query.first().reaction_id, 1)
            self.assertEqual(EnzymeReactionOrganism.query.first().organism_id, 1)
            self.assertEqual(EnzymeReactionOrganism.query.first().mechanism_id, 1)
            self.assertEqual(EnzymeReactionOrganism.query.first().mech_evidence_level_id, 1)

            self.assertEqual(EnzymeReactionOrganism.query.first().grasp_id, self.reaction_grasp_id)
            self.assertEqual(EnzymeReactionOrganism.query.first().subs_binding_order, self.subs_binding_order)
            self.assertEqual(EnzymeReactionOrganism.query.first().prod_release_order, self.prod_release_order)
            self.assertEqual(EnzymeReactionOrganism.query.first().reaction.name, self.reaction_name)
            self.assertEqual(EnzymeReactionOrganism.query.first().enzyme.isoenzyme, true_isoenzyme_acronym)
            self.assertEqual(EnzymeReactionOrganism.query.first().models[0], Model.query.first())
            self.assertEqual(EnzymeReactionOrganism.query.first().mech_evidence, EvidenceLevel.query.first())
            self.assertEqual(EnzymeReactionOrganism.query.first().mechanism, Mechanism.query.first())
            self.assertEqual(EnzymeReactionOrganism.query.all()[0].mechanism_references[0].doi, self.mechanism_references)

            self.assertEqual(GibbsEnergyReactionModel.query.count(), 1)
            self.assertEqual(GibbsEnergyReactionModel.query.first().reaction_id, 1)
            self.assertEqual(GibbsEnergyReactionModel.query.first().model_id, 1)
            self.assertEqual(GibbsEnergyReactionModel.query.first().gibbs_energy_id, 1)

            self.assertEqual(GibbsEnergy.query.first().standard_dg, self.std_gibbs_energy)
            self.assertEqual(GibbsEnergy.query.first().standard_dg_std, self.std_gibbs_energy_std)
            self.assertEqual(GibbsEnergy.query.first().ph, self.std_gibbs_energy_ph)
            self.assertEqual(GibbsEnergy.query.first().ionic_strength, self.std_gibbs_energy_ionic_strength)
            self.assertEqual(GibbsEnergy.query.first().references[0].title, true_gibbs_energy_ref)

            self.assertEqual(Reference.query.all()[0].title, true_gibbs_energy_ref)
            self.assertEqual(Reference.query.all()[0].type.type, 'Online database')
            self.assertEqual(Reference.query.all()[1].doi, self.mechanism_references)

            self.assertEqual(Metabolite.query.count(), 4)
            self.assertEqual(Metabolite.query.all()[0].bigg_id, 'pep')
            self.assertEqual(Metabolite.query.all()[0].grasp_id, 'pep')
            self.assertEqual(Metabolite.query.all()[0].compartments[0].bigg_id, 'c')
            self.assertEqual(Metabolite.query.all()[1].bigg_id, 'adp')
            self.assertEqual(Metabolite.query.all()[1].grasp_id, 'adp')
            self.assertEqual(Metabolite.query.all()[1].compartments[0].bigg_id, 'c')
            self.assertEqual(Metabolite.query.all()[2].bigg_id, 'pyr')
            self.assertEqual(Metabolite.query.all()[2].grasp_id, 'pyr')
            self.assertEqual(Metabolite.query.all()[2].compartments[0].bigg_id, 'c')
            self.assertEqual(Metabolite.query.all()[3].bigg_id, 'atp')
            self.assertEqual(Metabolite.query.all()[3].grasp_id, 'atp')
            self.assertEqual(Metabolite.query.all()[3].compartments[0].bigg_id, 'm')

            self.assertEqual(ReactionMetabolite.query.count(), 4)
            self.assertEqual(ReactionMetabolite.query.all()[0].metabolite.bigg_id, 'pep')
            self.assertEqual(ReactionMetabolite.query.all()[0].compartment.bigg_id, 'c')
            self.assertEqual(ReactionMetabolite.query.all()[0].stoich_coef, -1)
            self.assertEqual(ReactionMetabolite.query.all()[0].reaction.acronym, self.reaction_acronym)
            self.assertEqual(ReactionMetabolite.query.all()[1].metabolite.bigg_id, 'adp')
            self.assertEqual(ReactionMetabolite.query.all()[1].compartment.bigg_id, 'c')
            self.assertEqual(ReactionMetabolite.query.all()[1].stoich_coef, -1.5)
            self.assertEqual(ReactionMetabolite.query.all()[1].reaction.acronym, self.reaction_acronym)
            self.assertEqual(ReactionMetabolite.query.all()[2].metabolite.bigg_id, 'pyr')
            self.assertEqual(ReactionMetabolite.query.all()[2].compartment.bigg_id, 'c')
            self.assertEqual(ReactionMetabolite.query.all()[2].stoich_coef, 1)
            self.assertEqual(ReactionMetabolite.query.all()[2].reaction.acronym, self.reaction_acronym)
            self.assertEqual(ReactionMetabolite.query.all()[3].metabolite.bigg_id, 'atp')
            self.assertEqual(ReactionMetabolite.query.all()[3].compartment.bigg_id, 'm')
            self.assertEqual(ReactionMetabolite.query.all()[3].stoich_coef, 2)
            self.assertEqual(ReactionMetabolite.query.all()[3].reaction.acronym, self.reaction_acronym)

    """


class TestDownloadModel(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        populate_db('upload_model', self.client)

        self.file_name = 'HMP1489_r1_t0.xlsx'
        self.file = FileStorage(open(self.file_name, 'rb'))

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_download_model(self):
        return 0

if __name__ == '__main__':
    unittest.main(verbosity=2)
