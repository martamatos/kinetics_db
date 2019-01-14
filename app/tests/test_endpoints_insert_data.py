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
        gene_names = 'b001 b003'
        uniprot_ids = 'PC3W1, P34D'
        pdb_structure_ids = '3H8A, 1E9I'
        strain = 'WT'

        gene_name_list = parse_input_list(gene_names)
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
            gene_names=gene_names,
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
        self.assertEqual(Gene().query.all()[0].name, gene_name_list[0])
        self.assertEqual(Gene().query.all()[1].name, gene_name_list[1])
        self.assertEqual(Gene().query.all()[0].enzyme_gene_organisms.count(), 1)
        self.assertEqual(Gene().query.all()[1].enzyme_gene_organisms.count(), 1)

        self.assertEqual(EnzymeOrganism().query.count(), 2)
        self.assertEqual(EnzymeOrganism().query.all()[0].enzyme.name, enzyme_name)
        self.assertEqual(EnzymeOrganism().query.all()[1].enzyme.name, enzyme_name)
        self.assertEqual(EnzymeOrganism().query.all()[0].organism.name, organism_name)
        self.assertEqual(EnzymeOrganism().query.all()[1].organism.name, organism_name)
        self.assertEqual(EnzymeOrganism().query.all()[0].uniprot_id, uniprot_id_list[0])
        self.assertEqual(EnzymeOrganism().query.all()[1].uniprot_id, uniprot_id_list[1])
        self.assertEqual(EnzymeOrganism().query.all()[0].n_active_sites, number_of_active_sites)
        self.assertEqual(EnzymeOrganism().query.all()[1].n_active_sites, number_of_active_sites)

        self.assertEqual(EnzymeGeneOrganism().query.all()[0].gene.name, gene_name_list[0])
        self.assertEqual(EnzymeGeneOrganism().query.all()[0].enzyme.isoenzyme, isoenzyme)
        self.assertEqual(EnzymeGeneOrganism().query.all()[0].organism.name, organism_name)
        self.assertEqual(EnzymeGeneOrganism().query.all()[1].gene.name, gene_name_list[1])
        self.assertEqual(EnzymeGeneOrganism().query.all()[1].enzyme.isoenzyme, isoenzyme)
        self.assertEqual(EnzymeGeneOrganism().query.all()[1].organism.name, organism_name)

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
        gene_names = ''
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
            gene_names=gene_names,
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
        gene_names = ''
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
            gene_names=gene_names,
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
        gene_names = ''
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
            gene_names=gene_names,
            uniprot_id_list=uniprot_ids,
            pdb_structure_ids=pdb_structure_ids,
            strain=strain), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    Add enzyme - Kinetics DB \n</title>' in response.data)
        self.assertTrue(
            b'If you specify the number of active sites you must also specify the organism name.' in response.data)

        self.assertEqual(Enzyme().query.count(), 0)
        self.assertEqual(Organism().query.count(), 0)
        self.assertEqual(EnzymeOrganism().query.count(), 0)
        self.assertEqual(EnzymeStructure().query.count(), 0)

    def test_add_enzyme_gene_names_without_organism(self):
        enzyme_name = 'Phosphofructokinase'
        enzyme_acronym = 'PFK'
        isoenzyme = 'PFK1'
        ec_number = '1.2.1.31'

        number_of_active_sites = ''
        gene_names = 'b001'
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
            gene_names=gene_names,
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
        gene_names = ''
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
            gene_names=gene_names,
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
        gene_names = ''
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
            gene_names=gene_names,
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
        gene_names = ''
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
            gene_names=gene_names,
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
        gene_names = ''
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
            gene_names=gene_names,
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
        gene_names = ''
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
            gene_names=gene_names,
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
        gene_names = ''
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
            gene_names=gene_names,
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

        populate_db('enzyme_inhibition', self.client)

        self.enzyme = '1'
        self.reaction = '1'
        self.organism = '1'
        self.models = '1'
        self.inhibitor_met = 'adp'
        self.affected_met = 'atp'
        self.inhibition_type = 'Competitive'
        self.inhibition_constant = 1.3 * 10 ** -4

        self.evidence_level = '1'
        self.references = 'https://doi.org/10.1093/bioinformatics/bty942, https://doi.org/10.1093/bioinformatics/bty943'
        self.comments = ''
        self.reference_list = parse_input_list(self.references)

        self.grasp_id = 'PFK1'
        self.subs_binding_order = 'adp_c, pep_c'
        self.prod_release_order = 'pyr_c, atp_c'

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_add_first_inhibition(self):
        response = self.client.post('/add_enzyme_inhibition', data=dict(
            enzyme=self.enzyme,
            reaction=self.reaction,
            organism=self.organism,
            models=self.models,
            inhibitor_met=self.inhibitor_met,
            affected_met=self.affected_met,
            inhibition_type=self.inhibition_type,
            inhibition_constant=self.inhibition_constant,
            inhibition_evidence_level=self.evidence_level,
            references=self.references,
            comments=self.comments), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See enzyme inhibitor - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your enzyme inhibition is now live!' in response.data)

        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(GibbsEnergy.query.count(), 1)
        self.assertEqual(EnzymeReactionOrganism.query.count(), 2)
        self.assertEqual(EnzymeReactionInhibition.query.count(), 1)
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Reference.query.count(), 3)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

        self.assertEqual(EnzymeReactionOrganism.query.first().grasp_id, self.grasp_id)
        self.assertEqual(EnzymeReactionOrganism.query.first().subs_binding_order, self.subs_binding_order)
        self.assertEqual(EnzymeReactionOrganism.query.first().prod_release_order, self.prod_release_order)

        self.assertEqual(EnzymeReactionOrganism.query.first().reaction, Reaction.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.first().enzyme, Enzyme.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.first().models.count(), 2)

        self.assertEqual(EnzymeReactionOrganism.query.first().mech_evidence, EvidenceLevel.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.first().mechanism, Mechanism.query.first())

        self.assertEqual(Reference.query.all()[0].title, 'eQuilibrator')
        self.assertEqual(Reference.query.all()[0].type.type, 'Online database')
        self.assertEqual(Reference.query.all()[1].doi, self.reference_list[0])
        self.assertEqual(Reference.query.all()[2].doi, self.reference_list[1])

        self.assertEqual(Metabolite.query.count(), 4)

        self.assertEqual(ReactionMetabolite.query.count(), 4)

        self.assertEqual(EnzymeReactionInhibition.query.count(), 1)
        self.assertEqual(EnzymeReactionInhibition.query.first().inhibitor_met,
                         Metabolite.query.filter_by(bigg_id=self.inhibitor_met).first())
        self.assertEqual(EnzymeReactionInhibition.query.first().affected_met,
                         Metabolite.query.filter_by(bigg_id=self.affected_met).first())
        self.assertEqual(EnzymeReactionInhibition.query.first().inhibition_constant, self.inhibition_constant)
        self.assertEqual(EnzymeReactionInhibition.query.first().evidence, EvidenceLevel.query.first())
        self.assertEqual(EnzymeReactionInhibition.query.first().comments, self.comments)
        self.assertEqual(EnzymeReactionInhibition.query.first().references[0].doi, self.reference_list[0])
        self.assertEqual(EnzymeReactionInhibition.query.first().references[1].doi, self.reference_list[1])

        self.assertEqual(EnzymeReactionInhibition.query.first().models.count(), 1)
        self.assertEqual(EnzymeReactionInhibition.query.first().models[0], Model.query.first())

        self.assertEqual(Model.query.first().enzyme_reaction_inhibitions.count(), 1)
        self.assertEqual(Model.query.first().enzyme_reaction_inhibitions[0].id,
                         EnzymeReactionInhibition.query.first().id)
        self.assertEqual(Model.query.first().enzyme_reaction_organisms.count(), 2)

    def test_add_inhibition_two_models(self):
        self.models = ['1', '2']

        response = self.client.post('/add_enzyme_inhibition', data=dict(
            enzyme=self.enzyme,
            reaction=self.reaction,
            organism=self.organism,
            models=self.models,
            inhibitor_met=self.inhibitor_met,
            affected_met=self.affected_met,
            inhibition_type=self.inhibition_type,
            inhibition_constant=self.inhibition_constant,
            inhibition_evidence_level=self.evidence_level,
            references=self.references,
            comments=self.comments), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See enzyme inhibitor - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your enzyme inhibition is now live!' in response.data)

        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(GibbsEnergy.query.count(), 1)
        self.assertEqual(EnzymeReactionOrganism.query.count(), 2)
        self.assertEqual(EnzymeReactionInhibition.query.count(), 1)
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Reference.query.count(), 3)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

        self.assertEqual(EnzymeReactionOrganism.query.first().grasp_id, self.grasp_id)
        self.assertEqual(EnzymeReactionOrganism.query.first().subs_binding_order, self.subs_binding_order)
        self.assertEqual(EnzymeReactionOrganism.query.first().prod_release_order, self.prod_release_order)

        self.assertEqual(EnzymeReactionOrganism.query.first().reaction, Reaction.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.first().enzyme, Enzyme.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.first().models.count(), 2)

        self.assertEqual(EnzymeReactionOrganism.query.first().mech_evidence, EvidenceLevel.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.first().mechanism, Mechanism.query.first())

        self.assertEqual(Reference.query.all()[0].title, 'eQuilibrator')
        self.assertEqual(Reference.query.all()[0].type.type, 'Online database')
        self.assertEqual(Reference.query.all()[1].doi, self.reference_list[0])
        self.assertEqual(Reference.query.all()[2].doi, self.reference_list[1])

        self.assertEqual(Metabolite.query.count(), 4)

        self.assertEqual(ReactionMetabolite.query.count(), 4)

        self.assertEqual(EnzymeReactionInhibition.query.count(), 1)
        self.assertEqual(EnzymeReactionInhibition.query.first().inhibitor_met,
                         Metabolite.query.filter_by(bigg_id=self.inhibitor_met).first())
        self.assertEqual(EnzymeReactionInhibition.query.first().affected_met,
                         Metabolite.query.filter_by(bigg_id=self.affected_met).first())
        self.assertEqual(EnzymeReactionInhibition.query.first().inhibition_constant, self.inhibition_constant)
        self.assertEqual(EnzymeReactionInhibition.query.first().evidence, EvidenceLevel.query.first())
        self.assertEqual(EnzymeReactionInhibition.query.first().comments, self.comments)
        self.assertEqual(EnzymeReactionInhibition.query.first().references[0].doi, self.reference_list[0])
        self.assertEqual(EnzymeReactionInhibition.query.first().references[1].doi, self.reference_list[1])

        self.assertEqual(EnzymeReactionInhibition.query.first().models.count(), 2)
        self.assertEqual(EnzymeReactionInhibition.query.first().models[0], Model.query.first())
        self.assertEqual(EnzymeReactionInhibition.query.first().models[1], Model.query.all()[1])

        self.assertEqual(Model.query.first().enzyme_reaction_inhibitions.count(), 1)
        self.assertEqual(Model.query.all()[0].enzyme_reaction_inhibitions[0].id,
                         EnzymeReactionInhibition.query.first().id)
        self.assertEqual(Model.query.all()[1].enzyme_reaction_inhibitions[0].id,
                         EnzymeReactionInhibition.query.first().id)
        self.assertEqual(Model.query.first().enzyme_reaction_organisms.count(), 2)


