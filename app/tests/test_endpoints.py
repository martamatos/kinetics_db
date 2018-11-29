import unittest
from app import create_app, db
from app.models import Compartment, Enzyme, EnzymeOrganism, EnzymeReactionOrganism, EnzymeStructure, \
    EvidenceLevel, Gene, GibbsEnergy, GibbsEnergyReactionModel, Mechanism, Metabolite, Model, Organism, Reaction, ReactionMetabolite, Reference, \
    ReferenceType, EnzymeReactionInhibition, EnzymeReactionActivation, EnzymeReactionEffector, EnzymeReactionMiscInfo, \
    ModelAssumptions
from config import Config
from app.utils.parsers import parse_input_list, ReactionParser
from app.utils.populate_db import add_models, add_mechanisms, add_reactions, add_reference_types, add_enzymes, \
    add_compartments, add_evidence_levels, add_organisms, add_references, add_enzyme_reaction_organism
import re


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    LOGIN_DISABLED = True
    WTF_CSRF_ENABLED = False


def populate_db(test_case):

    if test_case == 'reaction':
        add_compartments()
        add_evidence_levels()
        add_mechanisms()
        add_organisms()
        add_enzymes()
        add_models()
        add_reference_types()
        add_references()

    else:
        add_compartments()
        add_evidence_levels()
        add_mechanisms()
        add_organisms()
        add_enzymes()
        add_models()
        add_reference_types()
        add_references()
        add_reactions()
        add_enzyme_reaction_organism()


class TestAddEnzyme(unittest.TestCase):
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

    def test_add_first_enzyme(self):

        enzyme_name = 'Phosphofructokinase'
        enzyme_acronym = 'PFK'
        isoenzyme = 'PFK1'
        ec_number = '1.2.1.31'

        organism_name = 'E. coli'
        number_of_active_sites = 4
        gene_bigg_ids = 'b001 b003'
        uniprot_ids = 'PC3W1, P34D'
        pdb_structure_ids = '3H8A, 1E9I'
        strain = 'WT'

        gene_bigg_id_list = parse_input_list(gene_bigg_ids)
        uniprot_id_list = parse_input_list(uniprot_ids)
        pdb_structure_id_list = parse_input_list(pdb_structure_ids)
        strain_list = parse_input_list(strain)

        organism = Organism(name=organism_name)
        db.session.add(organism)

        self.assertEqual(Organism().query.count(), 1)
        self.assertEqual(Organism().query.first().name, organism_name)
        self.assertEqual(Enzyme().query.count(), 0)
        self.assertEqual(EnzymeOrganism().query.count(), 0)
        self.assertEqual(EnzymeStructure().query.count(), 0)


        response = self.client.post('/add_enzyme', data=dict(
                                    name=enzyme_name,
                                    acronym=enzyme_acronym,
                                    isoenzyme=isoenzyme,
                                    ec_number=ec_number,
                                    organism_name='1',  # querySelectField
                                    number_of_active_sites=number_of_active_sites,
                                    gene_bigg_ids=gene_bigg_ids,
                                    uniprot_id_list=uniprot_ids,
                                    pdb_structure_ids=pdb_structure_ids,
                                    strain=strain), follow_redirects=True)


        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See enzymes - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your enzyme is now live!' in response.data)

        self.assertEqual(Enzyme().query.first().name, enzyme_name)
        self.assertEqual(Enzyme().query.first().acronym, enzyme_acronym)
        self.assertEqual(Enzyme().query.first().isoenzyme, isoenzyme)
        self.assertEqual(Enzyme().query.first().ec_number, ec_number)

        self.assertEqual(Enzyme().query.first().enzyme_structures.count(), 2)
        self.assertEqual(Enzyme().query.first().enzyme_structures[0].pdb_id, pdb_structure_id_list[0])
        self.assertEqual(Enzyme().query.first().enzyme_structures[1].pdb_id, pdb_structure_id_list[1])
        self.assertEqual(Enzyme().query.first().enzyme_organisms.count(), 2)
        self.assertEqual(Enzyme().query.first().enzyme_organisms[0].id, 1)
        self.assertEqual(Enzyme().query.first().enzyme_organisms[1].id, 2)

        self.assertEqual(Gene().query.count(), 2)
        self.assertEqual(Gene().query.all()[0].bigg_id, gene_bigg_id_list[0])
        self.assertEqual(Gene().query.all()[1].bigg_id, gene_bigg_id_list[1])
        self.assertEqual(Gene().query.all()[0].enzyme_organisms.count(), 2)
        self.assertEqual(Gene().query.all()[1].enzyme_organisms.count(), 2)

        self.assertEqual(EnzymeOrganism().query.count(), 2)
        self.assertEqual(EnzymeOrganism().query.all()[0].enzyme.name, enzyme_name)
        self.assertEqual(EnzymeOrganism().query.all()[1].enzyme.name, enzyme_name)
        self.assertEqual(EnzymeOrganism().query.all()[0].organism.name, organism_name)
        self.assertEqual(EnzymeOrganism().query.all()[1].organism.name, organism_name)
        self.assertEqual(EnzymeOrganism().query.all()[0].uniprot_id, uniprot_id_list[0])
        self.assertEqual(EnzymeOrganism().query.all()[1].uniprot_id, uniprot_id_list[1])
        self.assertEqual(EnzymeOrganism().query.all()[0].n_active_sites, number_of_active_sites)
        self.assertEqual(EnzymeOrganism().query.all()[1].n_active_sites, number_of_active_sites)
        self.assertEqual(EnzymeOrganism().query.all()[0].genes.count(), 2)
        self.assertEqual(EnzymeOrganism().query.all()[1].genes.count(), 2)
        self.assertEqual(EnzymeOrganism().query.all()[0].genes[0].bigg_id, gene_bigg_id_list[0])
        self.assertEqual(EnzymeOrganism().query.all()[0].genes[1].bigg_id, gene_bigg_id_list[1])
        self.assertEqual(EnzymeOrganism().query.all()[1].genes[0].bigg_id, gene_bigg_id_list[0])
        self.assertEqual(EnzymeOrganism().query.all()[1].genes[1].bigg_id, gene_bigg_id_list[1])

        self.assertEqual(EnzymeStructure().query.all()[0].enzyme.name, enzyme_name)
        self.assertEqual(EnzymeStructure().query.all()[1].enzyme.name, enzyme_name)
        self.assertEqual(EnzymeStructure().query.all()[0].organism.name, organism_name)
        self.assertEqual(EnzymeStructure().query.all()[1].organism.name, organism_name)
        self.assertEqual(EnzymeStructure().query.all()[0].pdb_id, pdb_structure_id_list[0])
        self.assertEqual(EnzymeStructure().query.all()[1].pdb_id, pdb_structure_id_list[1])
        self.assertEqual(EnzymeStructure().query.all()[0].strain, strain_list[0])
        self.assertEqual(EnzymeStructure().query.all()[1].strain, strain_list[0])


    def test_add_first_enzyme_basic(self):

        enzyme_name = 'Phosphofructokinase'
        enzyme_acronym = 'PFK'
        isoenzyme = 'PFK1'
        ec_number = '1.2.1.31'

        number_of_active_sites = ''
        gene_bigg_ids = ''
        uniprot_ids = ''
        pdb_structure_ids = ''
        strain = ''

        self.assertEqual(Organism().query.count(), 0)
        self.assertEqual(Enzyme().query.count(), 0)
        self.assertEqual(EnzymeOrganism().query.count(), 0)
        self.assertEqual(EnzymeStructure().query.count(), 0)

        response = self.client.post('/add_enzyme', data=dict(
                                    name=enzyme_name,
                                    acronym=enzyme_acronym,
                                    isoenzyme=isoenzyme,
                                    ec_number=ec_number,
                                    organism_name='__None',  # querySelectField
                                    number_of_active_sites=number_of_active_sites,
                                    gene_bigg_ids=gene_bigg_ids,
                                    uniprot_id_list=uniprot_ids,
                                    pdb_structure_ids=pdb_structure_ids,
                                    strain=strain), follow_redirects=True)


        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See enzymes - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your enzyme is now live!' in response.data)

        self.assertEqual(Enzyme().query.count(), 1)
        self.assertEqual(EnzymeOrganism().query.count(), 0)
        self.assertEqual(EnzymeStructure().query.count(), 0)

        self.assertEqual(Enzyme().query.first().name, enzyme_name)
        self.assertEqual(Enzyme().query.first().acronym, enzyme_acronym)
        self.assertEqual(Enzyme().query.first().isoenzyme, isoenzyme)
        self.assertEqual(Enzyme().query.first().ec_number, ec_number)

        self.assertEqual(Enzyme().query.first().enzyme_structures.count(), 0)
        self.assertEqual(Enzyme().query.first().enzyme_organisms.count(), 0)


    def test_add_repeated_isoenzyme(self):

        enzyme_name = 'Phosphofructokinase'
        enzyme_acronym = 'PFK'
        isoenzyme = 'PFK1'
        ec_number = '1.2.1.31'

        number_of_active_sites = ''
        gene_bigg_ids = ''
        uniprot_ids = ''
        pdb_structure_ids = ''
        strain = ''

        enzyme = Enzyme(name=enzyme_name,
                        acronym=enzyme_acronym,
                        isoenzyme=isoenzyme,
                        ec_number=ec_number)
        db.session.add(enzyme)

        self.assertEqual(Organism().query.count(), 0)
        self.assertEqual(Enzyme().query.count(), 1)
        self.assertEqual(Enzyme().query.first().name, enzyme_name)
        self.assertEqual(Enzyme().query.first().acronym, enzyme_acronym)
        self.assertEqual(Enzyme().query.first().isoenzyme, isoenzyme)
        self.assertEqual(Enzyme().query.first().ec_number, ec_number)

        self.assertEqual(Enzyme().query.first().enzyme_structures.count(), 0)
        self.assertEqual(Enzyme().query.first().enzyme_organisms.count(), 0)
        self.assertEqual(EnzymeOrganism().query.count(), 0)
        self.assertEqual(EnzymeStructure().query.count(), 0)

        response = self.client.post('/add_enzyme', data=dict(
                                    name=enzyme_name,
                                    acronym=enzyme_acronym,
                                    isoenzyme=isoenzyme,
                                    ec_number=ec_number,
                                    organism_name='__None',  # querySelectField
                                    number_of_active_sites=number_of_active_sites,
                                    gene_bigg_ids=gene_bigg_ids,
                                    uniprot_id_list=uniprot_ids,
                                    pdb_structure_ids=pdb_structure_ids,
                                    strain=strain), follow_redirects=True)


        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    Add enzyme - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'The isoenzyme you specified already exists. Please choose a different name.' in response.data)

        self.assertEqual(Enzyme().query.count(), 1)
        self.assertEqual(EnzymeOrganism().query.count(), 0)
        self.assertEqual(EnzymeStructure().query.count(), 0)

    def test_add_enzyme_number_of_active_sites_without_organism(self):

        enzyme_name = 'Phosphofructokinase'
        enzyme_acronym = 'PFK'
        isoenzyme = 'PFK1'
        ec_number = '1.2.1.31'

        number_of_active_sites = 4
        gene_bigg_ids = ''
        uniprot_ids = ''
        pdb_structure_ids = ''
        strain = ''


        self.assertEqual(Organism().query.count(), 0)
        self.assertEqual(Enzyme().query.count(), 0)
        self.assertEqual(EnzymeOrganism().query.count(), 0)
        self.assertEqual(EnzymeStructure().query.count(), 0)

        response = self.client.post('/add_enzyme', data=dict(
                                    name=enzyme_name,
                                    acronym=enzyme_acronym,
                                    isoenzyme=isoenzyme,
                                    ec_number=ec_number,
                                    organism_name='__None',  # querySelectField
                                    number_of_active_sites=number_of_active_sites,
                                    gene_bigg_ids=gene_bigg_ids,
                                    uniprot_id_list=uniprot_ids,
                                    pdb_structure_ids=pdb_structure_ids,
                                    strain=strain), follow_redirects=True)


        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    Add enzyme - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'If you specify the number of active sites you must also specify the organism name.' in response.data)

        self.assertEqual(Enzyme().query.count(), 0)
        self.assertEqual(Organism().query.count(), 0)
        self.assertEqual(EnzymeOrganism().query.count(), 0)
        self.assertEqual(EnzymeStructure().query.count(), 0)

    def test_add_enzyme_gene_bigg_ids_without_organism(self):

        enzyme_name = 'Phosphofructokinase'
        enzyme_acronym = 'PFK'
        isoenzyme = 'PFK1'
        ec_number = '1.2.1.31'

        number_of_active_sites = ''
        gene_bigg_ids = 'b001'
        uniprot_ids = ''
        pdb_structure_ids = ''
        strain = ''


        self.assertEqual(Organism().query.count(), 0)
        self.assertEqual(Enzyme().query.count(), 0)
        self.assertEqual(EnzymeOrganism().query.count(), 0)
        self.assertEqual(EnzymeStructure().query.count(), 0)

        response = self.client.post('/add_enzyme', data=dict(
                                    name=enzyme_name,
                                    acronym=enzyme_acronym,
                                    isoenzyme=isoenzyme,
                                    ec_number=ec_number,
                                    organism_name='__None',  # querySelectField
                                    number_of_active_sites=number_of_active_sites,
                                    gene_bigg_ids=gene_bigg_ids,
                                    uniprot_id_list=uniprot_ids,
                                    pdb_structure_ids=pdb_structure_ids,
                                    strain=strain), follow_redirects=True)


        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    Add enzyme - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'If you specify encoding genes you must also specify the organism name.' in response.data)

        self.assertEqual(Enzyme().query.count(), 0)
        self.assertEqual(Organism().query.count(), 0)
        self.assertEqual(EnzymeOrganism().query.count(), 0)
        self.assertEqual(EnzymeStructure().query.count(), 0)

    def test_add_enzyme_uniprot_id_list_without_organism(self):

        enzyme_name = 'Phosphofructokinase'
        enzyme_acronym = 'PFK'
        isoenzyme = 'PFK1'
        ec_number = '1.2.1.31'

        number_of_active_sites = ''
        gene_bigg_ids = ''
        uniprot_ids = 'PC1R3'
        pdb_structure_ids = ''
        strain = ''


        self.assertEqual(Organism().query.count(), 0)
        self.assertEqual(Enzyme().query.count(), 0)
        self.assertEqual(EnzymeOrganism().query.count(), 0)
        self.assertEqual(EnzymeStructure().query.count(), 0)

        response = self.client.post('/add_enzyme', data=dict(
                                    name=enzyme_name,
                                    acronym=enzyme_acronym,
                                    isoenzyme=isoenzyme,
                                    ec_number=ec_number,
                                    organism_name='__None',  # querySelectField
                                    number_of_active_sites=number_of_active_sites,
                                    gene_bigg_ids=gene_bigg_ids,
                                    uniprot_id_list=uniprot_ids,
                                    pdb_structure_ids=pdb_structure_ids,
                                    strain=strain), follow_redirects=True)


        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    Add enzyme - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'If you specify uniprot IDs you must also specify the organism name' in response.data)

        self.assertEqual(Enzyme().query.count(), 0)
        self.assertEqual(Organism().query.count(), 0)
        self.assertEqual(EnzymeOrganism().query.count(), 0)
        self.assertEqual(EnzymeStructure().query.count(), 0)


    def test_add_enzyme_pdb_structure_ids_without_organism(self):

        enzyme_name = 'Phosphofructokinase'
        enzyme_acronym = 'PFK'
        isoenzyme = 'PFK1'
        ec_number = '1.2.1.31'

        number_of_active_sites = ''
        gene_bigg_ids = ''
        uniprot_ids = ''
        pdb_structure_ids = '1E9I'
        strain = ''


        self.assertEqual(Organism().query.count(), 0)
        self.assertEqual(Enzyme().query.count(), 0)
        self.assertEqual(EnzymeOrganism().query.count(), 0)
        self.assertEqual(EnzymeStructure().query.count(), 0)

        response = self.client.post('/add_enzyme', data=dict(
                                    name=enzyme_name,
                                    acronym=enzyme_acronym,
                                    isoenzyme=isoenzyme,
                                    ec_number=ec_number,
                                    organism_name='__None',  # querySelectField
                                    number_of_active_sites=number_of_active_sites,
                                    gene_bigg_ids=gene_bigg_ids,
                                    uniprot_id_list=uniprot_ids,
                                    pdb_structure_ids=pdb_structure_ids,
                                    strain=strain), follow_redirects=True)


        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    Add enzyme - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'If you specify PDB structures you must also specify the organism name' in response.data)

        self.assertEqual(Enzyme().query.count(), 0)
        self.assertEqual(Organism().query.count(), 0)
        self.assertEqual(EnzymeOrganism().query.count(), 0)
        self.assertEqual(EnzymeStructure().query.count(), 0)


    def test_add_enzyme_mismatched_strain(self):

        enzyme_name = 'Phosphofructokinase'
        enzyme_acronym = 'PFK'
        isoenzyme = 'PFK1'
        ec_number = '1.2.1.31'

        number_of_active_sites = ''
        gene_bigg_ids = ''
        uniprot_ids = ''
        pdb_structure_ids = '1E9I, 38HA, UCW8'
        strain = 'WT, knockout'


        self.assertEqual(Organism().query.count(), 0)
        self.assertEqual(Enzyme().query.count(), 0)
        self.assertEqual(EnzymeOrganism().query.count(), 0)
        self.assertEqual(EnzymeStructure().query.count(), 0)

        response = self.client.post('/add_enzyme', data=dict(
                                    name=enzyme_name,
                                    acronym=enzyme_acronym,
                                    isoenzyme=isoenzyme,
                                    ec_number=ec_number,
                                    organism_name='__None',  # querySelectField
                                    number_of_active_sites=number_of_active_sites,
                                    gene_bigg_ids=gene_bigg_ids,
                                    uniprot_id_list=uniprot_ids,
                                    pdb_structure_ids=pdb_structure_ids,
                                    strain=strain), follow_redirects=True)


        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    Add enzyme - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'When providing PDB IDs either provide:' in response.data)

        self.assertEqual(Enzyme().query.count(), 0)
        self.assertEqual(Organism().query.count(), 0)
        self.assertEqual(EnzymeOrganism().query.count(), 0)
        self.assertEqual(EnzymeStructure().query.count(), 0)


    def test_add_enzyme_mismatched_strain_2(self):

        enzyme_name = 'Phosphofructokinase'
        enzyme_acronym = 'PFK'
        isoenzyme = 'PFK1'
        ec_number = '1.2.1.31'

        organism_name = 'E. coli'
        number_of_active_sites = ''
        gene_bigg_ids = ''
        uniprot_ids = ''
        pdb_structure_ids = '1E9I, 38HA'
        strain = 'WT, knockout'

        pdb_structure_id_list = parse_input_list(pdb_structure_ids)
        strain_list = parse_input_list(strain)

        organism = Organism(name=organism_name)
        db.session.add(organism)

        self.assertEqual(Organism().query.count(), 1)
        self.assertEqual(Enzyme().query.count(), 0)
        self.assertEqual(EnzymeOrganism().query.count(), 0)
        self.assertEqual(EnzymeStructure().query.count(), 0)

        response = self.client.post('/add_enzyme', data=dict(
                                    name=enzyme_name,
                                    acronym=enzyme_acronym,
                                    isoenzyme=isoenzyme,
                                    ec_number=ec_number,
                                    organism_name='1',  # querySelectField
                                    number_of_active_sites=number_of_active_sites,
                                    gene_bigg_ids=gene_bigg_ids,
                                    uniprot_id_list=uniprot_ids,
                                    pdb_structure_ids=pdb_structure_ids,
                                    strain=strain), follow_redirects=True)


        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See enzymes - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your enzyme is now live!' in response.data)

        self.assertEqual(Enzyme().query.first().name, enzyme_name)
        self.assertEqual(Enzyme().query.first().acronym, enzyme_acronym)
        self.assertEqual(Enzyme().query.first().isoenzyme, isoenzyme)
        self.assertEqual(Enzyme().query.first().ec_number, ec_number)

        self.assertEqual(Enzyme().query.first().enzyme_structures.count(), 2)
        self.assertEqual(Enzyme().query.first().enzyme_structures[0].pdb_id, pdb_structure_id_list[0])
        self.assertEqual(Enzyme().query.first().enzyme_structures[1].pdb_id, pdb_structure_id_list[1])
        self.assertEqual(Enzyme().query.first().enzyme_organisms.count(), 0)

        self.assertEqual(EnzymeOrganism().query.count(), 0)

        self.assertEqual(EnzymeStructure().query.all()[0].enzyme.name, enzyme_name)
        self.assertEqual(EnzymeStructure().query.all()[1].enzyme.name, enzyme_name)
        self.assertEqual(EnzymeStructure().query.all()[0].organism.name, organism_name)
        self.assertEqual(EnzymeStructure().query.all()[1].organism.name, organism_name)
        self.assertEqual(EnzymeStructure().query.all()[0].pdb_id, pdb_structure_id_list[0])
        self.assertEqual(EnzymeStructure().query.all()[1].pdb_id, pdb_structure_id_list[1])
        self.assertEqual(EnzymeStructure().query.all()[0].strain, strain_list[0])
        self.assertEqual(EnzymeStructure().query.all()[1].strain, strain_list[1])


    def test_add_enzyme_mismatched_strain_3(self):

        enzyme_name = 'Phosphofructokinase'
        enzyme_acronym = 'PFK'
        isoenzyme = 'PFK1'
        ec_number = '1.2.1.31'

        organism_name = 'E. coli'
        number_of_active_sites = ''
        gene_bigg_ids = ''
        uniprot_ids = ''
        pdb_structure_ids = '1E9I, 38HA, UCW8'
        strain = 'WT'

        pdb_structure_id_list = parse_input_list(pdb_structure_ids)
        strain_list = parse_input_list(strain)

        organism = Organism(name=organism_name)
        db.session.add(organism)

        self.assertEqual(Organism().query.count(), 1)
        self.assertEqual(Enzyme().query.count(), 0)
        self.assertEqual(EnzymeOrganism().query.count(), 0)
        self.assertEqual(EnzymeStructure().query.count(), 0)

        response = self.client.post('/add_enzyme', data=dict(
                                    name=enzyme_name,
                                    acronym=enzyme_acronym,
                                    isoenzyme=isoenzyme,
                                    ec_number=ec_number,
                                    organism_name='1',  # querySelectField
                                    number_of_active_sites=number_of_active_sites,
                                    gene_bigg_ids=gene_bigg_ids,
                                    uniprot_id_list=uniprot_ids,
                                    pdb_structure_ids=pdb_structure_ids,
                                    strain=strain), follow_redirects=True)


        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See enzymes - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your enzyme is now live!' in response.data)

        self.assertEqual(Enzyme().query.first().name, enzyme_name)
        self.assertEqual(Enzyme().query.first().acronym, enzyme_acronym)
        self.assertEqual(Enzyme().query.first().isoenzyme, isoenzyme)
        self.assertEqual(Enzyme().query.first().ec_number, ec_number)

        self.assertEqual(Enzyme().query.first().enzyme_structures.count(), 3)
        self.assertEqual(Enzyme().query.first().enzyme_structures[0].pdb_id, pdb_structure_id_list[0])
        self.assertEqual(Enzyme().query.first().enzyme_structures[1].pdb_id, pdb_structure_id_list[1])
        self.assertEqual(Enzyme().query.first().enzyme_structures[2].pdb_id, pdb_structure_id_list[2])
        self.assertEqual(Enzyme().query.first().enzyme_organisms.count(), 0)

        self.assertEqual(EnzymeOrganism().query.count(), 0)

        self.assertEqual(EnzymeStructure().query.all()[0].enzyme.name, enzyme_name)
        self.assertEqual(EnzymeStructure().query.all()[1].enzyme.name, enzyme_name)
        self.assertEqual(EnzymeStructure().query.all()[2].enzyme.name, enzyme_name)
        self.assertEqual(EnzymeStructure().query.all()[0].organism.name, organism_name)
        self.assertEqual(EnzymeStructure().query.all()[1].organism.name, organism_name)
        self.assertEqual(EnzymeStructure().query.all()[2].organism.name, organism_name)
        self.assertEqual(EnzymeStructure().query.all()[0].pdb_id, pdb_structure_id_list[0])
        self.assertEqual(EnzymeStructure().query.all()[1].pdb_id, pdb_structure_id_list[1])
        self.assertEqual(EnzymeStructure().query.all()[2].pdb_id, pdb_structure_id_list[2])
        self.assertEqual(EnzymeStructure().query.all()[0].strain, strain_list[0])
        self.assertEqual(EnzymeStructure().query.all()[1].strain, strain_list[0])
        self.assertEqual(EnzymeStructure().query.all()[2].strain, strain_list[0])


    def test_add_enzyme_mismatched_strain_4(self):

        enzyme_name = 'Phosphofructokinase'
        enzyme_acronym = 'PFK'
        isoenzyme = 'PFK1'
        ec_number = '1.2.1.31'

        organism_name = 'E. coli'
        number_of_active_sites = ''
        gene_bigg_ids = ''
        uniprot_ids = ''
        pdb_structure_ids = '1E9I, 38HA, UCW8'
        strain = ''

        pdb_structure_id_list = parse_input_list(pdb_structure_ids)
        strain_list = parse_input_list(strain)

        organism = Organism(name=organism_name)
        db.session.add(organism)

        self.assertEqual(Organism().query.count(), 1)
        self.assertEqual(Enzyme().query.count(), 0)
        self.assertEqual(EnzymeOrganism().query.count(), 0)
        self.assertEqual(EnzymeStructure().query.count(), 0)

        response = self.client.post('/add_enzyme', data=dict(
                                    name=enzyme_name,
                                    acronym=enzyme_acronym,
                                    isoenzyme=isoenzyme,
                                    ec_number=ec_number,
                                    organism_name='1',  # querySelectField
                                    number_of_active_sites=number_of_active_sites,
                                    gene_bigg_ids=gene_bigg_ids,
                                    uniprot_id_list=uniprot_ids,
                                    pdb_structure_ids=pdb_structure_ids,
                                    strain=strain), follow_redirects=True)


        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See enzymes - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your enzyme is now live!' in response.data)

        self.assertEqual(Enzyme().query.first().name, enzyme_name)
        self.assertEqual(Enzyme().query.first().acronym, enzyme_acronym)
        self.assertEqual(Enzyme().query.first().isoenzyme, isoenzyme)
        self.assertEqual(Enzyme().query.first().ec_number, ec_number)

        self.assertEqual(Enzyme().query.first().enzyme_structures.count(), 3)
        self.assertEqual(Enzyme().query.first().enzyme_structures[0].pdb_id, pdb_structure_id_list[0])
        self.assertEqual(Enzyme().query.first().enzyme_structures[1].pdb_id, pdb_structure_id_list[1])
        self.assertEqual(Enzyme().query.first().enzyme_structures[2].pdb_id, pdb_structure_id_list[2])
        self.assertEqual(Enzyme().query.first().enzyme_organisms.count(), 0)

        self.assertEqual(EnzymeOrganism().query.count(), 0)

        self.assertEqual(EnzymeStructure().query.all()[0].enzyme.name, enzyme_name)
        self.assertEqual(EnzymeStructure().query.all()[1].enzyme.name, enzyme_name)
        self.assertEqual(EnzymeStructure().query.all()[2].enzyme.name, enzyme_name)
        self.assertEqual(EnzymeStructure().query.all()[0].organism.name, organism_name)
        self.assertEqual(EnzymeStructure().query.all()[1].organism.name, organism_name)
        self.assertEqual(EnzymeStructure().query.all()[2].organism.name, organism_name)
        self.assertEqual(EnzymeStructure().query.all()[0].pdb_id, pdb_structure_id_list[0])
        self.assertEqual(EnzymeStructure().query.all()[1].pdb_id, pdb_structure_id_list[1])
        self.assertEqual(EnzymeStructure().query.all()[2].pdb_id, pdb_structure_id_list[2])
        self.assertEqual(EnzymeStructure().query.all()[0].strain, strain)
        self.assertEqual(EnzymeStructure().query.all()[1].strain, strain)
        self.assertEqual(EnzymeStructure().query.all()[2].strain, strain)


