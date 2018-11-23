from flask_wtf import FlaskForm
from wtforms import FloatField, IntegerField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import ValidationError, DataRequired, Length
from app.models import Compartment, Enzyme, EnzymeStructure, EvidenceLevel, Mechanism, Model, Organism, User
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from app.utils.parsers import parse_input_list


def get_models():
    models = Model.query.all()
    model_names = [model.name for model in models] if models else []
    return model_names

def get_compartments():
    compartments = Model.query.all()
    compartment_names = [compartment.name for compartment in compartments] if compartments else []
    return compartment_names

def get_mechanisms():
    mechanisms = Mechanism.query.all()
    mechanism_names = [mechanism.name for mechanism in mechanisms] if mechanisms else []
    return mechanism_names

def get_evidence_names():
    evidence_list = EvidenceLevel.query.all()
    evidence_names = [evidence.name for evidence in evidence_list] if evidence_list else []
    return evidence_names

def get_organism_names():
    return Organism.query

class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')

class PostForm(FlaskForm):
    post = TextAreaField('Say something', validators=[
        DataRequired(), Length(min=1, max=140)])
    submit = SubmitField('Submit')


class EnzymeForm(FlaskForm):
    name = StringField('Enzyme name (e.g. phosphofructokinase) *', validators=[DataRequired()])
    acronym = StringField('Enzyme acronym (eg. PFK) *', validators=[DataRequired()])
    isoenzyme = StringField('Isoenzyme (e.g. PFK1) *', validators=[DataRequired()])
    ec_number = StringField('EC number *', validators=[DataRequired()])

    organism_name = QuerySelectField('Organism name (eg. E coli)', query_factory=get_organism_names, allow_blank=True)
    number_of_active_sites = StringField('Number of enzyme subunits (you need to specify the organism first)')
    gene_bigg_ids = StringField('Encoding gene bigg IDs (you need to specify the organism first)', id='gene_bigg_ids')
    uniprot_id_list = StringField('Uniprod IDs (you need to specify the organism first) ')
    pdb_structure_ids = StringField('PDB structure IDs (you need to specify the organism first) (e.g. 3H8A, 1UCW)')
    strain = StringField('Strain for the PDB structure', id='strain')

    submit = SubmitField('Submit')
    """
    def validate_ec_number(self, ec_number):
        enzyme_db_list = Enzyme.query.filter(ec_number=ec_number.data).all()
        if enzyme_db_list:
            enzyme_db_list = [str((enzyme.ec_number, enzyme.acronym)) for enzyme in enzyme_db_list]
            raise ValidationError('An enzyme with the given EC number already exists in the database. Are you sure you want to continue\n' + '\n'.join(enzyme_db_list))
    """

    def validate_isoenzyme(self, isoenzyme):
        enzyme_list = Enzyme.query.all()
        isoenzyme_list = set([enzyme.isoenzyme for enzyme in enzyme_list]) if enzyme_list else {}
        if isoenzyme.data in isoenzyme_list:
            raise ValidationError('The isoenzyme you specified already exists. Please choose a different name.')

    def validate_organism_name(self, organism_name):
        organism_list = Organism.query.all()
        if not organism_list:
            raise ValidationError('No organisms have been introduced in the database. You should first introduce it.')

    def validate_number_of_active_sites(self, number_of_active_sites):
        if number_of_active_sites.data  and not self.organism_name.data :
            raise ValidationError('If you specify the number of active sites you must also specify the organism name')

    def validate_gene_bigg_ids(self, gene_bigg_ids):
        if gene_bigg_ids.data and not self.organism_name.data:
            raise ValidationError('If you specify encoding genes you must also specify the organism name')

    def validate_uniprot_id_list(self, uniprot_id_list):
        if uniprot_id_list.data and not self.organism_name.data:
            raise ValidationError('If you specify uniprot IDs you must also specify the organism name')

    def validate_pdb_structure_ids(self, pdb_structure_ids):
        if pdb_structure_ids.data and not self.organism_name.data:
            raise ValidationError('If you specify PDB structures you must also specify the organism name')

    def validate_strain(self, strain):
        strain_list = parse_input_list(strain.data)
        pdb_id_list = parse_input_list(self.pdb_structure_ids.data)
        if len(strain_list) > 1 and len(pdb_id_list) and len(strain_list) != len(pdb_id_list):
            raise ValidationError('When providing PDB IDs either provide:\n-the corresponding strains for each PDB ID;\n-a single strain name\n-or no strain names.')


