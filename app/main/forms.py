from flask_wtf import FlaskForm
from wtforms import FloatField, IntegerField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import ValidationError, DataRequired, Length, Optional
from app.models import Compartment, Enzyme, EnzymeStructure, EvidenceLevel, Mechanism, Model, Organism, Reaction, User
from wtforms.ext.sqlalchemy.fields import QuerySelectField, QuerySelectMultipleField
from app.utils.parsers import parse_input_list, ReactionParser
import re


def get_compartments():
    return Compartment.query


def get_enzymes():
    return Enzyme.query


def get_evidence_names():
    return EvidenceLevel.query


def get_reactions():
    return Reaction.query


def get_mechanisms():
    return Mechanism.query


def get_models():
    return Model.query


def get_organisms():
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
    acronym = StringField('Enzyme bigg_acronym (eg. PFK) *', validators=[DataRequired()])
    isoenzyme = StringField('Isoenzyme (e.g. PFK1) *', validators=[DataRequired()])
    ec_number = StringField('EC number *', validators=[DataRequired()])

    organism_name = QuerySelectField('Organism name (eg. E coli)', query_factory=get_organisms, allow_blank=True)
    number_of_active_sites = IntegerField('Number of enzyme subunits (you need to specify the organism first)', validators=[Optional()])
    gene_names = StringField('Encoding gene bigg IDs (you need to specify the organism first)', id='gene_bigg_ids')
    uniprot_id_list = StringField('Uniprod IDs (you need to specify the organism first) ')
    pdb_structure_ids = StringField('PDB structure IDs (you need to specify the organism first) (e.g. 3H8A, 1UCW)')
    strain = StringField('Strain for the PDB structure', id='strain')

    submit = SubmitField('Submit')

    def validate_isoenzyme(self, isoenzyme):
        enzyme_list = Enzyme.query.all()
        isoenzyme_list = set([enzyme.isoenzyme for enzyme in enzyme_list]) if enzyme_list else {}
        if isoenzyme.data in isoenzyme_list:
            raise ValidationError('The isoenzyme you specified already exists. Please choose a different name.')

    def validate_number_of_active_sites(self, number_of_active_sites):
        if number_of_active_sites.data  and not self.organism_name.data :
            raise ValidationError('If you specify the number of active sites you must also specify the organism name.')

    def validate_gene_names(self, gene_names):
        if gene_names.data and not self.organism_name.data:
            raise ValidationError('If you specify encoding genes you must also specify the organism name.')

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


class EnzymeInhibitionForm(FlaskForm):

    enzyme = QuerySelectField('Isoenzyme *', query_factory=get_enzymes)
    reaction = QuerySelectField('Reaction *', query_factory=get_reactions)
    organism = QuerySelectField('Organism *', query_factory=get_organisms)
    models = QuerySelectMultipleField('Model', query_factory=get_models)
    inhibitor_met = StringField('Inhibiting metabolite (e.g. adp), please use bigg IDs *', validators=[DataRequired()], id='metabolite_list')
    affected_met = StringField('Affected metabolite (e.g. atp), please use bigg IDs', id='metabolite_list')
    inhibition_type = SelectField('Inhibition type', choices=[('Unknown', 'Unknown'), ('Competitive', 'Competitive'),
                                                              ('Uncompetitive', 'Uncompetitive'),
                                                              ('Noncompetitive', 'Noncompetitive'),
                                                              ('Mixed', 'Mixed')])
    inhibition_constant = FloatField('Inhibition constant (in M)', validators=[Optional()])
    inhibition_evidence_level = QuerySelectField('Enzyme inhibition evidence level', query_factory=get_evidence_names, allow_blank=True)
    references = StringField('References, please use DOI (e.g. https://doi.org/10.1093/bioinformatics/bty942, http://doi.org/10.5334/jors.236)')
    comments = TextAreaField('Comments')

    submit = SubmitField('Submit')