class TestAddEnzymeInhibition(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        populate_db('enzyme_inhibition')


    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()


    def test_add_first_inhib(self):

        isoenzyme = '1'
        reaction = '1'
        model = '1'
        inhibitor_met = 'adp'
        affected_met = 'atp'
        inhibition_type = 'Competitive'
        inhibition_constant = 1.3*10**-4

        evidence_level = '1'
        references = 'https://doi.org/10.1093/bioinformatics/bty942, https://doi.org/10.1093/bioinformatics/bty943'
        comments = ''
        reference_list = parse_input_list(references)


        response = self.client.post('/add_enzyme_inhibition', data=dict(
                                    isoenzyme=isoenzyme,
                                     reaction=reaction,
                                     model=model,
                                     inhibitor_met=inhibitor_met,
                                     affected_met=affected_met,
                                     inhibition_type=inhibition_type,
                                     inhibition_constant=inhibition_constant,
                                     inhibition_evidence_level=evidence_level,
                                     references=references,
                                     comments=comments), follow_redirects=True)



        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See enzymes - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your enzyme inhibition is now live!' in response.data)


        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(GibbsEnergy.query.count(), 0)
        self.assertEqual(EnzymeReactionOrganism.query.count(), 1)
        self.assertEqual(EnzymeReactionInhibition.query.count(), 1)
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Reference.query.count(), 3)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)


        self.assertEqual(EnzymeReactionOrganism.query.first().grasp_id, '')
        self.assertEqual(EnzymeReactionOrganism.query.first().subs_binding_order, '')
        self.assertEqual(EnzymeReactionOrganism.query.first().prod_release_order, '')
        self.assertEqual(EnzymeReactionOrganism.query.first().included_in_model, True)

        self.assertEqual(EnzymeReactionOrganism.query.first().reaction, Reaction.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.first().enzyme, Enzyme.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.first().model, Model.query.first())

        self.assertEqual(EnzymeReactionOrganism.query.first().mech_evidence, '')
        self.assertEqual(EnzymeReactionOrganism.query.first().mechanism, '')
        self.assertEqual(EnzymeReactionOrganism.query.first().gibbs_energy, '')

        self.assertEqual(Reference.query.all()[0].title, 'eQuilibrator')
        self.assertEqual(Reference.query.all()[0].type_type, 'Online database')
        self.assertEqual(Reference.query.all()[1].doi, reference_list[0])
        self.assertEqual(Reference.query.all()[2].doi, reference_list[1])

        self.assertEqual(Metabolite.query.count(), 4)

        self.assertEqual(ReactionMetabolite.query.count(), 4)

        self.assertEqual(EnzymeReactionInhibition.query.count(), 1)
        self.assertEqual(EnzymeReactionInhibition.query.first().inhibitor_met, Metabolite.query.filter_by(bigg_id=inhibitor_met).first())
        self.assertEqual(EnzymeReactionInhibition.query.first().affected_met, Metabolite.query.filter_by(bigg_id=affected_met).first())
        self.assertEqual(EnzymeReactionInhibition.query.first().inhibition_constant, inhibition_constant)
        self.assertEqual(EnzymeReactionInhibition.query.first().evidence, EvidenceLevel.query.first())
        self.assertEqual(EnzymeReactionInhibition.query.first().comments, comments)
        self.assertEqual(EnzymeReactionInhibition.query.first().references[0], reference_list[0])
        self.assertEqual(EnzymeReactionInhibition.query.first().references[1], reference_list[1])


