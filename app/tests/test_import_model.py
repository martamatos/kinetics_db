import unittest

import numpy as np
import pandas as pd

from app import create_app, db
from app.main.utils import set_binding_release_order
from app.models import Enzyme, EnzymeReactionOrganism, Organism, Reaction
from app.utils.import_model import get_model_name, get_model_stoichiometry, get_model_enzymes, get_model_subunits, \
    get_model_mechanisms, get_model_inhibitors, get_model_activators, get_model_effectors, get_model_gibbs_energies
from app.utils.populate_db import add_models, add_mechanisms, add_reaction, add_reference_types, add_enzymes, \
    add_compartments, add_evidence_levels, add_organisms, add_references
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    LOGIN_DISABLED = True
    WTF_CSRF_ENABLED = False
    UPLOAD_FOLDER = '../../uploaded_models'


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

    elif test_case == 'model':
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


class TestImportModel(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        populate_db('import_model', self.client)

        self.file_name = 'HMP1489_r1_t0.xlsx'

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_get_model_name(self):
        true_model_name = 'HMP1489_r1_t0'
        sheet_name = 'general'
        model_name = get_model_name(self.file_name, sheet_name)

        self.assertEqual(model_name, true_model_name)

    def test_get_stoichiometry(self):
        true_rxns = ['TPH', 'DDC', 'AANAT', 'ASMT', 'DDC_tryptm', 'AANAT_tryptm', 'IN_trp', 'EX_trp', 'EX_meltn',
                     'EX_nactryptm']
        true_mets = ['accoa_c', 'sam_c', 'pterin1_c', 'trp_v', 'fivehtp_c', 'trp_c', 'srtn_c', 'nactsertn_c', 'meltn_c',
                     'tryptm_c', 'nactryptm_c', 'coa_c', 'sah_c', 'pterin2_c', 'nactryptm_e', 'meltn_e', 'trp_e']

        true_rxn_strings = ['1 pterin1_c + 1 trp_c <-> 1 fivehtp_c + 1 pterin2_c', '1 fivehtp_c <-> 1 srtn_c',
                            '1 accoa_c + 1 srtn_c <-> 1 nactsertn_c + 1 coa_c',
                            '1 sam_c + 1 nactsertn_c <-> 1 meltn_c + 1 sah_c', '1 trp_c <-> 1 tryptm_c',
                            '1 accoa_c + 1 tryptm_c <-> 1 nactryptm_c + 1 coa_c', '1 trp_v <-> 1 trp_c',
                            '1 trp_c <-> 1 trp_e', '1 meltn_c <-> 1 meltn_e', '1 nactryptm_c <-> 1 nactryptm_e']

        sheet_name = 'stoic'
        mets, rxns, rxn_strings = get_model_stoichiometry(self.file_name, sheet_name)

        self.assertEqual(list(rxns), true_rxns)
        self.assertEqual(list(mets), true_mets)
        self.assertEqual(rxn_strings, true_rxn_strings)

    def test_get_model_enzymes(self):
        true_enzyme_list = [{'reaction_id': 'TPH', 'enzyme_name': 'tryptophan hydroxylase', 'enzyme_acronym': 'TPH',
                             'isoenzyme': 'TPH', 'ec_number': '1.14.16.4', 'uniprot_ids': '', 'pdb_ids': '1UCW 1E9I',
                             'strain': ''}, {'reaction_id': 'DDC', 'enzyme_name': '5-hydroxy-L-tryptophan decarboxylase',
                             'enzyme_acronym': 'DDC', 'isoenzyme': 'DDC', 'ec_number': '4.1.1.28',
                             'uniprot_ids': '3CV8K H12KP', 'pdb_ids': '', 'strain': ''}, {'reaction_id': 'AANAT',
                             'enzyme_name': 'aralkylamine N-acetyltransferase', 'enzyme_acronym': 'AANAT',
                             'isoenzyme': 'AANAT', 'ec_number': '2.3.1.87', 'uniprot_ids': '', 'pdb_ids': '',
                             'strain': ''}, {'reaction_id': 'ASMT', 'enzyme_name': 'acetylserotonin methyltransferase',
                             'enzyme_acronym': 'ASMT', 'isoenzyme': 'ASMT', 'ec_number': '2.1.1.4', 'uniprot_ids': '',
                             'pdb_ids': '', 'strain': ''}, {'reaction_id': 'DDC_tryptm',
                             'enzyme_name': 'L-tryptophan decarboxylase', 'enzyme_acronym': 'DDC_tryptm',
                             'isoenzyme': 'DDC_tryptm', 'ec_number': '4.1.1.105', 'uniprot_ids': '', 'pdb_ids': '',
                             'strain': ''}, {'reaction_id': 'AANAT_tryptm',
                            'enzyme_name': 'aralkylamine N-acetyltransferase', 'enzyme_acronym': 'AANAT',
                            'isoenzyme': 'AANAT', 'ec_number': '2.3.1.87', 'uniprot_ids': '', 'pdb_ids': '',
                            'strain': ''}, {'reaction_id': 'IN_trp', 'enzyme_name': '', 'enzyme_acronym': '',
                            'isoenzyme': '', 'ec_number': '', 'uniprot_ids': '', 'pdb_ids': '', 'strain': ''},
                            {'reaction_id': 'EX_trp', 'enzyme_name': '', 'enzyme_acronym': '', 'isoenzyme': '',
                             'ec_number': '', 'uniprot_ids': '', 'pdb_ids': '', 'strain': ''},
                            {'reaction_id': 'EX_meltn', 'enzyme_name': '', 'enzyme_acronym': '', 'isoenzyme': '',
                             'ec_number': '', 'uniprot_ids': '', 'pdb_ids': '', 'strain': ''},
                            {'reaction_id': 'EX_nactryptm', 'enzyme_name': '', 'enzyme_acronym': '',
                             'isoenzyme': '', 'ec_number': '', 'uniprot_ids': '', 'pdb_ids': '', 'strain': ''}]

        sheet_name = 'enzyme_reaction'
        enzyme_list = get_model_enzymes(self.file_name, sheet_name)

        true_res = pd.DataFrame.from_dict(true_enzyme_list)
        res = pd.DataFrame.from_dict(enzyme_list)


        self.assertTrue(res.equals(true_res))
        #self.assertDictEqual(enzyme_list, true_enzyme_list)

    def test_get_model_subunits(self):
        true_subunit_dict = {'TPH': 4, 'DDC': 2, 'AANAT': 1, 'ASMT': 2, 'DDC_tryptm': 2, 'AANAT_tryptm': 1,
                             'IN_trp': 1, 'EX_trp': 1, 'EX_meltn': 1, 'EX_nactryptm': 1}

        sheet_name = 'kinetics1'
        subunit_dict = get_model_subunits(self.file_name, sheet_name)

        self.assertDictEqual(subunit_dict, true_subunit_dict)

    def test_get_model_mechanisms(self):

        true_mechanisms_dict = {'TPH': ('substrateInhibOrderedBiBi',
                                ['pterin1_c', 'trp_c', 'trp_c', 'fivehtp_c', 'pterin2_c'],
                                'https://doi.org/10.1093/bioinformatics/bty943 ref_a ref_b'),
                                'DDC': ('UniUniPromiscuous', ['fivehtp_c', 'trp_c', 'srtn_c', 'tryptm_c'],
                                'https://doi.org/10.1093/bioinformatics/bty943'),
                                'AANAT': ('OrderedBiBiCompInhibPromiscuousIndep',
                                ['accoa_c', 'srtn_c', 'accoa_c', 'tryptm_c', 'meltn_c', 'nactsertn_c', 'nactryptm_c', 'coa_c', 'coa_c'],
                                ''), 'ASMT': ('randomBiBiCompInhib', [], 'https://doi.org/10.1093/bioinformatics/bty943'),
                                'DDC_tryptm': ('UniUniPromiscuous', ['fivehtp_c', 'trp_c', 'srtn_c', 'tryptm_c'],
                                'https://doi.org/10.1093/bioinformatics/bty943'),
                                'AANAT_tryptm': ('OrderedBiBiCompInhibPromiscuousIndep',
                                ['accoa_c', 'srtn_c', 'accoa_c', 'tryptm_c', 'meltn_c', 'nactsertn_c', 'nactryptm_c', 'coa_c', 'coa_c'],
                                'https://doi.org/10.1093/bioinformatics/bty943'),
                                'IN_trp': ('massAction', [], 'https://doi.org/10.1093/bioinformatics/bty943'),
                                'EX_trp': ('massAction', [],
                                           'https://doi.org/10.1093/bioinformatics/bty942 https://doi.org/10.1093/bioinformatics/bty943'),
                                'EX_meltn': ('massAction', [], 'https://doi.org/10.1093/bioinformatics/bty943'),
                                'EX_nactryptm': ('massAction', [], 'https://doi.org/10.1093/bioinformatics/bty943')}

        sheet_name = 'kinetics1'
        mechanisms_dict = get_model_mechanisms(self.file_name, sheet_name)

        self.assertDictEqual(mechanisms_dict, true_mechanisms_dict)

    def test_get_model_inhibitors(self):
        true_inhibitors_dict = {'TPH': (['trp_c'], ['https://doi.org/10.1093/bioinformatics/bty942 https://doi.org/10.1093/bioinformatics/bty943']),
                                'DDC': ([], []), 'AANAT': (['bli_c'], ['https://doi.org/10.1093/bioinformatics/bty943']),
                                'ASMT': (['srtn_c', 'met_b'], ['https://doi.org/10.1093/bioinformatics/bty943 ref1', ' ref2']),
                                'DDC_tryptm': ([], []),
                                'AANAT_tryptm': (['meltn_c', 'bla_x'], ['https://doi.org/10.1093/bioinformatics/bty943 ', '']),
                                'IN_trp': ([], []), 'EX_trp': ([], []), 'EX_meltn': ([], []), 'EX_nactryptm': ([], [])}

        sheet_name = 'kinetics1'
        inhibitors_dict = get_model_inhibitors(self.file_name, sheet_name)

        self.assertDictEqual(inhibitors_dict, true_inhibitors_dict)

    def test_get_model_activators(self):
        true_activators_dict = {'TPH': ([], []), 'DDC': (['met_c', 'met_b'], ['ref_a ref_b', ' ref_c']),
                                'AANAT': ([], []), 'ASMT': ([], []),
                                'DDC_tryptm': (['ble_c'], ['https://doi.org/10.1093/bioinformatics/bty943']),
                                'AANAT_tryptm': ([], []), 'IN_trp': ([], []), 'EX_trp': ([], []),
                                'EX_meltn': ([], []), 'EX_nactryptm': ([], [])}

        sheet_name = 'kinetics1'
        activators_dict = get_model_activators(self.file_name, sheet_name)

        self.assertDictEqual(activators_dict, true_activators_dict)

    def test_get_model_effectors(self):
        true_neg_effectors_dict = {'TPH': ([], []),
                                   'DDC': (['a_c', 'b_c'], ['https://doi.org/10.1093/bioinformatics/bty943 ref_a ref_b', 'ref_bla']),
                                   'AANAT': ([], []), 'ASMT': ([], []), 'DDC_tryptm': ([], []),
                                   'AANAT_tryptm': (['met_c', 'met_a'], ['ref_a ref_b', '']), 'IN_trp': ([], []),
                                   'EX_trp': ([], []), 'EX_meltn': ([], []), 'EX_nactryptm': ([], [])}
        true_pos_effectors_dict = {'TPH': ([], []),
                                   'DDC': (['p_c', 'q_c'], ['https://doi.org/10.1093/bioinformatics/bty943', '']),
                                   'AANAT': ([], []), 'ASMT': ([], []),
                                   'DDC_tryptm': (['ble_c'], ['https://doi.org/10.1093/bioinformatics/bty943']),
                                   'AANAT_tryptm': ([], []), 'IN_trp': ([], []), 'EX_trp': ([], []),
                                   'EX_meltn': ([], []), 'EX_nactryptm': ([], [])}

        sheet_name = 'kinetics1'
        neg_effectors_dict, pos_effectors_dic = get_model_effectors(self.file_name, sheet_name)

        self.assertDictEqual(neg_effectors_dict, true_neg_effectors_dict)
        self.assertDictEqual(pos_effectors_dic, true_pos_effectors_dict)

    def test_get_model_gibbs_energies(self):
        true_gibbs_energies_dict = {'TPH': (-50.0, 10.0, ''), 'DDC': (-26.1, 11.1, ''),
                                    'AANAT': (-21.2, 3.4, ''), 'ASMT': (-18.24, 5.0, ''),
                                    'DDC_tryptm': (-32.2, 11.0, ''), 'AANAT_tryptm': (-21.2, 3.4, ''),
                                    'IN_trp': (-20.0, 20.0, ''), 'EX_trp': (-2.5, 7.5, ''),
                                    'EX_meltn': (-2.5, 7.5, ''), 'EX_nactryptm': (-12.5, 17.5, '')}

        sheet_name = 'thermoRxns'
        gibbs_energies_dict = get_model_gibbs_energies(self.file_name, sheet_name)

        true_res = pd.DataFrame.from_dict(true_gibbs_energies_dict)
        res = pd.DataFrame.from_dict(gibbs_energies_dict)

        self.assertTrue(res.equals(true_res))

    def test_get_binding_order(self):
        true_res = [['pterin1_c', 'trp_c'], ['fivehtp_c', 'pterin2_c']]

        sheet_name = 'kinetics1'
        mechanisms_dict = get_model_mechanisms(self.file_name, sheet_name)
        rxn = 'TPH'
        rxn_string = '1 pterin1_c + trp_c <-> 1 pterin2_c + fivehtp_c '

        enz_rxn_org = EnzymeReactionOrganism(enzyme=Enzyme.query.first(),
                                             reaction=Reaction.query.first(),
                                             organism=Organism.query.first())

        binding_order, release_order = set_binding_release_order(rxn, rxn_string, enz_rxn_org, mechanisms_dict)

        self.assertEqual([binding_order, release_order], true_res)