class TestAddEnzymeActivation(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        populate_db('enzyme_activation', self.client)

        self.enzyme = '1'
        self.reaction = '1'
        self.organism = '1'
        self.models = '1'
        self.activator_met = 'adp'
        self.activation_constant = 1.3 * 10 ** -4

        self.evidence_level = '1'
        self.references = 'https://doi.org/10.1093/bioinformatics/bty942, https://doi.org/10.1093/bioinformatics/bty943'
        self.comments = ''
        self.reference_list = parse_input_list(self.references)

        self.grasp_id = 'PFK1'
        self.subs_binding_order = 'adp_c, pep_c'
        self.prod_release_order = 'pyr_c, atp_c'

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_add_first_activation(self):
        response = self.client.post('/add_enzyme_activation', data=dict(
            enzyme=self.enzyme,
            reaction=self.reaction,
            organism=self.organism,
            models=self.models,
            activator_met=self.activator_met,
            activation_constant=self.activation_constant,
            activation_evidence_level=self.evidence_level,
            references=self.references,
            comments=self.comments), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See enzyme activator - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your enzyme activation is now live!' in response.data)

        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(GibbsEnergy.query.count(), 1)
        self.assertEqual(EnzymeReactionOrganism.query.count(), 2)
        self.assertEqual(EnzymeReactionActivation.query.count(), 1)
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Reference.query.count(), 3)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

        self.assertEqual(EnzymeReactionOrganism.query.first().grasp_id, self.grasp_id)
        self.assertEqual(EnzymeReactionOrganism.query.first().subs_binding_order, self.subs_binding_order)
        self.assertEqual(EnzymeReactionOrganism.query.first().prod_release_order, self.prod_release_order)

        self.assertEqual(EnzymeReactionOrganism.query.first().reaction, Reaction.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.first().enzyme, Enzyme.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.first().models.count(), 2)

        self.assertEqual(EnzymeReactionOrganism.query.first().mech_evidence, EvidenceLevel.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.first().mechanism, Mechanism.query.first())

        self.assertEqual(Reference.query.all()[0].title, 'eQuilibrator')
        self.assertEqual(Reference.query.all()[0].type.type, 'Online database')
        self.assertEqual(Reference.query.all()[1].doi, self.reference_list[0])
        self.assertEqual(Reference.query.all()[2].doi, self.reference_list[1])

        self.assertEqual(Metabolite.query.count(), 4)

        self.assertEqual(ReactionMetabolite.query.count(), 4)

        self.assertEqual(EnzymeReactionActivation.query.count(), 1)
        self.assertEqual(EnzymeReactionActivation.query.first().activator_met,
                         Metabolite.query.filter_by(bigg_id=self.activator_met).first())
        self.assertEqual(EnzymeReactionActivation.query.first().activation_constant, self.activation_constant)
        self.assertEqual(EnzymeReactionActivation.query.first().evidence, EvidenceLevel.query.first())
        self.assertEqual(EnzymeReactionActivation.query.first().comments, self.comments)
        self.assertEqual(EnzymeReactionActivation.query.first().references[0].doi, self.reference_list[0])
        self.assertEqual(EnzymeReactionActivation.query.first().references[1].doi, self.reference_list[1])

        self.assertEqual(EnzymeReactionActivation.query.first().models.count(), 1)
        self.assertEqual(EnzymeReactionActivation.query.first().models[0], Model.query.first())

        self.assertEqual(Model.query.first().enzyme_reaction_activations.count(), 1)
        self.assertEqual(Model.query.first().enzyme_reaction_activations[0].id,
                         EnzymeReactionActivation.query.first().id)
        self.assertEqual(Model.query.first().enzyme_reaction_organisms.count(), 2)

    def test_add_activation_two_models(self):
        self.models = ['1', '2']

        response = self.client.post('/add_enzyme_activation', data=dict(
            enzyme=self.enzyme,
            reaction=self.reaction,
            organism=self.organism,
            models=self.models,
            activator_met=self.activator_met,
            activation_constant=self.activation_constant,
            activation_evidence_level=self.evidence_level,
            references=self.references,
            comments=self.comments), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See enzyme activator - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your enzyme activation is now live!' in response.data)

        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(GibbsEnergy.query.count(), 1)
        self.assertEqual(EnzymeReactionOrganism.query.count(), 2)
        self.assertEqual(EnzymeReactionActivation.query.count(), 1)
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Reference.query.count(), 3)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

        self.assertEqual(EnzymeReactionOrganism.query.first().grasp_id, self.grasp_id)
        self.assertEqual(EnzymeReactionOrganism.query.first().subs_binding_order, self.subs_binding_order)
        self.assertEqual(EnzymeReactionOrganism.query.first().prod_release_order, self.prod_release_order)

        self.assertEqual(EnzymeReactionOrganism.query.first().reaction, Reaction.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.first().enzyme, Enzyme.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.first().models.count(), 2)

        self.assertEqual(EnzymeReactionOrganism.query.first().mech_evidence, EvidenceLevel.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.first().mechanism, Mechanism.query.first())

        self.assertEqual(Reference.query.all()[0].title, 'eQuilibrator')
        self.assertEqual(Reference.query.all()[0].type.type, 'Online database')
        self.assertEqual(Reference.query.all()[1].doi, self.reference_list[0])
        self.assertEqual(Reference.query.all()[2].doi, self.reference_list[1])

        self.assertEqual(Metabolite.query.count(), 4)

        self.assertEqual(ReactionMetabolite.query.count(), 4)

        self.assertEqual(EnzymeReactionActivation.query.count(), 1)
        self.assertEqual(EnzymeReactionActivation.query.first().activator_met,
                         Metabolite.query.filter_by(bigg_id=self.activator_met).first())
        self.assertEqual(EnzymeReactionActivation.query.first().activation_constant, self.activation_constant)
        self.assertEqual(EnzymeReactionActivation.query.first().evidence, EvidenceLevel.query.first())
        self.assertEqual(EnzymeReactionActivation.query.first().comments, self.comments)
        self.assertEqual(EnzymeReactionActivation.query.first().references[0].doi, self.reference_list[0])
        self.assertEqual(EnzymeReactionActivation.query.first().references[1].doi, self.reference_list[1])

        self.assertEqual(EnzymeReactionActivation.query.first().models.count(), 2)
        self.assertEqual(EnzymeReactionActivation.query.first().models[0], Model.query.first())
        self.assertEqual(EnzymeReactionActivation.query.first().models[1], Model.query.all()[1])

        self.assertEqual(Model.query.first().enzyme_reaction_activations.count(), 1)
        self.assertEqual(Model.query.all()[0].enzyme_reaction_activations[0].id,
                         EnzymeReactionActivation.query.first().id)
        self.assertEqual(Model.query.all()[1].enzyme_reaction_activations[0].id,
                         EnzymeReactionActivation.query.first().id)
        self.assertEqual(Model.query.first().enzyme_reaction_organisms.count(), 2)


class TestAddEnzymeEffector(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        populate_db('enzyme_effector', self.client)

        self.enzyme = '1'
        self.reaction = '1'
        self.organism = '1'
        self.models = '1'
        self.effector_met = 'adp'
        self.effector_type = 'Inhibiting'

        self.evidence_level = '1'
        self.references = 'https://doi.org/10.1093/bioinformatics/bty942, https://doi.org/10.1093/bioinformatics/bty943'
        self.comments = ''
        self.reference_list = parse_input_list(self.references)

        self.grasp_id = 'PFK1'
        self.subs_binding_order = 'adp_c, pep_c'
        self.prod_release_order = 'pyr_c, atp_c'

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_add_first_effector(self):
        response = self.client.post('/add_enzyme_effector', data=dict(
            enzyme=self.enzyme,
            reaction=self.reaction,
            organism=self.organism,
            models=self.models,
            effector_met=self.effector_met,
            effector_type=self.effector_type,
            effector_evidence_level=self.evidence_level,
            references=self.references,
            comments=self.comments), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See enzyme effector - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your enzyme effector is now live!' in response.data)

        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(GibbsEnergy.query.count(), 1)
        self.assertEqual(EnzymeReactionOrganism.query.count(), 2)
        self.assertEqual(EnzymeReactionEffector.query.count(), 1)
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Reference.query.count(), 3)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

        self.assertEqual(EnzymeReactionOrganism.query.first().grasp_id, self.grasp_id)
        self.assertEqual(EnzymeReactionOrganism.query.first().subs_binding_order, self.subs_binding_order)
        self.assertEqual(EnzymeReactionOrganism.query.first().prod_release_order, self.prod_release_order)

        self.assertEqual(EnzymeReactionOrganism.query.first().reaction, Reaction.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.first().enzyme, Enzyme.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.first().models.count(), 2)

        self.assertEqual(EnzymeReactionOrganism.query.first().mech_evidence, EvidenceLevel.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.first().mechanism, Mechanism.query.first())

        self.assertEqual(Reference.query.all()[0].title, 'eQuilibrator')
        self.assertEqual(Reference.query.all()[0].type.type, 'Online database')
        self.assertEqual(Reference.query.all()[1].doi, self.reference_list[0])
        self.assertEqual(Reference.query.all()[2].doi, self.reference_list[1])

        self.assertEqual(Metabolite.query.count(), 4)

        self.assertEqual(ReactionMetabolite.query.count(), 4)

        self.assertEqual(EnzymeReactionEffector.query.count(), 1)
        self.assertEqual(EnzymeReactionEffector.query.first().effector_met,
                         Metabolite.query.filter_by(bigg_id=self.effector_met).first())
        self.assertEqual(EnzymeReactionEffector.query.first().effector_type, self.effector_type)
        self.assertEqual(EnzymeReactionEffector.query.first().evidence, EvidenceLevel.query.first())
        self.assertEqual(EnzymeReactionEffector.query.first().comments, self.comments)
        self.assertEqual(EnzymeReactionEffector.query.first().references[0].doi, self.reference_list[0])
        self.assertEqual(EnzymeReactionEffector.query.first().references[1].doi, self.reference_list[1])

        self.assertEqual(EnzymeReactionEffector.query.first().models.count(), 1)
        self.assertEqual(EnzymeReactionEffector.query.first().models[0], Model.query.first())

        self.assertEqual(Model.query.first().enzyme_reaction_effectors.count(), 1)
        self.assertEqual(Model.query.first().enzyme_reaction_effectors[0].id, EnzymeReactionEffector.query.first().id)
        self.assertEqual(Model.query.first().enzyme_reaction_organisms.count(), 2)

    def test_add_effector_two_models(self):
        self.models = ['1', '2']

        response = self.client.post('/add_enzyme_effector', data=dict(
            enzyme=self.enzyme,
            reaction=self.reaction,
            organism=self.organism,
            models=self.models,
            effector_met=self.effector_met,
            effector_type=self.effector_type,
            effector_evidence_level=self.evidence_level,
            references=self.references,
            comments=self.comments), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See enzyme effector - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your enzyme effector is now live!' in response.data)

        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(GibbsEnergy.query.count(), 1)
        self.assertEqual(EnzymeReactionOrganism.query.count(), 2)
        self.assertEqual(EnzymeReactionEffector.query.count(), 1)
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Reference.query.count(), 3)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

        self.assertEqual(EnzymeReactionOrganism.query.first().grasp_id, self.grasp_id)
        self.assertEqual(EnzymeReactionOrganism.query.first().subs_binding_order, self.subs_binding_order)
        self.assertEqual(EnzymeReactionOrganism.query.first().prod_release_order, self.prod_release_order)

        self.assertEqual(EnzymeReactionOrganism.query.first().reaction, Reaction.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.first().enzyme, Enzyme.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.first().models.count(), 2)

        self.assertEqual(EnzymeReactionOrganism.query.first().mech_evidence, EvidenceLevel.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.first().mechanism, Mechanism.query.first())

        self.assertEqual(Reference.query.all()[0].title, 'eQuilibrator')
        self.assertEqual(Reference.query.all()[0].type.type, 'Online database')
        self.assertEqual(Reference.query.all()[1].doi, self.reference_list[0])
        self.assertEqual(Reference.query.all()[2].doi, self.reference_list[1])

        self.assertEqual(Metabolite.query.count(), 4)

        self.assertEqual(ReactionMetabolite.query.count(), 4)

        self.assertEqual(EnzymeReactionEffector.query.count(), 1)
        self.assertEqual(EnzymeReactionEffector.query.first().effector_met,
                         Metabolite.query.filter_by(bigg_id=self.effector_met).first())
        self.assertEqual(EnzymeReactionEffector.query.first().effector_type, self.effector_type)
        self.assertEqual(EnzymeReactionEffector.query.first().evidence, EvidenceLevel.query.first())
        self.assertEqual(EnzymeReactionEffector.query.first().comments, self.comments)
        self.assertEqual(EnzymeReactionEffector.query.first().references[0].doi, self.reference_list[0])
        self.assertEqual(EnzymeReactionEffector.query.first().references[1].doi, self.reference_list[1])

        self.assertEqual(EnzymeReactionEffector.query.first().models.count(), 2)
        self.assertEqual(EnzymeReactionEffector.query.first().models[0], Model.query.first())
        self.assertEqual(EnzymeReactionEffector.query.first().models[1], Model.query.all()[1])

        self.assertEqual(Model.query.first().enzyme_reaction_effectors.count(), 1)
        self.assertEqual(Model.query.all()[0].enzyme_reaction_effectors[0].id, EnzymeReactionEffector.query.first().id)
        self.assertEqual(Model.query.all()[1].enzyme_reaction_effectors[0].id, EnzymeReactionEffector.query.first().id)
        self.assertEqual(Model.query.first().enzyme_reaction_organisms.count(), 2)


class TestAddEnzymeMiscInfo(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        populate_db('enzyme_misc_info', self.client)

        self.enzyme = '1'
        self.reaction = '1'
        self.organism = '1'
        self.models = '1'
        self.topic = 'allostery'
        self.description = 'looks like this met is an allosteric inhibitor for that enzyme'

        self.evidence_level = '1'
        self.references = 'https://doi.org/10.1093/bioinformatics/bty942, https://doi.org/10.1093/bioinformatics/bty943'
        self.comments = ''
        self.reference_list = parse_input_list(self.references)

        self.grasp_id = 'PFK1'
        self.subs_binding_order = 'adp_c, pep_c'
        self.prod_release_order = 'pyr_c, atp_c'

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_add_first_misc_info(self):
        response = self.client.post('/add_enzyme_misc_info', data=dict(
            enzyme=self.enzyme,
            reaction=self.reaction,
            organism=self.organism,
            models=self.models,
            topic=self.topic,
            description=self.description,
            evidence_level=self.evidence_level,
            references=self.references,
            comments=self.comments), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See enzyme misc info - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your enzyme misc info is now live!' in response.data)

        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(GibbsEnergy.query.count(), 1)
        self.assertEqual(EnzymeReactionOrganism.query.count(), 2)
        self.assertEqual(EnzymeReactionMiscInfo.query.count(), 1)
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Reference.query.count(), 3)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

        self.assertEqual(EnzymeReactionOrganism.query.first().grasp_id, self.grasp_id)
        self.assertEqual(EnzymeReactionOrganism.query.first().subs_binding_order, self.subs_binding_order)
        self.assertEqual(EnzymeReactionOrganism.query.first().prod_release_order, self.prod_release_order)

        self.assertEqual(EnzymeReactionOrganism.query.first().reaction, Reaction.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.first().enzyme, Enzyme.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.first().models.count(), 2)

        self.assertEqual(EnzymeReactionOrganism.query.first().mech_evidence, EvidenceLevel.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.first().mechanism, Mechanism.query.first())

        self.assertEqual(Reference.query.all()[0].title, 'eQuilibrator')
        self.assertEqual(Reference.query.all()[0].type.type, 'Online database')
        self.assertEqual(Reference.query.all()[1].doi, self.reference_list[0])
        self.assertEqual(Reference.query.all()[2].doi, self.reference_list[1])

        self.assertEqual(Metabolite.query.count(), 4)

        self.assertEqual(ReactionMetabolite.query.count(), 4)

        self.assertEqual(EnzymeReactionMiscInfo.query.count(), 1)
        self.assertEqual(EnzymeReactionMiscInfo.query.first().topic, self.topic)
        self.assertEqual(EnzymeReactionMiscInfo.query.first().description, self.description)
        self.assertEqual(EnzymeReactionMiscInfo.query.first().evidence, EvidenceLevel.query.first())
        self.assertEqual(EnzymeReactionMiscInfo.query.first().comments, self.comments)
        self.assertEqual(EnzymeReactionMiscInfo.query.first().references[0].doi, self.reference_list[0])
        self.assertEqual(EnzymeReactionMiscInfo.query.first().references[1].doi, self.reference_list[1])

        self.assertEqual(EnzymeReactionMiscInfo.query.first().models.count(), 1)
        self.assertEqual(EnzymeReactionMiscInfo.query.first().models[0], Model.query.first())

        self.assertEqual(Model.query.first().enzyme_reaction_misc_infos.count(), 1)
        self.assertEqual(Model.query.first().enzyme_reaction_misc_infos[0].id, EnzymeReactionMiscInfo.query.first().id)
        self.assertEqual(Model.query.first().enzyme_reaction_organisms.count(), 2)

    def test_add_misc_info_two_models(self):
        self.models = ['1', '2']

        response = self.client.post('/add_enzyme_misc_info', data=dict(
            enzyme=self.enzyme,
            reaction=self.reaction,
            organism=self.organism,
            models=self.models,
            topic=self.topic,
            description=self.description,
            evidence_level=self.evidence_level,
            references=self.references,
            comments=self.comments), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See enzyme misc info - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your enzyme misc info is now live!' in response.data)

        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(GibbsEnergy.query.count(), 1)
        self.assertEqual(EnzymeReactionOrganism.query.count(), 2)
        self.assertEqual(EnzymeReactionMiscInfo.query.count(), 1)
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Reference.query.count(), 3)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

        self.assertEqual(EnzymeReactionOrganism.query.first().grasp_id, self.grasp_id)
        self.assertEqual(EnzymeReactionOrganism.query.first().subs_binding_order, self.subs_binding_order)
        self.assertEqual(EnzymeReactionOrganism.query.first().prod_release_order, self.prod_release_order)

        self.assertEqual(EnzymeReactionOrganism.query.first().reaction, Reaction.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.first().enzyme, Enzyme.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.first().models.count(), 2)

        self.assertEqual(EnzymeReactionOrganism.query.first().mech_evidence, EvidenceLevel.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.first().mechanism, Mechanism.query.first())

        self.assertEqual(Reference.query.all()[0].title, 'eQuilibrator')
        self.assertEqual(Reference.query.all()[0].type.type, 'Online database')
        self.assertEqual(Reference.query.all()[1].doi, self.reference_list[0])
        self.assertEqual(Reference.query.all()[2].doi, self.reference_list[1])

        self.assertEqual(Metabolite.query.count(), 4)

        self.assertEqual(ReactionMetabolite.query.count(), 4)

        self.assertEqual(EnzymeReactionMiscInfo.query.count(), 1)
        self.assertEqual(EnzymeReactionMiscInfo.query.first().topic, self.topic)
        self.assertEqual(EnzymeReactionMiscInfo.query.first().description, self.description)
        self.assertEqual(EnzymeReactionMiscInfo.query.first().evidence, EvidenceLevel.query.first())
        self.assertEqual(EnzymeReactionMiscInfo.query.first().comments, self.comments)
        self.assertEqual(EnzymeReactionMiscInfo.query.first().references[0].doi, self.reference_list[0])
        self.assertEqual(EnzymeReactionMiscInfo.query.first().references[1].doi, self.reference_list[1])

        self.assertEqual(EnzymeReactionMiscInfo.query.first().models.count(), 2)
        self.assertEqual(EnzymeReactionMiscInfo.query.first().models[0], Model.query.first())
        self.assertEqual(EnzymeReactionMiscInfo.query.first().models[1], Model.query.all()[1])

        self.assertEqual(Model.query.first().enzyme_reaction_misc_infos.count(), 1)
        self.assertEqual(Model.query.all()[0].enzyme_reaction_misc_infos[0].id, EnzymeReactionMiscInfo.query.first().id)
        self.assertEqual(Model.query.all()[1].enzyme_reaction_misc_infos[0].id, EnzymeReactionMiscInfo.query.first().id)
        self.assertEqual(Model.query.first().enzyme_reaction_organisms.count(), 2)


"""
class TestAddGene(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        self.name = 'gene_bla'
        self.name = 'b0001'

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
                                    bigg_id=organism_name), follow_redirects=True)


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
"""


class TestAddMetabolite(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        populate_db('enzyme_inhibition', self.client)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_add_first_metabolite(self):
        grasp_id = '2pg'
        name = '2-phosphoglycerate'
        bigg_id = '2pg'
        metanetx_id = 'MNXM23'

        compartments = ['1', '2']
        chebi_ids = 'CHEBI:86354, CHEBI:8685'
        inchis = 'InChI=1S/C3H4O3/c1-2(4)3(5)6/h4H,1H2,(H,5,6), InChI=1S/C3H4O4/c1-2(4)3(5)6/h4H,1H2,(H,5,6)'

        self.assertEqual(Metabolite.query.count(), 4)

        response = self.client.post('/add_metabolite', data=dict(
            grasp_id=grasp_id,
            name=name,
            bigg_id=bigg_id,
            metanetx_id=metanetx_id,
            compartments=compartments,
            chebi_ids=chebi_ids,
            inchis=inchis), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See metabolite - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your metabolite is now live!' in response.data)

        self.assertEqual(Metabolite.query.count(), 5)
        metabolite = Metabolite.query.filter_by(grasp_id=grasp_id).first()
        self.assertEqual(metabolite.grasp_id, grasp_id)
        self.assertEqual(metabolite.name, name)
        self.assertEqual(metabolite.bigg_id, bigg_id)
        self.assertEqual(metabolite.metanetx_id, metanetx_id)
        self.assertEqual(metabolite.compartments.count(), 2)
        self.assertEqual(metabolite.chebis.count(), 2)
        self.assertEqual(metabolite.chebis[0].chebi_id, 'CHEBI:86354')
        self.assertEqual(metabolite.chebis[1].chebi_id, 'CHEBI:8685')
        self.assertEqual(metabolite.chebis[0].inchi, 'InChI=1S/C3H4O3/c1-2(4)3(5)6/h4H,1H2,(H,5,6)')
        self.assertEqual(metabolite.chebis[1].inchi, 'InChI=1S/C3H4O4/c1-2(4)3(5)6/h4H,1H2,(H,5,6)')

    def test_add_existing_metabolite_grasp_id(self):
        grasp_id = 'pep'
        name = '2-phosphoglycerate'
        bigg_id = '2pg'
        metanetx_id = 'MNXM23'

        compartments = ['1', '2']
        chebi_ids = 'CHEBI:86354, CHEBI:8685'
        inchis = 'InChI=1S/C3H4O3/c1-2(4)3(5)6/h4H,1H2,(H,5,6), InChI=1S/C3H4O4/c1-2(4)3(5)6/h4H,1H2,(H,5,6)'

        self.assertEqual(Metabolite.query.count(), 4)

        response = self.client.post('/add_metabolite', data=dict(
            grasp_id=grasp_id,
            name=name,
            bigg_id=bigg_id,
            metanetx_id=metanetx_id,
            compartments=compartments,
            chebi_ids=chebi_ids,
            inchis=inchis), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    Add metabolite - Kinetics DB \n</title>' in response.data)
        self.assertTrue(
            b'The metabolite grasp id you specified already exists. Please choose a different one.' in response.data)

        self.assertEqual(Metabolite.query.count(), 4)

    def test_add_existing_metabolite_bigg_id(self):
        grasp_id = '2pg'
        name = '2-phosphoglycerate'
        bigg_id = 'pep'
        metanetx_id = 'MNXM23'

        compartments = ['1', '2']
        chebi_ids = 'CHEBI:86354, CHEBI:8685'
        inchis = 'InChI=1S/C3H4O3/c1-2(4)3(5)6/h4H,1H2,(H,5,6), InChI=1S/C3H4O4/c1-2(4)3(5)6/h4H,1H2,(H,5,6)'

        self.assertEqual(Metabolite.query.count(), 4)

        response = self.client.post('/add_metabolite', data=dict(
            grasp_id=grasp_id,
            name=name,
            bigg_id=bigg_id,
            metanetx_id=metanetx_id,
            compartments=compartments,
            chebi_ids=chebi_ids,
            inchis=inchis), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    Add metabolite - Kinetics DB \n</title>' in response.data)
        self.assertTrue(
            b'The metabolite bigg id you specified already exists. Please choose a different one.' in response.data)

        self.assertEqual(Metabolite.query.count(), 4)

    def test_add_metabolite_diff_chebi_inchi_size(self):
        grasp_id = '2pg'
        name = '2-phosphoglycerate'
        bigg_id = 'pep'
        metanetx_id = 'MNXM23'

        compartments = ['1', '2']
        chebi_ids = 'CHEBI:86354, CHEBI:8685'
        inchis = 'InChI=1S/C3H4O3/c1-2(4)3(5)6/h4H,1H2,(H,5,6)'

        self.assertEqual(Metabolite.query.count(), 4)

        response = self.client.post('/add_metabolite', data=dict(
            grasp_id=grasp_id,
            name=name,
            bigg_id=bigg_id,
            metanetx_id=metanetx_id,
            compartments=compartments,
            chebi_ids=chebi_ids,
            inchis=inchis), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    Add metabolite - Kinetics DB \n</title>' in response.data)
        self.assertTrue(
            b'The list of ChEBI ids and InChIs should have the same length. Also make sure you separated each value with a comma' in response.data)

        self.assertEqual(Metabolite.query.count(), 4)

    def test_add_metabolite_diff_chebi_inchi_size2(self):
        grasp_id = '2pg'
        name = '2-phosphoglycerate'
        bigg_id = 'pep'
        metanetx_id = 'MNXM23'

        compartments = ['1', '2']
        chebi_ids = 'CHEBI:86354'
        inchis = 'InChI=1S/C3H4O3/c1-2(4)3(5)6/h4H,1H2,(H,5,6), InChI=1S/C3H4O4/c1-2(4)3(5)6/h4H,1H2,(H,5,6)'

        self.assertEqual(Metabolite.query.count(), 4)

        response = self.client.post('/add_metabolite', data=dict(
            grasp_id=grasp_id,
            name=name,
            bigg_id=bigg_id,
            metanetx_id=metanetx_id,
            compartments=compartments,
            chebi_ids=chebi_ids,
            inchis=inchis), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    Add metabolite - Kinetics DB \n</title>' in response.data)
        self.assertTrue(
            b'The list of ChEBI ids and InChIs should have the same length. Also make sure you separated each value with a comma' in response.data)

        self.assertEqual(Metabolite.query.count(), 4)


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
        model_name = 'E. coli - iteration x'
        organism_name = 'E. coli2'
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

    # TODO updated
    def test_add_model_for_existing_organism(self):
        populate_db('model', self.client)

        model_name = 'E. coli - iteration x'
        organism_name = 'E. coli'
        strain = 'MG16555'
        enz_rxn_orgs = EnzymeReactionOrganism.query.all()[0]
        comments = 'Just testing...'

        self.assertEqual(Organism().query.first().name, organism_name)
        self.assertEqual(Organism().query.first().models.count(), 2)

        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

        self.assertEqual(EnzymeReactionOrganism.query.count(), 2)

        response = self.client.post('/add_model', data=dict(
            name=model_name,
            organism_name=organism_name,
            strain=strain,
            comments=comments), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See models - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your model is now live!' in response.data)

        self.assertEqual(Model().query.all()[2].name, model_name)
        self.assertEqual(Model().query.all()[2].strain, strain)
        self.assertEqual(Model().query.all()[2].enzyme_reaction_organisms.count(), 0)
        self.assertEqual(Model().query.all()[2].comments, comments)
        self.assertEqual(Organism().query.all()[0].models.count(), 3)
        self.assertEqual(Organism().query.all()[0].models[2].name, model_name)

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


class TestAddModelAssumption(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        populate_db('model_assumption', self.client)

        self.model = '1'
        self.assumption = 'allostery'
        self.description = 'looks like this met is an allosteric inhibitor for that enzyme'
        self.included_in_model = "True"

        self.evidence_level = '1'
        self.references = 'https://doi.org/10.1093/bioinformatics/bty942, https://doi.org/10.1093/bioinformatics/bty943'
        self.comments = ''
        self.reference_list = parse_input_list(self.references)

        self.grasp_id = 'PFK1'
        self.subs_binding_order = 'adp_c, pep_c'
        self.prod_release_order = 'pyr_c, atp_c'

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_add_first_model_assumption(self):
        response = self.client.post('/add_model_assumption', data=dict(
            model=self.model,
            assumption=self.assumption,
            description=self.description,
            evidence_level=self.evidence_level,
            included_in_model=self.included_in_model,
            references=self.references,
            comments=self.comments), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See models - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your model assumption is now live!' in response.data)

        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(GibbsEnergy.query.count(), 1)
        self.assertEqual(EnzymeReactionOrganism.query.count(), 2)
        self.assertEqual(ModelAssumptions.query.count(), 1)
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Reference.query.count(), 3)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

        self.assertEqual(EnzymeReactionOrganism.query.first().grasp_id, self.grasp_id)
        self.assertEqual(EnzymeReactionOrganism.query.first().subs_binding_order, self.subs_binding_order)
        self.assertEqual(EnzymeReactionOrganism.query.first().prod_release_order, self.prod_release_order)

        self.assertEqual(EnzymeReactionOrganism.query.first().reaction, Reaction.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.first().enzyme, Enzyme.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.first().models.count(), 2)

        self.assertEqual(EnzymeReactionOrganism.query.first().mech_evidence, EvidenceLevel.query.first())
        self.assertEqual(EnzymeReactionOrganism.query.first().mechanism, Mechanism.query.first())

        self.assertEqual(Reference.query.all()[0].title, 'eQuilibrator')
        self.assertEqual(Reference.query.all()[0].type.type, 'Online database')
        self.assertEqual(Reference.query.all()[1].doi, self.reference_list[0])
        self.assertEqual(Reference.query.all()[2].doi, self.reference_list[1])

        self.assertEqual(Metabolite.query.count(), 4)

        self.assertEqual(ReactionMetabolite.query.count(), 4)

        self.assertEqual(ModelAssumptions.query.count(), 1)
        self.assertEqual(ModelAssumptions.query.first().assumption, self.assumption)
        self.assertEqual(ModelAssumptions.query.first().description, self.description)
        self.assertEqual(ModelAssumptions.query.first().included_in_model, True)
        self.assertEqual(ModelAssumptions.query.first().evidence, EvidenceLevel.query.first())
        self.assertEqual(ModelAssumptions.query.first().comments, self.comments)
        self.assertEqual(ModelAssumptions.query.first().references[0].doi, self.reference_list[0])
        self.assertEqual(ModelAssumptions.query.first().references[1].doi, self.reference_list[1])

        self.assertEqual(Model.query.first().model_assumptions.count(), 1)
        self.assertEqual(Model.query.first().model_assumptions[0].id, ModelAssumptions.query.first().id)
        self.assertEqual(Model.query.first().enzyme_reaction_organisms.count(), 2)


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

        populate_db('reaction', self.client)

        self.reaction_name = 'phosphofructokinase'
        self.reaction_acronym = 'PFK'
        self.reaction_grasp_id = 'PFK1'
        self.reaction_string = '1 pep_c + 1.5 adp_c <-> pyr_c + 2.0 atp_m'
        self.metanetx_id = ''
        self.name = ''
        self.kegg_id = ''

        self.compartment = '1'
        self.organism = '1'
        self.models = ['1', '2']
        self.enzymes = ['1', '2']
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
            bigg_id=self.name,
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
            bigg_id=self.name,
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

    def test_add_reaction_two_models(self):
        true_isoenzyme_acronym1 = 'PFK1'
        true_isoenzyme_acronym2 = 'PFK2'
        true_gibbs_energy_ref = 'eQuilibrator'

        response = self.client.post('/add_reaction', data=dict(
            name=self.reaction_name,
            acronym=self.reaction_acronym,
            grasp_id=self.reaction_grasp_id,
            reaction_string=self.reaction_string,
            bigg_id=self.name,
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
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].mechanism_references[0].doi,
                         self.mechanism_references.split(', ')[0])
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].mechanism_references[1].doi,
                         self.mechanism_references.split(', ')[1])
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].mechanism_references[0].doi,
                         self.mechanism_references.split(', ')[0])
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].mechanism_references[1].doi,
                         self.mechanism_references.split(', ')[1])

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
        self.assertEqual(Reference.query.all()[0].type.type, 'Online database')
        self.assertEqual(Reference.query.all()[1].doi, self.mechanism_references.split(', ')[0])
        self.assertEqual(Reference.query.all()[2].doi, self.mechanism_references.split(', ')[1])

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
            bigg_id=self.name,
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
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].mechanism_references[0].doi,
                         true_mechanism_references[0])
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].mechanism_references[1].doi,
                         true_mechanism_references[1])
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].mechanism_references.count(), 2)
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].mechanism_references[0].doi,
                         true_mechanism_references[0])
        self.assertEqual(EnzymeReactionOrganism.query.all()[1].mechanism_references[1].doi,
                         true_mechanism_references[1])

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
        self.assertEqual(Reference.query.all()[0].type.type, 'Online database')
        self.assertEqual(Reference.query.all()[1].doi, true_mechanism_references[0])
        self.assertEqual(Reference.query.all()[2].doi, true_mechanism_references[1])

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
            bigg_id=self.name,
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

    def test_add_reaction_met_format(self):
        self.reaction_string = '1 pep_c + 1.5 adpc <-> pyr_c + 2.0 atp_m'
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
            bigg_id=self.name,
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
        self.assertTrue(b'Please specify the metabolite' in response.data)

        self.assertEqual(Reaction.query.count(), 0)
        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(GibbsEnergy.query.count(), 0)
        self.assertEqual(GibbsEnergyReactionModel.query.count(), 0)
        self.assertEqual(EnzymeReactionOrganism.query.count(), 0)
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Reference.query.count(), 1)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

    def test_add_reaction_met_compartment(self):
        self.reaction_string = '1 pep_c + 1.5 adp_x <-> pyr_c + 2.0 atp_m'
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
            bigg_id=self.name,
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
        self.assertTrue(b'The specified compartment bigg_acronym' in response.data)

        self.assertEqual(Reaction.query.count(), 0)
        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(GibbsEnergy.query.count(), 0)
        self.assertEqual(GibbsEnergyReactionModel.query.count(), 0)
        self.assertEqual(EnzymeReactionOrganism.query.count(), 0)
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Reference.query.count(), 1)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

    def test_add_reaction_met_subs_binding(self):
        self.subs_binding_order = 'adx_c, pep_c'

        response = self.client.post('/add_reaction', data=dict(
            name=self.reaction_name,
            acronym=self.reaction_acronym,
            grasp_id=self.reaction_grasp_id,
            reaction_string=self.reaction_string,
            bigg_id=self.name,
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
        self.assertTrue(b'does not match any metabolite in' in response.data)

        self.assertEqual(Reaction.query.count(), 0)
        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(GibbsEnergy.query.count(), 0)
        self.assertEqual(GibbsEnergyReactionModel.query.count(), 0)
        self.assertEqual(EnzymeReactionOrganism.query.count(), 0)
        self.assertEqual(Mechanism.query.count(), 2)
        self.assertEqual(Reference.query.count(), 1)
        self.assertEqual(Model.query.count(), 2)
        self.assertEqual(Organism.query.count(), 2)

    def test_add_reaction_met_prod_release(self):
        self.prod_release_order = 'atp_m, pyr2_c'

        response = self.client.post('/add_reaction', data=dict(
            name=self.reaction_name,
            acronym=self.reaction_acronym,
            grasp_id=self.reaction_grasp_id,
            reaction_string=self.reaction_string,
            bigg_id=self.name,
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
        self.assertTrue(b'does not match any metabolite in' in response.data)

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
            bigg_id=self.name,
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
        self.assertTrue(
            b'If you add a reaction mechanism, you need to specify the catalyzing isoenzyme(s).' in response.data)

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
            bigg_id=self.name,
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
        self.assertTrue(
            b'You cannot specify evidence level for the mechanism without specifying a mechanism.' in response.data)

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
            bigg_id=self.name,
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
        self.assertTrue(
            b'If you add substrate binding order without specifying the catalyzing isoenzyme(s)' in response.data)

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
            bigg_id=self.name,
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
        self.assertTrue(
            b'If you add product release order without specifying the catalyzing isoenzyme(s)' in response.data)

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
            bigg_id=self.name,
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
        self.assertTrue(
            b'Gibbs energies cannot be added to reactions alone, a model must be associated as well. Please add model name.' in response.data)

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
            bigg_id=self.name,
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
            bigg_id=self.name,
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
            bigg_id=self.name,
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
            bigg_id=self.name,
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
            bigg_id=self.name,
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
            bigg_id=self.name,
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
        self.assertEqual(Reference.query.all()[0].type.type, 'Online database')

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
            bigg_id=self.name,
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
        self.assertEqual(Reference.query.all()[0].type.type, 'Online database')

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
            bigg_id=self.name,
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
        self.assertEqual(Reference.query.all()[0].type.type, 'Online database')
        self.assertEqual(Reference.query.all()[1].doi, self.mechanism_references.split(', ')[0])
        self.assertEqual(Reference.query.all()[2].doi, self.mechanism_references.split(', ')[1])

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
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].mechanism_references[0].doi,
                         self.mechanism_references.split(', ')[0])
        self.assertEqual(EnzymeReactionOrganism.query.all()[0].mechanism_references[1].doi,
                         self.mechanism_references.split(', ')[1])

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
            bigg_id=self.name,
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
        self.assertEqual(Reference.query.all()[0].type.type, 'Online database')

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


if __name__ == '__main__':
    unittest.main(verbosity=2)