class TestAddEnzymeActivation(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        self.populate_db()


    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def populate_db(self):
        compartment_list = [('Cytosol', 'c'), ('Mitochondria', 'm')]

        for name, acronym in compartment_list:
            compartment = Compartment(name=name, acronym=acronym)
            db.session.add(compartment)
        db.session.commit()


        evidence_list = [('Literature 1', 'Got it from papers for the given organism'),
                         ('Literature 2', 'Got it from papers of other organisms'),
                         ('Predicted', 'Predicted by some algorithm'),
                         ('Educated guess', '')]

        for name, description in evidence_list:
            evidence = EvidenceLevel(name=name, description=description)
            db.session.add(evidence)
        db.session.commit()


        mechanism_list = ['UniUni', 'OrderedBiBi']

        for name in mechanism_list:
            mechanism = Mechanism(name=name)
            db.session.add(mechanism)
        db.session.commit()


        organism_list = ['E. coli', 'S. cerevisiae']

        for name in organism_list:
            organism = Organism(name=name)
            db.session.add(organism)
        db.session.commit()


        enzyme_list = [('Phosphofructokinase', 'PFK', 'PFK1', '1.2.3.33'),
                         ('Phosphofructokinase', 'PFK', 'PFK2', '1.2.3.33')]

        for name, acronym, isoenzyme, ec_number in enzyme_list:
            enzyme = Enzyme(name=name, acronym=acronym, isoenzyme=isoenzyme, ec_number=ec_number)
            db.session.add(enzyme)
        db.session.commit()


        model_list = [('E. coli - iteration 1', 'E. coli', 'MG16555'),
                      ('E. coli - iteration 2', 'E. coli', 'MG16555')]

        for name, organism_name, strain in model_list:
            model = Model(name=name, organism_name=organism_name, strain=strain)
            db.session.add(model)
        db.session.commit()


        reference_type_list = ['Article', 'Thesis', 'Online database', 'Book']

        for type in reference_type_list:
            reference_type = ReferenceType(type=type)
            db.session.add(reference_type)
        db.session.commit()


        reference = Reference(title='eQuilibrator', type_type='Online database')
        db.session.add(reference)
        db.session.commit()



    def test_add_first_reaction(self):

        reaction_name = 'phosphofructokinase'
        reaction_acronym = 'PFK'
        reaction_grasp_id = 'PFK1'
        reaction_string = '1 pep_c + 1.5 adp_c <-> pyr_c + 2.0 atp_m'
        metanetx_id = ''
        bigg_id = ''
        kegg_id = ''

        compartment_name = '1'
        model_name = '1'
        isoenzyme_acronyms = 'PFK1'
        mechanism = '1'
        mechanism_references = 'https://doi.org/10.1093/bioinformatics/bty942'
        mechanism_evidence_level = '1'
        subs_binding_order = 'adp_c, pep_c'
        prod_release_order = 'atp_m, pyr_c'
        std_gibbs_energy = 2.1
        std_gibbs_energy_std = 0.2
        std_gibbs_energy_ph = 7
        std_gibbs_energy_ionic_strength = 0.2
        std_gibbs_energy_references = 'equilibrator'


        response = self.client.post('/add_reaction', data=dict(
                                    name=reaction_name,
                                    acronym=reaction_acronym,
                                    grasp_id=reaction_grasp_id,
                                    reaction_string=reaction_string,
                                    bigg_id=bigg_id,
                                    kegg_id=kegg_id,
                                    metanetx_id=metanetx_id,
                                    compartment_name=compartment_name,
                                    model_name=model_name,
                                    isoenzyme_acronyms=isoenzyme_acronyms,
                                    mechanism=mechanism,
                                    mechanism_references=mechanism_references,
                                    mechanism_evidence_level=mechanism_evidence_level,
                                    subs_binding_order=subs_binding_order,
                                    prod_release_order=prod_release_order,
                                    std_gibbs_energy=std_gibbs_energy,
                                    std_gibbs_energy_std=std_gibbs_energy_std,
                                    std_gibbs_energy_ph=std_gibbs_energy_ph,
                                    std_gibbs_energy_ionic_strength=std_gibbs_energy_ionic_strength,
                                    std_gibbs_energy_references=std_gibbs_energy_references), follow_redirects=True)




        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See reactions - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your reaction is now live!' in response.data)


        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(GibbsEnergy.query.count(), 1)
        self.assertEqual(EnzymeReactionOrganism.query.count(), 1)
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Reference.query.count(), 2)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

        self.assertEqual(Reaction.query.count(), 1)
        self.assertEqual(Reaction.query.first().name, reaction_name)
        self.assertEqual(Reaction.query.first().compartment_name, Compartment.query.first().name)

        self.assertEqual(EnzymeReactionOrganism.query.first().grasp_id, reaction_grasp_id)
        self.assertEqual(EnzymeReactionOrganism.query.first().subs_binding_order, subs_binding_order)
        self.assertEqual(EnzymeReactionOrganism.query.first().prod_release_order, prod_release_order)
        self.assertEqual(EnzymeReactionOrganism.query.first().included_in_model, True)
        self.assertEqual(EnzymeReactionOrganism.query.first().reaction.name, reaction_name)
        self.assertEqual(EnzymeReactionOrganism.query.first().enzyme.isoenzyme, isoenzyme_acronyms)
        self.assertEqual(EnzymeReactionOrganism.query.first().model, Model.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.first().mech_evidence, EvidenceLevel.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.first().mechanism, Mechanism.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.first().gibbs_energy, GibbsEnergy.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.first().gibbs_energy.standard_dg, std_gibbs_energy)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].mechanism_references[0].doi, mechanism_references)

        self.assertEqual(GibbsEnergy.query.first().standard_dg, std_gibbs_energy)
        self.assertEqual(GibbsEnergy.query.first().standard_dg_std, std_gibbs_energy_std)
        self.assertEqual(GibbsEnergy.query.first().ph, std_gibbs_energy_ph)
        self.assertEqual(GibbsEnergy.query.first().ionic_strength, std_gibbs_energy_ionic_strength)
        self.assertEqual(GibbsEnergy.query.first().references[0].title, 'eQuilibrator')

        self.assertEqual(Reference.query.all()[0].title, 'eQuilibrator')
        self.assertEqual(Reference.query.all()[0].type_type, 'Online database')
        self.assertEqual(Reference.query.all()[1].doi, mechanism_references)

        self.assertEqual(Metabolite.query.count(), 4)
        self.assertEqual(Metabolite.query.all()[0].bigg_id, 'pep')
        self.assertEqual(Metabolite.query.all()[0].grasp_id, 'pep')
        self.assertEqual(Metabolite.query.all()[0].compartment_acronym, 'c')
        self.assertEqual(Metabolite.query.all()[1].bigg_id, 'adp')
        self.assertEqual(Metabolite.query.all()[1].grasp_id, 'adp')
        self.assertEqual(Metabolite.query.all()[1].compartment_acronym, 'c')
        self.assertEqual(Metabolite.query.all()[2].bigg_id, 'pyr')
        self.assertEqual(Metabolite.query.all()[2].grasp_id, 'pyr')
        self.assertEqual(Metabolite.query.all()[2].compartment_acronym, 'c')
        self.assertEqual(Metabolite.query.all()[3].bigg_id, 'atp')
        self.assertEqual(Metabolite.query.all()[3].grasp_id, 'atp')
        self.assertEqual(Metabolite.query.all()[3].compartment_acronym, 'm')

        self.assertEqual(ReactionMetabolite.query.count(), 4)
        self.assertEqual(ReactionMetabolite.query.all()[0].metabolite.bigg_id, 'pep')
        self.assertEqual(ReactionMetabolite.query.all()[0].stoich_coef, -1)
        self.assertEqual(ReactionMetabolite.query.all()[0].reaction.acronym, reaction_acronym)
        self.assertEqual(ReactionMetabolite.query.all()[1].metabolite.bigg_id, 'adp')
        self.assertEqual(ReactionMetabolite.query.all()[1].stoich_coef, -1.5)
        self.assertEqual(ReactionMetabolite.query.all()[1].reaction.acronym, reaction_acronym)
        self.assertEqual(ReactionMetabolite.query.all()[2].metabolite.bigg_id, 'pyr')
        self.assertEqual(ReactionMetabolite.query.all()[2].stoich_coef, 1)
        self.assertEqual(ReactionMetabolite.query.all()[2].reaction.acronym, reaction_acronym)
        self.assertEqual(ReactionMetabolite.query.all()[3].metabolite.bigg_id, 'atp')
        self.assertEqual(ReactionMetabolite.query.all()[3].stoich_coef, 2)
        self.assertEqual(ReactionMetabolite.query.all()[3].reaction.acronym, reaction_acronym)


class TestAddEnzymeEffector(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        self.populate_db()


    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def populate_db(self):
        compartment_list = [('Cytosol', 'c'), ('Mitochondria', 'm')]

        for name, acronym in compartment_list:
            compartment = Compartment(name=name, acronym=acronym)
            db.session.add(compartment)
        db.session.commit()


        evidence_list = [('Literature 1', 'Got it from papers for the given organism'),
                         ('Literature 2', 'Got it from papers of other organisms'),
                         ('Predicted', 'Predicted by some algorithm'),
                         ('Educated guess', '')]

        for name, description in evidence_list:
            evidence = EvidenceLevel(name=name, description=description)
            db.session.add(evidence)
        db.session.commit()


        mechanism_list = ['UniUni', 'OrderedBiBi']

        for name in mechanism_list:
            mechanism = Mechanism(name=name)
            db.session.add(mechanism)
        db.session.commit()


        organism_list = ['E. coli', 'S. cerevisiae']

        for name in organism_list:
            organism = Organism(name=name)
            db.session.add(organism)
        db.session.commit()


        enzyme_list = [('Phosphofructokinase', 'PFK', 'PFK1', '1.2.3.33'),
                         ('Phosphofructokinase', 'PFK', 'PFK2', '1.2.3.33')]

        for name, acronym, isoenzyme, ec_number in enzyme_list:
            enzyme = Enzyme(name=name, acronym=acronym, isoenzyme=isoenzyme, ec_number=ec_number)
            db.session.add(enzyme)
        db.session.commit()


        model_list = [('E. coli - iteration 1', 'E. coli', 'MG16555'),
                      ('E. coli - iteration 2', 'E. coli', 'MG16555')]

        for name, organism_name, strain in model_list:
            model = Model(name=name, organism_name=organism_name, strain=strain)
            db.session.add(model)
        db.session.commit()


        reference_type_list = ['Article', 'Thesis', 'Online database', 'Book']

        for type in reference_type_list:
            reference_type = ReferenceType(type=type)
            db.session.add(reference_type)
        db.session.commit()


        reference = Reference(title='eQuilibrator', type_type='Online database')
        db.session.add(reference)
        db.session.commit()



    def test_add_first_reaction(self):

        reaction_name = 'phosphofructokinase'
        reaction_acronym = 'PFK'
        reaction_grasp_id = 'PFK1'
        reaction_string = '1 pep_c + 1.5 adp_c <-> pyr_c + 2.0 atp_m'
        metanetx_id = ''
        bigg_id = ''
        kegg_id = ''

        compartment_name = '1'
        model_name = '1'
        isoenzyme_acronyms = 'PFK1'
        mechanism = '1'
        mechanism_references = 'https://doi.org/10.1093/bioinformatics/bty942'
        mechanism_evidence_level = '1'
        subs_binding_order = 'adp_c, pep_c'
        prod_release_order = 'atp_m, pyr_c'
        std_gibbs_energy = 2.1
        std_gibbs_energy_std = 0.2
        std_gibbs_energy_ph = 7
        std_gibbs_energy_ionic_strength = 0.2
        std_gibbs_energy_references = 'equilibrator'


        response = self.client.post('/add_reaction', data=dict(
                                    name=reaction_name,
                                    acronym=reaction_acronym,
                                    grasp_id=reaction_grasp_id,
                                    reaction_string=reaction_string,
                                    bigg_id=bigg_id,
                                    kegg_id=kegg_id,
                                    metanetx_id=metanetx_id,
                                    compartment_name=compartment_name,
                                    model_name=model_name,
                                    isoenzyme_acronyms=isoenzyme_acronyms,
                                    mechanism=mechanism,
                                    mechanism_references=mechanism_references,
                                    mechanism_evidence_level=mechanism_evidence_level,
                                    subs_binding_order=subs_binding_order,
                                    prod_release_order=prod_release_order,
                                    std_gibbs_energy=std_gibbs_energy,
                                    std_gibbs_energy_std=std_gibbs_energy_std,
                                    std_gibbs_energy_ph=std_gibbs_energy_ph,
                                    std_gibbs_energy_ionic_strength=std_gibbs_energy_ionic_strength,
                                    std_gibbs_energy_references=std_gibbs_energy_references), follow_redirects=True)




        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See reactions - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your reaction is now live!' in response.data)


        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(GibbsEnergy.query.count(), 1)
        self.assertEqual(EnzymeReactionOrganism.query.count(), 1)
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Reference.query.count(), 2)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

        self.assertEqual(Reaction.query.count(), 1)
        self.assertEqual(Reaction.query.first().name, reaction_name)
        self.assertEqual(Reaction.query.first().compartment_name, Compartment.query.first().name)

        self.assertEqual(EnzymeReactionOrganism.query.first().grasp_id, reaction_grasp_id)
        self.assertEqual(EnzymeReactionOrganism.query.first().subs_binding_order, subs_binding_order)
        self.assertEqual(EnzymeReactionOrganism.query.first().prod_release_order, prod_release_order)
        self.assertEqual(EnzymeReactionOrganism.query.first().included_in_model, True)
        self.assertEqual(EnzymeReactionOrganism.query.first().reaction.name, reaction_name)
        self.assertEqual(EnzymeReactionOrganism.query.first().enzyme.isoenzyme, isoenzyme_acronyms)
        self.assertEqual(EnzymeReactionOrganism.query.first().model, Model.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.first().mech_evidence, EvidenceLevel.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.first().mechanism, Mechanism.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.first().gibbs_energy, GibbsEnergy.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.first().gibbs_energy.standard_dg, std_gibbs_energy)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].mechanism_references[0].doi, mechanism_references)

        self.assertEqual(GibbsEnergy.query.first().standard_dg, std_gibbs_energy)
        self.assertEqual(GibbsEnergy.query.first().standard_dg_std, std_gibbs_energy_std)
        self.assertEqual(GibbsEnergy.query.first().ph, std_gibbs_energy_ph)
        self.assertEqual(GibbsEnergy.query.first().ionic_strength, std_gibbs_energy_ionic_strength)
        self.assertEqual(GibbsEnergy.query.first().references[0].title, 'eQuilibrator')

        self.assertEqual(Reference.query.all()[0].title, 'eQuilibrator')
        self.assertEqual(Reference.query.all()[0].type_type, 'Online database')
        self.assertEqual(Reference.query.all()[1].doi, mechanism_references)

        self.assertEqual(Metabolite.query.count(), 4)
        self.assertEqual(Metabolite.query.all()[0].bigg_id, 'pep')
        self.assertEqual(Metabolite.query.all()[0].grasp_id, 'pep')
        self.assertEqual(Metabolite.query.all()[0].compartment_acronym, 'c')
        self.assertEqual(Metabolite.query.all()[1].bigg_id, 'adp')
        self.assertEqual(Metabolite.query.all()[1].grasp_id, 'adp')
        self.assertEqual(Metabolite.query.all()[1].compartment_acronym, 'c')
        self.assertEqual(Metabolite.query.all()[2].bigg_id, 'pyr')
        self.assertEqual(Metabolite.query.all()[2].grasp_id, 'pyr')
        self.assertEqual(Metabolite.query.all()[2].compartment_acronym, 'c')
        self.assertEqual(Metabolite.query.all()[3].bigg_id, 'atp')
        self.assertEqual(Metabolite.query.all()[3].grasp_id, 'atp')
        self.assertEqual(Metabolite.query.all()[3].compartment_acronym, 'm')

        self.assertEqual(ReactionMetabolite.query.count(), 4)
        self.assertEqual(ReactionMetabolite.query.all()[0].metabolite.bigg_id, 'pep')
        self.assertEqual(ReactionMetabolite.query.all()[0].stoich_coef, -1)
        self.assertEqual(ReactionMetabolite.query.all()[0].reaction.acronym, reaction_acronym)
        self.assertEqual(ReactionMetabolite.query.all()[1].metabolite.bigg_id, 'adp')
        self.assertEqual(ReactionMetabolite.query.all()[1].stoich_coef, -1.5)
        self.assertEqual(ReactionMetabolite.query.all()[1].reaction.acronym, reaction_acronym)
        self.assertEqual(ReactionMetabolite.query.all()[2].metabolite.bigg_id, 'pyr')
        self.assertEqual(ReactionMetabolite.query.all()[2].stoich_coef, 1)
        self.assertEqual(ReactionMetabolite.query.all()[2].reaction.acronym, reaction_acronym)
        self.assertEqual(ReactionMetabolite.query.all()[3].metabolite.bigg_id, 'atp')
        self.assertEqual(ReactionMetabolite.query.all()[3].stoich_coef, 2)
        self.assertEqual(ReactionMetabolite.query.all()[3].reaction.acronym, reaction_acronym)


