from datetime import datetime, timedelta
import unittest
from app import create_app, db
from app.main.forms import ModelForm
from app.main.routes import add_model
from app.models import User, Post, Compartment, Enzyme, EnzymeOrganism, EnzymeReactionModel, EnzymeStructure, \
    EvidenceLevel, Gene, GibbsEnergy, Mechanism, Metabolite, Model, Organism, Reaction, ReactionMetabolite, Reference, \
    ReferenceType
from config import Config
from app.main.routes import add_metabolites_to_reaction, _add_enzyme_organism, _add_enzyme_structures
from app.utils.parsers import parse_input_list
import re


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    LOGIN_DISABLED = True
    WTF_CSRF_ENABLED = False


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
        self.assertEqual(EnzymeReactionModel.query.count(), 1)
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Reference.query.count(), 2)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

        self.assertEqual(Reaction.query.count(), 1)
        self.assertEqual(Reaction.query.first().name, reaction_name)
        self.assertEqual(Reaction.query.first().compartment_name, Compartment.query.first().name)

        self.assertEqual(EnzymeReactionModel.query.first().grasp_id, reaction_grasp_id)
        self.assertEqual(EnzymeReactionModel.query.first().subs_binding_order, subs_binding_order)
        self.assertEqual(EnzymeReactionModel.query.first().prod_release_order, prod_release_order)
        self.assertEqual(EnzymeReactionModel.query.first().included_in_model, True)
        self.assertEqual(EnzymeReactionModel.query.first().reaction.name, reaction_name)
        self.assertEqual(EnzymeReactionModel.query.first().enzyme.isoenzyme, isoenzyme_acronyms)
        self.assertEqual(EnzymeReactionModel.query.first().model, Model.query.first())
        self.assertEqual(EnzymeReactionModel.query.first().mech_evidence, EvidenceLevel.query.first())
        self.assertEqual(EnzymeReactionModel.query.first().mechanism, Mechanism.query.first())
        self.assertEqual(EnzymeReactionModel.query.first().gibbs_energy, GibbsEnergy.query.first())
        self.assertEqual(EnzymeReactionModel.query.first().gibbs_energy.standard_dg, std_gibbs_energy)
        self.assertEqual(EnzymeReactionModel.query.all()[0].mechanism_references[0].doi, mechanism_references)

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

    def test_add_reaction_two_isoenzymes(self):

        reaction_name = 'phosphofructokinase'
        reaction_acronym = 'PFK'
        reaction_grasp_id = 'PFK1'
        reaction_string = '1 pep_c + 1.5 adp_c <-> pyr_c + 2.0 atp_m'
        metanetx_id = ''
        bigg_id = ''
        kegg_id = ''

        compartment_name = '1'
        model_name = '1'
        isoenzyme_acronyms = 'PFK1, PFK2'
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

        isoenzyme_list = parse_input_list(isoenzyme_acronyms)


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

        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Reference.query.count(), 2)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

        self.assertEqual(Reaction.query.count(), 1)
        self.assertEqual(Reaction.query.first().name, reaction_name)
        self.assertEqual(Reaction.query.first().compartment_name, Compartment.query.first().name)

        self.assertEqual(EnzymeReactionModel.query.count(), 2)
        self.assertEqual(EnzymeReactionModel.query.all()[0].grasp_id, reaction_grasp_id)
        self.assertEqual(EnzymeReactionModel.query.all()[1].grasp_id, reaction_grasp_id)
        self.assertEqual(EnzymeReactionModel.query.all()[0].subs_binding_order, subs_binding_order)
        self.assertEqual(EnzymeReactionModel.query.all()[1].subs_binding_order, subs_binding_order)
        self.assertEqual(EnzymeReactionModel.query.all()[0].prod_release_order, prod_release_order)
        self.assertEqual(EnzymeReactionModel.query.all()[1].prod_release_order, prod_release_order)
        self.assertEqual(EnzymeReactionModel.query.all()[0].included_in_model, True)
        self.assertEqual(EnzymeReactionModel.query.all()[1].included_in_model, True)
        self.assertEqual(EnzymeReactionModel.query.all()[0].reaction.name, reaction_name)
        self.assertEqual(EnzymeReactionModel.query.all()[1].reaction.name, reaction_name)
        self.assertEqual(EnzymeReactionModel.query.all()[0].enzyme.isoenzyme, isoenzyme_list[0])
        self.assertEqual(EnzymeReactionModel.query.all()[1].enzyme.isoenzyme, isoenzyme_list[1])
        self.assertEqual(EnzymeReactionModel.query.all()[0].model, Model.query.first())
        self.assertEqual(EnzymeReactionModel.query.all()[1].model, Model.query.first())
        self.assertEqual(EnzymeReactionModel.query.all()[0].mech_evidence, EvidenceLevel.query.first())
        self.assertEqual(EnzymeReactionModel.query.all()[1].mech_evidence, EvidenceLevel.query.first())
        self.assertEqual(EnzymeReactionModel.query.all()[0].mechanism, Mechanism.query.first())
        self.assertEqual(EnzymeReactionModel.query.all()[1].mechanism, Mechanism.query.first())
        self.assertEqual(EnzymeReactionModel.query.all()[0].gibbs_energy, GibbsEnergy.query.first())
        self.assertEqual(EnzymeReactionModel.query.all()[1].gibbs_energy, GibbsEnergy.query.first())
        self.assertEqual(EnzymeReactionModel.query.all()[0].gibbs_energy.standard_dg, std_gibbs_energy)
        self.assertEqual(EnzymeReactionModel.query.all()[1].gibbs_energy.standard_dg, std_gibbs_energy)
        self.assertEqual(EnzymeReactionModel.query.all()[0].mechanism_references.count(), 1)
        self.assertEqual(EnzymeReactionModel.query.all()[0].mechanism_references[0].doi, mechanism_references)
        self.assertEqual(EnzymeReactionModel.query.all()[1].mechanism_references[0].doi,mechanism_references)

        self.assertEqual(GibbsEnergy.query.count(), 1)
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

    def test_add_reaction_two_mechanism_references(self):

        reaction_name = 'phosphofructokinase'
        reaction_acronym = 'PFK'
        reaction_grasp_id = 'PFK1'
        reaction_string = '1 pep_c + 1.5 adp_c <-> pyr_c + 2.0 atp_m'
        metanetx_id = ''
        bigg_id = ''
        kegg_id = ''

        compartment_name = '1'
        model_name = '1'
        isoenzyme_acronyms = 'PFK1, PFK2'
        mechanism = '1'
        mechanism_references = 'https://doi.org/10.1093/bioinformatics/bty942, https://doi.org/10.1093/bioinformatics/bty943'
        mechanism_evidence_level = '1'
        subs_binding_order = 'adp_c, pep_c'
        prod_release_order = 'atp_m, pyr_c'
        std_gibbs_energy = 2.1
        std_gibbs_energy_std = 0.2
        std_gibbs_energy_ph = 7
        std_gibbs_energy_ionic_strength = 0.2
        std_gibbs_energy_references = 'equilibrator'

        isoenzyme_list = parse_input_list(isoenzyme_acronyms)
        mechanism_reference_list = parse_input_list(mechanism_references)


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
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

        self.assertEqual(Reaction.query.count(), 1)
        self.assertEqual(Reaction.query.first().name, reaction_name)
        self.assertEqual(Reaction.query.first().compartment_name, Compartment.query.first().name)

        self.assertEqual(EnzymeReactionModel.query.count(), 2)
        self.assertEqual(EnzymeReactionModel.query.all()[0].grasp_id, reaction_grasp_id)
        self.assertEqual(EnzymeReactionModel.query.all()[1].grasp_id, reaction_grasp_id)
        self.assertEqual(EnzymeReactionModel.query.all()[0].subs_binding_order, subs_binding_order)
        self.assertEqual(EnzymeReactionModel.query.all()[1].subs_binding_order, subs_binding_order)
        self.assertEqual(EnzymeReactionModel.query.all()[0].prod_release_order, prod_release_order)
        self.assertEqual(EnzymeReactionModel.query.all()[1].prod_release_order, prod_release_order)
        self.assertEqual(EnzymeReactionModel.query.all()[0].included_in_model, True)
        self.assertEqual(EnzymeReactionModel.query.all()[1].included_in_model, True)
        self.assertEqual(EnzymeReactionModel.query.all()[0].reaction.name, reaction_name)
        self.assertEqual(EnzymeReactionModel.query.all()[1].reaction.name, reaction_name)
        self.assertEqual(EnzymeReactionModel.query.all()[0].enzyme.isoenzyme, isoenzyme_list[0])
        self.assertEqual(EnzymeReactionModel.query.all()[1].enzyme.isoenzyme, isoenzyme_list[1])
        self.assertEqual(EnzymeReactionModel.query.all()[0].model, Model.query.first())
        self.assertEqual(EnzymeReactionModel.query.all()[1].model, Model.query.first())
        self.assertEqual(EnzymeReactionModel.query.all()[0].mech_evidence, EvidenceLevel.query.first())
        self.assertEqual(EnzymeReactionModel.query.all()[1].mech_evidence, EvidenceLevel.query.first())
        self.assertEqual(EnzymeReactionModel.query.all()[0].mechanism, Mechanism.query.first())
        self.assertEqual(EnzymeReactionModel.query.all()[1].mechanism, Mechanism.query.first())
        self.assertEqual(EnzymeReactionModel.query.all()[0].gibbs_energy, GibbsEnergy.query.first())
        self.assertEqual(EnzymeReactionModel.query.all()[1].gibbs_energy, GibbsEnergy.query.first())
        self.assertEqual(EnzymeReactionModel.query.all()[0].gibbs_energy.standard_dg, std_gibbs_energy)
        self.assertEqual(EnzymeReactionModel.query.all()[1].gibbs_energy.standard_dg, std_gibbs_energy)
        self.assertEqual(EnzymeReactionModel.query.all()[0].mechanism_references.count(), 2)
        self.assertEqual(EnzymeReactionModel.query.all()[0].mechanism_references[0].doi, mechanism_reference_list[0])
        self.assertEqual(EnzymeReactionModel.query.all()[0].mechanism_references[1].doi, mechanism_reference_list[1])
        self.assertEqual(EnzymeReactionModel.query.all()[1].mechanism_references.count(), 2)
        self.assertEqual(EnzymeReactionModel.query.all()[1].mechanism_references[0].doi, mechanism_reference_list[0])
        self.assertEqual(EnzymeReactionModel.query.all()[1].mechanism_references[1].doi, mechanism_reference_list[1])

        self.assertEqual(GibbsEnergy.query.count(), 1)
        self.assertEqual(GibbsEnergy.query.first().standard_dg, std_gibbs_energy)
        self.assertEqual(GibbsEnergy.query.first().standard_dg_std, std_gibbs_energy_std)
        self.assertEqual(GibbsEnergy.query.first().ph, std_gibbs_energy_ph)
        self.assertEqual(GibbsEnergy.query.first().ionic_strength, std_gibbs_energy_ionic_strength)
        self.assertEqual(GibbsEnergy.query.first().references[0].title, 'eQuilibrator')

        self.assertEqual(Reference.query.count(), 3)
        self.assertEqual(Reference.query.all()[0].title, 'eQuilibrator')
        self.assertEqual(Reference.query.all()[0].type_type, 'Online database')
        self.assertEqual(Reference.query.all()[1].doi, mechanism_reference_list[0])
        self.assertEqual(Reference.query.all()[2].doi, mechanism_reference_list[1])



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

    def test_add_reaction_no_isoenzyme(self):

        reaction_name = 'phosphofructokinase'
        reaction_acronym = 'PFK'
        reaction_grasp_id = 'PFK1'
        reaction_string = '1 pep_c + 1.5 adp_c <-> pyr_c + 2.0 atp_m'
        metanetx_id = ''
        bigg_id = ''
        kegg_id = ''

        compartment_name = '1'
        model_name = '1'
        isoenzyme_acronyms = 'PFK3'
        mechanism = '1'
        mechanism_references = 'https://doi.org/10.1093/bioinformatics/bty942, https://doi.org/10.1093/bioinformatics/bty943'
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
        self.assertTrue(b'<title>\n    Add reaction - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'is not part of the database' in response.data)

        self.assertEqual(Reaction.query.count(), 0)
        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(GibbsEnergy.query.count(), 0)
        self.assertEqual(EnzymeReactionModel.query.count(), 0)
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Reference.query.count(), 1)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

    def test_add_reaction_mechanism_and_no_isoenzyme(self):

        reaction_name = 'phosphofructokinase'
        reaction_acronym = 'PFK'
        reaction_grasp_id = 'PFK1'
        reaction_string = '1 pep_c + 1.5 adp_c <-> pyr_c + 2.0 atp_m'
        metanetx_id = ''
        bigg_id = ''
        kegg_id = ''

        compartment_name = '1'
        model_name = '1'
        isoenzyme_acronyms = ''
        mechanism = '1'
        mechanism_references = 'https://doi.org/10.1093/bioinformatics/bty942, https://doi.org/10.1093/bioinformatics/bty943'
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
        self.assertTrue(b'<title>\n    Add reaction - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'If you add a reaction mechanism, you need to specify the catalyzing isoenzyme(s).' in response.data)

        self.assertEqual(Reaction.query.count(), 0)
        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(GibbsEnergy.query.count(), 0)
        self.assertEqual(EnzymeReactionModel.query.count(), 0)
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Reference.query.count(), 1)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

    def test_add_reaction_mechanism_evidence_level(self):

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
        mechanism = ''
        mechanism_references = 'https://doi.org/10.1093/bioinformatics/bty942, https://doi.org/10.1093/bioinformatics/bty943'
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
        self.assertTrue(b'<title>\n    Add reaction - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'You cannot specify evidence level for the mechanism without specifying a mechanism.' in response.data)

        self.assertEqual(Reaction.query.count(), 0)
        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(GibbsEnergy.query.count(), 0)
        self.assertEqual(EnzymeReactionModel.query.count(), 0)
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Reference.query.count(), 1)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

    def test_add_reaction_subs_binding_order(self):

        reaction_name = 'phosphofructokinase'
        reaction_acronym = 'PFK'
        reaction_grasp_id = 'PFK1'
        reaction_string = '1 pep_c + 1.5 adp_c <-> pyr_c + 2.0 atp_m'
        metanetx_id = ''
        bigg_id = ''
        kegg_id = ''

        compartment_name = '1'
        model_name = ''
        isoenzyme_acronyms = ''
        mechanism = '1'
        mechanism_references = 'mechanism_doi'
        mechanism_evidence_level = '1'
        subs_binding_order = 'pep_c, 1.5 adp_c'
        prod_release_order = 'pyr_c, atp_m'
        std_gibbs_energy = ''
        std_gibbs_energy_std = ''
        std_gibbs_energy_ph = ''
        std_gibbs_energy_ionic_strength = ''
        std_gibbs_energy_references = ''


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
        self.assertTrue(b'<title>\n    Add reaction - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'If you add substrate binding order without specifying the catalyzing isoenzyme(s)' in response.data)

        self.assertEqual(Reaction.query.count(), 0)
        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(GibbsEnergy.query.count(), 0)
        self.assertEqual(EnzymeReactionModel.query.count(), 0)
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Reference.query.count(), 1)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

    def test_add_reaction_prod_release_order(self):

        reaction_name = 'phosphofructokinase'
        reaction_acronym = 'PFK'
        reaction_grasp_id = 'PFK1'
        reaction_string = '1 pep_c + 1.5 adp_c <-> pyr_c + 2.0 atp_m'
        metanetx_id = ''
        bigg_id = ''
        kegg_id = ''

        compartment_name = '1'
        model_name = ''
        isoenzyme_acronyms = ''
        mechanism = '1'
        mechanism_references = 'mechanism_doi'
        mechanism_evidence_level = '1'
        subs_binding_order = ''
        prod_release_order = 'pyr_c, atp_m'
        std_gibbs_energy = ''
        std_gibbs_energy_std = ''
        std_gibbs_energy_ph = ''
        std_gibbs_energy_ionic_strength = ''
        std_gibbs_energy_references = ''


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
        self.assertTrue(b'<title>\n    Add reaction - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'If you add product release order without specifying the catalyzing isoenzyme(s)' in response.data)

        self.assertEqual(Reaction.query.count(), 0)
        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(GibbsEnergy.query.count(), 0)
        self.assertEqual(EnzymeReactionModel.query.count(), 0)
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Reference.query.count(), 1)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

    def test_add_reaction_std_gibbs_energy_std(self):

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
        mechanism_references = 'https://doi.org/10.1093/bioinformatics/bty942, https://doi.org/10.1093/bioinformatics/bty943'
        mechanism_evidence_level = '1'
        subs_binding_order = 'adp_c, pep_c'
        prod_release_order = 'atp_m, pyr_c'
        std_gibbs_energy = ''
        std_gibbs_energy_std = 0.2
        std_gibbs_energy_ph = ''
        std_gibbs_energy_ionic_strength = ''
        std_gibbs_energy_references = ''


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
        self.assertTrue(b'<title>\n    Add reaction - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Please specify the standard Gibbs energy as well.' in response.data)

        self.assertEqual(Reaction.query.count(), 0)
        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(GibbsEnergy.query.count(), 0)
        self.assertEqual(EnzymeReactionModel.query.count(), 0)
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Reference.query.count(), 1)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

    def test_add_reaction_std_gibbs_energy_std_no_model(self):

        reaction_name = 'phosphofructokinase'
        reaction_acronym = 'PFK'
        reaction_grasp_id = 'PFK1'
        reaction_string = '1 pep_c + 1.5 adp_c <-> pyr_c + 2.0 atp_m'
        metanetx_id = ''
        bigg_id = ''
        kegg_id = ''

        compartment_name = '1'
        model_name = ''
        isoenzyme_acronyms = 'PFK1'
        mechanism = '1'
        mechanism_references = 'https://doi.org/10.1093/bioinformatics/bty942, https://doi.org/10.1093/bioinformatics/bty943'
        mechanism_evidence_level = '1'
        subs_binding_order = 'adp_c, pep_c'
        prod_release_order = 'atp_m, pyr_c'
        std_gibbs_energy = ''
        std_gibbs_energy_std = 0.2
        std_gibbs_energy_ph = ''
        std_gibbs_energy_ionic_strength = ''
        std_gibbs_energy_references = ''


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
        self.assertTrue(b'<title>\n    Add reaction - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Gibbs energies cannot be added to reactions alone, a model must be associated as well. Please add model name.' in response.data)

        self.assertEqual(Reaction.query.count(), 0)
        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(GibbsEnergy.query.count(), 0)
        self.assertEqual(EnzymeReactionModel.query.count(), 0)
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Reference.query.count(), 1)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

    def test_add_reaction_std_gibbs_energy_ph(self):

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
        mechanism_references = 'https://doi.org/10.1093/bioinformatics/bty942, https://doi.org/10.1093/bioinformatics/bty943'
        mechanism_evidence_level = '1'
        subs_binding_order = 'adp_c, pep_c'
        prod_release_order = 'atp_m, pyr_c'
        std_gibbs_energy = ''
        std_gibbs_energy_std = ''
        std_gibbs_energy_ph = 7
        std_gibbs_energy_ionic_strength = ''
        std_gibbs_energy_references = ''


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
        self.assertTrue(b'<title>\n    Add reaction - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Please specify the standard Gibbs energy as well.' in response.data)

        self.assertEqual(Reaction.query.count(), 0)
        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(GibbsEnergy.query.count(), 0)
        self.assertEqual(EnzymeReactionModel.query.count(), 0)
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Reference.query.count(), 1)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

    def test_add_reaction_std_gibbs_energy_is(self):

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
        mechanism_references = 'https://doi.org/10.1093/bioinformatics/bty942, https://doi.org/10.1093/bioinformatics/bty943'
        mechanism_evidence_level = '1'
        subs_binding_order = 'adp_c, pep_c'
        prod_release_order = 'atp_m, pyr_c'
        std_gibbs_energy = ''
        std_gibbs_energy_std = ''
        std_gibbs_energy_ph = ''
        std_gibbs_energy_ionic_strength = 0.2
        std_gibbs_energy_references = ''


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
        self.assertTrue(b'<title>\n    Add reaction - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Please specify the standard Gibbs energy as well.' in response.data)

        self.assertEqual(Reaction.query.count(), 0)
        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(GibbsEnergy.query.count(), 0)
        self.assertEqual(EnzymeReactionModel.query.count(), 0)
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Reference.query.count(), 1)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

    def test_add_reaction_std_gibbs_energy_refs(self):

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
        mechanism_references = 'https://doi.org/10.1093/bioinformatics/bty942, https://doi.org/10.1093/bioinformatics/bty943'
        mechanism_evidence_level = '1'
        subs_binding_order = 'adp_c, pep_c'
        prod_release_order = 'atp_m, pyr_c'
        std_gibbs_energy = ''
        std_gibbs_energy_std = ''
        std_gibbs_energy_ph = ''
        std_gibbs_energy_ionic_strength = ''
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
        self.assertTrue(b'<title>\n    Add reaction - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Please specify the standard Gibbs energy as well.' in response.data)

        self.assertEqual(Reaction.query.count(), 0)
        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(GibbsEnergy.query.count(), 0)
        self.assertEqual(EnzymeReactionModel.query.count(), 0)
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Reference.query.count(), 1)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

    def test_add_reaction_std_gibbs_energy_refs_2(self):

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
        mechanism_references = 'https://doi.org/10.1093/bioinformatics/bty942, https://doi.org/10.1093/bioinformatics/bty943'
        mechanism_evidence_level = '1'
        subs_binding_order = 'adp_c, pep_c'
        prod_release_order = 'atp_m, pyr_c'
        std_gibbs_energy = 7.1
        std_gibbs_energy_std = ''
        std_gibbs_energy_ph = ''
        std_gibbs_energy_ionic_strength = ''
        std_gibbs_energy_references = ''


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
        self.assertTrue(b'<title>\n    Add reaction - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Please specify the reference for the above standard Gibbs energy' in response.data)

        self.assertEqual(Reaction.query.count(), 0)
        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(GibbsEnergy.query.count(), 0)
        self.assertEqual(EnzymeReactionModel.query.count(), 0)
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Reference.query.count(), 1)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

    def test_add_reaction_only(self):

        reaction_name = 'phosphofructokinase'
        reaction_acronym = 'PFK'
        reaction_grasp_id = 'PFK1'
        reaction_string = '1 pep_c + 1.5 adp_c <-> pyr_c + 2.0 atp_m'
        metanetx_id = ''
        bigg_id = ''
        kegg_id = ''

        compartment_name = ''
        model_name = ''
        isoenzyme_acronyms = ''
        mechanism = ''
        mechanism_references = ''
        mechanism_evidence_level = ''
        subs_binding_order = ''
        prod_release_order = ''
        std_gibbs_energy = ''
        std_gibbs_energy_std = ''
        std_gibbs_energy_ph = ''
        std_gibbs_energy_ionic_strength = ''
        std_gibbs_energy_references = ''


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

        self.assertEqual(Reaction.query.count(), 1)
        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(GibbsEnergy.query.count(), 0)
        self.assertEqual(EnzymeReactionModel.query.count(), 0)
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Reference.query.count(), 1)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

        self.assertEqual(Reaction.query.count(), 1)
        self.assertEqual(Reaction.query.first().name, reaction_name)
        self.assertEqual(Reaction.query.first().compartment_name, '')

        self.assertEqual(Reference.query.count(), 1)
        self.assertEqual(Reference.query.all()[0].title, 'eQuilibrator')
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

    def test_add_reaction_compartment(self):

        reaction_name = 'phosphofructokinase'
        reaction_acronym = 'PFK'
        reaction_grasp_id = 'PFK1'
        reaction_string = '1 pep_c + 1.5 adp_c <-> pyr_c + 2.0 atp_m'
        metanetx_id = ''
        bigg_id = ''
        kegg_id = ''

        compartment_name = '1'
        model_name = ''
        isoenzyme_acronyms = ''
        mechanism = ''
        mechanism_references = ''
        mechanism_evidence_level = ''
        subs_binding_order = ''
        prod_release_order = ''
        std_gibbs_energy = ''
        std_gibbs_energy_std = ''
        std_gibbs_energy_ph = ''
        std_gibbs_energy_ionic_strength = ''
        std_gibbs_energy_references = ''


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

        self.assertEqual(Reaction.query.count(), 1)
        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(GibbsEnergy.query.count(), 0)
        self.assertEqual(EnzymeReactionModel.query.count(), 0)
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Reference.query.count(), 1)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

        self.assertEqual(Reaction.query.count(), 1)
        self.assertEqual(Reaction.query.first().name, reaction_name)
        self.assertEqual(Reaction.query.first().compartment_name, Compartment.query.first().name)

        self.assertEqual(Reference.query.count(), 1)
        self.assertEqual(Reference.query.all()[0].title, 'eQuilibrator')
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

    def test_add_reaction_mechanism(self):

        reaction_name = 'phosphofructokinase'
        reaction_acronym = 'PFK'
        reaction_grasp_id = 'PFK1'
        reaction_string = '1 pep_c + 1.5 adp_c <-> pyr_c + 2.0 atp_m'
        metanetx_id = ''
        bigg_id = ''
        kegg_id = ''

        compartment_name = '1'
        model_name = ''
        isoenzyme_acronyms = 'PFK1'
        mechanism = '1'
        mechanism_references = 'mechanism_fake_ref'
        mechanism_evidence_level = '1'
        subs_binding_order = 'pep_c, adp_c'
        prod_release_order = 'pyr_c, atp_m'
        std_gibbs_energy = ''
        std_gibbs_energy_std = ''
        std_gibbs_energy_ph = ''
        std_gibbs_energy_ionic_strength = ''
        std_gibbs_energy_references = ''


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

        self.assertEqual(Reaction.query.count(), 1)
        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(GibbsEnergy.query.count(), 0)
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

        self.assertEqual(Reaction.query.count(), 1)
        self.assertEqual(Reaction.query.first().name, reaction_name)
        self.assertEqual(Reaction.query.first().compartment_name, Compartment.query.first().name)

        self.assertEqual(Reference.query.count(), 2)
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

        self.assertEqual(EnzymeReactionModel.query.count(), 1)
        self.assertEqual(EnzymeReactionModel.query.all()[0].grasp_id, reaction_grasp_id)
        self.assertEqual(EnzymeReactionModel.query.all()[0].subs_binding_order, subs_binding_order)
        self.assertEqual(EnzymeReactionModel.query.all()[0].prod_release_order, prod_release_order)
        self.assertEqual(EnzymeReactionModel.query.all()[0].included_in_model, False)
        self.assertEqual(EnzymeReactionModel.query.all()[0].reaction.name, reaction_name)
        self.assertEqual(EnzymeReactionModel.query.all()[0].enzyme.isoenzyme, isoenzyme_acronyms)
        self.assertEqual(EnzymeReactionModel.query.all()[0].model, None)
        self.assertEqual(EnzymeReactionModel.query.all()[0].mech_evidence, EvidenceLevel.query.first())
        self.assertEqual(EnzymeReactionModel.query.all()[0].mechanism, Mechanism.query.first())
        self.assertEqual(EnzymeReactionModel.query.all()[0].mechanism_references.count(), 1)
        self.assertEqual(EnzymeReactionModel.query.all()[0].mechanism_references[0].doi, mechanism_references)

    def test_add_reaction_gibbs_energy(self):

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
        mechanism = ''
        mechanism_references = ''
        mechanism_evidence_level = ''
        subs_binding_order = ''
        prod_release_order = ''
        std_gibbs_energy = 7.1
        std_gibbs_energy_std = 0.5
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
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

        self.assertEqual(Reaction.query.count(), 1)
        self.assertEqual(Reaction.query.first().name, reaction_name)
        self.assertEqual(Reaction.query.first().compartment_name, Compartment.query.first().name)

        self.assertEqual(EnzymeReactionModel.query.count(), 1)
        self.assertEqual(EnzymeReactionModel.query.all()[0].grasp_id, reaction_grasp_id)
        self.assertEqual(EnzymeReactionModel.query.all()[0].subs_binding_order, subs_binding_order)
        self.assertEqual(EnzymeReactionModel.query.all()[0].prod_release_order, prod_release_order)
        self.assertEqual(EnzymeReactionModel.query.all()[0].included_in_model, True)
        self.assertEqual(EnzymeReactionModel.query.all()[0].reaction.name, reaction_name)
        self.assertEqual(EnzymeReactionModel.query.all()[0].enzyme.isoenzyme, isoenzyme_acronyms)
        self.assertEqual(EnzymeReactionModel.query.all()[0].model, Model.query.first())
        self.assertEqual(EnzymeReactionModel.query.all()[0].mechanism, None)
        self.assertEqual(EnzymeReactionModel.query.all()[0].gibbs_energy, GibbsEnergy.query.first())
        self.assertEqual(EnzymeReactionModel.query.all()[0].gibbs_energy.standard_dg, std_gibbs_energy)

        self.assertEqual(GibbsEnergy.query.count(), 1)
        self.assertEqual(GibbsEnergy.query.first().standard_dg, std_gibbs_energy)
        self.assertEqual(GibbsEnergy.query.first().standard_dg_std, std_gibbs_energy_std)
        self.assertEqual(GibbsEnergy.query.first().ph, std_gibbs_energy_ph)
        self.assertEqual(GibbsEnergy.query.first().ionic_strength, std_gibbs_energy_ionic_strength)
        self.assertEqual(GibbsEnergy.query.first().references[0].title, 'eQuilibrator')

        self.assertEqual(Reference.query.count(), 1)
        self.assertEqual(Reference.query.all()[0].title, 'eQuilibrator')
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

    def test_add_reaction_gibbs_energy_no_isoenzyme(self):

        reaction_name = 'phosphofructokinase'
        reaction_acronym = 'PFK'
        reaction_grasp_id = 'PFK1'
        reaction_string = '1 pep_c + 1.5 adp_c <-> pyr_c + 2.0 atp_m'
        metanetx_id = ''
        bigg_id = ''
        kegg_id = ''

        compartment_name = '1'
        model_name = '1'
        isoenzyme_acronyms = ''
        mechanism = ''
        mechanism_references = ''
        mechanism_evidence_level = ''
        subs_binding_order = ''
        prod_release_order = ''
        std_gibbs_energy = 7.1
        std_gibbs_energy_std = 0.5
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
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

        self.assertEqual(Reaction.query.count(), 1)
        self.assertEqual(Reaction.query.first().name, reaction_name)
        self.assertEqual(Reaction.query.first().compartment_name, Compartment.query.first().name)

        self.assertEqual(EnzymeReactionModel.query.count(), 1)
        self.assertEqual(EnzymeReactionModel.query.all()[0].grasp_id, reaction_grasp_id)
        self.assertEqual(EnzymeReactionModel.query.all()[0].subs_binding_order, subs_binding_order)
        self.assertEqual(EnzymeReactionModel.query.all()[0].prod_release_order, prod_release_order)
        self.assertEqual(EnzymeReactionModel.query.all()[0].included_in_model, True)
        self.assertEqual(EnzymeReactionModel.query.all()[0].reaction.name, reaction_name)
        self.assertEqual(EnzymeReactionModel.query.all()[0].enzyme, None)
        self.assertEqual(EnzymeReactionModel.query.all()[0].model, Model.query.first())
        self.assertEqual(EnzymeReactionModel.query.all()[0].mechanism, None)
        self.assertEqual(EnzymeReactionModel.query.all()[0].gibbs_energy, GibbsEnergy.query.first())
        self.assertEqual(EnzymeReactionModel.query.all()[0].gibbs_energy.standard_dg, std_gibbs_energy)

        self.assertEqual(GibbsEnergy.query.count(), 1)
        self.assertEqual(GibbsEnergy.query.first().standard_dg, std_gibbs_energy)
        self.assertEqual(GibbsEnergy.query.first().standard_dg_std, std_gibbs_energy_std)
        self.assertEqual(GibbsEnergy.query.first().ph, std_gibbs_energy_ph)
        self.assertEqual(GibbsEnergy.query.first().ionic_strength, std_gibbs_energy_ionic_strength)
        self.assertEqual(GibbsEnergy.query.first().references[0].title, 'eQuilibrator')

        self.assertEqual(Reference.query.count(), 1)
        self.assertEqual(Reference.query.all()[0].title, 'eQuilibrator')
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