class GeneForm(FlaskForm):
    name = StringField('Gene name (e.g. pfkA) *', validators=[DataRequired()])
    bigg_id = StringField('Bigg ID (eg. pfkA)')
    organism = QuerySelectField('Organism name (eg. E coli)', query_factory=get_organism_names)

    submit = SubmitField('Submit')


class ModelForm(FlaskForm):
    name = StringField('Model name (e.g. E coli - iteration 1) *', validators=[DataRequired()])
    organism_name = StringField('Organism name (eg. E coli) *', validators=[DataRequired()], id='organism_name')
    strain = StringField('Organism strain (e.g. MG1655)')
    comments = TextAreaField('Comments')

    submit = SubmitField('Submit')

    def validate_name(self, name):
        model_db = Model.query.filter_by(name=name.data).first()
        if model_db:
            raise ValidationError('A model with that name already exists, please use another name')



class OrganismForm(FlaskForm):
    name = StringField('Organism name (e.g. E coli)', validators=[DataRequired()])

    def validate_name(self, name):
        organism_db = Organism.query.filter_by(name=name.data).first()
        if organism_db:
            raise ValidationError('An organism with that name already exists, please use another name')



    submit = SubmitField('Submit')

"""
class ReactionForm(FlaskForm):

    name = StringField('Reaction name (e.g. Phosphofructokinase)', validators=[DataRequired()])
    acronym = StringField('Reaction acronym (e.g. PFK)', validators=[DataRequired()])
    grasp_id = StringField('GRASP ID (e.g. PFK1)', validators=[DataRequired()])
    reaction_string = StringField('Reaction string, use either Bigg IDs or Chebi IDs (e.g. 1 pep_c + 1.5 adp_c <-> 1 pyr_c + 2.0 atp_m)', validators=[DataRequired()])
    metanetx_id = StringField('Organism name (e.g. E coli)')
    bigg_id = StringField('Organism name (e.g. E coli)')
    kegg_id = StringField('Organism name (e.g. E coli)')
    compartment_name = QuerySelectField('Compartment name', query_factory=get_compartments)
    model_name = QuerySelectField('Model name' , query_factory=get_models)
    enzymes = StringField('Enzymes that catalyze the reaction (e.g. PFK1, PFK2)', id='inputOne')
    mechanism = QuerySelectField('Reaction mechanism name', query_factory=get_mechanisms)
    mechanism_references = SelectField('DOI for mechanism references (e.g. https://doi.org/10.1093/bioinformatics/bty942, http://doi.org/10.5334/jors.236) ')
    mechanism_evidence_level = QuerySelectField('Reaction mechanism evidence level', query_factory=get_evidence_names)
    subs_binding_order = StringField('Substrate binding order (e.g. adp_c, pep_c)')
    prod_release_order = StringField('Substrate binding order (e.g. atp_c, pyr_c)')
    std_gibbs_energy = FloatField('Standard Gibbs energy (in kJ/mol)')
    std_gibbs_energy_std = FloatField('Standard Gibbs energy standard deviation(in kJ/mol)')
    std_gibbs_energy_ph = FloatField('pH for Gibbs energy')
    std_gibbs_energy_ionic_strength = FloatField('Ionic strength for Gibbs energy')
    std_gibbs_energy_references = StringField('Reference for Gibbs energy (if it is equilibrator just type equilibrator, otherwise use DOI, https://doi.org/10.1093/bioinformatics/bty942, http://doi.org/10.5334/jors.236')

    submit = SubmitField('Submit')
"""