class TestAddEnzymeMiscInfo(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        self.populate_db()


    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def populate_db(self):
        compartment_list = [('Cytosol', 'c'), ('Mitochondria', 'm')]

        for name, acronym in compartment_list:
            compartment = Compartment(name=name, acronym=acronym)
            db.session.add(compartment)
        db.session.commit()


        evidence_list = [('Literature 1', 'Got it from papers for the given organism'),
                         ('Literature 2', 'Got it from papers of other organisms'),
                         ('Predicted', 'Predicted by some algorithm'),
                         ('Educated guess', '')]

        for name, description in evidence_list:
            evidence = EvidenceLevel(name=name, description=description)
            db.session.add(evidence)
        db.session.commit()


        mechanism_list = ['UniUni', 'OrderedBiBi']

        for name in mechanism_list:
            mechanism = Mechanism(name=name)
            db.session.add(mechanism)
        db.session.commit()


        organism_list = ['E. coli', 'S. cerevisiae']

        for name in organism_list:
            organism = Organism(name=name)
            db.session.add(organism)
        db.session.commit()


        enzyme_list = [('Phosphofructokinase', 'PFK', 'PFK1', '1.2.3.33'),
                         ('Phosphofructokinase', 'PFK', 'PFK2', '1.2.3.33')]

        for name, acronym, isoenzyme, ec_number in enzyme_list:
            enzyme = Enzyme(name=name, acronym=acronym, isoenzyme=isoenzyme, ec_number=ec_number)
            db.session.add(enzyme)
        db.session.commit()


        model_list = [('E. coli - iteration 1', 'E. coli', 'MG16555'),
                      ('E. coli - iteration 2', 'E. coli', 'MG16555')]

        for name, organism_name, strain in model_list:
            model = Model(name=name, organism_name=organism_name, strain=strain)
            db.session.add(model)
        db.session.commit()


        reference_type_list = ['Article', 'Thesis', 'Online database', 'Book']

        for type in reference_type_list:
            reference_type = ReferenceType(type=type)
            db.session.add(reference_type)
        db.session.commit()


        reference = Reference(title='eQuilibrator', type_type='Online database')
        db.session.add(reference)
        db.session.commit()



    def test_add_first_reaction(self):

        reaction_name = 'phosphofructokinase'
        reaction_acronym = 'PFK'
        reaction_grasp_id = 'PFK1'
        reaction_string = '1 pep_c + 1.5 adp_c <-> pyr_c + 2.0 atp_m'
        metanetx_id = ''
        bigg_id = ''
        kegg_id = ''

        compartment_name = '1'
        model_name = '1'
        isoenzyme_acronyms = 'PFK1'
        mechanism = '1'
        mechanism_references = 'https://doi.org/10.1093/bioinformatics/bty942'
        mechanism_evidence_level = '1'
        subs_binding_order = 'adp_c, pep_c'
        prod_release_order = 'atp_m, pyr_c'
        std_gibbs_energy = 2.1
        std_gibbs_energy_std = 0.2
        std_gibbs_energy_ph = 7
        std_gibbs_energy_ionic_strength = 0.2
        std_gibbs_energy_references = 'equilibrator'


        response = self.client.post('/add_reaction', data=dict(
                                    name=reaction_name,
                                    acronym=reaction_acronym,
                                    grasp_id=reaction_grasp_id,
                                    reaction_string=reaction_string,
                                    bigg_id=bigg_id,
                                    kegg_id=kegg_id,
                                    metanetx_id=metanetx_id,
                                    compartment_name=compartment_name,
                                    model_name=model_name,
                                    isoenzyme_acronyms=isoenzyme_acronyms,
                                    mechanism=mechanism,
                                    mechanism_references=mechanism_references,
                                    mechanism_evidence_level=mechanism_evidence_level,
                                    subs_binding_order=subs_binding_order,
                                    prod_release_order=prod_release_order,
                                    std_gibbs_energy=std_gibbs_energy,
                                    std_gibbs_energy_std=std_gibbs_energy_std,
                                    std_gibbs_energy_ph=std_gibbs_energy_ph,
                                    std_gibbs_energy_ionic_strength=std_gibbs_energy_ionic_strength,
                                    std_gibbs_energy_references=std_gibbs_energy_references), follow_redirects=True)




        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See reactions - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your reaction is now live!' in response.data)


        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(GibbsEnergy.query.count(), 1)
        self.assertEqual(EnzymeReactionOrganism.query.count(), 1)
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Reference.query.count(), 2)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

        self.assertEqual(Reaction.query.count(), 1)
        self.assertEqual(Reaction.query.first().name, reaction_name)
        self.assertEqual(Reaction.query.first().compartment_name, Compartment.query.first().name)

        self.assertEqual(EnzymeReactionOrganism.query.first().grasp_id, reaction_grasp_id)
        self.assertEqual(EnzymeReactionOrganism.query.first().subs_binding_order, subs_binding_order)
        self.assertEqual(EnzymeReactionOrganism.query.first().prod_release_order, prod_release_order)
        self.assertEqual(EnzymeReactionOrganism.query.first().included_in_model, True)
        self.assertEqual(EnzymeReactionOrganism.query.first().reaction.name, reaction_name)
        self.assertEqual(EnzymeReactionOrganism.query.first().enzyme.isoenzyme, isoenzyme_acronyms)
        self.assertEqual(EnzymeReactionOrganism.query.first().model, Model.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.first().mech_evidence, EvidenceLevel.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.first().mechanism, Mechanism.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.first().gibbs_energy, GibbsEnergy.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.first().gibbs_energy.standard_dg, std_gibbs_energy)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].mechanism_references[0].doi, mechanism_references)

        self.assertEqual(GibbsEnergy.query.first().standard_dg, std_gibbs_energy)
        self.assertEqual(GibbsEnergy.query.first().standard_dg_std, std_gibbs_energy_std)
        self.assertEqual(GibbsEnergy.query.first().ph, std_gibbs_energy_ph)
        self.assertEqual(GibbsEnergy.query.first().ionic_strength, std_gibbs_energy_ionic_strength)
        self.assertEqual(GibbsEnergy.query.first().references[0].title, 'eQuilibrator')

        self.assertEqual(Reference.query.all()[0].title, 'eQuilibrator')
        self.assertEqual(Reference.query.all()[0].type_type, 'Online database')
        self.assertEqual(Reference.query.all()[1].doi, mechanism_references)

        self.assertEqual(Metabolite.query.count(), 4)
        self.assertEqual(Metabolite.query.all()[0].bigg_id, 'pep')
        self.assertEqual(Metabolite.query.all()[0].grasp_id, 'pep')
        self.assertEqual(Metabolite.query.all()[0].compartment_acronym, 'c')
        self.assertEqual(Metabolite.query.all()[1].bigg_id, 'adp')
        self.assertEqual(Metabolite.query.all()[1].grasp_id, 'adp')
        self.assertEqual(Metabolite.query.all()[1].compartment_acronym, 'c')
        self.assertEqual(Metabolite.query.all()[2].bigg_id, 'pyr')
        self.assertEqual(Metabolite.query.all()[2].grasp_id, 'pyr')
        self.assertEqual(Metabolite.query.all()[2].compartment_acronym, 'c')
        self.assertEqual(Metabolite.query.all()[3].bigg_id, 'atp')
        self.assertEqual(Metabolite.query.all()[3].grasp_id, 'atp')
        self.assertEqual(Metabolite.query.all()[3].compartment_acronym, 'm')

        self.assertEqual(ReactionMetabolite.query.count(), 4)
        self.assertEqual(ReactionMetabolite.query.all()[0].metabolite.bigg_id, 'pep')
        self.assertEqual(ReactionMetabolite.query.all()[0].stoich_coef, -1)
        self.assertEqual(ReactionMetabolite.query.all()[0].reaction.acronym, reaction_acronym)
        self.assertEqual(ReactionMetabolite.query.all()[1].metabolite.bigg_id, 'adp')
        self.assertEqual(ReactionMetabolite.query.all()[1].stoich_coef, -1.5)
        self.assertEqual(ReactionMetabolite.query.all()[1].reaction.acronym, reaction_acronym)
        self.assertEqual(ReactionMetabolite.query.all()[2].metabolite.bigg_id, 'pyr')
        self.assertEqual(ReactionMetabolite.query.all()[2].stoich_coef, 1)
        self.assertEqual(ReactionMetabolite.query.all()[2].reaction.acronym, reaction_acronym)
        self.assertEqual(ReactionMetabolite.query.all()[3].metabolite.bigg_id, 'atp')
        self.assertEqual(ReactionMetabolite.query.all()[3].stoich_coef, 2)
        self.assertEqual(ReactionMetabolite.query.all()[3].reaction.acronym, reaction_acronym)