class EnzymeActivationForm(FlaskForm):

    enzyme = QuerySelectField('Isoenzyme *', query_factory=get_enzymes, validators=[DataRequired()])
    reaction = QuerySelectField('Reaction *', query_factory=get_reactions, validators=[DataRequired()])
    organism = QuerySelectField('Organism *', query_factory=get_organisms)
    models = QuerySelectMultipleField('Model', query_factory=get_models)
    activator_met = StringField('Activating metabolite (e.g. adp), please use bigg IDs *', validators=[DataRequired()], id='metabolite_list')
    activation_constant = FloatField('Activation constant (in M)', validators=[Optional()])
    activation_evidence_level = QuerySelectField('Activation inhibition evidence level', query_factory=get_evidence_names, allow_blank=True)
    references = StringField('References, please use DOI (e.g. https://doi.org/10.1093/bioinformatics/bty942, http://doi.org/10.5334/jors.236)')
    comments = TextAreaField('Comments')

    submit = SubmitField('Submit')


class EnzymeEffectorForm(FlaskForm):

    enzyme = QuerySelectField('Isoenzyme *', query_factory=get_enzymes, validators=[DataRequired()])
    reaction = QuerySelectField('Reaction *', query_factory=get_reactions, validators=[DataRequired()])
    organism = QuerySelectField('Organism *', query_factory=get_organisms)
    models = QuerySelectMultipleField('Model', query_factory=get_models)
    effector_met = StringField('Effector metabolite (e.g. adp), please use bigg IDs *', validators=[DataRequired()], id='metabolite_list')
    effector_type = SelectField('Effector type',  choices=[('Activating', 'Activating'), ('Inhibiting', 'Inhibiting')])
    effector_evidence_level = QuerySelectField('Effector evidence level', query_factory=get_evidence_names, allow_blank=True)
    references = StringField('References, please use DOI (e.g. https://doi.org/10.1093/bioinformatics/bty942, http://doi.org/10.5334/jors.236)')
    comments = TextAreaField('Comments')

    submit = SubmitField('Submit')


class EnzymeMiscInfoForm(FlaskForm):

    enzyme = QuerySelectField('Isoenzyme *', query_factory=get_enzymes, validators=[DataRequired()])
    reaction = QuerySelectField('Reaction *', query_factory=get_reactions, validators=[DataRequired()])
    organism = QuerySelectField('Organism *', query_factory=get_organisms)
    models = QuerySelectMultipleField('Model', query_factory=get_models)
    topic = StringField('Topic (e.g. allostery) *', validators=[DataRequired()])
    description = TextAreaField('Description *',  validators=[DataRequired()])
    evidence_level = QuerySelectField('Evidence level', query_factory=get_evidence_names, allow_blank=True)
    references = StringField('References, please use DOI (e.g. https://doi.org/10.1093/bioinformatics/bty942, http://doi.org/10.5334/jors.236)')
    comments = TextAreaField('Comments')

    submit = SubmitField('Submit')


class GeneForm(FlaskForm):
    name = StringField('Gene name (e.g. pfkA) *', validators=[DataRequired()])
    organism = QuerySelectField('Organism name (eg. E coli)', query_factory=get_organisms)

    submit = SubmitField('Submit')


class ModelAssumptionsForm(FlaskForm):

    model = QuerySelectField('Model *', query_factory=get_models)
    assumption = StringField('Assumption *', validators=[DataRequired()])
    description = TextAreaField('Description *',  validators=[DataRequired()])
    evidence_level = QuerySelectField('Evidence level', query_factory=get_evidence_names, allow_blank=True)
    included_in_model = SelectField('Is this assumption included in the model?', choices=[('True', 'True'), ('False', 'False')])
    references = StringField('References, please use DOI (e.g. https://doi.org/10.1093/bioinformatics/bty942, http://doi.org/10.5334/jors.236)')
    comments = TextAreaField('Comments')

    submit = SubmitField('Submit')


