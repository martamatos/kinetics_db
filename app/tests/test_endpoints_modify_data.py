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
    add_compartments, add_evidence_levels, add_organisms, add_references, add_activations, add_effectors, \
    add_inhibitions, \
    add_misc_infos, add_model_assumptions, add_metabolite
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    LOGIN_DISABLED = True
    WTF_CSRF_ENABLED = False


def populate_db(test_case, client=None):
    if test_case == 'organism':
        add_organisms()
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
        add_metabolite(client)


class TestModifyOrganism(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        populate_db('organism', self.client)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_modify_organism(self):
        current_organism_name = 'E. coli'
        new_organism_name = 'CHO'

        organism = Organism.query.filter_by(name=current_organism_name).first()

        response = self.client.post('/modify_organism/' + current_organism_name, data=dict(
            name=new_organism_name), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See organism - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your organism has been modified' in response.data)

        self.assertEqual(organism.name, new_organism_name)

    def test_modify_organism_existing_name(self):
        current_organism_name = 'E. coli'
        new_organism_name = 'S. cerevisiae'

        organism = Organism.query.filter_by(name=current_organism_name).first()

        response = self.client.post('/modify_organism/' + current_organism_name, data=dict(
            name=new_organism_name), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    Modify organism - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'An organism with that name already exists, please use another name' in response.data)

        self.assertEqual(organism.name, current_organism_name)


class TestModifyMetabolite(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        populate_db('metabolite', self.client)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_modify_metabolite_change_nothing(self):
        grasp_id = '2pg'
        name = '2-phosphoglycerate'
        bigg_id = '2pg'
        metanetx_id = 'MNXM23'

        compartments = ['1', '2']
        chebi_ids = 'CHEBI:86354, CHEBI:8685'
        inchis = 'InChI=1S/C3H4O3/c1-2(4)3(5)6/h4H,1H2,(H,5,6), InChI=1S/C3H4O4/c1-2(4)3(5)6/h4H,1H2,(H,5,6)'

        self.assertEqual(Metabolite.query.count(), 7)
        metabolite = Metabolite.query.filter_by(grasp_id=grasp_id).first()

        response = self.client.post('/modify_metabolite/' + grasp_id, data=dict(
            grasp_id=grasp_id,
            name=name,
            bigg_id=bigg_id,
            metanetx_id=metanetx_id,
            compartments=compartments,
            chebi_ids=chebi_ids,
            inchis=inchis), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See metabolite - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your metabolite has been modified' in response.data)

        self.assertEqual(Metabolite.query.count(), 7)
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

    def test_modify_metabolite_change_all(self):
        current_grasp_id = '2pg'
        new_grasp_id = '2pg1'
        name = '2-phosphoglycerate1'
        bigg_id = '2pg1'
        metanetx_id = 'MNXM231'

        compartments = ['1']
        chebi_ids = 'CHEBI:863541'
        inchis = 'InChI=1S/C3H4O3/c1-2(4)3(5)6/h4H,1H2,(H,5,6)1'

        self.assertEqual(Metabolite.query.count(), 7)
        metabolite = Metabolite.query.filter_by(grasp_id=current_grasp_id).first()

        response = self.client.post('/modify_metabolite/' + current_grasp_id, data=dict(
            grasp_id=new_grasp_id,
            name=name,
            bigg_id=bigg_id,
            metanetx_id=metanetx_id,
            compartments=compartments,
            chebi_ids=chebi_ids,
            inchis=inchis), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See metabolite - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your metabolite has been modified' in response.data)

        self.assertEqual(Metabolite.query.count(), 7)
        self.assertEqual(metabolite.grasp_id, new_grasp_id)
        self.assertEqual(metabolite.name, name)
        self.assertEqual(metabolite.bigg_id, bigg_id)
        self.assertEqual(metabolite.metanetx_id, metanetx_id)
        self.assertEqual(metabolite.compartments.count(), 1)
        self.assertEqual(metabolite.chebis.count(), 1)
        self.assertEqual(metabolite.chebis[0].chebi_id, 'CHEBI:863541')
        self.assertEqual(metabolite.chebis[0].inchi, 'InChI=1S/C3H4O3/c1-2(4)3(5)6/h4H,1H2,(H,5,6)1')

    def test_modify_metabolite_existing_met(self):
        current_grasp_id = '2pg'
        new_grasp_id = 'pep'
        name = '2-phosphoglycerate'
        bigg_id = '2pg'
        metanetx_id = 'MNXM23'

        compartments = ['1', '2']
        chebi_ids = 'CHEBI:86354, CHEBI:8685'
        inchis = 'InChI=1S/C3H4O3/c1-2(4)3(5)6/h4H,1H2,(H,5,6), InChI=1S/C3H4O4/c1-2(4)3(5)6/h4H,1H2,(H,5,6)'

        self.assertEqual(Metabolite.query.count(), 7)
        metabolite = Metabolite.query.filter_by(grasp_id=current_grasp_id).first()

        response = self.client.post('/modify_metabolite/' + current_grasp_id, data=dict(
            grasp_id=new_grasp_id,
            name=name,
            bigg_id=bigg_id,
            metanetx_id=metanetx_id,
            compartments=compartments,
            chebi_ids=chebi_ids,
            inchis=inchis), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    Modify metabolite - Kinetics DB \n</title>' in response.data)
        self.assertTrue(
            b'The metabolite grasp id you specified already exists. Please choose a different one.' in response.data)

        self.assertEqual(Metabolite.query.count(), 7)
        self.assertEqual(metabolite.grasp_id, current_grasp_id)
        self.assertEqual(metabolite.name, name)
        self.assertEqual(metabolite.bigg_id, bigg_id)
        self.assertEqual(metabolite.metanetx_id, metanetx_id)
        self.assertEqual(metabolite.compartments.count(), 2)
        self.assertEqual(metabolite.chebis.count(), 2)
        self.assertEqual(metabolite.chebis[0].chebi_id, 'CHEBI:86354')
        self.assertEqual(metabolite.chebis[1].chebi_id, 'CHEBI:8685')
        self.assertEqual(metabolite.chebis[0].inchi, 'InChI=1S/C3H4O3/c1-2(4)3(5)6/h4H,1H2,(H,5,6)')
        self.assertEqual(metabolite.chebis[1].inchi, 'InChI=1S/C3H4O4/c1-2(4)3(5)6/h4H,1H2,(H,5,6)')


class TestModifyModel(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        populate_db('model', self.client)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_modify_model_change_all(self):
        current_model_name = 'E. coli - iteration 1'
        new_model_name = 'E. coli - iteration 3'

        organism_name = 'Yeast'
        strain = 'WT'
        enz_rxns_orgs = []
        model_inhibitions = []
        model_activations = []
        model_effectors = []
        model_misc_info = []
        model_assumptions = []
        comments = 'blerb'

        model = Model.query.filter_by(name=current_model_name).first()
        self.assertEqual(model.enzyme_reaction_organisms.count(), 2)
        self.assertEqual(model.enzyme_reaction_inhibitions.count(), 2)
        self.assertEqual(model.enzyme_reaction_activations.count(), 2)
        self.assertEqual(model.enzyme_reaction_effectors.count(), 2)
        self.assertEqual(model.enzyme_reaction_misc_infos.count(), 2)

        response = self.client.post('/modify_model/' + current_model_name, data=dict(
            name=new_model_name,
            organism_name=organism_name,
            strain=strain,
            enz_rxn_orgs=enz_rxns_orgs,
            model_inhibitions=model_inhibitions,
            model_activations=model_activations,
            model_effectors=model_effectors,
            model_misc_infos=model_misc_info,
            model_assumptions=model_assumptions,
            comments=comments), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See model - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your model has been modified' in response.data)

        self.assertEqual(Organism.query.filter_by(name=organism_name).first().name, organism_name)
        self.assertEqual(model.name, new_model_name)
        self.assertEqual(model.strain, strain)
        self.assertEqual(model.comments, comments)
        self.assertEqual(model.organism.name, organism_name)
        self.assertEqual(model.enzyme_reaction_organisms.count(), 0)
        self.assertEqual(model.enzyme_reaction_inhibitions.count(), 0)
        self.assertEqual(model.enzyme_reaction_activations.count(), 0)
        self.assertEqual(model.enzyme_reaction_effectors.count(), 0)
        self.assertEqual(model.enzyme_reaction_misc_infos.count(), 0)

    def test_modify_model_change_some(self):
        current_model_name = 'E. coli - iteration 1'
        new_model_name = 'E. coli - iteration 3'

        organism_name = 'Yeast'
        strain = 'WT'
        enz_rxns_orgs = ['1:1:1']
        model_inhibitions = ['1']
        model_activations = ['1']
        model_effectors = ['2']
        model_misc_info = ['1']
        model_assumptions = []
        comments = 'blerb'

        model = Model.query.filter_by(name=current_model_name).first()
        self.assertEqual(model.enzyme_reaction_organisms.count(), 2)
        self.assertEqual(model.enzyme_reaction_inhibitions.count(), 2)
        self.assertEqual(model.enzyme_reaction_activations.count(), 2)
        self.assertEqual(model.enzyme_reaction_effectors.count(), 2)
        self.assertEqual(model.enzyme_reaction_misc_infos.count(), 2)

        response = self.client.post('/modify_model/' + current_model_name, data=dict(
            name=new_model_name,
            organism_name=organism_name,
            strain=strain,
            enz_rxn_orgs=enz_rxns_orgs,
            model_inhibitions=model_inhibitions,
            model_activations=model_activations,
            model_effectors=model_effectors,
            model_misc_infos=model_misc_info,
            model_assumptions=model_assumptions,
            comments=comments), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See model - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your model has been modified' in response.data)

        self.assertEqual(Organism.query.filter_by(name=organism_name).first().name, organism_name)
        self.assertEqual(model.name, new_model_name)
        self.assertEqual(model.strain, strain)
        self.assertEqual(model.comments, comments)
        self.assertEqual(model.organism.name, organism_name)
        self.assertEqual(model.enzyme_reaction_organisms.count(), 1)
        self.assertEqual(model.enzyme_reaction_inhibitions.count(), 1)
        self.assertEqual(model.enzyme_reaction_activations.count(), 1)
        self.assertEqual(model.enzyme_reaction_effectors.count(), 1)
        self.assertEqual(model.enzyme_reaction_misc_infos.count(), 1)

    def test_modify_model_change_nothing(self):
        current_model_name = 'E. coli - iteration 1'
        new_model_name = 'E. coli - iteration 1'

        organism_name = 'E. coli'
        strain = 'MG16555'
        enz_rxns_orgs = ['1:1:1', '2:1:1']
        model_inhibitions = ['1', '2']
        model_activations = ['1', '2']
        model_effectors = ['1', '2']
        model_misc_info = ['1', '2']
        model_assumptions = []
        comments = ''

        model = Model.query.filter_by(name=current_model_name).first()
        self.assertEqual(model.enzyme_reaction_organisms.count(), 2)
        self.assertEqual(model.enzyme_reaction_inhibitions.count(), 2)
        self.assertEqual(model.enzyme_reaction_activations.count(), 2)
        self.assertEqual(model.enzyme_reaction_effectors.count(), 2)
        self.assertEqual(model.enzyme_reaction_misc_infos.count(), 2)

        response = self.client.post('/modify_model/' + current_model_name, data=dict(
            name=new_model_name,
            organism_name=organism_name,
            strain=strain,
            enz_rxn_orgs=enz_rxns_orgs,
            model_inhibitions=model_inhibitions,
            model_activations=model_activations,
            model_effectors=model_effectors,
            model_misc_infos=model_misc_info,
            model_assumptions=model_assumptions,
            comments=comments), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See model - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your model has been modified' in response.data)

        self.assertEqual(Organism.query.filter_by(name=organism_name).first().name, organism_name)
        self.assertEqual(model.name, new_model_name)
        self.assertEqual(model.strain, strain)
        self.assertEqual(model.comments, comments)
        self.assertEqual(model.organism.name, organism_name)
        self.assertEqual(model.enzyme_reaction_organisms.count(), 2)
        self.assertEqual(model.enzyme_reaction_inhibitions.count(), 2)
        self.assertEqual(model.enzyme_reaction_activations.count(), 2)
        self.assertEqual(model.enzyme_reaction_effectors.count(), 2)
        self.assertEqual(model.enzyme_reaction_misc_infos.count(), 2)

    def test_modify_model_existing_name(self):
        current_model_name = 'E. coli - iteration 1'
        new_model_name = 'E. coli - iteration 2'

        organism_name = 'Yeast'
        strain = 'WT'
        enz_rxns_orgs = []
        model_inhibitions = []
        model_activations = []
        model_effectors = []
        model_misc_info = []
        model_assumptions = []
        comments = 'blerb'

        model = Model.query.filter_by(name=current_model_name).first()
        self.assertEqual(model.enzyme_reaction_organisms.count(), 2)
        self.assertEqual(model.enzyme_reaction_inhibitions.count(), 2)
        self.assertEqual(model.enzyme_reaction_activations.count(), 2)
        self.assertEqual(model.enzyme_reaction_effectors.count(), 2)
        self.assertEqual(model.enzyme_reaction_misc_infos.count(), 2)

        response = self.client.post('/modify_model/' + current_model_name, data=dict(
            name=new_model_name,
            organism_name=organism_name,
            strain=strain,
            enz_rxn_orgs=enz_rxns_orgs,
            model_inhibitions=model_inhibitions,
            model_activations=model_activations,
            model_effectors=model_effectors,
            model_misc_infos=model_misc_info,
            model_assumptions=model_assumptions,
            comments=comments), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    Modify model - Kinetics DB \n</title>' in response.data)
        self.assertTrue(
            b'A model with that name already exists, please use either the original name or another one.' in response.data)

        self.assertEqual(Organism.query.filter_by(name=organism_name).first(), None)
        self.assertEqual(model.name, current_model_name)
        self.assertEqual(model.strain, 'MG16555')
        self.assertEqual(model.comments, None)
        self.assertEqual(model.organism.name, 'E. coli')
        self.assertEqual(model.enzyme_reaction_organisms.count(), 2)
        self.assertEqual(model.enzyme_reaction_inhibitions.count(), 2)
        self.assertEqual(model.enzyme_reaction_activations.count(), 2)
        self.assertEqual(model.enzyme_reaction_effectors.count(), 2)
        self.assertEqual(model.enzyme_reaction_misc_infos.count(), 2)


class TestModifyModelAssumption(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        populate_db('enzyme_inhibitor', self.client)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_modify_model_assumption_change_nothing(self):
        model_assumption_id = 1

        model = '1'
        assumption = 'allostery sucks'
        description = 'looks like this met is an allosteric inhibitor for that enzyme'
        included_in_model = 'True'
        evidence_level = '1'
        references = 'https://doi.org/10.1093/bioinformatics/bty942, https://doi.org/10.1093/bioinformatics/bty943'
        comments = ''

        model_assumption = ModelAssumptions.query.filter_by(id=model_assumption_id).first()
        self.assertEqual(ModelAssumptions.query.count(), 2)

        response = self.client.post('/modify_model_assumption/' + str(model_assumption_id), data=dict(
            model=model,
            assumption=assumption,
            description=description,
            evidence_level=evidence_level,
            included_in_model=included_in_model,
            references=references,
            comments=comments), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See model assumption - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your model assumption has been modified.' in response.data)

        self.assertEqual(ModelAssumptions.query.count(), 2)
        self.assertEqual(model_assumption.model.id, 1)
        self.assertEqual(model_assumption.assumption, assumption)
        self.assertEqual(model_assumption.description, description)
        self.assertEqual(model_assumption.included_in_model, bool(included_in_model))
        self.assertEqual(model_assumption.evidence_level_id, int(evidence_level))
        self.assertEqual(model_assumption.references[0].doi, 'https://doi.org/10.1093/bioinformatics/bty942')
        self.assertEqual(model_assumption.comments, comments)

    def test_modify_model_assumption_change_all(self):
        model_assumption_id = 1

        model = '1'
        assumption = 'allostery is cool'
        description = 'looks like this met is not an allosteric inhibitor for that enzyme'
        included_in_model = 'False'
        evidence_level = '2'
        references = 'https://doi.org/10.1093/bioinformatics/bty9410, https://doi.org/10.1093/bioinformatics/bty943'
        comments = 'yey'

        model_assumption = ModelAssumptions.query.filter_by(id=model_assumption_id).first()
        self.assertEqual(ModelAssumptions.query.count(), 2)

        response = self.client.post('/modify_model_assumption/' + str(model_assumption_id), data=dict(
            model=model,
            assumption=assumption,
            description=description,
            evidence_level=evidence_level,
            included_in_model=included_in_model,
            references=references,
            comments=comments), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See model assumption - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your model assumption has been modified.' in response.data)

        self.assertEqual(ModelAssumptions.query.count(), 2)
        self.assertEqual(model_assumption.model.id, 1)
        self.assertEqual(model_assumption.assumption, assumption)
        self.assertEqual(model_assumption.description, description)
        self.assertEqual(model_assumption.included_in_model, bool(included_in_model))
        self.assertEqual(model_assumption.evidence_level_id, int(evidence_level))
        self.assertEqual(model_assumption.references[0].doi, 'https://doi.org/10.1093/bioinformatics/bty9410')
        self.assertEqual(model_assumption.comments, comments)

    def test_modify_model_assumption_change_all_model(self):
        model_assumption_id = 1

        model = '2'
        assumption = 'allostery is cool'
        description = 'looks like this met is not an allosteric inhibitor for that enzyme'
        included_in_model = 'False'
        evidence_level = '2'
        references = 'https://doi.org/10.1093/bioinformatics/bty9410, https://doi.org/10.1093/bioinformatics/bty943'
        comments = 'yey'

        model_assumption = ModelAssumptions.query.filter_by(id=model_assumption_id).first()
        self.assertEqual(ModelAssumptions.query.count(), 2)

        response = self.client.post('/modify_model_assumption/' + str(model_assumption_id), data=dict(
            model=model,
            assumption=assumption,
            description=description,
            evidence_level=evidence_level,
            included_in_model=included_in_model,
            references=references,
            comments=comments), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See model assumption - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your model assumption has been modified.' in response.data)

        self.assertEqual(ModelAssumptions.query.count(), 2)
        self.assertEqual(model_assumption.model.id, 2)
        self.assertEqual(model_assumption.assumption, assumption)
        self.assertEqual(model_assumption.description, description)
        self.assertEqual(model_assumption.included_in_model, bool(included_in_model))
        self.assertEqual(model_assumption.evidence_level_id, int(evidence_level))
        self.assertEqual(model_assumption.references[0].doi, 'https://doi.org/10.1093/bioinformatics/bty9410')
        self.assertEqual(model_assumption.comments, comments)


class TestModifyEnzyme(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        populate_db('enzyme', self.client)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_modify_enzyme_change_all(self):
        current_isoenzyme = 'PFK1'
        current_organism_name = 'E. coli'
        current_uniprot_id_list = 'PC3W1, P34D'
        current_number_of_active_sites = 4
        current_pdb_structure_ids = '3H8A, 1E9I'
        current_strain = 'WT'
        current_gene_names = 'b001 b003'

        enzyme_name = 'bla1'
        enzyme_acronym = 'ble2'
        isoenzyme = 'bli3'
        ec_number = ' 1.1.1.1'
        organism_name = '1'
        number_of_active_sites = 3
        gene_names = 'b004'
        uniprot_id_list = 'EC1P0'
        pdb_structure_ids = '1UCW'
        strain = 'MG1655'

        enzyme = Enzyme.query.filter_by(isoenzyme=current_isoenzyme).first()

        data_form = dict(name=enzyme.name,
                         acronym=enzyme.acronym,
                         isoenzyme=enzyme.isoenzyme,
                         ec_number=enzyme.ec_number,
                         organism_name=current_organism_name,
                         uniprot_id_list=current_uniprot_id_list,
                         number_of_active_sites=current_number_of_active_sites,
                         pdb_structure_ids=current_pdb_structure_ids,
                         strain=current_strain,
                         gene_names=current_gene_names)

        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(enzyme.enzyme_structures.count(), 2)
        self.assertEqual(enzyme.enzyme_organisms.count(), 2)
        self.assertEqual(enzyme.enzyme_reaction_organisms.count(), 1)
        self.assertEqual(enzyme.enzyme_gene_organisms.count(), 2)
        self.assertEqual(enzyme.enzyme_subunits.count(), 0)

        response = self.client.post('/modify_enzyme/' + current_isoenzyme, data=dict(
            name=enzyme_name,
            acronym=enzyme_acronym,
            isoenzyme=isoenzyme,
            ec_number=ec_number,
            organism_name=organism_name,
            number_of_active_sites=number_of_active_sites,
            gene_names=gene_names,
            uniprot_id_list=uniprot_id_list,
            pdb_structure_ids=pdb_structure_ids,
            strain=strain), follow_redirects=True, query_string={'data_form': data_form})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See enzyme - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your enzyme has been modified' in response.data)

        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(enzyme.name, enzyme_name)
        self.assertEqual(enzyme.acronym, enzyme_acronym)
        self.assertEqual(enzyme.isoenzyme, isoenzyme)
        self.assertEqual(enzyme.ec_number, ec_number)
        self.assertEqual(enzyme.enzyme_structures.count(), 1)
        self.assertEqual(enzyme.enzyme_organisms.count(), 1)
        self.assertEqual(enzyme.enzyme_reaction_organisms.count(), 1)
        self.assertEqual(enzyme.enzyme_gene_organisms.count(), 1)
        self.assertEqual(enzyme.enzyme_subunits.count(), 0)

    def test_modify_enzyme_change_nothing(self):
        current_isoenzyme = 'PFK1'
        enzyme_name = 'Phosphofructokinase'
        enzyme_acronym = 'PFK'
        isoenzyme = 'PFK1'
        current_organism_name = '1'
        current_uniprot_id_list = 'PC3W1, P34D'
        current_number_of_active_sites = 4
        current_pdb_structure_ids = '3H8A, 1E9I'
        current_strain = 'WT'
        current_gene_names = 'b001 b003'
        ec_number = '1.2.1.31'

        enzyme = Enzyme.query.filter_by(isoenzyme=current_isoenzyme).first()

        data_form = dict(name=enzyme.name,
                         acronym=enzyme.acronym,
                         isoenzyme=enzyme.isoenzyme,
                         ec_number=enzyme.ec_number,
                         organism_name=current_organism_name,
                         uniprot_id_list=current_uniprot_id_list,
                         number_of_active_sites=current_number_of_active_sites,
                         pdb_structure_ids=current_pdb_structure_ids,
                         strain=current_strain,
                         gene_names=current_gene_names)

        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(enzyme.enzyme_structures.count(), 2)
        self.assertEqual(enzyme.enzyme_organisms.count(), 2)
        self.assertEqual(enzyme.enzyme_reaction_organisms.count(), 1)
        self.assertEqual(enzyme.enzyme_gene_organisms.count(), 2)
        self.assertEqual(enzyme.enzyme_subunits.count(), 0)

        response = self.client.post('/modify_enzyme/' + current_isoenzyme, data=dict(
            name=enzyme_name,
            acronym=enzyme_acronym,
            isoenzyme=isoenzyme,
            ec_number=ec_number,
            organism_name=current_organism_name,
            number_of_active_sites=current_number_of_active_sites,
            gene_names=current_gene_names,
            uniprot_id_list=current_uniprot_id_list,
            pdb_structure_ids=current_pdb_structure_ids,
            strain=current_strain), follow_redirects=True, query_string={'data_form': data_form})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See enzyme - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your enzyme has been modified' in response.data)

        self.assertEqual(Enzyme.query.count(), 2)
        self.assertEqual(enzyme.name, enzyme_name)
        self.assertEqual(enzyme.acronym, enzyme_acronym)
        self.assertEqual(enzyme.isoenzyme, isoenzyme)
        self.assertEqual(enzyme.ec_number, ec_number)
        self.assertEqual(enzyme.enzyme_structures.count(), 2)
        self.assertEqual(enzyme.enzyme_organisms.count(), 2)
        self.assertEqual(enzyme.enzyme_reaction_organisms.count(), 1)
        self.assertEqual(enzyme.enzyme_gene_organisms.count(), 2)
        self.assertEqual(enzyme.enzyme_subunits.count(), 0)


class TestModifyEnzymeInhibitor(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        populate_db('enzyme_inhibitor', self.client)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_modify_enzyme_inhibitor_change_all(self):
        inhibitor_id = 1

        enzyme = '1'
        reaction = '1'
        organism = '1'
        models = '1'
        inhibitor_met = 'ble'
        affected_met = 'blu'
        inhibition_type = 'Mixed'
        inhibition_constant = 1.5 * 10 ** -4

        evidence_level = '2'
        references = 'https://doi.org/10.1093/bioinformatics/bty9410, https://doi.org/10.1093/bioinformatics/bty943'
        comments = 'bbbb'

        enz_inhib = EnzymeReactionInhibition.query.filter_by(id=inhibitor_id).first()

        self.assertEqual(EnzymeReactionInhibition.query.count(), 2)

        self.assertEqual(enz_inhib.enzyme_reaction_organism.id, 1)
        self.assertEqual(enz_inhib.models.count(), 1)
        self.assertEqual(enz_inhib.references.count(), 2)

        response = self.client.post('/modify_enzyme_inhibitor/' + str(inhibitor_id), data=dict(
            enzyme=enzyme,
            reaction=reaction,
            organism=organism,
            models=models,
            inhibitor_met=inhibitor_met,
            affected_met=affected_met,
            inhibition_type=inhibition_type,
            inhibition_constant=inhibition_constant,
            inhibition_evidence_level=evidence_level,
            references=references,
            comments=comments), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See enzyme inhibitor - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your enzyme inhibition has been modified.' in response.data)

        self.assertEqual(EnzymeReactionInhibition.query.count(), 2)
        self.assertEqual(enz_inhib.enzyme_reaction_organism.id, 1)
        self.assertEqual(enz_inhib.enz_rxn_org_id, 1)
        self.assertEqual(enz_inhib.models.count(), 1)
        self.assertEqual(enz_inhib.inhibitor_met.bigg_id, inhibitor_met)
        self.assertEqual(enz_inhib.inhibitor_met.id, enz_inhib.inhibitor_met.id)
        self.assertEqual(enz_inhib.inhibitor_met_id, enz_inhib.inhibitor_met.id)
        self.assertEqual(enz_inhib.affected_met.bigg_id, affected_met)
        self.assertEqual(enz_inhib.inhibition_type, inhibition_type)
        self.assertEqual(enz_inhib.inhibition_constant, inhibition_constant)
        self.assertEqual(enz_inhib.evidence_level_id, int(evidence_level))
        self.assertEqual(enz_inhib.references[0].doi, 'https://doi.org/10.1093/bioinformatics/bty9410')
        self.assertEqual(enz_inhib.comments, comments)

    def test_modify_enzyme_inhibitor_change_all_enzyme(self):
        inhibitor_id = 1

        enzyme = '2'
        reaction = '1'
        organism = '1'
        models = '1'
        inhibitor_met = 'ble'
        affected_met = 'blu'
        inhibition_type = 'Mixed'
        inhibition_constant = 1.5 * 10 ** -4

        evidence_level = '2'
        references = 'https://doi.org/10.1093/bioinformatics/bty9410, https://doi.org/10.1093/bioinformatics/bty943'
        comments = 'bbbb'

        enz_inhib = EnzymeReactionInhibition.query.filter_by(id=inhibitor_id).first()

        self.assertEqual(EnzymeReactionInhibition.query.count(), 2)

        self.assertEqual(enz_inhib.enzyme_reaction_organism.id, 1)
        self.assertEqual(enz_inhib.models.count(), 1)
        self.assertEqual(enz_inhib.references.count(), 2)

        response = self.client.post('/modify_enzyme_inhibitor/' + str(inhibitor_id), data=dict(
            enzyme=enzyme,
            reaction=reaction,
            organism=organism,
            models=models,
            inhibitor_met=inhibitor_met,
            affected_met=affected_met,
            inhibition_type=inhibition_type,
            inhibition_constant=inhibition_constant,
            inhibition_evidence_level=evidence_level,
            references=references,
            comments=comments), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See enzyme inhibitor - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your enzyme inhibition has been modified.' in response.data)

        self.assertEqual(EnzymeReactionInhibition.query.count(), 2)
        self.assertEqual(enz_inhib.enzyme_reaction_organism.id, 2)
        self.assertEqual(enz_inhib.enzyme_reaction_organism.id, enz_inhib.enz_rxn_org_id)
        self.assertEqual(enz_inhib.enz_rxn_org_id, 2)
        self.assertEqual(enz_inhib.models.count(), 1)
        self.assertEqual(enz_inhib.inhibitor_met.bigg_id, inhibitor_met)
        self.assertEqual(enz_inhib.affected_met.bigg_id, affected_met)
        self.assertEqual(enz_inhib.inhibition_type, inhibition_type)
        self.assertEqual(enz_inhib.inhibition_constant, inhibition_constant)
        self.assertEqual(enz_inhib.evidence_level_id, int(evidence_level))
        self.assertEqual(enz_inhib.references[0].doi, 'https://doi.org/10.1093/bioinformatics/bty9410')
        self.assertEqual(enz_inhib.comments, comments)

    def test_modify_enzyme_inhibitor_change_all_organism(self):
        inhibitor_id = 1

        enzyme = '1'
        reaction = '1'
        organism = '2'
        models = '1'
        inhibitor_met = 'ble'
        affected_met = 'blu'
        inhibition_type = 'Mixed'
        inhibition_constant = 1.5 * 10 ** -4

        evidence_level = '2'
        references = 'https://doi.org/10.1093/bioinformatics/bty9410, https://doi.org/10.1093/bioinformatics/bty943'
        comments = 'bbbb'

        enz_inhib = EnzymeReactionInhibition.query.filter_by(id=inhibitor_id).first()

        self.assertEqual(EnzymeReactionInhibition.query.count(), 2)

        self.assertEqual(enz_inhib.enzyme_reaction_organism.id, 1)
        self.assertEqual(enz_inhib.models.count(), 1)
        self.assertEqual(enz_inhib.references.count(), 2)

        response = self.client.post('/modify_enzyme_inhibitor/' + str(inhibitor_id), data=dict(
            enzyme=enzyme,
            reaction=reaction,
            organism=organism,
            models=models,
            inhibitor_met=inhibitor_met,
            affected_met=affected_met,
            inhibition_type=inhibition_type,
            inhibition_constant=inhibition_constant,
            inhibition_evidence_level=evidence_level,
            references=references,
            comments=comments), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See enzyme inhibitor - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your enzyme inhibition has been modified.' in response.data)

        self.assertEqual(EnzymeReactionInhibition.query.count(), 2)
        self.assertEqual(enz_inhib.enzyme_reaction_organism.id, 3)
        self.assertEqual(enz_inhib.enzyme_reaction_organism.id, enz_inhib.enz_rxn_org_id)
        self.assertEqual(enz_inhib.enz_rxn_org_id, 3)
        self.assertEqual(enz_inhib.models.count(), 1)
        self.assertEqual(enz_inhib.inhibitor_met.bigg_id, inhibitor_met)
        self.assertEqual(enz_inhib.affected_met.bigg_id, affected_met)
        self.assertEqual(enz_inhib.inhibition_type, inhibition_type)
        self.assertEqual(enz_inhib.inhibition_constant, inhibition_constant)
        self.assertEqual(enz_inhib.evidence_level_id, int(evidence_level))
        self.assertEqual(enz_inhib.references[0].doi, 'https://doi.org/10.1093/bioinformatics/bty9410')
        self.assertEqual(enz_inhib.comments, comments)

    def test_modify_enzyme_inhibitor_change_all_model(self):
        inhibitor_id = 1

        enzyme = '1'
        reaction = '1'
        organism = '1'
        models = '2'
        inhibitor_met = 'ble'
        affected_met = 'blu'
        inhibition_type = 'Mixed'
        inhibition_constant = 1.5 * 10 ** -4

        evidence_level = '2'
        references = 'https://doi.org/10.1093/bioinformatics/bty9410, https://doi.org/10.1093/bioinformatics/bty943'
        comments = 'bbbb'

        enz_inhib = EnzymeReactionInhibition.query.filter_by(id=inhibitor_id).first()

        self.assertEqual(EnzymeReactionInhibition.query.count(), 2)

        self.assertEqual(enz_inhib.enzyme_reaction_organism.id, 1)
        self.assertEqual(enz_inhib.models.count(), 1)
        self.assertEqual(enz_inhib.references.count(), 2)

        response = self.client.post('/modify_enzyme_inhibitor/' + str(inhibitor_id), data=dict(
            enzyme=enzyme,
            reaction=reaction,
            organism=organism,
            models=models,
            inhibitor_met=inhibitor_met,
            affected_met=affected_met,
            inhibition_type=inhibition_type,
            inhibition_constant=inhibition_constant,
            inhibition_evidence_level=evidence_level,
            references=references,
            comments=comments), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See enzyme inhibitor - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your enzyme inhibition has been modified.' in response.data)

        self.assertEqual(EnzymeReactionInhibition.query.count(), 2)
        self.assertEqual(enz_inhib.enzyme_reaction_organism.id, 1)
        self.assertEqual(enz_inhib.enzyme_reaction_organism.id, enz_inhib.enz_rxn_org_id)
        self.assertEqual(enz_inhib.enz_rxn_org_id, 1)
        self.assertEqual(enz_inhib.models.count(), 2)
        self.assertEqual(enz_inhib.inhibitor_met.bigg_id, inhibitor_met)
        self.assertEqual(enz_inhib.affected_met.bigg_id, affected_met)
        self.assertEqual(enz_inhib.inhibition_type, inhibition_type)
        self.assertEqual(enz_inhib.inhibition_constant, inhibition_constant)
        self.assertEqual(enz_inhib.evidence_level_id, int(evidence_level))
        self.assertEqual(enz_inhib.references[0].doi, 'https://doi.org/10.1093/bioinformatics/bty9410')
        self.assertEqual(enz_inhib.comments, comments)

    def test_modify_enzyme_inhibitor_change_nothing(self):
        inhibitor_id = 1

        enzyme = '1'
        reaction = '1'
        organism = '1'
        models = '1'
        inhibitor_met = 'adp'
        affected_met = 'atp'
        inhibition_type = 'Competitive'
        inhibition_constant = 1.3 * 10 ** -4

        evidence_level = '1'
        references = 'https://doi.org/10.1093/bioinformatics/bty942, https://doi.org/10.1093/bioinformatics/bty943'
        comments = ''

        enz_inhib = EnzymeReactionInhibition.query.filter_by(id=inhibitor_id).first()

        self.assertEqual(EnzymeReactionInhibition.query.count(), 2)

        self.assertEqual(enz_inhib.enzyme_reaction_organism.id, 1)
        self.assertEqual(enz_inhib.models.count(), 1)
        self.assertEqual(enz_inhib.references.count(), 2)

        response = self.client.post('/modify_enzyme_inhibitor/' + str(inhibitor_id), data=dict(
            enzyme=enzyme,
            reaction=reaction,
            organism=organism,
            models=models,
            inhibitor_met=inhibitor_met,
            affected_met=affected_met,
            inhibition_type=inhibition_type,
            inhibition_constant=inhibition_constant,
            inhibition_evidence_level=evidence_level,
            references=references,
            comments=comments), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See enzyme inhibitor - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your enzyme inhibition has been modified.' in response.data)

        self.assertEqual(EnzymeReactionInhibition.query.count(), 2)
        self.assertEqual(enz_inhib.enzyme_reaction_organism.id, 1)
        self.assertEqual(enz_inhib.enz_rxn_org_id, 1)
        self.assertEqual(enz_inhib.models.count(), 1)
        self.assertEqual(enz_inhib.inhibitor_met.bigg_id, inhibitor_met)
        self.assertEqual(enz_inhib.affected_met.bigg_id, affected_met)
        self.assertEqual(enz_inhib.inhibition_type, inhibition_type)
        self.assertEqual(enz_inhib.inhibition_constant, inhibition_constant)
        self.assertEqual(enz_inhib.evidence_level_id, int(evidence_level))
        self.assertEqual(enz_inhib.references[0].doi, 'https://doi.org/10.1093/bioinformatics/bty942')
        self.assertEqual(enz_inhib.comments, comments)


class TestModifyEnzymeActivator(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        populate_db('enzyme_inhibitor', self.client)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_modify_enzyme_activator_change_all(self):
        activator_id = 1

        enzyme = '1'
        reaction = '1'
        organism = '1'
        models = '1'
        activator_met = 'amp'
        activation_constant = 2.3 * 10 ** -4

        evidence_level = '2'
        references = 'https://doi.org/10.1093/bioinformatics/bty9410, https://doi.org/10.1093/bioinformatics/bty943'
        comments = 'bbbb'

        enz_activation = EnzymeReactionActivation.query.filter_by(id=activator_id).first()

        self.assertEqual(EnzymeReactionActivation.query.count(), 2)

        self.assertEqual(enz_activation.enzyme_reaction_organism.id, 1)
        self.assertEqual(enz_activation.models.count(), 1)
        self.assertEqual(enz_activation.references.count(), 2)

        response = self.client.post('/modify_enzyme_activator/' + str(activator_id), data=dict(
            enzyme=enzyme,
            reaction=reaction,
            organism=organism,
            models=models,
            activator_met=activator_met,
            activation_constant=activation_constant,
            activation_evidence_level=evidence_level,
            references=references,
            comments=comments), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See enzyme activator - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your enzyme activation has been modified.' in response.data)

        self.assertEqual(EnzymeReactionActivation.query.count(), 2)
        self.assertEqual(enz_activation.enzyme_reaction_organism.id, 1)
        self.assertEqual(enz_activation.enz_rxn_org_id, 1)
        self.assertEqual(enz_activation.models.count(), 1)
        self.assertEqual(enz_activation.activator_met.bigg_id, activator_met)
        self.assertEqual(enz_activation.activator_met.id, enz_activation.activator_met.id)
        self.assertEqual(enz_activation.activator_met.id, enz_activation.activator_met.id)
        self.assertEqual(enz_activation.activation_constant, activation_constant)
        self.assertEqual(enz_activation.evidence_level_id, int(evidence_level))
        self.assertEqual(enz_activation.references[0].doi, 'https://doi.org/10.1093/bioinformatics/bty9410')
        self.assertEqual(enz_activation.comments, comments)

    def test_modify_enzyme_activator_change_all_enzyme(self):
        activator_id = 1

        enzyme = '2'
        reaction = '1'
        organism = '1'
        models = '1'
        activator_met = 'amp'
        activation_constant = 2.3 * 10 ** -4

        evidence_level = '2'
        references = 'https://doi.org/10.1093/bioinformatics/bty9410, https://doi.org/10.1093/bioinformatics/bty943'
        comments = 'bbbb'

        enz_activation = EnzymeReactionActivation.query.filter_by(id=activator_id).first()

        self.assertEqual(EnzymeReactionActivation.query.count(), 2)

        self.assertEqual(enz_activation.enzyme_reaction_organism.id, 1)
        self.assertEqual(enz_activation.models.count(), 1)
        self.assertEqual(enz_activation.references.count(), 2)

        response = self.client.post('/modify_enzyme_activator/' + str(activator_id), data=dict(
            enzyme=enzyme,
            reaction=reaction,
            organism=organism,
            models=models,
            activator_met=activator_met,
            activation_constant=activation_constant,
            activation_evidence_level=evidence_level,
            references=references,
            comments=comments), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See enzyme activator - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your enzyme activation has been modified.' in response.data)

        self.assertEqual(EnzymeReactionActivation.query.count(), 2)
        self.assertEqual(enz_activation.enzyme_reaction_organism.id, 2)
        self.assertEqual(enz_activation.enz_rxn_org_id, 2)
        self.assertEqual(enz_activation.models.count(), 1)
        self.assertEqual(enz_activation.activator_met.bigg_id, activator_met)
        self.assertEqual(enz_activation.activator_met.id, enz_activation.activator_met.id)
        self.assertEqual(enz_activation.activator_met.id, enz_activation.activator_met.id)
        self.assertEqual(enz_activation.activation_constant, activation_constant)
        self.assertEqual(enz_activation.evidence_level_id, int(evidence_level))
        self.assertEqual(enz_activation.references[0].doi, 'https://doi.org/10.1093/bioinformatics/bty9410')
        self.assertEqual(enz_activation.comments, comments)

    def test_modify_enzyme_activator_change_all_organism(self):
        activator_id = 1

        enzyme = '1'
        reaction = '1'
        organism = '2'
        models = '1'
        activator_met = 'amp'
        activation_constant = 2.3 * 10 ** -4

        evidence_level = '2'
        references = 'https://doi.org/10.1093/bioinformatics/bty9410, https://doi.org/10.1093/bioinformatics/bty943'
        comments = 'bbbb'

        enz_activation = EnzymeReactionActivation.query.filter_by(id=activator_id).first()

        self.assertEqual(EnzymeReactionActivation.query.count(), 2)

        self.assertEqual(enz_activation.enzyme_reaction_organism.id, 1)
        self.assertEqual(enz_activation.models.count(), 1)
        self.assertEqual(enz_activation.references.count(), 2)

        response = self.client.post('/modify_enzyme_activator/' + str(activator_id), data=dict(
            enzyme=enzyme,
            reaction=reaction,
            organism=organism,
            models=models,
            activator_met=activator_met,
            activation_constant=activation_constant,
            activation_evidence_level=evidence_level,
            references=references,
            comments=comments), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See enzyme activator - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your enzyme activation has been modified.' in response.data)

        self.assertEqual(EnzymeReactionActivation.query.count(), 2)
        self.assertEqual(enz_activation.enzyme_reaction_organism.id, 3)
        self.assertEqual(enz_activation.enz_rxn_org_id, 3)
        self.assertEqual(enz_activation.models.count(), 1)
        self.assertEqual(enz_activation.activator_met.bigg_id, activator_met)
        self.assertEqual(enz_activation.activator_met.id, enz_activation.activator_met.id)
        self.assertEqual(enz_activation.activator_met.id, enz_activation.activator_met.id)
        self.assertEqual(enz_activation.activation_constant, activation_constant)
        self.assertEqual(enz_activation.evidence_level_id, int(evidence_level))
        self.assertEqual(enz_activation.references[0].doi, 'https://doi.org/10.1093/bioinformatics/bty9410')
        self.assertEqual(enz_activation.comments, comments)

    def test_modify_enzyme_activator_change_all_model(self):
        activator_id = 1

        enzyme = '1'
        reaction = '1'
        organism = '1'
        models = '2'
        activator_met = 'amp'
        activation_constant = 2.3 * 10 ** -4

        evidence_level = '2'
        references = 'https://doi.org/10.1093/bioinformatics/bty9410, https://doi.org/10.1093/bioinformatics/bty943'
        comments = 'bbbb'

        enz_activation = EnzymeReactionActivation.query.filter_by(id=activator_id).first()

        self.assertEqual(EnzymeReactionActivation.query.count(), 2)

        self.assertEqual(enz_activation.enzyme_reaction_organism.id, 1)
        self.assertEqual(enz_activation.models.count(), 1)
        self.assertEqual(enz_activation.references.count(), 2)

        response = self.client.post('/modify_enzyme_activator/' + str(activator_id), data=dict(
            enzyme=enzyme,
            reaction=reaction,
            organism=organism,
            models=models,
            activator_met=activator_met,
            activation_constant=activation_constant,
            activation_evidence_level=evidence_level,
            references=references,
            comments=comments), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See enzyme activator - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your enzyme activation has been modified.' in response.data)

        self.assertEqual(EnzymeReactionActivation.query.count(), 2)
        self.assertEqual(enz_activation.enzyme_reaction_organism.id, 1)
        self.assertEqual(enz_activation.enz_rxn_org_id, 1)
        self.assertEqual(enz_activation.models.count(), 2)
        self.assertEqual(enz_activation.activator_met.bigg_id, activator_met)
        self.assertEqual(enz_activation.activator_met.id, enz_activation.activator_met.id)
        self.assertEqual(enz_activation.activator_met.id, enz_activation.activator_met.id)
        self.assertEqual(enz_activation.activation_constant, activation_constant)
        self.assertEqual(enz_activation.evidence_level_id, int(evidence_level))
        self.assertEqual(enz_activation.references[0].doi, 'https://doi.org/10.1093/bioinformatics/bty9410')
        self.assertEqual(enz_activation.comments, comments)

    def test_modify_enzyme_activator_change_nothing(self):
        activator_id = 1

        enzyme = '1'
        reaction = '1'
        organism = '1'
        models = '1'
        activator_met = 'adp'
        activation_constant = 1.3 * 10 ** -4

        evidence_level = '1'
        references = 'https://doi.org/10.1093/bioinformatics/bty942, https://doi.org/10.1093/bioinformatics/bty943'
        comments = ''

        enz_activation = EnzymeReactionActivation.query.filter_by(id=activator_id).first()

        self.assertEqual(EnzymeReactionActivation.query.count(), 2)

        self.assertEqual(enz_activation.enzyme_reaction_organism.id, 1)
        self.assertEqual(enz_activation.models.count(), 1)
        self.assertEqual(enz_activation.references.count(), 2)

        response = self.client.post('/modify_enzyme_activator/' + str(activator_id), data=dict(
            enzyme=enzyme,
            reaction=reaction,
            organism=organism,
            models=models,
            activator_met=activator_met,
            activation_constant=activation_constant,
            activation_evidence_level=evidence_level,
            references=references,
            comments=comments), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See enzyme activator - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your enzyme activation has been modified.' in response.data)

        self.assertEqual(EnzymeReactionActivation.query.count(), 2)
        self.assertEqual(enz_activation.enzyme_reaction_organism.id, 1)
        self.assertEqual(enz_activation.enz_rxn_org_id, 1)
        self.assertEqual(enz_activation.models.count(), 1)
        self.assertEqual(enz_activation.activator_met.bigg_id, activator_met)
        self.assertEqual(enz_activation.activator_met.id, enz_activation.activator_met.id)
        self.assertEqual(enz_activation.activator_met.id, enz_activation.activator_met.id)
        self.assertEqual(enz_activation.activation_constant, activation_constant)
        self.assertEqual(enz_activation.evidence_level_id, int(evidence_level))
        self.assertEqual(enz_activation.references[0].doi, 'https://doi.org/10.1093/bioinformatics/bty942')
        self.assertEqual(enz_activation.comments, comments)


class TestModifyEnzymeEffector(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        populate_db('enzyme_inhibitor', self.client)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_modify_enzyme_activator_change_all(self):
        effector_id = 1

        enzyme = '1'
        reaction = '1'
        organism = '1'
        models = '1'
        effector_met = 'bgg'
        effector_type = 'Activating'

        evidence_level = '2'
        references = 'https://doi.org/10.1093/bioinformatics/bty9410, https://doi.org/10.1093/bioinformatics/bty943'
        comments = 'it\'s cold today'

        enz_effector = EnzymeReactionEffector.query.filter_by(id=effector_id).first()

        self.assertEqual(EnzymeReactionEffector.query.count(), 2)

        self.assertEqual(enz_effector.enzyme_reaction_organism.id, 1)
        self.assertEqual(enz_effector.models.count(), 1)
        self.assertEqual(enz_effector.references.count(), 2)

        response = self.client.post('/modify_enzyme_effector/' + str(effector_id), data=dict(
            enzyme=enzyme,
            reaction=reaction,
            organism=organism,
            models=models,
            effector_met=effector_met,
            effector_type=effector_type,
            effector_evidence_level=evidence_level,
            references=references,
            comments=comments), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See enzyme effector - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your enzyme effector has been modified.' in response.data)

        self.assertEqual(EnzymeReactionEffector.query.count(), 2)
        self.assertEqual(enz_effector.enzyme_reaction_organism.id, 1)
        self.assertEqual(enz_effector.enz_rxn_org_id, 1)
        self.assertEqual(enz_effector.models.count(), 1)
        self.assertEqual(enz_effector.effector_met.bigg_id, effector_met)
        self.assertEqual(enz_effector.effector_met.id, enz_effector.effector_met.id)
        self.assertEqual(enz_effector.effector_met.id, enz_effector.effector_met.id)
        self.assertEqual(enz_effector.effector_type, effector_type)
        self.assertEqual(enz_effector.evidence_level_id, int(evidence_level))
        self.assertEqual(enz_effector.references[0].doi, 'https://doi.org/10.1093/bioinformatics/bty9410')
        self.assertEqual(enz_effector.comments, comments)

    def test_modify_enzyme_activator_change_all_enzyme(self):
        effector_id = 1

        enzyme = '2'
        reaction = '1'
        organism = '1'
        models = '1'
        effector_met = 'bgg'
        effector_type = 'Activating'

        evidence_level = '2'
        references = 'https://doi.org/10.1093/bioinformatics/bty9410, https://doi.org/10.1093/bioinformatics/bty943'
        comments = 'it\'s cold today'

        enz_effector = EnzymeReactionEffector.query.filter_by(id=effector_id).first()

        self.assertEqual(EnzymeReactionEffector.query.count(), 2)

        self.assertEqual(enz_effector.enzyme_reaction_organism.id, 1)
        self.assertEqual(enz_effector.models.count(), 1)
        self.assertEqual(enz_effector.references.count(), 2)

        response = self.client.post('/modify_enzyme_effector/' + str(effector_id), data=dict(
            enzyme=enzyme,
            reaction=reaction,
            organism=organism,
            models=models,
            effector_met=effector_met,
            effector_type=effector_type,
            effector_evidence_level=evidence_level,
            references=references,
            comments=comments), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See enzyme effector - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your enzyme effector has been modified.' in response.data)

        self.assertEqual(EnzymeReactionEffector.query.count(), 2)
        self.assertEqual(enz_effector.enzyme_reaction_organism.id, 2)
        self.assertEqual(enz_effector.enz_rxn_org_id, 2)
        self.assertEqual(enz_effector.models.count(), 1)
        self.assertEqual(enz_effector.effector_met.bigg_id, effector_met)
        self.assertEqual(enz_effector.effector_met.id, enz_effector.effector_met.id)
        self.assertEqual(enz_effector.effector_met.id, enz_effector.effector_met.id)
        self.assertEqual(enz_effector.effector_type, effector_type)
        self.assertEqual(enz_effector.evidence_level_id, int(evidence_level))
        self.assertEqual(enz_effector.references[0].doi, 'https://doi.org/10.1093/bioinformatics/bty9410')
        self.assertEqual(enz_effector.comments, comments)

    def test_modify_enzyme_activator_change_all_organism(self):
        effector_id = 1

        enzyme = '1'
        reaction = '1'
        organism = '2'
        models = '1'
        effector_met = 'bgg'
        effector_type = 'Activating'

        evidence_level = '2'
        references = 'https://doi.org/10.1093/bioinformatics/bty9410, https://doi.org/10.1093/bioinformatics/bty943'
        comments = 'it\'s cold today'

        enz_effector = EnzymeReactionEffector.query.filter_by(id=effector_id).first()

        self.assertEqual(EnzymeReactionEffector.query.count(), 2)

        self.assertEqual(enz_effector.enzyme_reaction_organism.id, 1)
        self.assertEqual(enz_effector.models.count(), 1)
        self.assertEqual(enz_effector.references.count(), 2)

        response = self.client.post('/modify_enzyme_effector/' + str(effector_id), data=dict(
            enzyme=enzyme,
            reaction=reaction,
            organism=organism,
            models=models,
            effector_met=effector_met,
            effector_type=effector_type,
            effector_evidence_level=evidence_level,
            references=references,
            comments=comments), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See enzyme effector - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your enzyme effector has been modified.' in response.data)

        self.assertEqual(EnzymeReactionEffector.query.count(), 2)
        self.assertEqual(enz_effector.enzyme_reaction_organism.id, 3)
        self.assertEqual(enz_effector.enz_rxn_org_id, 3)
        self.assertEqual(enz_effector.models.count(), 1)
        self.assertEqual(enz_effector.effector_met.bigg_id, effector_met)
        self.assertEqual(enz_effector.effector_met.id, enz_effector.effector_met.id)
        self.assertEqual(enz_effector.effector_met.id, enz_effector.effector_met.id)
        self.assertEqual(enz_effector.effector_type, effector_type)
        self.assertEqual(enz_effector.evidence_level_id, int(evidence_level))
        self.assertEqual(enz_effector.references[0].doi, 'https://doi.org/10.1093/bioinformatics/bty9410')
        self.assertEqual(enz_effector.comments, comments)

    def test_modify_enzyme_activator_change_all_model(self):
        effector_id = 1

        enzyme = '1'
        reaction = '1'
        organism = '1'
        models = '2'
        effector_met = 'bgg'
        effector_type = 'Activating'

        evidence_level = '2'
        references = 'https://doi.org/10.1093/bioinformatics/bty9410, https://doi.org/10.1093/bioinformatics/bty943'
        comments = 'it\'s cold today'

        enz_effector = EnzymeReactionEffector.query.filter_by(id=effector_id).first()

        self.assertEqual(EnzymeReactionEffector.query.count(), 2)

        self.assertEqual(enz_effector.enzyme_reaction_organism.id, 1)
        self.assertEqual(enz_effector.models.count(), 1)
        self.assertEqual(enz_effector.references.count(), 2)

        response = self.client.post('/modify_enzyme_effector/' + str(effector_id), data=dict(
            enzyme=enzyme,
            reaction=reaction,
            organism=organism,
            models=models,
            effector_met=effector_met,
            effector_type=effector_type,
            effector_evidence_level=evidence_level,
            references=references,
            comments=comments), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See enzyme effector - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your enzyme effector has been modified.' in response.data)

        self.assertEqual(EnzymeReactionEffector.query.count(), 2)
        self.assertEqual(enz_effector.enzyme_reaction_organism.id, 1)
        self.assertEqual(enz_effector.enz_rxn_org_id, 1)
        self.assertEqual(enz_effector.models.count(), 2)
        self.assertEqual(enz_effector.effector_met.bigg_id, effector_met)
        self.assertEqual(enz_effector.effector_met.id, enz_effector.effector_met.id)
        self.assertEqual(enz_effector.effector_met.id, enz_effector.effector_met.id)
        self.assertEqual(enz_effector.effector_type, effector_type)
        self.assertEqual(enz_effector.evidence_level_id, int(evidence_level))
        self.assertEqual(enz_effector.references[0].doi, 'https://doi.org/10.1093/bioinformatics/bty9410')
        self.assertEqual(enz_effector.comments, comments)

    def test_modify_enzyme_activator_change_nothing(self):
        effector_id = 1

        enzyme = '1'
        reaction = '1'
        organism = '1'
        models = '1'
        effector_met = 'adp'
        effector_type = 'Inhibiting'

        evidence_level = '1'
        references = 'https://doi.org/10.1093/bioinformatics/bty942, https://doi.org/10.1093/bioinformatics/bty943'
        comments = ''

        enz_effector = EnzymeReactionEffector.query.filter_by(id=effector_id).first()

        self.assertEqual(EnzymeReactionEffector.query.count(), 2)

        self.assertEqual(enz_effector.enzyme_reaction_organism.id, 1)
        self.assertEqual(enz_effector.models.count(), 1)
        self.assertEqual(enz_effector.references.count(), 2)

        response = self.client.post('/modify_enzyme_effector/' + str(effector_id), data=dict(
            enzyme=enzyme,
            reaction=reaction,
            organism=organism,
            models=models,
            effector_met=effector_met,
            effector_type=effector_type,
            effector_evidence_level=evidence_level,
            references=references,
            comments=comments), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See enzyme effector - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your enzyme effector has been modified.' in response.data)

        self.assertEqual(EnzymeReactionEffector.query.count(), 2)
        self.assertEqual(enz_effector.enzyme_reaction_organism.id, 1)
        self.assertEqual(enz_effector.enz_rxn_org_id, 1)
        self.assertEqual(enz_effector.models.count(), 1)
        self.assertEqual(enz_effector.effector_met.bigg_id, effector_met)
        self.assertEqual(enz_effector.effector_met.id, enz_effector.effector_met.id)
        self.assertEqual(enz_effector.effector_met.id, enz_effector.effector_met.id)
        self.assertEqual(enz_effector.effector_type, effector_type)
        self.assertEqual(enz_effector.evidence_level_id, int(evidence_level))
        self.assertEqual(enz_effector.references[0].doi, 'https://doi.org/10.1093/bioinformatics/bty942')
        self.assertEqual(enz_effector.comments, comments)


class TestModifyEnzymeMiscInfo(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        populate_db('enzyme_inhibitor', self.client)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_modify_enzyme_activator_change_all(self):
        misc_info_id = 1

        enzyme = '1'
        reaction = '1'
        organism = '1'
        models = '1'
        topic = 'allostery2'
        description = 'looks like this met is an allosteric inhibitor for that enzyme222'

        evidence_level = '2'
        references = 'https://doi.org/10.1093/bioinformatics/bty9410, https://doi.org/10.1093/bioinformatics/bty943'
        comments = 'lalalala'

        enz_misc_info = EnzymeReactionMiscInfo.query.filter_by(id=misc_info_id).first()

        self.assertEqual(EnzymeReactionMiscInfo.query.count(), 2)

        self.assertEqual(enz_misc_info.enzyme_reaction_organism.id, 1)
        self.assertEqual(enz_misc_info.models.count(), 1)
        self.assertEqual(enz_misc_info.references.count(), 2)

        response = self.client.post('/modify_enzyme_misc_info/' + str(misc_info_id), data=dict(
            enzyme=enzyme,
            reaction=reaction,
            organism=organism,
            models=models,
            topic=topic,
            description=description,
            evidence_level=evidence_level,
            references=references,
            comments=comments), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See enzyme misc info - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your enzyme misc info has been modified.' in response.data)

        self.assertEqual(EnzymeReactionMiscInfo.query.count(), 2)
        self.assertEqual(enz_misc_info.enzyme_reaction_organism.id, 1)
        self.assertEqual(enz_misc_info.enz_rxn_org_id, 1)
        self.assertEqual(enz_misc_info.models.count(), 1)
        self.assertEqual(enz_misc_info.topic, topic)
        self.assertEqual(enz_misc_info.description, description)
        self.assertEqual(enz_misc_info.evidence_level_id, int(evidence_level))
        self.assertEqual(enz_misc_info.references[0].doi, 'https://doi.org/10.1093/bioinformatics/bty9410')
        self.assertEqual(enz_misc_info.comments, comments)

    def test_modify_enzyme_activator_change_all_enzyme(self):
        misc_info_id = 1

        enzyme = '2'
        reaction = '1'
        organism = '1'
        models = '1'
        topic = 'allostery2'
        description = 'looks like this met is an allosteric inhibitor for that enzyme222'

        evidence_level = '2'
        references = 'https://doi.org/10.1093/bioinformatics/bty9410, https://doi.org/10.1093/bioinformatics/bty943'
        comments = 'lalalala'

        enz_misc_info = EnzymeReactionMiscInfo.query.filter_by(id=misc_info_id).first()

        self.assertEqual(EnzymeReactionMiscInfo.query.count(), 2)

        self.assertEqual(enz_misc_info.enzyme_reaction_organism.id, 1)
        self.assertEqual(enz_misc_info.models.count(), 1)
        self.assertEqual(enz_misc_info.references.count(), 2)

        response = self.client.post('/modify_enzyme_misc_info/' + str(misc_info_id), data=dict(
            enzyme=enzyme,
            reaction=reaction,
            organism=organism,
            models=models,
            topic=topic,
            description=description,
            evidence_level=evidence_level,
            references=references,
            comments=comments), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See enzyme misc info - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your enzyme misc info has been modified.' in response.data)

        self.assertEqual(EnzymeReactionMiscInfo.query.count(), 2)
        self.assertEqual(enz_misc_info.enzyme_reaction_organism.id, 2)
        self.assertEqual(enz_misc_info.enz_rxn_org_id, 2)
        self.assertEqual(enz_misc_info.models.count(), 1)
        self.assertEqual(enz_misc_info.topic, topic)
        self.assertEqual(enz_misc_info.description, description)
        self.assertEqual(enz_misc_info.evidence_level_id, int(evidence_level))
        self.assertEqual(enz_misc_info.references[0].doi, 'https://doi.org/10.1093/bioinformatics/bty9410')
        self.assertEqual(enz_misc_info.comments, comments)

    def test_modify_enzyme_activator_change_all_organism(self):
        misc_info_id = 1

        enzyme = '1'
        reaction = '1'
        organism = '2'
        models = '1'
        topic = 'allostery2'
        description = 'looks like this met is an allosteric inhibitor for that enzyme222'

        evidence_level = '2'
        references = 'https://doi.org/10.1093/bioinformatics/bty9410, https://doi.org/10.1093/bioinformatics/bty943'
        comments = 'lalalala'

        enz_misc_info = EnzymeReactionMiscInfo.query.filter_by(id=misc_info_id).first()

        self.assertEqual(EnzymeReactionMiscInfo.query.count(), 2)

        self.assertEqual(enz_misc_info.enzyme_reaction_organism.id, 1)
        self.assertEqual(enz_misc_info.models.count(), 1)
        self.assertEqual(enz_misc_info.references.count(), 2)

        response = self.client.post('/modify_enzyme_misc_info/' + str(misc_info_id), data=dict(
            enzyme=enzyme,
            reaction=reaction,
            organism=organism,
            models=models,
            topic=topic,
            description=description,
            evidence_level=evidence_level,
            references=references,
            comments=comments), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See enzyme misc info - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your enzyme misc info has been modified.' in response.data)

        self.assertEqual(EnzymeReactionMiscInfo.query.count(), 2)
        self.assertEqual(enz_misc_info.enzyme_reaction_organism.id, 3)
        self.assertEqual(enz_misc_info.enz_rxn_org_id, 3)
        self.assertEqual(enz_misc_info.models.count(), 1)
        self.assertEqual(enz_misc_info.topic, topic)
        self.assertEqual(enz_misc_info.description, description)
        self.assertEqual(enz_misc_info.evidence_level_id, int(evidence_level))
        self.assertEqual(enz_misc_info.references[0].doi, 'https://doi.org/10.1093/bioinformatics/bty9410')
        self.assertEqual(enz_misc_info.comments, comments)

    def test_modify_enzyme_activator_change_all_model(self):
        misc_info_id = 1

        enzyme = '1'
        reaction = '1'
        organism = '1'
        models = '1'
        topic = 'allostery'
        description = 'looks like this met is an allosteric inhibitor for that enzyme'

        evidence_level = '1'
        references = 'https://doi.org/10.1093/bioinformatics/bty942, https://doi.org/10.1093/bioinformatics/bty943'
        comments = ''

        enz_misc_info = EnzymeReactionMiscInfo.query.filter_by(id=misc_info_id).first()

        self.assertEqual(EnzymeReactionMiscInfo.query.count(), 2)

        self.assertEqual(enz_misc_info.enzyme_reaction_organism.id, 1)
        self.assertEqual(enz_misc_info.models.count(), 1)
        self.assertEqual(enz_misc_info.references.count(), 2)

        response = self.client.post('/modify_enzyme_misc_info/' + str(misc_info_id), data=dict(
            enzyme=enzyme,
            reaction=reaction,
            organism=organism,
            models=models,
            topic=topic,
            description=description,
            evidence_level=evidence_level,
            references=references,
            comments=comments), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See enzyme misc info - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your enzyme misc info has been modified.' in response.data)

        self.assertEqual(EnzymeReactionMiscInfo.query.count(), 2)
        self.assertEqual(enz_misc_info.enzyme_reaction_organism.id, 1)
        self.assertEqual(enz_misc_info.enz_rxn_org_id, 1)
        self.assertEqual(enz_misc_info.models.count(), 1)
        self.assertEqual(enz_misc_info.topic, topic)
        self.assertEqual(enz_misc_info.description, description)
        self.assertEqual(enz_misc_info.evidence_level_id, int(evidence_level))
        self.assertEqual(enz_misc_info.references[0].doi, 'https://doi.org/10.1093/bioinformatics/bty942')
        self.assertEqual(enz_misc_info.comments, comments)

    def test_modify_enzyme_activator_change_nothing(self):
        misc_info_id = 1

        enzyme = '1'
        reaction = '1'
        organism = '1'
        models = '1'
        topic = 'allostery'
        description = 'looks like this met is an allosteric inhibitor for that enzyme'

        evidence_level = '1'
        references = 'https://doi.org/10.1093/bioinformatics/bty942, https://doi.org/10.1093/bioinformatics/bty943'
        comments = ''

        enz_misc_info = EnzymeReactionMiscInfo.query.filter_by(id=misc_info_id).first()

        self.assertEqual(EnzymeReactionMiscInfo.query.count(), 2)

        self.assertEqual(enz_misc_info.enzyme_reaction_organism.id, 1)
        self.assertEqual(enz_misc_info.models.count(), 1)
        self.assertEqual(enz_misc_info.references.count(), 2)

        response = self.client.post('/modify_enzyme_misc_info/' + str(misc_info_id), data=dict(
            enzyme=enzyme,
            reaction=reaction,
            organism=organism,
            models=models,
            topic=topic,
            description=description,
            evidence_level=evidence_level,
            references=references,
            comments=comments), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See enzyme misc info - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your enzyme misc info has been modified.' in response.data)

        self.assertEqual(EnzymeReactionMiscInfo.query.count(), 2)
        self.assertEqual(enz_misc_info.enzyme_reaction_organism.id, 1)
        self.assertEqual(enz_misc_info.enz_rxn_org_id, 1)
        self.assertEqual(enz_misc_info.models.count(), 1)
        self.assertEqual(enz_misc_info.topic, topic)
        self.assertEqual(enz_misc_info.description, description)
        self.assertEqual(enz_misc_info.evidence_level_id, int(evidence_level))
        self.assertEqual(enz_misc_info.references[0].doi, 'https://doi.org/10.1093/bioinformatics/bty942')
        self.assertEqual(enz_misc_info.comments, comments)


class TestModifyReaction(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        populate_db('reaction', self.client)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_modify_reaction_change_nothing(self):
        reaction_name = 'phosphofructokinase'
        reaction_acronym = 'PFK'
        reaction_grasp_id = 'PFK1'
        reaction_string = '1 pep_c + 1.5 adp_c <-> pyr_c + 2.0 atp_c'
        metanetx_id = ''
        bigg_id = ''
        kegg_id = ''
        isoenzyme = 'PFK1'

        compartment = '1'
        compartment_name = 'Cytosol'
        organism = 'E. coli'
        models = 'E. coli - iteration 1'
        enzymes = ['1']
        mechanism = '1'
        mechanism_references = 'https://doi.org/10.1093/bioinformatics/bty942, https://doi.org/10.1093/bioinformatics/bty943'
        mechanism_evidence_level = '1'
        subs_binding_order = 'adp_c, pep_c'
        prod_release_order = 'pyr_c, atp_c'
        std_gibbs_energy = 2.1
        std_gibbs_energy_std = 0.2
        std_gibbs_energy_ph = 7
        std_gibbs_energy_ionic_strength = 0.2
        std_gibbs_energy_references = 'equilibrator'
        comments = ''

        data_form = dict(name=reaction_name,
                         acronym=reaction_acronym,
                         grasp_id=reaction_grasp_id,
                         reaction_string=reaction_string,
                         bigg_id=bigg_id,
                         kegg_id=kegg_id,
                         metanetx_id=metanetx_id,
                         compartment=compartment,
                         organism=organism,
                         model=models,
                         isoenzyme=isoenzyme,
                         mechanism=mechanism,
                         mechanism_references=mechanism_references,
                         mechanism_evidence_level=mechanism_evidence_level,
                         subs_binding_order=subs_binding_order,
                         prod_release_order=prod_release_order,
                         std_gibbs_energy=std_gibbs_energy,
                         std_gibbs_energy_std=std_gibbs_energy_std,
                         std_gibbs_energy_ph=std_gibbs_energy_ph,
                         std_gibbs_energy_ionic_strength=std_gibbs_energy_ionic_strength,
                         std_gibbs_energy_references=std_gibbs_energy_references,
                         comments=comments)

        reaction = Reaction.query.filter_by(acronym=reaction_acronym).first()
        self.assertEqual(Reaction.query.count(), 1)
        self.assertEqual(reaction.enzyme_reaction_organisms.count(), 2)
        self.assertEqual(reaction.metabolites.count(), 4)
        self.assertEqual(reaction.gibbs_energy_reaction_models.count(), 2)

        response = self.client.post('/modify_reaction/' + reaction_acronym, data=dict(
            name=reaction_name,
            acronym=reaction_acronym,
            grasp_id=reaction_grasp_id,
            reaction_string=reaction_string,
            bigg_id=bigg_id,
            kegg_id=kegg_id,
            metanetx_id=metanetx_id,
            compartment=compartment,
            organism='1',
            models='1',
            enzymes=enzymes,
            mechanism=mechanism,
            mechanism_references=mechanism_references,
            mechanism_evidence_level=mechanism_evidence_level,
            subs_binding_order=subs_binding_order,
            prod_release_order=prod_release_order,
            std_gibbs_energy=std_gibbs_energy,
            std_gibbs_energy_std=std_gibbs_energy_std,
            std_gibbs_energy_ph=std_gibbs_energy_ph,
            std_gibbs_energy_ionic_strength=std_gibbs_energy_ionic_strength,
            std_gibbs_energy_references=std_gibbs_energy_references,
            comments=comments), follow_redirects=True, query_string={'data_form': data_form})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See reaction - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your reaction has been modified' in response.data)

        self.assertEqual(Reaction.query.count(), 1)
        self.assertEqual(reaction.enzyme_reaction_organisms.count(), 2)
        self.assertEqual(reaction.metabolites.count(), 4)
        self.assertEqual(reaction.gibbs_energy_reaction_models.count(), 2)

        self.assertEqual(reaction.name, reaction_name)
        self.assertEqual(reaction.acronym, reaction_acronym)
        self.assertEqual(reaction.metanetx_id, metanetx_id)
        self.assertEqual(reaction.bigg_id, bigg_id)
        self.assertEqual(reaction.kegg_id, kegg_id)
        self.assertEqual(reaction.compartment_name, compartment_name)

        gibbs_energy_id = reaction.gibbs_energy_reaction_models[0].gibbs_energy_id
        self.assertEqual(GibbsEnergy.query.filter_by(id=gibbs_energy_id).first().standard_dg, std_gibbs_energy)

    def test_modify_reaction_change_all(self):
        reaction_name = 'phosphofructokinase'
        reaction_acronym = 'PFK'
        reaction_grasp_id = 'PFK1'
        reaction_string = '1 pep_c + 1.5 adp_c <-> pyr_c + 2.0 atp_c'
        metanetx_id = ''
        bigg_id = ''
        kegg_id = ''
        isoenzyme = 'PFK1'

        compartment = '1'
        compartment_name = 'Cytosol'
        organism = 'E. coli'
        models = 'E. coli - iteration 1'
        enzymes = ['1']
        mechanism = '1'
        mechanism_references = 'https://doi.org/10.1093/bioinformatics/bty942, https://doi.org/10.1093/bioinformatics/bty943'
        mechanism_evidence_level = '1'
        subs_binding_order = 'adp_c, pep_c'
        prod_release_order = 'pyr_c, atp_c'
        std_gibbs_energy = 2.1
        std_gibbs_energy_std = 0.2
        std_gibbs_energy_ph = 7
        std_gibbs_energy_ionic_strength = 0.2
        std_gibbs_energy_references = 'equilibrator'
        comments = ''

        data_form = dict(name=reaction_name,
                         acronym=reaction_acronym,
                         grasp_id=reaction_grasp_id,
                         reaction_string=reaction_string,
                         bigg_id=bigg_id,
                         kegg_id=kegg_id,
                         metanetx_id=metanetx_id,
                         compartment=compartment,
                         organism=organism,
                         model=models,
                         isoenzyme=isoenzyme,
                         mechanism=mechanism,
                         mechanism_references=mechanism_references,
                         mechanism_evidence_level=mechanism_evidence_level,
                         subs_binding_order=subs_binding_order,
                         prod_release_order=prod_release_order,
                         std_gibbs_energy=std_gibbs_energy,
                         std_gibbs_energy_std=std_gibbs_energy_std,
                         std_gibbs_energy_ph=std_gibbs_energy_ph,
                         std_gibbs_energy_ionic_strength=std_gibbs_energy_ionic_strength,
                         std_gibbs_energy_references=std_gibbs_energy_references,
                         comments=comments)

        reaction = Reaction.query.filter_by(acronym=reaction_acronym).first()
        self.assertEqual(Reaction.query.count(), 1)
        self.assertEqual(reaction.enzyme_reaction_organisms.count(), 2)
        self.assertEqual(reaction.metabolites.count(), 4)
        self.assertEqual(reaction.gibbs_energy_reaction_models.count(), 2)

        self.assertEqual(reaction.enzyme_reaction_organisms.all()[0].reaction_id, 1)
        self.assertEqual(reaction.enzyme_reaction_organisms.all()[0].organism_id, 1)
        self.assertEqual(reaction.enzyme_reaction_organisms.all()[0].enzyme_id, 1)

        self.assertEqual(reaction.enzyme_reaction_organisms.all()[1].reaction_id, 1)
        self.assertEqual(reaction.enzyme_reaction_organisms.all()[1].organism_id, 1)
        self.assertEqual(reaction.enzyme_reaction_organisms.all()[1].enzyme_id, 2)

        reaction_name = 'phosphofructokinase'
        reaction_acronym = 'PFK'
        reaction_grasp_id = 'PFK1'
        reaction_string = '1 pep_c + 1.5 atp_c <-> pyr_c + 2.0 atp_c'
        metanetx_id = ''
        bigg_id = ''
        kegg_id = ''
        isoenzyme = 'PFK1'

        compartment = '1'
        compartment_name = 'Cytosol'
        organism_name = 'E. coli'
        organism = '1'
        model_name = 'E. coli - iteration 2'
        models = '2'
        enzymes = ['2']
        mechanism = '1'
        mechanism_references = 'https://doi.org/10.1093/bioinformatics/bty9410, https://doi.org/10.1093/bioinformatics/bty943'
        mechanism_evidence_level = '1'
        subs_binding_order = 'atp_c, pep_c'
        prod_release_order = 'pyr_c, atp_c'
        std_gibbs_energy = 2.1
        std_gibbs_energy_std = 0.2
        std_gibbs_energy_ph = 7
        std_gibbs_energy_ionic_strength = 0.2
        std_gibbs_energy_references = 'equilibrator'
        comments = ''

        response = self.client.post('/modify_reaction/' + reaction_acronym, data=dict(
            name=reaction_name,
            acronym=reaction_acronym,
            grasp_id=reaction_grasp_id,
            reaction_string=reaction_string,
            bigg_id=bigg_id,
            kegg_id=kegg_id,
            metanetx_id=metanetx_id,
            compartment=compartment,
            organism=organism,
            models=models,
            enzymes=enzymes,
            mechanism=mechanism,
            mechanism_references=mechanism_references,
            mechanism_evidence_level=mechanism_evidence_level,
            subs_binding_order=subs_binding_order,
            prod_release_order=prod_release_order,
            std_gibbs_energy=std_gibbs_energy,
            std_gibbs_energy_std=std_gibbs_energy_std,
            std_gibbs_energy_ph=std_gibbs_energy_ph,
            std_gibbs_energy_ionic_strength=std_gibbs_energy_ionic_strength,
            std_gibbs_energy_references=std_gibbs_energy_references,
            comments=comments), follow_redirects=True, query_string={'data_form': data_form})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See reaction - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your reaction has been modified' in response.data)

        self.assertEqual(Reaction.query.count(), 1)
        self.assertEqual(reaction.enzyme_reaction_organisms.count(), 2)

        self.assertEqual(reaction.metabolites.count(), 3)
        self.assertEqual(reaction.gibbs_energy_reaction_models.count(), 2)

        self.assertEqual(reaction.name, reaction_name)
        self.assertEqual(reaction.acronym, reaction_acronym)
        self.assertEqual(reaction.metanetx_id, metanetx_id)
        self.assertEqual(reaction.bigg_id, bigg_id)
        self.assertEqual(reaction.kegg_id, kegg_id)
        self.assertEqual(reaction.compartment_name, compartment_name)

        gibbs_energy_id = reaction.gibbs_energy_reaction_models[0].gibbs_energy_id

        self.assertEqual(GibbsEnergy.query.filter_by(id=gibbs_energy_id).first().standard_dg, std_gibbs_energy)

        self.assertEqual(reaction.enzyme_reaction_organisms.all()[0].reaction_id, 1)
        self.assertEqual(reaction.enzyme_reaction_organisms.all()[0].organism_id, 1)
        self.assertEqual(reaction.enzyme_reaction_organisms.all()[0].enzyme_id, 1)

        self.assertEqual(reaction.enzyme_reaction_organisms.all()[1].reaction_id, 1)
        self.assertEqual(reaction.enzyme_reaction_organisms.all()[1].organism_id, 1)
        self.assertEqual(reaction.enzyme_reaction_organisms.all()[1].enzyme_id, 2)

        self.assertEqual(reaction.enzyme_reaction_organisms.all()[1].organism.name, organism_name)
        self.assertEqual(reaction.enzyme_reaction_organisms.all()[1].models[1].name, model_name)
        self.assertEqual(reaction.enzyme_reaction_organisms.all()[1].subs_binding_order, subs_binding_order)

        self.assertEqual(reaction.enzyme_reaction_organisms.all()[0].mechanism_references[0].doi,
                         'https://doi.org/10.1093/bioinformatics/bty942')
        self.assertEqual(reaction.enzyme_reaction_organisms.all()[1].mechanism_references[0].doi,
                         'https://doi.org/10.1093/bioinformatics/bty9410')

    def test_modify_reaction_change_all_organism(self):
        reaction_name = 'phosphofructokinase'
        reaction_acronym = 'PFK'
        reaction_grasp_id = 'PFK1'
        reaction_string = '1 pep_c + 1.5 adp_c <-> pyr_c + 2.0 atp_c'
        metanetx_id = ''
        bigg_id = ''
        kegg_id = ''
        isoenzyme = 'PFK1'

        compartment = '1'
        compartment_name = 'Cytosol'
        organism = 'E. coli'
        models = 'E. coli - iteration 1'
        enzymes = ['1']
        mechanism = '1'
        mechanism_references = 'https://doi.org/10.1093/bioinformatics/bty942, https://doi.org/10.1093/bioinformatics/bty943'
        mechanism_evidence_level = '1'
        subs_binding_order = 'adp_c, pep_c'
        prod_release_order = 'pyr_c, atp_c'
        std_gibbs_energy = 2.1
        std_gibbs_energy_std = 0.2
        std_gibbs_energy_ph = 7
        std_gibbs_energy_ionic_strength = 0.2
        std_gibbs_energy_references = 'equilibrator'
        comments = ''

        data_form = dict(name=reaction_name,
                         acronym=reaction_acronym,
                         grasp_id=reaction_grasp_id,
                         reaction_string=reaction_string,
                         bigg_id=bigg_id,
                         kegg_id=kegg_id,
                         metanetx_id=metanetx_id,
                         compartment=compartment,
                         organism=organism,
                         model=models,
                         isoenzyme=isoenzyme,
                         mechanism=mechanism,
                         mechanism_references=mechanism_references,
                         mechanism_evidence_level=mechanism_evidence_level,
                         subs_binding_order=subs_binding_order,
                         prod_release_order=prod_release_order,
                         std_gibbs_energy=std_gibbs_energy,
                         std_gibbs_energy_std=std_gibbs_energy_std,
                         std_gibbs_energy_ph=std_gibbs_energy_ph,
                         std_gibbs_energy_ionic_strength=std_gibbs_energy_ionic_strength,
                         std_gibbs_energy_references=std_gibbs_energy_references,
                         comments=comments)

        reaction = Reaction.query.filter_by(acronym=reaction_acronym).first()
        self.assertEqual(Reaction.query.count(), 1)
        self.assertEqual(reaction.enzyme_reaction_organisms.count(), 2)
        self.assertEqual(reaction.metabolites.count(), 4)
        self.assertEqual(reaction.gibbs_energy_reaction_models.count(), 2)

        reaction_name = 'phosphofructokinase'
        reaction_acronym = 'PFK'
        reaction_grasp_id = 'PFK1'
        reaction_string = '1 pep_c + 1.5 atp_c <-> pyr_c + 2.0 atp_c'
        metanetx_id = ''
        bigg_id = ''
        kegg_id = ''
        isoenzyme = 'PFK1'

        compartment = '1'
        compartment_name = 'Cytosol'
        organism_name = 'S. cerevisiae'
        organism = '2'
        model_name = 'E. coli - iteration 2'
        models = '2'
        enzymes = ['1']
        mechanism = '1'
        mechanism_references = 'https://doi.org/10.1093/bioinformatics/bty9410, https://doi.org/10.1093/bioinformatics/bty943'
        mechanism_evidence_level = '1'
        subs_binding_order = 'atp_c, pep_c'
        prod_release_order = 'pyr_c, atp_c'
        std_gibbs_energy = 2.1
        std_gibbs_energy_std = 0.2
        std_gibbs_energy_ph = 7
        std_gibbs_energy_ionic_strength = 0.2
        std_gibbs_energy_references = 'equilibrator'
        comments = ''

        response = self.client.post('/modify_reaction/' + reaction_acronym, data=dict(
            name=reaction_name,
            acronym=reaction_acronym,
            grasp_id=reaction_grasp_id,
            reaction_string=reaction_string,
            bigg_id=bigg_id,
            kegg_id=kegg_id,
            metanetx_id=metanetx_id,
            compartment=compartment,
            organism=organism,
            models=models,
            enzymes=enzymes,
            mechanism=mechanism,
            mechanism_references=mechanism_references,
            mechanism_evidence_level=mechanism_evidence_level,
            subs_binding_order=subs_binding_order,
            prod_release_order=prod_release_order,
            std_gibbs_energy=std_gibbs_energy,
            std_gibbs_energy_std=std_gibbs_energy_std,
            std_gibbs_energy_ph=std_gibbs_energy_ph,
            std_gibbs_energy_ionic_strength=std_gibbs_energy_ionic_strength,
            std_gibbs_energy_references=std_gibbs_energy_references,
            comments=comments), follow_redirects=True, query_string={'data_form': data_form})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'<title>\n    See reaction - Kinetics DB \n</title>' in response.data)
        self.assertTrue(b'Your reaction has been modified' in response.data)

        self.assertEqual(Reaction.query.count(), 1)
        self.assertEqual(reaction.enzyme_reaction_organisms.count(), 3)

        self.assertEqual(reaction.metabolites.count(), 3)
        self.assertEqual(reaction.gibbs_energy_reaction_models.count(), 2)

        self.assertEqual(reaction.name, reaction_name)
        self.assertEqual(reaction.acronym, reaction_acronym)
        self.assertEqual(reaction.metanetx_id, metanetx_id)
        self.assertEqual(reaction.bigg_id, bigg_id)
        self.assertEqual(reaction.kegg_id, kegg_id)
        self.assertEqual(reaction.compartment_name, compartment_name)

        gibbs_energy_id = reaction.gibbs_energy_reaction_models[0].gibbs_energy_id
        self.assertEqual(GibbsEnergy.query.filter_by(id=gibbs_energy_id).first().standard_dg, std_gibbs_energy)
        self.assertEqual(reaction.enzyme_reaction_organisms.all()[2].organism.name, organism_name)
        self.assertEqual(reaction.enzyme_reaction_organisms.all()[2].models[0].name, model_name)
        self.assertEqual(reaction.enzyme_reaction_organisms.all()[2].subs_binding_order, subs_binding_order)
        self.assertEqual(reaction.enzyme_reaction_organisms.all()[2].mechanism_references[0].doi,
                         'https://doi.org/10.1093/bioinformatics/bty9410')


if __name__ == '__main__':
    unittest.main(verbosity=2)