class TestAddModel(unittest.TestCase):
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

    def test_add_first_model(self):

        model_name = 'E. coli - iteration 1'
        organism_name = 'E. coli'
        strain = 'MG16555'
        comments = 'Just testing...'

        self.assertEqual(Model.query.count(), 0)
        self.assertEqual(Organism.query.count(), 0)

        response = self.client.post('/add_model', data=dict(
                                    name=model_name,
                                    organism_name=organism_name,
                                    strain=strain,
                                    comments=comments), follow_redirects=True)


        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See models - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your model is now live!' in response.data)

        self.assertEqual(Model().query.first().name, model_name)
        self.assertEqual(Model().query.first().organism_name, organism_name)
        self.assertEqual(Model().query.first().strain, strain)
        self.assertEqual(Model().query.first().comments, comments)
        self.assertEqual(Organism().query.first().name, organism_name)
        self.assertEqual(Organism().query.first().models.count(), 1)
        self.assertEqual(Organism().query.first().models[0].name, model_name)


    def test_add_model_for_existing_organism(self):

        model_name = 'E. coli - iteration 1'
        organism_name = 'E. coli'
        strain = 'MG16555'
        comments = 'Just testing...'

        organism = Organism(name=organism_name)
        db.session.add(organism)

        self.assertEqual(Organism().query.first().name, organism_name)
        self.assertEqual(Organism().query.first().models.count(), 0)

        self.assertEqual(Model.query.count(), 0)
        self.assertEqual(Organism.query.count(), 1)


        response = self.client.post('/add_model', data=dict(
                                    name=model_name,
                                    organism_name=organism_name,
                                    strain=strain,
                                    comments=comments), follow_redirects=True)


        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See models - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your model is now live!' in response.data)

        self.assertEqual(Model().query.first().name, model_name)
        self.assertEqual(Model().query.first().strain, strain)
        self.assertEqual(Model().query.first().comments, comments)
        self.assertEqual(Organism().query.first().models.count(), 1)
        self.assertEqual(Organism().query.first().models[0].name, model_name)


    def test_add_model_empty_organism_name(self):

        model_name = 'E. coli - iteration 1'
        organism_name = 'E. coli'
        strain = 'MG16555'
        comments = 'Just testing...'

        organism = Organism(name=organism_name)
        db.session.add(organism)

        self.assertEqual(Organism().query.first().name, organism_name)
        self.assertEqual(Organism().query.first().models.count(), 0)

        self.assertEqual(Model.query.count(), 0)
        self.assertEqual(Organism.query.count(), 1)


        response = self.client.post('/add_model', data=dict(
                                    name=model_name,
                                    strain=strain,
                                    comments=comments), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    Add model - Kinetics DB \n</title>' in response.data)

        self.assertEqual(Model.query.count(), 0)
        self.assertEqual(Organism().query.first().models.count(), 0)


    def test_add_existing_model_name(self):
        model_name = 'E. coli - iteration 2'
        organism_name = 'E. coli'
        strain = 'MG16555'
        comments = 'Just testing...'

        model = Model(name=model_name,
                         organism_name=organism_name,
                         strain=strain)
        db.session.add(model)

        self.assertEqual(Model().query.first().name, model_name)
        self.assertEqual(Model().query.first().organism_name, organism_name)
        self.assertEqual(Model().query.first().strain, strain)

        self.assertEqual(Model.query.count(), 1)
        self.assertEqual(Organism.query.count(), 0)


        response = self.client.post('/add_model', data=dict(
                                    name=model_name,
                                    organism_name=organism_name,
                                    strain=strain,
                                    comments=comments), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    Add model - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'A model with that name already exists, please use another name' in response.data)

        self.assertEqual(Model.query.count(), 1)
        self.assertEqual(Organism().query.count(), 0)


    def test_add_second_model_name(self):

        model_name = 'E. coli - iteration 1'
        organism_name = 'E. coli'
        strain = 'MG16555'
        comments = 'Just testing...'

        model = Model(name=model_name,
                      organism_name=organism_name,
                      strain=strain)
        db.session.add(model)

        self.assertEqual(Model().query.first().name, model_name)
        self.assertEqual(Model().query.first().organism_name, organism_name)
        self.assertEqual(Model().query.first().strain, strain)

        self.assertEqual(Model.query.count(), 1)
        self.assertEqual(Organism.query.count(), 0)

        model_name = 'E. coli - iteration 2'

        response = self.client.post('/add_model', data=dict(
                                    name=model_name,
                                    organism_name=organism_name,
                                    strain=strain,
                                    comments=comments), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See models - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your model is now live!' in response.data)

        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism().query.count(), 1)
        self.assertEqual(Model().query.filter_by(name=model_name).first().name, model_name)
        self.assertEqual(Model().query.filter_by(name=model_name).first().strain, strain)
        self.assertEqual(Model().query.filter_by(name=model_name).first().comments, comments)
        self.assertEqual(Organism().query.first().models.count(), 2)
        self.assertEqual(Organism().query.first().models[0].name, 'E. coli - iteration 1')
        self.assertEqual(Organism().query.first().models[1].name, model_name)


class TestAddOrganism(unittest.TestCase):
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

    def test_add_organism(self):

        organism_name = 'E. coli'

        self.assertEqual(Organism.query.count(), 0)

        response = self.client.post('/add_organism', data=dict(
                                    name=organism_name), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See organisms - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your organism is now live!' in response.data)

        self.assertEqual(Organism().query.first().name, organism_name)
        self.assertEqual(Organism().query.first().models.count(), 0)


    def test_add_model_empty_organism_name(self):

        organism_name = 'E. coli'

        organism = Organism(name=organism_name)
        db.session.add(organism)

        self.assertEqual(Organism.query.count(), 1)
        self.assertEqual(Organism().query.first().name, organism_name)
        self.assertEqual(Organism().query.first().models.count(), 0)


        response = self.client.post('/add_organism', data=dict(
                                    name=organism_name), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    Add organism - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'An organism with that name already exists, please use another name' in response.data)

        self.assertEqual(Organism().query.first().name, organism_name)
        self.assertEqual(Organism().query.first().models.count(), 0)


class TestAddReaction(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        populate_db('reaction')

        self.reaction_name = 'phosphofructokinase'
        self.reaction_acronym = 'PFK'
        self.reaction_grasp_id = 'PFK1'
        self.reaction_string = '1 pep_c + 1.5 adp_c <-> pyr_c + 2.0 atp_m'
        self.metanetx_id = ''
        self.bigg_id = ''
        self.kegg_id = ''

        self.compartment = '1'
        self.organism='1'
        self.models = ['1', '2']
        self.enzymes = ['1','2']
        self.mechanism = '1'
        self.mechanism_references = 'https://doi.org/10.1093/bioinformatics/bty942, https://doi.org/10.1093/bioinformatics/bty943'
        self.mechanism_evidence_level = '1'
        self.subs_binding_order = 'adp_c, pep_c'
        self.prod_release_order = 'atp_m, pyr_c'
        self.std_gibbs_energy = 2.1
        self.std_gibbs_energy_std = 0.2
        self.std_gibbs_energy_ph = 7
        self.std_gibbs_energy_ionic_strength = 0.2
        self.std_gibbs_energy_references = 'equilibrator'
        self.comments = ''

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()


    def test_add_first_reaction(self):


        true_isoenzyme_acronym = 'PFK1'
        true_gibbs_energy_ref = 'eQuilibrator'
        self.models = '1'
        self.enzymes = '1'
        self.mechanism_references = 'https://doi.org/10.1093/bioinformatics/bty942'


        response = self.client.post('/add_reaction', data=dict(
                                    name=self.reaction_name,
                                    acronym=self.reaction_acronym,
                                    grasp_id=self.reaction_grasp_id,
                                    reaction_string=self.reaction_string,
                                    bigg_id=self.bigg_id,
                                    kegg_id=self.kegg_id,
                                    metanetx_id=self.metanetx_id,
                                    compartment=self.compartment,
                                    organism=self.organism,
                                    models=self.models,
                                    enzymes=self.enzymes,
                                    mechanism=self.mechanism,
                                    mechanism_references=self.mechanism_references,
                                    mechanism_evidence_level=self.mechanism_evidence_level,
                                    subs_binding_order=self.subs_binding_order,
                                    prod_release_order=self.prod_release_order,
                                    std_gibbs_energy=self.std_gibbs_energy,
                                    std_gibbs_energy_std=self.std_gibbs_energy_std,
                                    std_gibbs_energy_ph=self.std_gibbs_energy_ph,
                                    std_gibbs_energy_ionic_strength=self.std_gibbs_energy_ionic_strength,
                                    std_gibbs_energy_references=self.std_gibbs_energy_references,
                                    comments=self.comments), follow_redirects=True)



        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See reactions - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your reaction is now live!' in response.data)


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
        self.assertEqual(Reference.query.all()[0].type_type, 'Online database')
        self.assertEqual(Reference.query.all()[1].doi, self.mechanism_references)

        self.assertEqual(Metabolite.query.count(), 4)
        self.assertEqual(Metabolite.query.all()[0].bigg_id, 'pep')
        self.assertEqual(Metabolite.query.all()[0].grasp_id, 'pep')
        self.assertEqual(Metabolite.query.all()[0].compartment_acronym, 'c')
        self.assertEqual(Metabolite.query.all()[1].bigg_id, 'adp')
        self.assertEqual(Metabolite.query.all()[1].grasp_id, 'adp')
        self.assertEqual(Metabolite.query.all()[1].compartment_acronym, 'c')
        self.assertEqual(Metabolite.query.all()[2].bigg_id, 'pyr')
        self.assertEqual(Metabolite.query.all()[2].grasp_id, 'pyr')
        self.assertEqual(Metabolite.query.all()[2].compartment_acronym, 'c')
        self.assertEqual(Metabolite.query.all()[3].bigg_id, 'atp')
        self.assertEqual(Metabolite.query.all()[3].grasp_id, 'atp')
        self.assertEqual(Metabolite.query.all()[3].compartment_acronym, 'm')

        self.assertEqual(ReactionMetabolite.query.count(), 4)
        self.assertEqual(ReactionMetabolite.query.all()[0].metabolite.bigg_id, 'pep')
        self.assertEqual(ReactionMetabolite.query.all()[0].stoich_coef, -1)
        self.assertEqual(ReactionMetabolite.query.all()[0].reaction.acronym, self.reaction_acronym)
        self.assertEqual(ReactionMetabolite.query.all()[1].metabolite.bigg_id, 'adp')
        self.assertEqual(ReactionMetabolite.query.all()[1].stoich_coef, -1.5)
        self.assertEqual(ReactionMetabolite.query.all()[1].reaction.acronym, self.reaction_acronym)
        self.assertEqual(ReactionMetabolite.query.all()[2].metabolite.bigg_id, 'pyr')
        self.assertEqual(ReactionMetabolite.query.all()[2].stoich_coef, 1)
        self.assertEqual(ReactionMetabolite.query.all()[2].reaction.acronym, self.reaction_acronym)
        self.assertEqual(ReactionMetabolite.query.all()[3].metabolite.bigg_id, 'atp')
        self.assertEqual(ReactionMetabolite.query.all()[3].stoich_coef, 2)
        self.assertEqual(ReactionMetabolite.query.all()[3].reaction.acronym, self.reaction_acronym)

    def test_add_reaction_two_isoenzymes(self):

        true_isoenzyme_acronym1 = 'PFK1'
        true_isoenzyme_acronym2 = 'PFK2'
        true_gibbs_energy_ref = 'eQuilibrator'
        self.models = '1'
        self.mechanism_references = 'https://doi.org/10.1093/bioinformatics/bty942'


        response = self.client.post('/add_reaction', data=dict(
                                    name=self.reaction_name,
                                    acronym=self.reaction_acronym,
                                    grasp_id=self.reaction_grasp_id,
                                    reaction_string=self.reaction_string,
                                    bigg_id=self.bigg_id,
                                    kegg_id=self.kegg_id,
                                    metanetx_id=self.metanetx_id,
                                    compartment=self.compartment,
                                    organism=self.organism,
                                    models=self.models,
                                    enzymes=self.enzymes,
                                    mechanism=self.mechanism,
                                    mechanism_references=self.mechanism_references,
                                    mechanism_evidence_level=self.mechanism_evidence_level,
                                    subs_binding_order=self.subs_binding_order,
                                    prod_release_order=self.prod_release_order,
                                    std_gibbs_energy=self.std_gibbs_energy,
                                    std_gibbs_energy_std=self.std_gibbs_energy_std,
                                    std_gibbs_energy_ph=self.std_gibbs_energy_ph,
                                    std_gibbs_energy_ionic_strength=self.std_gibbs_energy_ionic_strength,
                                    std_gibbs_energy_references=self.std_gibbs_energy_references,
                                    comments=self.comments), follow_redirects=True)




        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See reactions - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your reaction is now live!' in response.data)


        self.assertEqual(Enzyme.query.count(), 2)

        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Reference.query.count(), 2)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)
        self.assertEqual(Model.query.first().enzyme_reaction_organisms.count(), 2)

        self.assertEqual(Reaction.query.count(), 1)
        self.assertEqual(Reaction.query.first().name, self.reaction_name)
        self.assertEqual(Reaction.query.first().compartment_name, Compartment.query.first().name)

        self.assertEqual(EnzymeReactionOrganism.query.all()[0].enzyme_id, 1)
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].enzyme_id, 2)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].reaction_id, 1)
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].reaction_id, 1)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].organism_id, 1)
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].organism_id, 1)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].mechanism_id, 1)
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].mechanism_id, 1)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].mech_evidence_level_id, 1)
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].mech_evidence_level_id, 1)

        self.assertEqual(EnzymeReactionOrganism.query.count(), 2)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].grasp_id, self.reaction_grasp_id)
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].grasp_id, self.reaction_grasp_id)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].subs_binding_order, self.subs_binding_order)
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].subs_binding_order, self.subs_binding_order)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].prod_release_order, self.prod_release_order)
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].prod_release_order, self.prod_release_order)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].reaction.name, self.reaction_name)
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].reaction.name, self.reaction_name)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].enzyme.isoenzyme, true_isoenzyme_acronym1)
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].enzyme.isoenzyme, true_isoenzyme_acronym2)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].models[0], Model.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].models[0], Model.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].mech_evidence, EvidenceLevel.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].mech_evidence, EvidenceLevel.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].mechanism, Mechanism.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].mechanism, Mechanism.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].mechanism_references.count(), 1)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].mechanism_references[0].doi, self.mechanism_references)
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].mechanism_references[0].doi, self.mechanism_references)

        self.assertEqual(GibbsEnergy.query.count(), 1)
        self.assertEqual(GibbsEnergy.query.first().standard_dg, self.std_gibbs_energy)
        self.assertEqual(GibbsEnergy.query.first().standard_dg_std, self.std_gibbs_energy_std)
        self.assertEqual(GibbsEnergy.query.first().ph, self.std_gibbs_energy_ph)
        self.assertEqual(GibbsEnergy.query.first().ionic_strength, self.std_gibbs_energy_ionic_strength)
        self.assertEqual(GibbsEnergy.query.first().references[0].title, true_gibbs_energy_ref)

        self.assertEqual(GibbsEnergyReactionModel.query.count(), 1)
        self.assertEqual(GibbsEnergyReactionModel.query.first().reaction_id, 1)
        self.assertEqual(GibbsEnergyReactionModel.query.first().model_id, 1)
        self.assertEqual(GibbsEnergyReactionModel.query.first().gibbs_energy_id, 1)

        self.assertEqual(Reference.query.all()[0].title, true_gibbs_energy_ref)
        self.assertEqual(Reference.query.all()[0].type_type, 'Online database')
        self.assertEqual(Reference.query.all()[1].doi, self.mechanism_references)

        self.assertEqual(Metabolite.query.count(), 4)
        self.assertEqual(Metabolite.query.all()[0].bigg_id, 'pep')
        self.assertEqual(Metabolite.query.all()[0].grasp_id, 'pep')
        self.assertEqual(Metabolite.query.all()[0].compartment_acronym, 'c')
        self.assertEqual(Metabolite.query.all()[1].bigg_id, 'adp')
        self.assertEqual(Metabolite.query.all()[1].grasp_id, 'adp')
        self.assertEqual(Metabolite.query.all()[1].compartment_acronym, 'c')
        self.assertEqual(Metabolite.query.all()[2].bigg_id, 'pyr')
        self.assertEqual(Metabolite.query.all()[2].grasp_id, 'pyr')
        self.assertEqual(Metabolite.query.all()[2].compartment_acronym, 'c')
        self.assertEqual(Metabolite.query.all()[3].bigg_id, 'atp')
        self.assertEqual(Metabolite.query.all()[3].grasp_id, 'atp')
        self.assertEqual(Metabolite.query.all()[3].compartment_acronym, 'm')

        self.assertEqual(ReactionMetabolite.query.count(), 4)
        self.assertEqual(ReactionMetabolite.query.all()[0].metabolite.bigg_id, 'pep')
        self.assertEqual(ReactionMetabolite.query.all()[0].stoich_coef, -1)
        self.assertEqual(ReactionMetabolite.query.all()[0].reaction.acronym, self.reaction_acronym)
        self.assertEqual(ReactionMetabolite.query.all()[1].metabolite.bigg_id, 'adp')
        self.assertEqual(ReactionMetabolite.query.all()[1].stoich_coef, -1.5)
        self.assertEqual(ReactionMetabolite.query.all()[1].reaction.acronym, self.reaction_acronym)
        self.assertEqual(ReactionMetabolite.query.all()[2].metabolite.bigg_id, 'pyr')
        self.assertEqual(ReactionMetabolite.query.all()[2].stoich_coef, 1)
        self.assertEqual(ReactionMetabolite.query.all()[2].reaction.acronym, self.reaction_acronym)
        self.assertEqual(ReactionMetabolite.query.all()[3].metabolite.bigg_id, 'atp')
        self.assertEqual(ReactionMetabolite.query.all()[3].stoich_coef, 2)
        self.assertEqual(ReactionMetabolite.query.all()[3].reaction.acronym, self.reaction_acronym)

    def test_add_reaction_two_models(self):
        true_isoenzyme_acronym1 = 'PFK1'
        true_isoenzyme_acronym2 = 'PFK2'
        true_gibbs_energy_ref = 'eQuilibrator'

        response = self.client.post('/add_reaction', data=dict(
                                    name=self.reaction_name,
                                    acronym=self.reaction_acronym,
                                    grasp_id=self.reaction_grasp_id,
                                    reaction_string=self.reaction_string,
                                    bigg_id=self.bigg_id,
                                    kegg_id=self.kegg_id,
                                    metanetx_id=self.metanetx_id,
                                    compartment=self.compartment,
                                    organism=self.organism,
                                    models=self.models,
                                    enzymes=self.enzymes,
                                    mechanism=self.mechanism,
                                    mechanism_references=self.mechanism_references,
                                    mechanism_evidence_level=self.mechanism_evidence_level,
                                    subs_binding_order=self.subs_binding_order,
                                    prod_release_order=self.prod_release_order,
                                    std_gibbs_energy=self.std_gibbs_energy,
                                    std_gibbs_energy_std=self.std_gibbs_energy_std,
                                    std_gibbs_energy_ph=self.std_gibbs_energy_ph,
                                    std_gibbs_energy_ionic_strength=self.std_gibbs_energy_ionic_strength,
                                    std_gibbs_energy_references=self.std_gibbs_energy_references,
                                    comments=self.comments), follow_redirects=True)




        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See reactions - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your reaction is now live!' in response.data)


        self.assertEqual(Enzyme.query.count(), 2)

        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Reference.query.count(), 3)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)
        self.assertEqual(Model.query.all()[0].enzyme_reaction_organisms.count(), 2)
        self.assertEqual(Model.query.all()[1].enzyme_reaction_organisms.count(), 2)

        self.assertEqual(Reaction.query.count(), 1)
        self.assertEqual(Reaction.query.first().name, self.reaction_name)
        self.assertEqual(Reaction.query.first().compartment_name, Compartment.query.first().name)

        self.assertEqual(EnzymeReactionOrganism.query.all()[0].enzyme_id, 1)
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].enzyme_id, 2)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].reaction_id, 1)
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].reaction_id, 1)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].organism_id, 1)
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].organism_id, 1)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].mechanism_id, 1)
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].mechanism_id, 1)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].mech_evidence_level_id, 1)
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].mech_evidence_level_id, 1)

        self.assertEqual(EnzymeReactionOrganism.query.count(), 2)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].grasp_id, self.reaction_grasp_id)
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].grasp_id, self.reaction_grasp_id)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].subs_binding_order, self.subs_binding_order)
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].subs_binding_order, self.subs_binding_order)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].prod_release_order, self.prod_release_order)
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].prod_release_order, self.prod_release_order)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].reaction.name, self.reaction_name)
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].reaction.name, self.reaction_name)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].enzyme.isoenzyme, true_isoenzyme_acronym1)
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].enzyme.isoenzyme, true_isoenzyme_acronym2)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].models.count(), 2)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].models[0], Model.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].models[0], Model.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].mech_evidence, EvidenceLevel.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].mech_evidence, EvidenceLevel.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].mechanism, Mechanism.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].mechanism, Mechanism.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].mechanism_references.count(), 2)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].mechanism_references[0].doi, self.mechanism_references.split(', ')[0])
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].mechanism_references[1].doi, self.mechanism_references.split(', ')[1])
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].mechanism_references[0].doi, self.mechanism_references.split(', ')[0])
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].mechanism_references[1].doi, self.mechanism_references.split(', ')[1])


        self.assertEqual(GibbsEnergyReactionModel.query.count(), 2)
        self.assertEqual(GibbsEnergyReactionModel.query.all()[0].reaction_id, 1)
        self.assertEqual(GibbsEnergyReactionModel.query.all()[1].reaction_id, 1)
        self.assertEqual(GibbsEnergyReactionModel.query.all()[0].model_id, 1)
        self.assertEqual(GibbsEnergyReactionModel.query.all()[1].model_id, 2)
        self.assertEqual(GibbsEnergyReactionModel.query.all()[0].gibbs_energy_id, 1)
        self.assertEqual(GibbsEnergyReactionModel.query.all()[1].gibbs_energy_id, 1)

        self.assertEqual(GibbsEnergy.query.count(), 1)
        self.assertEqual(GibbsEnergy.query.first().standard_dg, self.std_gibbs_energy)
        self.assertEqual(GibbsEnergy.query.first().standard_dg_std, self.std_gibbs_energy_std)
        self.assertEqual(GibbsEnergy.query.first().ph, self.std_gibbs_energy_ph)
        self.assertEqual(GibbsEnergy.query.first().ionic_strength, self.std_gibbs_energy_ionic_strength)
        self.assertEqual(GibbsEnergy.query.first().references[0].title, true_gibbs_energy_ref)

        self.assertEqual(Reference.query.all()[0].title, true_gibbs_energy_ref)
        self.assertEqual(Reference.query.all()[0].type_type, 'Online database')
        self.assertEqual(Reference.query.all()[1].doi, self.mechanism_references.split(', ')[0])
        self.assertEqual(Reference.query.all()[2].doi, self.mechanism_references.split(', ')[1])

        self.assertEqual(Metabolite.query.count(), 4)
        self.assertEqual(Metabolite.query.all()[0].bigg_id, 'pep')
        self.assertEqual(Metabolite.query.all()[0].grasp_id, 'pep')
        self.assertEqual(Metabolite.query.all()[0].compartment_acronym, 'c')
        self.assertEqual(Metabolite.query.all()[1].bigg_id, 'adp')
        self.assertEqual(Metabolite.query.all()[1].grasp_id, 'adp')
        self.assertEqual(Metabolite.query.all()[1].compartment_acronym, 'c')
        self.assertEqual(Metabolite.query.all()[2].bigg_id, 'pyr')
        self.assertEqual(Metabolite.query.all()[2].grasp_id, 'pyr')
        self.assertEqual(Metabolite.query.all()[2].compartment_acronym, 'c')
        self.assertEqual(Metabolite.query.all()[3].bigg_id, 'atp')
        self.assertEqual(Metabolite.query.all()[3].grasp_id, 'atp')
        self.assertEqual(Metabolite.query.all()[3].compartment_acronym, 'm')

        self.assertEqual(ReactionMetabolite.query.count(), 4)
        self.assertEqual(ReactionMetabolite.query.all()[0].metabolite.bigg_id, 'pep')
        self.assertEqual(ReactionMetabolite.query.all()[0].stoich_coef, -1)
        self.assertEqual(ReactionMetabolite.query.all()[0].reaction.acronym, self.reaction_acronym)
        self.assertEqual(ReactionMetabolite.query.all()[1].metabolite.bigg_id, 'adp')
        self.assertEqual(ReactionMetabolite.query.all()[1].stoich_coef, -1.5)
        self.assertEqual(ReactionMetabolite.query.all()[1].reaction.acronym, self.reaction_acronym)
        self.assertEqual(ReactionMetabolite.query.all()[2].metabolite.bigg_id, 'pyr')
        self.assertEqual(ReactionMetabolite.query.all()[2].stoich_coef, 1)
        self.assertEqual(ReactionMetabolite.query.all()[2].reaction.acronym, self.reaction_acronym)
        self.assertEqual(ReactionMetabolite.query.all()[3].metabolite.bigg_id, 'atp')
        self.assertEqual(ReactionMetabolite.query.all()[3].stoich_coef, 2)
        self.assertEqual(ReactionMetabolite.query.all()[3].reaction.acronym, self.reaction_acronym)

    def test_add_reaction_two_mechanism_references(self):

        true_isoenzyme_acronym1 = 'PFK1'
        true_isoenzyme_acronym2 = 'PFK2'
        true_gibbs_energy_ref = 'eQuilibrator'
        true_mechanism_references = self.mechanism_references.split(', ')
        self.models = '1'
        self.enzymes = ['1', '2']

        response = self.client.post('/add_reaction', data=dict(
                                    name=self.reaction_name,
                                    acronym=self.reaction_acronym,
                                    grasp_id=self.reaction_grasp_id,
                                    reaction_string=self.reaction_string,
                                    bigg_id=self.bigg_id,
                                    kegg_id=self.kegg_id,
                                    metanetx_id=self.metanetx_id,
                                    compartment=self.compartment,
                                    organism=self.organism,
                                    models=self.models,
                                    enzymes=self.enzymes,
                                    mechanism=self.mechanism,
                                    mechanism_references=self.mechanism_references,
                                    mechanism_evidence_level=self.mechanism_evidence_level,
                                    subs_binding_order=self.subs_binding_order,
                                    prod_release_order=self.prod_release_order,
                                    std_gibbs_energy=self.std_gibbs_energy,
                                    std_gibbs_energy_std=self.std_gibbs_energy_std,
                                    std_gibbs_energy_ph=self.std_gibbs_energy_ph,
                                    std_gibbs_energy_ionic_strength=self.std_gibbs_energy_ionic_strength,
                                    std_gibbs_energy_references=self.std_gibbs_energy_references,
                                    comments=self.comments), follow_redirects=True)


        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See reactions - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your reaction is now live!' in response.data)


        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

        self.assertEqual(Reaction.query.count(), 1)
        self.assertEqual(Reaction.query.first().name, self.reaction_name)
        self.assertEqual(Reaction.query.first().compartment_name, Compartment.query.first().name)

        self.assertEqual(EnzymeReactionOrganism.query.all()[0].enzyme_id, 1)
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].enzyme_id, 2)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].reaction_id, 1)
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].reaction_id, 1)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].organism_id, 1)
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].organism_id, 1)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].mechanism_id, 1)
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].mechanism_id, 1)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].mech_evidence_level_id, 1)
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].mech_evidence_level_id, 1)

        self.assertEqual(EnzymeReactionOrganism.query.count(), 2)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].grasp_id, self.reaction_grasp_id)
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].grasp_id, self.reaction_grasp_id)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].subs_binding_order, self.subs_binding_order)
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].subs_binding_order, self.subs_binding_order)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].prod_release_order, self.prod_release_order)
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].prod_release_order, self.prod_release_order)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].reaction.name, self.reaction_name)
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].reaction.name, self.reaction_name)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].enzyme.isoenzyme, true_isoenzyme_acronym1)
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].enzyme.isoenzyme, true_isoenzyme_acronym2)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].models[0], Model.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].models[0], Model.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].mech_evidence, EvidenceLevel.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].mech_evidence, EvidenceLevel.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].mechanism, Mechanism.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].mechanism, Mechanism.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].mechanism_references.count(), 2)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].mechanism_references[0].doi, true_mechanism_references[0])
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].mechanism_references[1].doi, true_mechanism_references[1])
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].mechanism_references.count(), 2)
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].mechanism_references[0].doi, true_mechanism_references[0])
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].mechanism_references[1].doi, true_mechanism_references[1])


        self.assertEqual(GibbsEnergyReactionModel.query.count(), 1)
        self.assertEqual(GibbsEnergyReactionModel.query.all()[0].reaction_id, 1)
        self.assertEqual(GibbsEnergyReactionModel.query.all()[0].model_id, 1)
        self.assertEqual(GibbsEnergyReactionModel.query.all()[0].gibbs_energy_id, 1)

        self.assertEqual(GibbsEnergy.query.count(), 1)
        self.assertEqual(GibbsEnergy.query.first().standard_dg, self.std_gibbs_energy)
        self.assertEqual(GibbsEnergy.query.first().standard_dg_std, self.std_gibbs_energy_std)
        self.assertEqual(GibbsEnergy.query.first().ph, self.std_gibbs_energy_ph)
        self.assertEqual(GibbsEnergy.query.first().ionic_strength, self.std_gibbs_energy_ionic_strength)
        self.assertEqual(GibbsEnergy.query.first().references[0].title, true_gibbs_energy_ref)

        self.assertEqual(Reference.query.count(), 3)
        self.assertEqual(Reference.query.all()[0].title, true_gibbs_energy_ref)
        self.assertEqual(Reference.query.all()[0].type_type, 'Online database')
        self.assertEqual(Reference.query.all()[1].doi, true_mechanism_references[0])
        self.assertEqual(Reference.query.all()[2].doi, true_mechanism_references[1])

        self.assertEqual(Metabolite.query.count(), 4)
        self.assertEqual(Metabolite.query.all()[0].bigg_id, 'pep')
        self.assertEqual(Metabolite.query.all()[0].grasp_id, 'pep')
        self.assertEqual(Metabolite.query.all()[0].compartment_acronym, 'c')
        self.assertEqual(Metabolite.query.all()[1].bigg_id, 'adp')
        self.assertEqual(Metabolite.query.all()[1].grasp_id, 'adp')
        self.assertEqual(Metabolite.query.all()[1].compartment_acronym, 'c')
        self.assertEqual(Metabolite.query.all()[2].bigg_id, 'pyr')
        self.assertEqual(Metabolite.query.all()[2].grasp_id, 'pyr')
        self.assertEqual(Metabolite.query.all()[2].compartment_acronym, 'c')
        self.assertEqual(Metabolite.query.all()[3].bigg_id, 'atp')
        self.assertEqual(Metabolite.query.all()[3].grasp_id, 'atp')
        self.assertEqual(Metabolite.query.all()[3].compartment_acronym, 'm')

        self.assertEqual(ReactionMetabolite.query.count(), 4)
        self.assertEqual(ReactionMetabolite.query.all()[0].metabolite.bigg_id, 'pep')
        self.assertEqual(ReactionMetabolite.query.all()[0].stoich_coef, -1)
        self.assertEqual(ReactionMetabolite.query.all()[0].reaction.acronym, self.reaction_acronym)
        self.assertEqual(ReactionMetabolite.query.all()[1].metabolite.bigg_id, 'adp')
        self.assertEqual(ReactionMetabolite.query.all()[1].stoich_coef, -1.5)
        self.assertEqual(ReactionMetabolite.query.all()[1].reaction.acronym, self.reaction_acronym)
        self.assertEqual(ReactionMetabolite.query.all()[2].metabolite.bigg_id, 'pyr')
        self.assertEqual(ReactionMetabolite.query.all()[2].stoich_coef, 1)
        self.assertEqual(ReactionMetabolite.query.all()[2].reaction.acronym, self.reaction_acronym)
        self.assertEqual(ReactionMetabolite.query.all()[3].metabolite.bigg_id, 'atp')
        self.assertEqual(ReactionMetabolite.query.all()[3].stoich_coef, 2)
        self.assertEqual(ReactionMetabolite.query.all()[3].reaction.acronym, self.reaction_acronym)

    def test_add_reaction_no_isoenzyme(self):

        self.models = '1'
        self.enzymes = ''
        self.mechanism = ''
        self.mechanism_references = ''
        self.mechanism_evidence_level = ''
        self.subs_binding_order = ''
        self.prod_release_order = ''

        response = self.client.post('/add_reaction', data=dict(
                                    name=self.reaction_name,
                                    acronym=self.reaction_acronym,
                                    grasp_id=self.reaction_grasp_id,
                                    reaction_string=self.reaction_string,
                                    bigg_id=self.bigg_id,
                                    kegg_id=self.kegg_id,
                                    metanetx_id=self.metanetx_id,
                                    compartment=self.compartment,
                                    organism=self.organism,
                                    models=self.models,
                                    enzymes=self.enzymes,
                                    mechanism=self.mechanism,
                                    mechanism_references=self.mechanism_references,
                                    mechanism_evidence_level=self.mechanism_evidence_level,
                                    subs_binding_order=self.subs_binding_order,
                                    prod_release_order=self.prod_release_order,
                                    std_gibbs_energy=self.std_gibbs_energy,
                                    std_gibbs_energy_std=self.std_gibbs_energy_std,
                                    std_gibbs_energy_ph=self.std_gibbs_energy_ph,
                                    std_gibbs_energy_ionic_strength=self.std_gibbs_energy_ionic_strength,
                                    std_gibbs_energy_references=self.std_gibbs_energy_references,
                                    comments=self.comments), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    Add reaction - Kinetics DB \n</title>' in response.data)

        self.assertEqual(Reaction.query.count(), 0)
        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(GibbsEnergy.query.count(), 0)
        self.assertEqual(GibbsEnergyReactionModel.query.count(), 0)
        self.assertEqual(EnzymeReactionOrganism.query.count(), 0)
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Reference.query.count(), 1)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

    def test_add_reaction_mechanism_and_no_isoenzyme(self):

        self.models = '1'
        self.enzymes = ''

        response = self.client.post('/add_reaction', data=dict(
                                    name=self.reaction_name,
                                    acronym=self.reaction_acronym,
                                    grasp_id=self.reaction_grasp_id,
                                    reaction_string=self.reaction_string,
                                    bigg_id=self.bigg_id,
                                    kegg_id=self.kegg_id,
                                    metanetx_id=self.metanetx_id,
                                    compartment=self.compartment,
                                    organism=self.organism,
                                    models=self.models,
                                    enzymes=self.enzymes,
                                    mechanism=self.mechanism,
                                    mechanism_references=self.mechanism_references,
                                    mechanism_evidence_level=self.mechanism_evidence_level,
                                    subs_binding_order=self.subs_binding_order,
                                    prod_release_order=self.prod_release_order,
                                    std_gibbs_energy=self.std_gibbs_energy,
                                    std_gibbs_energy_std=self.std_gibbs_energy_std,
                                    std_gibbs_energy_ph=self.std_gibbs_energy_ph,
                                    std_gibbs_energy_ionic_strength=self.std_gibbs_energy_ionic_strength,
                                    std_gibbs_energy_references=self.std_gibbs_energy_references,
                                    comments=self.comments), follow_redirects=True)


        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    Add reaction - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'If you add a reaction mechanism, you need to specify the catalyzing isoenzyme(s).' in response.data)

        self.assertEqual(Reaction.query.count(), 0)
        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(GibbsEnergy.query.count(), 0)
        self.assertEqual(GibbsEnergyReactionModel.query.count(), 0)
        self.assertEqual(EnzymeReactionOrganism.query.count(), 0)
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Reference.query.count(), 1)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

    def test_add_reaction_mechanism_evidence_level(self):

        self.models = '1'
        self.mechanism = ''

        response = self.client.post('/add_reaction', data=dict(
                                    name=self.reaction_name,
                                    acronym=self.reaction_acronym,
                                    grasp_id=self.reaction_grasp_id,
                                    reaction_string=self.reaction_string,
                                    bigg_id=self.bigg_id,
                                    kegg_id=self.kegg_id,
                                    metanetx_id=self.metanetx_id,
                                    compartment=self.compartment,
                                    organism=self.organism,
                                    models=self.models,
                                    enzymes=self.enzymes,
                                    mechanism=self.mechanism,
                                    mechanism_references=self.mechanism_references,
                                    mechanism_evidence_level=self.mechanism_evidence_level,
                                    subs_binding_order=self.subs_binding_order,
                                    prod_release_order=self.prod_release_order,
                                    std_gibbs_energy=self.std_gibbs_energy,
                                    std_gibbs_energy_std=self.std_gibbs_energy_std,
                                    std_gibbs_energy_ph=self.std_gibbs_energy_ph,
                                    std_gibbs_energy_ionic_strength=self.std_gibbs_energy_ionic_strength,
                                    std_gibbs_energy_references=self.std_gibbs_energy_references,
                                    comments=self.comments), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    Add reaction - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'You cannot specify evidence level for the mechanism without specifying a mechanism.' in response.data)

        self.assertEqual(Reaction.query.count(), 0)
        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(GibbsEnergy.query.count(), 0)
        self.assertEqual(GibbsEnergyReactionModel.query.count(), 0)
        self.assertEqual(EnzymeReactionOrganism.query.count(), 0)
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Reference.query.count(), 1)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

    def test_add_reaction_subs_binding_order(self):

        self.models = '1'
        self.enzymes = ''

        response = self.client.post('/add_reaction', data=dict(
                                    name=self.reaction_name,
                                    acronym=self.reaction_acronym,
                                    grasp_id=self.reaction_grasp_id,
                                    reaction_string=self.reaction_string,
                                    bigg_id=self.bigg_id,
                                    kegg_id=self.kegg_id,
                                    metanetx_id=self.metanetx_id,
                                    compartment=self.compartment,
                                    organism=self.organism,
                                    models=self.models,
                                    enzymes=self.enzymes,
                                    mechanism=self.mechanism,
                                    mechanism_references=self.mechanism_references,
                                    mechanism_evidence_level=self.mechanism_evidence_level,
                                    subs_binding_order=self.subs_binding_order,
                                    prod_release_order=self.prod_release_order,
                                    std_gibbs_energy=self.std_gibbs_energy,
                                    std_gibbs_energy_std=self.std_gibbs_energy_std,
                                    std_gibbs_energy_ph=self.std_gibbs_energy_ph,
                                    std_gibbs_energy_ionic_strength=self.std_gibbs_energy_ionic_strength,
                                    std_gibbs_energy_references=self.std_gibbs_energy_references,
                                    comments=self.comments), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    Add reaction - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'If you add substrate binding order without specifying the catalyzing isoenzyme(s)' in response.data)

        self.assertEqual(Reaction.query.count(), 0)
        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(GibbsEnergy.query.count(), 0)
        self.assertEqual(GibbsEnergyReactionModel.query.count(), 0)
        self.assertEqual(EnzymeReactionOrganism.query.count(), 0)
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Reference.query.count(), 1)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

    def test_add_reaction_prod_release_order(self):

        self.models = '1'
        self.enzymes = ''
        self.subs_binding_order = ''
        self.prod_release_order = 'pyr_c, atp_m'
        self.std_gibbs_energy = ''
        self.std_gibbs_energy_std = ''
        self.std_gibbs_energy_ph = ''
        self.std_gibbs_energy_ionic_strength = ''
        self.std_gibbs_energy_references = ''

        response = self.client.post('/add_reaction', data=dict(
                                    name=self.reaction_name,
                                    acronym=self.reaction_acronym,
                                    grasp_id=self.reaction_grasp_id,
                                    reaction_string=self.reaction_string,
                                    bigg_id=self.bigg_id,
                                    kegg_id=self.kegg_id,
                                    metanetx_id=self.metanetx_id,
                                    compartment=self.compartment,
                                    organism=self.organism,
                                    models=self.models,
                                    enzymes=self.enzymes,
                                    mechanism=self.mechanism,
                                    mechanism_references=self.mechanism_references,
                                    mechanism_evidence_level=self.mechanism_evidence_level,
                                    subs_binding_order=self.subs_binding_order,
                                    prod_release_order=self.prod_release_order,
                                    std_gibbs_energy=self.std_gibbs_energy,
                                    std_gibbs_energy_std=self.std_gibbs_energy_std,
                                    std_gibbs_energy_ph=self.std_gibbs_energy_ph,
                                    std_gibbs_energy_ionic_strength=self.std_gibbs_energy_ionic_strength,
                                    std_gibbs_energy_references=self.std_gibbs_energy_references,
                                    comments=self.comments), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    Add reaction - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'If you add product release order without specifying the catalyzing isoenzyme(s)' in response.data)

        self.assertEqual(Reaction.query.count(), 0)
        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(GibbsEnergy.query.count(), 0)
        self.assertEqual(GibbsEnergyReactionModel.query.count(), 0)
        self.assertEqual(EnzymeReactionOrganism.query.count(), 0)
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Reference.query.count(), 1)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

    def test_add_reaction_std_gibbs_energy_std_no_model(self):

        self.models = ''
        self.enzymes = '1'

        response = self.client.post('/add_reaction', data=dict(
                                    name=self.reaction_name,
                                    acronym=self.reaction_acronym,
                                    grasp_id=self.reaction_grasp_id,
                                    reaction_string=self.reaction_string,
                                    bigg_id=self.bigg_id,
                                    kegg_id=self.kegg_id,
                                    metanetx_id=self.metanetx_id,
                                    compartment=self.compartment,
                                    organism=self.organism,
                                    models=self.models,
                                    enzymes=self.enzymes,
                                    mechanism=self.mechanism,
                                    mechanism_references=self.mechanism_references,
                                    mechanism_evidence_level=self.mechanism_evidence_level,
                                    subs_binding_order=self.subs_binding_order,
                                    prod_release_order=self.prod_release_order,
                                    std_gibbs_energy=self.std_gibbs_energy,
                                    std_gibbs_energy_std=self.std_gibbs_energy_std,
                                    std_gibbs_energy_ph=self.std_gibbs_energy_ph,
                                    std_gibbs_energy_ionic_strength=self.std_gibbs_energy_ionic_strength,
                                    std_gibbs_energy_references=self.std_gibbs_energy_references,
                                    comments=self.comments), follow_redirects=True)


        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    Add reaction - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Gibbs energies cannot be added to reactions alone, a model must be associated as well. Please add model name.' in response.data)

        self.assertEqual(Reaction.query.count(), 0)
        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(GibbsEnergyReactionModel.query.count(), 0)
        self.assertEqual(EnzymeReactionOrganism.query.count(), 0)
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Reference.query.count(), 1)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

    def test_add_reaction_std_gibbs_energy_std(self):

        self.models = '1'
        self.enzymes = '1'
        self.std_gibbs_energy = ''
        self.std_gibbs_energy_std = 0.2
        self.std_gibbs_energy_ph = ''
        self.std_gibbs_energy_ionic_strength = ''
        self.std_gibbs_energy_references = ''

        response = self.client.post('/add_reaction', data=dict(
                                    name=self.reaction_name,
                                    acronym=self.reaction_acronym,
                                    grasp_id=self.reaction_grasp_id,
                                    reaction_string=self.reaction_string,
                                    bigg_id=self.bigg_id,
                                    kegg_id=self.kegg_id,
                                    metanetx_id=self.metanetx_id,
                                    compartment=self.compartment,
                                    organism=self.organism,
                                    models=self.models,
                                    enzymes=self.enzymes,
                                    mechanism=self.mechanism,
                                    mechanism_references=self.mechanism_references,
                                    mechanism_evidence_level=self.mechanism_evidence_level,
                                    subs_binding_order=self.subs_binding_order,
                                    prod_release_order=self.prod_release_order,
                                    std_gibbs_energy=self.std_gibbs_energy,
                                    std_gibbs_energy_std=self.std_gibbs_energy_std,
                                    std_gibbs_energy_ph=self.std_gibbs_energy_ph,
                                    std_gibbs_energy_ionic_strength=self.std_gibbs_energy_ionic_strength,
                                    std_gibbs_energy_references=self.std_gibbs_energy_references,
                                    comments=self.comments), follow_redirects=True)


        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    Add reaction - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Please specify the standard Gibbs energy as well.' in response.data)

        self.assertEqual(Reaction.query.count(), 0)
        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(GibbsEnergyReactionModel.query.count(), 0)
        self.assertEqual(EnzymeReactionOrganism.query.count(), 0)
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Reference.query.count(), 1)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

    def test_add_reaction_std_gibbs_energy_ph(self):

        self.models = '1'
        self.enzymes = '1'
        self.std_gibbs_energy = ''
        self.std_gibbs_energy_std = ''
        self.std_gibbs_energy_ph = 7
        self.std_gibbs_energy_ionic_strength = ''
        self.std_gibbs_energy_references = ''


        response = self.client.post('/add_reaction', data=dict(
                                    name=self.reaction_name,
                                    acronym=self.reaction_acronym,
                                    grasp_id=self.reaction_grasp_id,
                                    reaction_string=self.reaction_string,
                                    bigg_id=self.bigg_id,
                                    kegg_id=self.kegg_id,
                                    metanetx_id=self.metanetx_id,
                                    compartment=self.compartment,
                                    organism=self.organism,
                                    models=self.models,
                                    enzymes=self.enzymes,
                                    mechanism=self.mechanism,
                                    mechanism_references=self.mechanism_references,
                                    mechanism_evidence_level=self.mechanism_evidence_level,
                                    subs_binding_order=self.subs_binding_order,
                                    prod_release_order=self.prod_release_order,
                                    std_gibbs_energy=self.std_gibbs_energy,
                                    std_gibbs_energy_std=self.std_gibbs_energy_std,
                                    std_gibbs_energy_ph=self.std_gibbs_energy_ph,
                                    std_gibbs_energy_ionic_strength=self.std_gibbs_energy_ionic_strength,
                                    std_gibbs_energy_references=self.std_gibbs_energy_references,
                                    comments=self.comments), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    Add reaction - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Please specify the standard Gibbs energy as well.' in response.data)

        self.assertEqual(Reaction.query.count(), 0)
        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(GibbsEnergyReactionModel.query.count(), 0)
        self.assertEqual(EnzymeReactionOrganism.query.count(), 0)
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Reference.query.count(), 1)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

    def test_add_reaction_std_gibbs_energy_is(self):

        self.models = '1'
        self.enzymes = '1'
        self.std_gibbs_energy = ''
        self.std_gibbs_energy_std = ''
        self.std_gibbs_energy_ph = ''
        self.std_gibbs_energy_ionic_strength = 0.1
        self.std_gibbs_energy_references = ''


        response = self.client.post('/add_reaction', data=dict(
                                    name=self.reaction_name,
                                    acronym=self.reaction_acronym,
                                    grasp_id=self.reaction_grasp_id,
                                    reaction_string=self.reaction_string,
                                    bigg_id=self.bigg_id,
                                    kegg_id=self.kegg_id,
                                    metanetx_id=self.metanetx_id,
                                    compartment=self.compartment,
                                    organism=self.organism,
                                    models=self.models,
                                    enzymes=self.enzymes,
                                    mechanism=self.mechanism,
                                    mechanism_references=self.mechanism_references,
                                    mechanism_evidence_level=self.mechanism_evidence_level,
                                    subs_binding_order=self.subs_binding_order,
                                    prod_release_order=self.prod_release_order,
                                    std_gibbs_energy=self.std_gibbs_energy,
                                    std_gibbs_energy_std=self.std_gibbs_energy_std,
                                    std_gibbs_energy_ph=self.std_gibbs_energy_ph,
                                    std_gibbs_energy_ionic_strength=self.std_gibbs_energy_ionic_strength,
                                    std_gibbs_energy_references=self.std_gibbs_energy_references,
                                    comments=self.comments), follow_redirects=True)



        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    Add reaction - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Please specify the standard Gibbs energy as well.' in response.data)

        self.assertEqual(Reaction.query.count(), 0)
        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(GibbsEnergyReactionModel.query.count(), 0)
        self.assertEqual(EnzymeReactionOrganism.query.count(), 0)
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Reference.query.count(), 1)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

    def test_add_reaction_std_gibbs_energy_refs(self):


        self.models = '1'
        self.enzymes = '1'
        self.std_gibbs_energy = ''
        self.std_gibbs_energy_std = ''
        self.std_gibbs_energy_ph = ''
        self.std_gibbs_energy_ionic_strength = ''
        self.std_gibbs_energy_references = 'equilibrator'


        response = self.client.post('/add_reaction', data=dict(
                                    name=self.reaction_name,
                                    acronym=self.reaction_acronym,
                                    grasp_id=self.reaction_grasp_id,
                                    reaction_string=self.reaction_string,
                                    bigg_id=self.bigg_id,
                                    kegg_id=self.kegg_id,
                                    metanetx_id=self.metanetx_id,
                                    compartment=self.compartment,
                                    organism=self.organism,
                                    models=self.models,
                                    enzymes=self.enzymes,
                                    mechanism=self.mechanism,
                                    mechanism_references=self.mechanism_references,
                                    mechanism_evidence_level=self.mechanism_evidence_level,
                                    subs_binding_order=self.subs_binding_order,
                                    prod_release_order=self.prod_release_order,
                                    std_gibbs_energy=self.std_gibbs_energy,
                                    std_gibbs_energy_std=self.std_gibbs_energy_std,
                                    std_gibbs_energy_ph=self.std_gibbs_energy_ph,
                                    std_gibbs_energy_ionic_strength=self.std_gibbs_energy_ionic_strength,
                                    std_gibbs_energy_references=self.std_gibbs_energy_references,
                                    comments=self.comments), follow_redirects=True)



        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    Add reaction - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Please specify the standard Gibbs energy as well.' in response.data)

        self.assertEqual(Reaction.query.count(), 0)
        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(GibbsEnergy.query.count(), 0)
        self.assertEqual(GibbsEnergyReactionModel.query.count(), 0)
        self.assertEqual(EnzymeReactionOrganism.query.count(), 0)
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Reference.query.count(), 1)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

    def test_add_reaction_std_gibbs_energy_no_refs(self):

        self.models = '1'
        self.enzymes = '1'
        self.std_gibbs_energy = 7.1
        self.std_gibbs_energy_std = ''
        self.std_gibbs_energy_ph = ''
        self.std_gibbs_energy_ionic_strength = ''
        self.std_gibbs_energy_references = ''


        response = self.client.post('/add_reaction', data=dict(
                                    name=self.reaction_name,
                                    acronym=self.reaction_acronym,
                                    grasp_id=self.reaction_grasp_id,
                                    reaction_string=self.reaction_string,
                                    bigg_id=self.bigg_id,
                                    kegg_id=self.kegg_id,
                                    metanetx_id=self.metanetx_id,
                                    compartment=self.compartment,
                                    organism=self.organism,
                                    models=self.models,
                                    enzymes=self.enzymes,
                                    mechanism=self.mechanism,
                                    mechanism_references=self.mechanism_references,
                                    mechanism_evidence_level=self.mechanism_evidence_level,
                                    subs_binding_order=self.subs_binding_order,
                                    prod_release_order=self.prod_release_order,
                                    std_gibbs_energy=self.std_gibbs_energy,
                                    std_gibbs_energy_std=self.std_gibbs_energy_std,
                                    std_gibbs_energy_ph=self.std_gibbs_energy_ph,
                                    std_gibbs_energy_ionic_strength=self.std_gibbs_energy_ionic_strength,
                                    std_gibbs_energy_references=self.std_gibbs_energy_references,
                                    comments=self.comments), follow_redirects=True)


        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    Add reaction - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Please specify the reference for the above standard Gibbs energy' in response.data)

        self.assertEqual(Reaction.query.count(), 0)
        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(GibbsEnergy.query.count(), 0)
        self.assertEqual(GibbsEnergyReactionModel.query.count(), 0)
        self.assertEqual(EnzymeReactionOrganism.query.count(), 0)
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Reference.query.count(), 1)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

    def test_add_reaction_only(self):

        true_gibbs_energy_ref = 'eQuilibrator'

        self.compartment = ''
        self.models = ''
        self.enzymes = '1'
        self.mechanism = ''
        self.mechanism_references = ''
        self.mechanism_evidence_level = ''
        self.subs_binding_order = ''
        self.prod_release_order = ''
        self.std_gibbs_energy = ''
        self.std_gibbs_energy_std = ''
        self.std_gibbs_energy_ph = ''
        self.std_gibbs_energy_ionic_strength = ''
        self.std_gibbs_energy_references = ''

        response = self.client.post('/add_reaction', data=dict(
                                    name=self.reaction_name,
                                    acronym=self.reaction_acronym,
                                    grasp_id=self.reaction_grasp_id,
                                    reaction_string=self.reaction_string,
                                    bigg_id=self.bigg_id,
                                    kegg_id=self.kegg_id,
                                    metanetx_id=self.metanetx_id,
                                    compartment=self.compartment,
                                    organism=self.organism,
                                    models=self.models,
                                    enzymes=self.enzymes,
                                    mechanism=self.mechanism,
                                    mechanism_references=self.mechanism_references,
                                    mechanism_evidence_level=self.mechanism_evidence_level,
                                    subs_binding_order=self.subs_binding_order,
                                    prod_release_order=self.prod_release_order,
                                    std_gibbs_energy=self.std_gibbs_energy,
                                    std_gibbs_energy_std=self.std_gibbs_energy_std,
                                    std_gibbs_energy_ph=self.std_gibbs_energy_ph,
                                    std_gibbs_energy_ionic_strength=self.std_gibbs_energy_ionic_strength,
                                    std_gibbs_energy_references=self.std_gibbs_energy_references,
                                    comments=self.comments), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See reactions - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your reaction is now live!' in response.data)

        self.assertEqual(Reaction.query.count(), 1)
        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(GibbsEnergy.query.count(), 0)
        self.assertEqual(GibbsEnergyReactionModel.query.count(), 0)

        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Reference.query.count(), 1)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

        self.assertEqual(EnzymeReactionOrganism.query.count(), 1)
        self.assertEqual(EnzymeReactionOrganism.query.first().enzyme_id, 1)
        self.assertEqual(EnzymeReactionOrganism.query.first().reaction_id, 1)
        self.assertEqual(EnzymeReactionOrganism.query.first().organism_id, 1)

        self.assertEqual(Reaction.query.count(), 1)
        self.assertEqual(Reaction.query.first().name, self.reaction_name)
        self.assertEqual(Reaction.query.first().compartment_name, '')

        self.assertEqual(Reference.query.count(), 1)
        self.assertEqual(Reference.query.all()[0].title, true_gibbs_energy_ref)
        self.assertEqual(Reference.query.all()[0].type_type, 'Online database')


        self.assertEqual(Metabolite.query.count(), 4)
        self.assertEqual(Metabolite.query.all()[0].bigg_id, 'pep')
        self.assertEqual(Metabolite.query.all()[0].grasp_id, 'pep')
        self.assertEqual(Metabolite.query.all()[0].compartment_acronym, 'c')
        self.assertEqual(Metabolite.query.all()[1].bigg_id, 'adp')
        self.assertEqual(Metabolite.query.all()[1].grasp_id, 'adp')
        self.assertEqual(Metabolite.query.all()[1].compartment_acronym, 'c')
        self.assertEqual(Metabolite.query.all()[2].bigg_id, 'pyr')
        self.assertEqual(Metabolite.query.all()[2].grasp_id, 'pyr')
        self.assertEqual(Metabolite.query.all()[2].compartment_acronym, 'c')
        self.assertEqual(Metabolite.query.all()[3].bigg_id, 'atp')
        self.assertEqual(Metabolite.query.all()[3].grasp_id, 'atp')
        self.assertEqual(Metabolite.query.all()[3].compartment_acronym, 'm')

        self.assertEqual(ReactionMetabolite.query.count(), 4)
        self.assertEqual(ReactionMetabolite.query.all()[0].metabolite.bigg_id, 'pep')
        self.assertEqual(ReactionMetabolite.query.all()[0].stoich_coef, -1)
        self.assertEqual(ReactionMetabolite.query.all()[0].reaction.acronym, self.reaction_acronym)
        self.assertEqual(ReactionMetabolite.query.all()[1].metabolite.bigg_id, 'adp')
        self.assertEqual(ReactionMetabolite.query.all()[1].stoich_coef, -1.5)
        self.assertEqual(ReactionMetabolite.query.all()[1].reaction.acronym, self.reaction_acronym)
        self.assertEqual(ReactionMetabolite.query.all()[2].metabolite.bigg_id, 'pyr')
        self.assertEqual(ReactionMetabolite.query.all()[2].stoich_coef, 1)
        self.assertEqual(ReactionMetabolite.query.all()[2].reaction.acronym, self.reaction_acronym)
        self.assertEqual(ReactionMetabolite.query.all()[3].metabolite.bigg_id, 'atp')
        self.assertEqual(ReactionMetabolite.query.all()[3].stoich_coef, 2)
        self.assertEqual(ReactionMetabolite.query.all()[3].reaction.acronym, self.reaction_acronym)

    def test_add_reaction_compartment(self):

        true_gibbs_energy_ref = 'eQuilibrator'

        self.compartment = '1'
        self.models = ''
        self.enzymes = '1'
        self.mechanism = ''
        self.mechanism_references = ''
        self.mechanism_evidence_level = ''
        self.subs_binding_order = ''
        self.prod_release_order = ''
        self.std_gibbs_energy = ''
        self.std_gibbs_energy_std = ''
        self.std_gibbs_energy_ph = ''
        self.std_gibbs_energy_ionic_strength = ''
        self.std_gibbs_energy_references = ''

        response = self.client.post('/add_reaction', data=dict(
                                    name=self.reaction_name,
                                    acronym=self.reaction_acronym,
                                    grasp_id=self.reaction_grasp_id,
                                    reaction_string=self.reaction_string,
                                    bigg_id=self.bigg_id,
                                    kegg_id=self.kegg_id,
                                    metanetx_id=self.metanetx_id,
                                    compartment=self.compartment,
                                    organism=self.organism,
                                    models=self.models,
                                    enzymes=self.enzymes,
                                    mechanism=self.mechanism,
                                    mechanism_references=self.mechanism_references,
                                    mechanism_evidence_level=self.mechanism_evidence_level,
                                    subs_binding_order=self.subs_binding_order,
                                    prod_release_order=self.prod_release_order,
                                    std_gibbs_energy=self.std_gibbs_energy,
                                    std_gibbs_energy_std=self.std_gibbs_energy_std,
                                    std_gibbs_energy_ph=self.std_gibbs_energy_ph,
                                    std_gibbs_energy_ionic_strength=self.std_gibbs_energy_ionic_strength,
                                    std_gibbs_energy_references=self.std_gibbs_energy_references,
                                    comments=self.comments), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See reactions - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your reaction is now live!' in response.data)

        self.assertEqual(Reaction.query.count(), 1)
        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(GibbsEnergy.query.count(), 0)
        self.assertEqual(GibbsEnergyReactionModel.query.count(), 0)
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Reference.query.count(), 1)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

        self.assertEqual(Reaction.query.count(), 1)
        self.assertEqual(Reaction.query.first().name, self.reaction_name)
        self.assertEqual(Reaction.query.first().compartment_name, Compartment.query.first().name)

        self.assertEqual(EnzymeReactionOrganism.query.count(), 1)
        self.assertEqual(EnzymeReactionOrganism.query.first().enzyme_id, 1)
        self.assertEqual(EnzymeReactionOrganism.query.first().reaction_id, 1)
        self.assertEqual(EnzymeReactionOrganism.query.first().organism_id, 1)

        self.assertEqual(Reference.query.count(), 1)
        self.assertEqual(Reference.query.all()[0].title, true_gibbs_energy_ref)
        self.assertEqual(Reference.query.all()[0].type_type, 'Online database')

        self.assertEqual(Metabolite.query.count(), 4)
        self.assertEqual(Metabolite.query.all()[0].bigg_id, 'pep')
        self.assertEqual(Metabolite.query.all()[0].grasp_id, 'pep')
        self.assertEqual(Metabolite.query.all()[0].compartment_acronym, 'c')
        self.assertEqual(Metabolite.query.all()[1].bigg_id, 'adp')
        self.assertEqual(Metabolite.query.all()[1].grasp_id, 'adp')
        self.assertEqual(Metabolite.query.all()[1].compartment_acronym, 'c')
        self.assertEqual(Metabolite.query.all()[2].bigg_id, 'pyr')
        self.assertEqual(Metabolite.query.all()[2].grasp_id, 'pyr')
        self.assertEqual(Metabolite.query.all()[2].compartment_acronym, 'c')
        self.assertEqual(Metabolite.query.all()[3].bigg_id, 'atp')
        self.assertEqual(Metabolite.query.all()[3].grasp_id, 'atp')
        self.assertEqual(Metabolite.query.all()[3].compartment_acronym, 'm')

        self.assertEqual(ReactionMetabolite.query.count(), 4)
        self.assertEqual(ReactionMetabolite.query.all()[0].metabolite.bigg_id, 'pep')
        self.assertEqual(ReactionMetabolite.query.all()[0].stoich_coef, -1)
        self.assertEqual(ReactionMetabolite.query.all()[0].reaction.acronym, self.reaction_acronym)
        self.assertEqual(ReactionMetabolite.query.all()[1].metabolite.bigg_id, 'adp')
        self.assertEqual(ReactionMetabolite.query.all()[1].stoich_coef, -1.5)
        self.assertEqual(ReactionMetabolite.query.all()[1].reaction.acronym, self.reaction_acronym)
        self.assertEqual(ReactionMetabolite.query.all()[2].metabolite.bigg_id, 'pyr')
        self.assertEqual(ReactionMetabolite.query.all()[2].stoich_coef, 1)
        self.assertEqual(ReactionMetabolite.query.all()[2].reaction.acronym, self.reaction_acronym)
        self.assertEqual(ReactionMetabolite.query.all()[3].metabolite.bigg_id, 'atp')
        self.assertEqual(ReactionMetabolite.query.all()[3].stoich_coef, 2)
        self.assertEqual(ReactionMetabolite.query.all()[3].reaction.acronym, self.reaction_acronym)

    def test_add_reaction_mechanism(self):

        true_gibbs_energy_ref = 'eQuilibrator'

        self.models = ''
        self.enzymes = '1'

        self.std_gibbs_energy = ''
        self.std_gibbs_energy_std = ''
        self.std_gibbs_energy_ph = ''
        self.std_gibbs_energy_ionic_strength = ''
        self.std_gibbs_energy_references = ''

        response = self.client.post('/add_reaction', data=dict(
                                    name=self.reaction_name,
                                    acronym=self.reaction_acronym,
                                    grasp_id=self.reaction_grasp_id,
                                    reaction_string=self.reaction_string,
                                    bigg_id=self.bigg_id,
                                    kegg_id=self.kegg_id,
                                    metanetx_id=self.metanetx_id,
                                    compartment=self.compartment,
                                    organism=self.organism,
                                    models=self.models,
                                    enzymes=self.enzymes,
                                    mechanism=self.mechanism,
                                    mechanism_references=self.mechanism_references,
                                    mechanism_evidence_level=self.mechanism_evidence_level,
                                    subs_binding_order=self.subs_binding_order,
                                    prod_release_order=self.prod_release_order,
                                    std_gibbs_energy=self.std_gibbs_energy,
                                    std_gibbs_energy_std=self.std_gibbs_energy_std,
                                    std_gibbs_energy_ph=self.std_gibbs_energy_ph,
                                    std_gibbs_energy_ionic_strength=self.std_gibbs_energy_ionic_strength,
                                    std_gibbs_energy_references=self.std_gibbs_energy_references,
                                    comments=self.comments), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See reactions - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your reaction is now live!' in response.data)

        self.assertEqual(Reaction.query.count(), 1)
        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(GibbsEnergy.query.count(), 0)
        self.assertEqual(GibbsEnergyReactionModel.query.count(), 0)
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

        self.assertEqual(Reaction.query.count(), 1)
        self.assertEqual(Reaction.query.first().name, self.reaction_name)
        self.assertEqual(Reaction.query.first().compartment_name, Compartment.query.first().name)

        self.assertEqual(Reference.query.count(), 3)
        self.assertEqual(Reference.query.all()[0].title, true_gibbs_energy_ref)
        self.assertEqual(Reference.query.all()[0].type_type, 'Online database')
        self.assertEqual(Reference.query.all()[1].doi, self.mechanism_references.split(', ')[0])
        self.assertEqual(Reference.query.all()[2].doi, self.mechanism_references.split(', ')[1])

        self.assertEqual(Metabolite.query.count(), 4)
        self.assertEqual(Metabolite.query.all()[0].bigg_id, 'pep')
        self.assertEqual(Metabolite.query.all()[0].grasp_id, 'pep')
        self.assertEqual(Metabolite.query.all()[0].compartment_acronym, 'c')
        self.assertEqual(Metabolite.query.all()[1].bigg_id, 'adp')
        self.assertEqual(Metabolite.query.all()[1].grasp_id, 'adp')
        self.assertEqual(Metabolite.query.all()[1].compartment_acronym, 'c')
        self.assertEqual(Metabolite.query.all()[2].bigg_id, 'pyr')
        self.assertEqual(Metabolite.query.all()[2].grasp_id, 'pyr')
        self.assertEqual(Metabolite.query.all()[2].compartment_acronym, 'c')
        self.assertEqual(Metabolite.query.all()[3].bigg_id, 'atp')
        self.assertEqual(Metabolite.query.all()[3].grasp_id, 'atp')
        self.assertEqual(Metabolite.query.all()[3].compartment_acronym, 'm')

        self.assertEqual(ReactionMetabolite.query.count(), 4)
        self.assertEqual(ReactionMetabolite.query.all()[0].metabolite.bigg_id, 'pep')
        self.assertEqual(ReactionMetabolite.query.all()[0].stoich_coef, -1)
        self.assertEqual(ReactionMetabolite.query.all()[0].reaction.acronym, self.reaction_acronym)
        self.assertEqual(ReactionMetabolite.query.all()[1].metabolite.bigg_id, 'adp')
        self.assertEqual(ReactionMetabolite.query.all()[1].stoich_coef, -1.5)
        self.assertEqual(ReactionMetabolite.query.all()[1].reaction.acronym, self.reaction_acronym)
        self.assertEqual(ReactionMetabolite.query.all()[2].metabolite.bigg_id, 'pyr')
        self.assertEqual(ReactionMetabolite.query.all()[2].stoich_coef, 1)
        self.assertEqual(ReactionMetabolite.query.all()[2].reaction.acronym, self.reaction_acronym)
        self.assertEqual(ReactionMetabolite.query.all()[3].metabolite.bigg_id, 'atp')
        self.assertEqual(ReactionMetabolite.query.all()[3].stoich_coef, 2)
        self.assertEqual(ReactionMetabolite.query.all()[3].reaction.acronym, self.reaction_acronym)

        self.assertEqual(EnzymeReactionOrganism.query.count(), 1)
        self.assertEqual(EnzymeReactionOrganism.query.first().enzyme_id, 1)
        self.assertEqual(EnzymeReactionOrganism.query.first().reaction_id, 1)
        self.assertEqual(EnzymeReactionOrganism.query.first().organism_id, 1)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].grasp_id, self.reaction_grasp_id)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].subs_binding_order, self.subs_binding_order)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].prod_release_order, self.prod_release_order)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].reaction.name, self.reaction_name)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].enzyme.isoenzyme, 'PFK1')
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].models.count(), 0)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].mech_evidence, EvidenceLevel.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].mechanism, Mechanism.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].mechanism_references.count(), 2)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].mechanism_references[0].doi, self.mechanism_references.split(', ')[0])
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].mechanism_references[1].doi, self.mechanism_references.split(', ')[1])

    def test_add_reaction_gibbs_energy(self):

        true_gibbs_energy_ref = 'eQuilibrator'

        self.models = '1'
        self.enzymes = '1'

        self.mechanism = ''
        self.mechanism_references = ''
        self.mechanism_evidence_level = ''
        self.subs_binding_order = ''
        self.prod_release_order = ''

        response = self.client.post('/add_reaction', data=dict(
                                    name=self.reaction_name,
                                    acronym=self.reaction_acronym,
                                    grasp_id=self.reaction_grasp_id,
                                    reaction_string=self.reaction_string,
                                    bigg_id=self.bigg_id,
                                    kegg_id=self.kegg_id,
                                    metanetx_id=self.metanetx_id,
                                    compartment=self.compartment,
                                    organism=self.organism,
                                    models=self.models,
                                    enzymes=self.enzymes,
                                    mechanism=self.mechanism,
                                    mechanism_references=self.mechanism_references,
                                    mechanism_evidence_level=self.mechanism_evidence_level,
                                    subs_binding_order=self.subs_binding_order,
                                    prod_release_order=self.prod_release_order,
                                    std_gibbs_energy=self.std_gibbs_energy,
                                    std_gibbs_energy_std=self.std_gibbs_energy_std,
                                    std_gibbs_energy_ph=self.std_gibbs_energy_ph,
                                    std_gibbs_energy_ionic_strength=self.std_gibbs_energy_ionic_strength,
                                    std_gibbs_energy_references=self.std_gibbs_energy_references,
                                    comments=self.comments), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See reactions - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your reaction is now live!' in response.data)

        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

        self.assertEqual(Reaction.query.count(), 1)
        self.assertEqual(Reaction.query.first().name, self.reaction_name)
        self.assertEqual(Reaction.query.first().compartment_name, Compartment.query.first().name)

        self.assertEqual(EnzymeReactionOrganism.query.count(), 1)
        self.assertEqual(EnzymeReactionOrganism.query.first().enzyme_id, 1)
        self.assertEqual(EnzymeReactionOrganism.query.first().reaction_id, 1)
        self.assertEqual(EnzymeReactionOrganism.query.first().organism_id, 1)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].grasp_id, self.reaction_grasp_id)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].subs_binding_order, self.subs_binding_order)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].prod_release_order, self.prod_release_order)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].reaction.name, self.reaction_name)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].enzyme.isoenzyme, 'PFK1')
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].models[0], Model.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].mechanism, None)

        self.assertEqual(GibbsEnergyReactionModel.query.count(), 1)
        self.assertEqual(GibbsEnergyReactionModel.query.all()[0].reaction_id, 1)
        self.assertEqual(GibbsEnergyReactionModel.query.all()[0].model_id, 1)
        self.assertEqual(GibbsEnergyReactionModel.query.all()[0].gibbs_energy_id, 1)

        self.assertEqual(GibbsEnergy.query.count(), 1)
        self.assertEqual(GibbsEnergy.query.first().standard_dg, self.std_gibbs_energy)
        self.assertEqual(GibbsEnergy.query.first().standard_dg_std, self.std_gibbs_energy_std)
        self.assertEqual(GibbsEnergy.query.first().ph, self.std_gibbs_energy_ph)
        self.assertEqual(GibbsEnergy.query.first().ionic_strength, self.std_gibbs_energy_ionic_strength)
        self.assertEqual(GibbsEnergy.query.first().references[0].title, true_gibbs_energy_ref)

        self.assertEqual(Reference.query.count(), 1)
        self.assertEqual(Reference.query.all()[0].title, true_gibbs_energy_ref)
        self.assertEqual(Reference.query.all()[0].type_type, 'Online database')

        self.assertEqual(Metabolite.query.count(), 4)
        self.assertEqual(Metabolite.query.all()[0].bigg_id, 'pep')
        self.assertEqual(Metabolite.query.all()[0].grasp_id, 'pep')
        self.assertEqual(Metabolite.query.all()[0].compartment_acronym, 'c')
        self.assertEqual(Metabolite.query.all()[1].bigg_id, 'adp')
        self.assertEqual(Metabolite.query.all()[1].grasp_id, 'adp')
        self.assertEqual(Metabolite.query.all()[1].compartment_acronym, 'c')
        self.assertEqual(Metabolite.query.all()[2].bigg_id, 'pyr')
        self.assertEqual(Metabolite.query.all()[2].grasp_id, 'pyr')
        self.assertEqual(Metabolite.query.all()[2].compartment_acronym, 'c')
        self.assertEqual(Metabolite.query.all()[3].bigg_id, 'atp')
        self.assertEqual(Metabolite.query.all()[3].grasp_id, 'atp')
        self.assertEqual(Metabolite.query.all()[3].compartment_acronym, 'm')

        self.assertEqual(ReactionMetabolite.query.count(), 4)
        self.assertEqual(ReactionMetabolite.query.all()[0].metabolite.bigg_id, 'pep')
        self.assertEqual(ReactionMetabolite.query.all()[0].stoich_coef, -1)
        self.assertEqual(ReactionMetabolite.query.all()[0].reaction.acronym, self.reaction_acronym)
        self.assertEqual(ReactionMetabolite.query.all()[1].metabolite.bigg_id, 'adp')
        self.assertEqual(ReactionMetabolite.query.all()[1].stoich_coef, -1.5)
        self.assertEqual(ReactionMetabolite.query.all()[1].reaction.acronym, self.reaction_acronym)
        self.assertEqual(ReactionMetabolite.query.all()[2].metabolite.bigg_id, 'pyr')
        self.assertEqual(ReactionMetabolite.query.all()[2].stoich_coef, 1)
        self.assertEqual(ReactionMetabolite.query.all()[2].reaction.acronym, self.reaction_acronym)
        self.assertEqual(ReactionMetabolite.query.all()[3].metabolite.bigg_id, 'atp')
        self.assertEqual(ReactionMetabolite.query.all()[3].stoich_coef, 2)
        self.assertEqual(ReactionMetabolite.query.all()[3].reaction.acronym, self.reaction_acronym)