class ModelForm(FlaskForm):
    name = StringField('Model name (e.g. E coli - iteration 1) *', validators=[DataRequired()])
    organism_name = StringField('Organism name (e.g. E coli) *', validators=[DataRequired()], id='organism_name')
    strain = StringField('Organism strain (e.g. MG1655)')
    comments = TextAreaField('Comments')

    submit = SubmitField('Submit')

    def validate_name(self, name):
        model_db = Model.query.filter_by(name=name.data).first()
        if model_db:
            raise ValidationError('A model with that name already exists, please use another name')


class OrganismForm(FlaskForm):
    name = StringField('Organism name (e.g. E coli) *', validators=[DataRequired()])

    submit = SubmitField('Submit')

    def validate_name(self, name):
        organism_db = Organism.query.filter_by(name=name.data).first()
        if organism_db:
            raise ValidationError('An organism with that name already exists, please use another name')


class ReactionForm(FlaskForm):

    name = StringField('Reaction name (e.g. phosphofructokinase) *', validators=[DataRequired()])
    acronym = StringField('Reaction bigg_acronym (e.g. PFK) *', validators=[DataRequired()])
    grasp_id = StringField('GRASP ID (e.g. PFK1) *', validators=[DataRequired()])
    reaction_string = StringField('Reaction string, use either Bigg IDs or Chebi IDs (e.g. 1 pep_c + 1.5 adp_c <-> 1 pyr_c + 2.0 atp_m) *', validators=[DataRequired()])
    metanetx_id = StringField('Metanetx ID')
    bigg_id = StringField('Bigg ID')
    kegg_id = StringField('Kegg ID')

    compartment = QuerySelectField('Compartment name', query_factory=get_compartments, allow_blank=True)
    organism = QuerySelectField('Organism name *' , query_factory=get_organisms)
    models = QuerySelectMultipleField('Model name' , query_factory=get_models)
    enzymes = QuerySelectMultipleField('Isoenzyme(s) that catalyze the reaction (e.g. PFK1, PFK2) *', query_factory=get_enzymes, validators=[DataRequired()])

    mechanism = QuerySelectField('Enzyme mechanism name (if you add the mechanism, you also need to add the isoenzyme(s) that catalyze the reaction)', query_factory=get_mechanisms, allow_blank=True)
    mechanism_references = StringField('DOI for mechanism references (e.g. https://doi.org/10.1093/bioinformatics/bty942, http://doi.org/10.5334/jors.236) ')
    mechanism_evidence_level = QuerySelectField('Enzyme mechanism evidence level', query_factory=get_evidence_names, allow_blank=True)
    subs_binding_order = StringField('Substrate binding order (e.g. adp_c, pep_c)')
    prod_release_order = StringField('Product release order (e.g. atp_c, pyr_c)')

    std_gibbs_energy = FloatField('Standard Gibbs energy (in kJ/mol)', validators=[Optional()])
    std_gibbs_energy_std = FloatField('Standard Gibbs energy standard deviation(in kJ/mol)', validators=[Optional()])
    std_gibbs_energy_ph = FloatField('pH for Gibbs energy', validators=[Optional()])
    std_gibbs_energy_ionic_strength = FloatField('Ionic strength for Gibbs energy', validators=[Optional()])
    std_gibbs_energy_references = StringField('Reference for Gibbs energy (if it is equilibrator just type equilibrator, otherwise use DOI, https://doi.org/10.1093/bioinformatics/bty942, http://doi.org/10.5334/jors.236')

    comments = TextAreaField('Comments')

    submit = SubmitField('Submit')

    def validate_reaction_string(self, reaction_string):
        reversible, stoichiometry = ReactionParser().parse_reaction(reaction_string.data)
        # (True, OrderedDict([('m_pep_c', -1.0), ('m_adp_c', -1.5), ('m_pyr_c', 1.0), ('m_atp_m', 2.0)]))

        for met, stoich_coef in stoichiometry.items():
            met_compartment = re.findall('(\w+)_(\w+)', met)

            if not met_compartment:
                raise ValidationError('Please specify the metabolite' + met + 'as metabolite_compartmentAcronym, e.g. adp_c.')

            compartment_db = Compartment.query.filter_by(bigg_id=met_compartment[0][1]).first()
            if not compartment_db:
                raise ValidationError('The specified compartment bigg_acronym' + met_compartment[0][1] + ' is not part of the database, please insert it first.')

    def validate_mechanism(self, mechanism):
        if mechanism.data and not self.enzymes.data:
            raise ValidationError('If you add a reaction mechanism, you need to specify the catalyzing isoenzyme(s).')


    def validate_mechanism_evidence_level(self, mechanism_evidence_level):
        if mechanism_evidence_level.data  and not self.mechanism.data :
            raise ValidationError('You cannot specify evidence level for the mechanism without specifying a mechanism.')


    def validate_subs_binding_order(self, subs_binding_order):
        if subs_binding_order.data and not self.enzymes.data:
            raise ValidationError('If you add substrate binding order without specifying the catalyzing isoenzyme(s).')

        substrate_list = parse_input_list(subs_binding_order.data)
        for substrate in substrate_list:
            if self.reaction_string.data.find(substrate) == -1:
                raise ValidationError('The metabolite'+ substrate + 'does not match any metabolite in' + self.reaction_string.data + '.')


    def validate_prod_release_order(self, prod_release_order):
        if prod_release_order.data and not self.enzymes.data:
            raise ValidationError('If you add product release order without specifying the catalyzing isoenzyme(s).')

        product_list = parse_input_list(prod_release_order.data)
        for product in product_list:
            if self.reaction_string.data.find(product) == -1:
                raise ValidationError('The metabolite' + product + 'does not match any metabolite in' + self.reaction_string.data + '.')


    def validate_std_gibbs_energy_std(self, std_gibbs_energy_std):
        if not self.models.data:
            raise ValidationError('Gibbs energies cannot be added to reactions alone, a model must be associated as well. Please add model name. ')

        if std_gibbs_energy_std.data  and not self.std_gibbs_energy.data :
            raise ValidationError('Please specify the standard Gibbs energy as well.')


    def validate_std_gibbs_energy_ph(self, std_gibbs_energy_ph):
        if std_gibbs_energy_ph.data  and not self.std_gibbs_energy.data :
            raise ValidationError('Please specify the standard Gibbs energy as well.')


    def validate_std_gibbs_energy_ionic_strength(self, std_gibbs_energy_ionic_strength):
        if std_gibbs_energy_ionic_strength.data  and not self.std_gibbs_energy.data :
            raise ValidationError('Please specify the standard Gibbs energy as well.')


    def validate_std_gibbs_energy_references(self, std_gibbs_energy_references):
        if self.std_gibbs_energy.data and not std_gibbs_energy_references.data:
            raise ValidationError('Please specify the reference for the above standard Gibbs energy.')

        if std_gibbs_energy_references.data  and not self.std_gibbs_energy.data :
            raise ValidationError('Please specify the standard Gibbs energy as well.')


class ModifyData(FlaskForm):
    submit = SubmitField('Modify')


from flask_wtf import FlaskForm
from wtforms import StringField, SelectMultipleField
from wtforms.widgets import ListWidget, CheckboxInput
from wtforms.validators import Required

class MultiCheckboxField(SelectMultipleField):
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()


class FormProject(FlaskForm):
    Code = StringField('Code', [Required(message='Please enter your code')])
    Tasks = MultiCheckboxField('Proses', [Required(message='Please tick your task')], choices=[('nyapu','Nyapu'), ('ngepel','Ngepel')])