class TestAddEnzymeModelAssumption(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        self.populate_db()


    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def populate_db(self):
        compartment_list = [('Cytosol', 'c'), ('Mitochondria', 'm')]

        for name, acronym in compartment_list:
            compartment = Compartment(name=name, acronym=acronym)
            db.session.add(compartment)
        db.session.commit()


        evidence_list = [('Literature 1', 'Got it from papers for the given organism'),
                         ('Literature 2', 'Got it from papers of other organisms'),
                         ('Predicted', 'Predicted by some algorithm'),
                         ('Educated guess', '')]

        for name, description in evidence_list:
            evidence = EvidenceLevel(name=name, description=description)
            db.session.add(evidence)
        db.session.commit()


        mechanism_list = ['UniUni', 'OrderedBiBi']

        for name in mechanism_list:
            mechanism = Mechanism(name=name)
            db.session.add(mechanism)
        db.session.commit()


        organism_list = ['E. coli', 'S. cerevisiae']

        for name in organism_list:
            organism = Organism(name=name)
            db.session.add(organism)
        db.session.commit()


        enzyme_list = [('Phosphofructokinase', 'PFK', 'PFK1', '1.2.3.33'),
                         ('Phosphofructokinase', 'PFK', 'PFK2', '1.2.3.33')]

        for name, acronym, isoenzyme, ec_number in enzyme_list:
            enzyme = Enzyme(name=name, acronym=acronym, isoenzyme=isoenzyme, ec_number=ec_number)
            db.session.add(enzyme)
        db.session.commit()


        model_list = [('E. coli - iteration 1', 'E. coli', 'MG16555'),
                      ('E. coli - iteration 2', 'E. coli', 'MG16555')]

        for name, organism_name, strain in model_list:
            model = Model(name=name, organism_name=organism_name, strain=strain)
            db.session.add(model)
        db.session.commit()


        reference_type_list = ['Article', 'Thesis', 'Online database', 'Book']

        for type in reference_type_list:
            reference_type = ReferenceType(type=type)
            db.session.add(reference_type)
        db.session.commit()


        reference = Reference(title='eQuilibrator', type_type='Online database')
        db.session.add(reference)
        db.session.commit()



    def test_add_first_reaction(self):

        reaction_name = 'phosphofructokinase'
        reaction_acronym = 'PFK'
        reaction_grasp_id = 'PFK1'
        reaction_string = '1 pep_c + 1.5 adp_c <-> pyr_c + 2.0 atp_m'
        metanetx_id = ''
        bigg_id = ''
        kegg_id = ''

        compartment_name = '1'
        model_name = '1'
        isoenzyme_acronyms = 'PFK1'
        mechanism = '1'
        mechanism_references = 'https://doi.org/10.1093/bioinformatics/bty942'
        mechanism_evidence_level = '1'
        subs_binding_order = 'adp_c, pep_c'
        prod_release_order = 'atp_m, pyr_c'
        std_gibbs_energy = 2.1
        std_gibbs_energy_std = 0.2
        std_gibbs_energy_ph = 7
        std_gibbs_energy_ionic_strength = 0.2
        std_gibbs_energy_references = 'equilibrator'


        response = self.client.post('/add_reaction', data=dict(
                                    name=reaction_name,
                                    acronym=reaction_acronym,
                                    grasp_id=reaction_grasp_id,
                                    reaction_string=reaction_string,
                                    bigg_id=bigg_id,
                                    kegg_id=kegg_id,
                                    metanetx_id=metanetx_id,
                                    compartment_name=compartment_name,
                                    model_name=model_name,
                                    isoenzyme_acronyms=isoenzyme_acronyms,
                                    mechanism=mechanism,
                                    mechanism_references=mechanism_references,
                                    mechanism_evidence_level=mechanism_evidence_level,
                                    subs_binding_order=subs_binding_order,
                                    prod_release_order=prod_release_order,
                                    std_gibbs_energy=std_gibbs_energy,
                                    std_gibbs_energy_std=std_gibbs_energy_std,
                                    std_gibbs_energy_ph=std_gibbs_energy_ph,
                                    std_gibbs_energy_ionic_strength=std_gibbs_energy_ionic_strength,
                                    std_gibbs_energy_references=std_gibbs_energy_references), follow_redirects=True)




        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See reactions - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your reaction is now live!' in response.data)


        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(GibbsEnergy.query.count(), 1)
        self.assertEqual(EnzymeReactionOrganism.query.count(), 1)
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Reference.query.count(), 2)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

        self.assertEqual(Reaction.query.count(), 1)
        self.assertEqual(Reaction.query.first().name, reaction_name)
        self.assertEqual(Reaction.query.first().compartment_name, Compartment.query.first().name)

        self.assertEqual(EnzymeReactionOrganism.query.first().grasp_id, reaction_grasp_id)
        self.assertEqual(EnzymeReactionOrganism.query.first().subs_binding_order, subs_binding_order)
        self.assertEqual(EnzymeReactionOrganism.query.first().prod_release_order, prod_release_order)
        self.assertEqual(EnzymeReactionOrganism.query.first().included_in_model, True)
        self.assertEqual(EnzymeReactionOrganism.query.first().reaction.name, reaction_name)
        self.assertEqual(EnzymeReactionOrganism.query.first().enzyme.isoenzyme, isoenzyme_acronyms)
        self.assertEqual(EnzymeReactionOrganism.query.first().model, Model.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.first().mech_evidence, EvidenceLevel.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.first().mechanism, Mechanism.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.first().gibbs_energy, GibbsEnergy.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.first().gibbs_energy.standard_dg, std_gibbs_energy)
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].mechanism_references[0].doi, mechanism_references)

        self.assertEqual(GibbsEnergy.query.first().standard_dg, std_gibbs_energy)
        self.assertEqual(GibbsEnergy.query.first().standard_dg_std, std_gibbs_energy_std)
        self.assertEqual(GibbsEnergy.query.first().ph, std_gibbs_energy_ph)
        self.assertEqual(GibbsEnergy.query.first().ionic_strength, std_gibbs_energy_ionic_strength)
        self.assertEqual(GibbsEnergy.query.first().references[0].title, 'eQuilibrator')

        self.assertEqual(Reference.query.all()[0].title, 'eQuilibrator')
        self.assertEqual(Reference.query.all()[0].type_type, 'Online database')
        self.assertEqual(Reference.query.all()[1].doi, mechanism_references)

        self.assertEqual(Metabolite.query.count(), 4)
        self.assertEqual(Metabolite.query.all()[0].bigg_id, 'pep')
        self.assertEqual(Metabolite.query.all()[0].grasp_id, 'pep')
        self.assertEqual(Metabolite.query.all()[0].compartment_acronym, 'c')
        self.assertEqual(Metabolite.query.all()[1].bigg_id, 'adp')
        self.assertEqual(Metabolite.query.all()[1].grasp_id, 'adp')
        self.assertEqual(Metabolite.query.all()[1].compartment_acronym, 'c')
        self.assertEqual(Metabolite.query.all()[2].bigg_id, 'pyr')
        self.assertEqual(Metabolite.query.all()[2].grasp_id, 'pyr')
        self.assertEqual(Metabolite.query.all()[2].compartment_acronym, 'c')
        self.assertEqual(Metabolite.query.all()[3].bigg_id, 'atp')
        self.assertEqual(Metabolite.query.all()[3].grasp_id, 'atp')
        self.assertEqual(Metabolite.query.all()[3].compartment_acronym, 'm')

        self.assertEqual(ReactionMetabolite.query.count(), 4)
        self.assertEqual(ReactionMetabolite.query.all()[0].metabolite.bigg_id, 'pep')
        self.assertEqual(ReactionMetabolite.query.all()[0].stoich_coef, -1)
        self.assertEqual(ReactionMetabolite.query.all()[0].reaction.acronym, reaction_acronym)
        self.assertEqual(ReactionMetabolite.query.all()[1].metabolite.bigg_id, 'adp')
        self.assertEqual(ReactionMetabolite.query.all()[1].stoich_coef, -1.5)
        self.assertEqual(ReactionMetabolite.query.all()[1].reaction.acronym, reaction_acronym)
        self.assertEqual(ReactionMetabolite.query.all()[2].metabolite.bigg_id, 'pyr')
        self.assertEqual(ReactionMetabolite.query.all()[2].stoich_coef, 1)
        self.assertEqual(ReactionMetabolite.query.all()[2].reaction.acronym, reaction_acronym)
        self.assertEqual(ReactionMetabolite.query.all()[3].metabolite.bigg_id, 'atp')
        self.assertEqual(ReactionMetabolite.query.all()[3].stoich_coef, 2)
        self.assertEqual(ReactionMetabolite.query.all()[3].reaction.acronym, reaction_acronym)



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

        _add_metabolites_to_reaction(reaction, reaction_string)
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
