from app.main.forms import  EnzymeForm, EnzymeActivationForm, EnzymeEffectorForm, EnzymeInhibitionForm, EnzymeMiscInfoForm, GeneForm, ModelAssumptionsForm, ModelForm, OrganismForm, ReactionForm, ModelFormBase
from flask import render_template, flash, redirect, url_for
from flask_login import login_required
from app import current_app, db
from app.models import Compartment, Enzyme,EnzymeGeneOrganism,  EnzymeReactionOrganism, EnzymeReactionActivation, \
    EnzymeReactionEffector, EnzymeReactionInhibition, EnzymeReactionMiscInfo, EnzymeOrganism, EnzymeStructure, \
    EvidenceLevel, Gene,GibbsEnergy, GibbsEnergyReactionModel, Mechanism, Metabolite, Model, ModelAssumptions, \
    Organism, Reaction, ReactionMetabolite, Reference
from app.main.routes_modify_data import modify_model
from app.main import bp
from app.utils.parsers import ReactionParser, parse_input_list
import re


def _add_enzyme_organism(enzyme, organism_id, uniprot_id_list, number_of_active_sites):
    for uniprot_id in uniprot_id_list:
        enzyme_organism_db = EnzymeOrganism.query.filter_by(uniprot_id=uniprot_id).first()
        if not enzyme_organism_db:
            enzyme_organism_db = EnzymeOrganism(enzyme_id=enzyme.id,
                                                organism_id=organism_id,
                                                uniprot_id=uniprot_id,
                                                n_active_sites=number_of_active_sites)
            db.session.add(enzyme_organism_db)
        enzyme.add_enzyme_organism(enzyme_organism_db)


def _add_genes(gene_names, enzyme, organism_id):
        # populate genes
        if gene_names:
            gene_bigg_ids_list = parse_input_list(gene_names)
            for gene_name in gene_bigg_ids_list:
                gene_db = Gene.query.filter_by(name=gene_name).first()
                if not gene_db:
                    gene_db = Gene(name=gene_name)
                    db.session.add(gene_db)
                    db.session.commit()

                enzyme_gene_organism_db = EnzymeGeneOrganism.query.filter_by(gene_id=gene_db.id,
                                                                             enzyme_id=enzyme.id,
                                                                             organism_id=organism_id).first()
                if not enzyme_gene_organism_db:
                    enzyme_gene_organism = EnzymeGeneOrganism(gene_id=gene_db.id,
                                                              enzyme_id=enzyme.id,
                                                              organism_id=organism_id)
                    db.session.add(enzyme_gene_organism)


def _add_enzyme_structures(enzyme, organism_id, pdb_id_list, strain_list):

    if len(strain_list) == 1 and len(pdb_id_list) > 1:
        pdb_id_strain_list = zip(pdb_id_list, [strain_list[0] for i in range(len(pdb_id_list))])
    elif len(strain_list) == 0 and len(pdb_id_list) > 1:
        pdb_id_strain_list = zip(pdb_id_list, ['' for i in range(len(pdb_id_list))])
    elif len(strain_list) == len(pdb_id_list):
        pdb_id_strain_list = zip(pdb_id_list, strain_list)

    for pdb_id, pdb_id_strain in pdb_id_strain_list:
        enzyme_structure_db = EnzymeStructure.query.filter_by(pdb_id=pdb_id).first()
        if not enzyme_structure_db:
            enzyme_structure_db = EnzymeStructure(enzyme_id=enzyme.id,
                                                  pdb_id=pdb_id,
                                                  organism_id=organism_id,
                                                  strain=pdb_id_strain)
            db.session.add(enzyme_structure_db)

        #enzyme.add_structure(enzyme_structure_db)


@bp.route('/add_enzyme', methods=['GET', 'POST'])
@login_required
def add_enzyme():
    form = EnzymeForm()

    genes = Gene.query.all()
    gene_bigg_ids = {'id_value': '#gene_bigg_ids', 'input_data': [{'field1': gene.name} for gene in genes] if genes else []}

    enzyme_structures = EnzymeStructure.query.all()
    enzyme_structure_strains = set([enzyme_structure.strain for enzyme_structure in enzyme_structures]) if enzyme_structures else []
    strain = {'id_value': '#strain', 'input_data': [{'field1': strain} for strain in
              enzyme_structure_strains] if enzyme_structures else []}

    data_list = [gene_bigg_ids, strain]

    if form.validate_on_submit():

        enzyme_db_list = Enzyme.query.filter_by(ec_number=form.ec_number.data).all()
        if enzyme_db_list:
            enzyme_db_list = [str((enzyme.ec_number, enzyme.acronym)) for enzyme in enzyme_db_list]
            flash(
                'An enzyme with the given EC number already exists in the database. Are you sure you want to continue\n' + '\n'.join(
                    enzyme_db_list), 'warning')

        enzyme = Enzyme(name=form.name.data,
                        acronym=form.acronym.data,
                        isoenzyme=form.isoenzyme.data,
                        ec_number=form.ec_number.data)
        db.session.add(enzyme)

        if form.organism_name.data:
            organism_db = Organism.query.filter_by(name=form.organism_name.data.name).first()
            organism_id = organism_db.id

            if form.gene_names.data:
                _add_genes(form.gene_names.data, enzyme, organism_id)

            # populate enzyme_structure
            if form.pdb_structure_ids.data:
                pdb_id_list = parse_input_list(form.pdb_structure_ids.data)
                strain_list = parse_input_list(form.strain.data)
                _add_enzyme_structures(enzyme, organism_id, pdb_id_list, strain_list)

            # populate enzyme_organism
            if form.uniprot_id_list.data:
                uniprot_id_list = parse_input_list(form.uniprot_id_list.data)
                _add_enzyme_organism(enzyme, organism_id, uniprot_id_list, form.number_of_active_sites.data)




        db.session.commit()
        flash('Your enzyme is now live!')
        return redirect(url_for('main.see_enzyme_list'))
    return render_template('insert_data.html', title='Add enzyme', form=form, header='Add enzyme', data_list=data_list)



def _check_metabolite(bigg_id):
    met_db = Metabolite.query.filter_by(bigg_id=bigg_id).first()
    if not met_db:
        met_db = Metabolite(bigg_id=bigg_id,
                            grasp_id=bigg_id)
        db.session.add(met_db)

    return met_db


def _add_references(references):
    reference_list = parse_input_list(references)
    ref_db_list = []
    for reference in reference_list:
        ref_db = Reference.query.filter_by(doi=reference).first()
        if not ref_db:
            ref_db = Reference(doi=reference)
        ref_db_list.append(ref_db)

    return ref_db_list


@bp.route('/add_enzyme_inhibition', methods=['GET', 'POST'])
@login_required
def add_enzyme_inhibition():

    form = EnzymeInhibitionForm()

    metabolites = Metabolite.query.all()
    metabolite_list = {'id_value': '#metabolite_list', 'input_data': [{'field1': metabolite.bigg_id} for metabolite in metabolites] if metabolites else []}
    data_list = [metabolite_list]

    if form.validate_on_submit():

        inhib_met = _check_metabolite(form.inhibitor_met.data)
        affected_met = _check_metabolite(form.affected_met.data)
        inhibition_evidence_level_id = form.inhibition_evidence_level.data.id if form.inhibition_evidence_level.data else None


        enz_rxn_org = EnzymeReactionOrganism.query.filter_by(enzyme_id=form.enzyme.data.id,
                                                             reaction_id=form.reaction.data.id,
                                                             organism_id=form.organism.data.id).first()

        enz_rxn_inhib = EnzymeReactionInhibition(enz_rxn_org_id=enz_rxn_org.id,
                                                 inhibitor_met_id=inhib_met.id,
                                                 affected_met_id=affected_met.id,
                                                 inhibition_constant=form.inhibition_constant.data,
                                                 inhibition_type=form.inhibition_type.data,
                                                 evidence_level_id=inhibition_evidence_level_id,
                                                 comments=form.comments.data)
        db.session.add(enz_rxn_inhib)

        if form.models.data:
            for model in form.models.data:
                enz_rxn_inhib.add_model(model)

        if form.references.data:
            ref_db_list = _add_references(form.references.data)
            for ref_db in ref_db_list:
                enz_rxn_inhib.add_reference(ref_db)

        db.session.commit()


        flash('Your enzyme inhibition is now live!', 'success')

        return redirect(url_for('main.see_enzyme_list'))
    return render_template('insert_data.html', title='Add enzyme inhibition', form=form, header='Add enzyme inhibition', data_list=data_list)


@bp.route('/add_enzyme_activation', methods=['GET', 'POST'])
@login_required
def add_enzyme_activation():

    form = EnzymeActivationForm()

    metabolites = Metabolite.query.all()
    metabolite_list = {'id_value': '#metabolite_list', 'input_data': [{'field1': metabolite.bigg_id} for metabolite in metabolites] if metabolites else []}
    data_list = [metabolite_list]

    """
      isoenzyme = QuerySelectField('Isoenzyme *', query_factory=get_enzymes, validators=[DataRequired()])
    reaction = QuerySelectField('Reaction *', query_factory=get_reactions, validators=[DataRequired()])
    organism = QuerySelectField('Organism *', query_factory=get_organisms)
    models = QuerySelectMultipleField('Model', query_factory=get_models)
    activator_met = StringField('Activating metabolite (e.g. adp), please use bigg IDs *', validators=[DataRequired()], id='metabolite_list')
    activation_constant = FloatField('Activation constant (in M)', validators=[Optional()])
    activation_evidence_level = QuerySelectField('Activation inhibition evidence level', query_factory=get_evidence_names, allow_blank=True)
    references = StringField('References, please use DOI (e.g. https://doi.org/10.1093/bioinformatics/bty942, http://doi.org/10.5334/jors.236)')
    comments = TextAreaField('Comments')"""
    if form.validate_on_submit():

        activator_met = _check_metabolite(form.activator_met.data)
        activation_evidence_level_id = form.activation_evidence_level.data.id if form.activation_evidence_level.data else None


        enz_rxn_org = EnzymeReactionOrganism.query.filter_by(enzyme_id = form.enzyme.data.id,
                                                             reaction_id=form.reaction.data.id,
                                                             organism_id=form.organism.data.id).first()

        enz_rxn_activation = EnzymeReactionActivation(enz_rxn_org_id=enz_rxn_org.id,
                                                     activator_met_id=activator_met.id,
                                                     activation_constant=form.activation_constant.data,
                                                     evidence_level_id = activation_evidence_level_id,
                                                     comments=form.comments.data)
        db.session.add(enz_rxn_activation)

        if form.models.data:
            for model in form.models.data:
                enz_rxn_activation.add_model(model)

        if form.references.data:
            ref_db_list = _add_references(form.references.data)
            for ref_db in ref_db_list:
                enz_rxn_activation.add_reference(ref_db)

        db.session.commit()

        flash('Your enzyme activation is now live!', 'success')

        return redirect(url_for('main.see_enzyme_list'))
    return render_template('insert_data.html', title='Add enzyme activation', form=form, header='Add enzyme activation', data_list=data_list)


@bp.route('/add_enzyme_effector', methods=['GET', 'POST'])
@login_required
def add_enzyme_effector():

    form = EnzymeEffectorForm()

    metabolites = Metabolite.query.all()
    metabolite_list = {'id_value': '#metabolite_list', 'input_data': [{'field1': metabolite.bigg_id} for metabolite in metabolites] if metabolites else []}
    data_list = [metabolite_list]

    if form.validate_on_submit():
        effector_met = _check_metabolite(form.effector_met.data)
        effector_evidence_level_id = form.effector_evidence_level.data.id if form.effector_evidence_level.data else None

        enz_rxn_org = EnzymeReactionOrganism.query.filter_by(enzyme_id = form.enzyme.data.id,
                                                             reaction_id=form.reaction.data.id,
                                                             organism_id=form.organism.data.id).first()

        enz_rxn_effector = EnzymeReactionEffector(enz_rxn_org_id=enz_rxn_org.id,
                                                     effector_met_id=effector_met.id,
                                                     effector_type=form.effector_type.data,
                                                     evidence_level_id = effector_evidence_level_id,
                                                     comments=form.comments.data)
        db.session.add(enz_rxn_effector)

        if form.models.data:
            for model in form.models.data:
                enz_rxn_effector.add_model(model)

        if form.references.data:
            ref_db_list = _add_references(form.references.data)
            for ref_db in ref_db_list:
                enz_rxn_effector.add_reference(ref_db)

        db.session.commit()
        flash('Your enzyme effector is now live!', 'success')

        return redirect(url_for('main.see_enzyme_list'))
    return render_template('insert_data.html', title='Add enzyme effector', form=form, header='Add enzyme effector', data_list=data_list)


@bp.route('/add_enzyme_misc_info', methods=['GET', 'POST'])
@login_required
def add_enzyme_misc_info():

    form = EnzymeMiscInfoForm()

    if form.validate_on_submit():

        evidence_level_id = form.evidence_level.data.id if form.evidence_level.data else None

        enz_rxn_org = EnzymeReactionOrganism.query.filter_by(enzyme_id = form.enzyme.data.id,
                                                             reaction_id=form.reaction.data.id,
                                                             organism_id=form.organism.data.id).first()

        enz_rxn_misc_info = EnzymeReactionMiscInfo(enz_rxn_org_id=enz_rxn_org.id,
                                                     topic=form.topic.data,
                                                     description=form.description.data,
                                                     evidence_level_id = evidence_level_id,
                                                     comments=form.comments.data)
        db.session.add(enz_rxn_misc_info)

        if form.models.data:
            for model in form.models.data:
                enz_rxn_misc_info.add_model(model)

        if form.references.data:
            ref_db_list = _add_references(form.references.data)
            for ref_db in ref_db_list:
                enz_rxn_misc_info.add_reference(ref_db)

        db.session.commit()

        flash('Your enzyme misc info is now live!', 'success')

        return redirect(url_for('main.see_enzyme_list'))
    return render_template('insert_data.html', title='Add enzyme misc info', form=form, header='Add enzyme misc info')


@bp.route('/add_gene', methods=['GET', 'POST'])
@login_required
def add_gene():
    form = GeneForm()

    if form.validate_on_submit():
        gene = Gene(name=form.name.data)

        db.session.add(gene)

        db.session.commit()

        flash('Your enzyme is now live!')
        return redirect(url_for('main.see_enzyme_list'))
    return render_template('insert_data.html', title='Add gene', form=form, header='Add gene')


@bp.route('/add_model', methods=['GET', 'POST'])
@login_required
def add_model():

    text = 'If you want to build a model from an existing one, please select the desired model. Otherwise press "Continue".'

    form_base = ModelFormBase()

    if form_base.validate_on_submit():

        if form_base.model_base.data:
            return redirect(url_for('main.modify_model', model_name=form_base.model_base.data.name))

        else:
            organisms = Organism.query.all()
            organism_name = {'id_value': '#organism_name', 'input_data': [{'field1': organism.name} for organism in organisms] if organisms else []}
            data_list = [organism_name]

            form = ModelForm()

            if form.validate_on_submit():

                organism = Organism.query.filter_by(name=form.organism_name.data).first()
                if not organism:
                    organism = Organism(name=form.organism_name.data)
                    db.session.add(organism)

                model = Model(name=form.name.data,
                              organism_name=form.organism_name.data,
                              strain=form.strain.data,
                              comments=form.comments.data)

                db.session.add(model)
                db.session.commit()

                if form.enz_rxn_orgs.data:
                    for enz_rxn_org in form.enz_rxn_orgs.data:
                        model.add_enzyme_reaction_organism(enz_rxn_org)

                db.session.commit()

                flash('Your model is now live!')
                return redirect(url_for('main.see_model_list'))

            return render_template('insert_data.html', title='Add model', form=form, header='Add model',
                                   data_list=data_list)

    return render_template('insert_data.html', title='Add model', form=form_base, header='Add model', text=text)


@bp.route('/add_model_assumption', methods=['GET', 'POST'])
@login_required
def add_model_assumption():

    form = ModelAssumptionsForm()

    if form.validate_on_submit():

        evidence_level_id = form.evidence_level.data.id if form.evidence_level.data else None
        included_in_model = True if form.included_in_model.data == 'True' else False

        model_assumption = ModelAssumptions(model_id=form.model.data.id,
                                             assumption=form.assumption.data,
                                             description=form.description.data,
                                             evidence_level_id=evidence_level_id,
                                             #included_in_model=form.included_in_model.data,
                                             included_in_model=included_in_model,
                                             comments=form.comments.data)
        db.session.add(model_assumption)

        if form.references.data:
            ref_db_list = _add_references(form.references.data)
            for ref_db in ref_db_list:
                model_assumption.add_reference(ref_db)

        db.session.commit()

        flash('Your model assumption is now live!', 'success')

        return redirect(url_for('main.see_model_list'))
    return render_template('insert_data.html', title='Add model assumption', form=form, header='Add model assumption')


@bp.route('/add_organism', methods=['GET', 'POST'])
@login_required
def add_organism():
    form = OrganismForm()

    if form.validate_on_submit():
        organism = Organism(name=form.name.data)
        db.session.add(organism)
        db.session.commit()

        flash('Your organism is now live!', 'success')

        return redirect(url_for('main.see_organism_list'))
    return render_template('insert_data.html', title='Add organism', form=form, header='Add organism')


def _add_metabolites_to_reaction(reaction, reaction_string):

    reversible, stoichiometry = ReactionParser().parse_reaction(reaction_string)
    # (True, OrderedDict([('m_pep_c', -1.0), ('m_adp_c', -1.5), ('m_pyr_c', 1.0), ('m_atp_m', 2.0)]))

    for met, stoich_coef in stoichiometry.items():
        met_compartment = re.findall('(\w+)_(\w+)', met)[0]

        bigg_id = met_compartment[0]
        met_db = Metabolite.query.filter_by(bigg_id=bigg_id).first()

        compartment_acronym = met_compartment[1]

        if not met_db:
            met_db = Metabolite(bigg_id=bigg_id,
                                grasp_id=bigg_id)
            db.session.add(met_db)

        compartment_db = Compartment.query.filter_by(bigg_id=compartment_acronym).first()
        met_db.add_compartment(compartment_db)

        reaction.add_metabolite(met_db, stoich_coef, compartment_db)

    return reaction


def _add_gibbs_energy(reaction_id, model_id, standard_dg, standard_dg_std, standard_dg_ph, standard_dg_is, std_gibbs_energy_references):

    gibbs_energy_db = GibbsEnergy.query.filter_by(standard_dg=standard_dg,
                                                  standard_dg_std=standard_dg_std,
                                                  ph=standard_dg_ph,
                                                  ionic_strength=standard_dg_is).first()


    if gibbs_energy_db:
        gibbs_energy_reaction_model_db = GibbsEnergyReactionModel.query.filter_by(reaction_id=reaction_id,
                                                                                  model_id=model_id,
                                                                                  gibbs_energy_id=gibbs_energy_db.id).first()

        if not gibbs_energy_reaction_model_db:
            gibbs_energy_reaction_model_db = GibbsEnergyReactionModel(reaction_id=reaction_id,
                                                                      model_id=model_id,
                                                                      gibbs_energy_id=gibbs_energy_db.id)

            db.session.add(gibbs_energy_reaction_model_db)

    if not gibbs_energy_db:

        gibbs_energy_db = GibbsEnergy(standard_dg=standard_dg,
                                      standard_dg_std=standard_dg_std,
                                      ph=standard_dg_ph,
                                      ionic_strength=standard_dg_is)

        db.session.add(gibbs_energy_db)
        db.session.commit()

        gibbs_energy_reaction_model_db = GibbsEnergyReactionModel(reaction_id=reaction_id,
                                                                  model_id=model_id,
                                                                  gibbs_energy_id=gibbs_energy_db.id)

        db.session.add(gibbs_energy_reaction_model_db)

        db.session.commit()

    if std_gibbs_energy_references.lower().strip() != 'equilibrator':

        gibbs_references = parse_input_list(std_gibbs_energy_references)
        for ref_doi in gibbs_references:
            ref_db = Reference.query.filter(doi=ref_doi).first()
            if not ref_db:
                ref_db = Reference(doi=ref_doi)
                db.session.add(ref_db)
            gibbs_energy_db.add_reference(ref_db.id)

    if std_gibbs_energy_references.lower().strip() == 'equilibrator':
        ref_db = Reference.query.filter_by(title='eQuilibrator').first()
        gibbs_energy_db.add_reference(ref_db)


def _add_mechanism(mechanism_references, enzyme_reaction_model):
        mech_references = parse_input_list(mechanism_references)

        for ref_doi in mech_references:
            ref_db = Reference.query.filter_by(doi=ref_doi).first()
            if not ref_db:
                ref_db = Reference(doi=ref_doi)
                db.session.add(ref_db)

            enzyme_reaction_model.add_mechanism_reference(ref_db)

@bp.route('/add_reaction', methods=['GET', 'POST'])
@login_required
def add_reaction():
    """
    Entity EnzymeReactionOrganism() is only created if either isoenzymes or model_id are provided besides the reaction.

    :return:
    """

    form = ReactionForm()

    enzymes = Enzyme.query.all()
    isoenzyme_list = {'id_value': '#isoenzyme_acronyms', 'input_data': [{'field1': enzyme.isoenzyme} for enzyme in enzymes] if enzymes else []}
    data_list = [isoenzyme_list]

    if form.validate_on_submit():

        compartment_name = form.compartment.data.name if form.compartment.data else ''
        reaction = Reaction(name=form.name.data,
                            acronym=form.acronym.data,
                            metanetx_id=form.metanetx_id.data,
                            bigg_id=form.bigg_id.data,
                            kegg_id=form.kegg_id.data,
                            compartment_name=compartment_name)

        db.session.add(reaction)

        _add_metabolites_to_reaction(reaction, form.reaction_string.data)

        if compartment_name:
            compartment = Compartment.query.filter_by(name=compartment_name).first()
            compartment.add_reaction(reaction)

        mechanism_id = form.mechanism.data.id if form.mechanism.data else ''
        mech_evidence_level_id = form.mechanism_evidence_level.data.id if form.mechanism_evidence_level.data else ''


        for enzyme in form.enzymes.data:

            enzyme_reaction_organism = EnzymeReactionOrganism(id=EnzymeReactionOrganism.query.count()+1,
                                                              enzyme_id=enzyme.id,
                                                              reaction_id=reaction.id,
                                                              organism_id=form.organism.data.id,
                                                              mechanism_id=mechanism_id,
                                                              mech_evidence_level_id=mech_evidence_level_id,
                                                              grasp_id=form.grasp_id.data,
                                                              subs_binding_order=form.subs_binding_order.data,
                                                              prod_release_order=form.prod_release_order.data,
                                                              comments=form.comments.data)
            db.session.add(enzyme_reaction_organism)

            if form.mechanism_references.data:
                _add_mechanism(form.mechanism_references.data, enzyme_reaction_organism)

            if form.models.data:
                for model in form.models.data:

                    enzyme_reaction_organism.add_model(model)


                    if form.std_gibbs_energy.data:
                        _add_gibbs_energy(reaction.id, model.id, form.std_gibbs_energy.data, form.std_gibbs_energy_std.data,
                                          form.std_gibbs_energy_ph.data, form.std_gibbs_energy_ionic_strength.data,
                                          form.std_gibbs_energy_references.data)

        db.session.commit()


        flash('Your reaction is now live!', 'success')

        return redirect(url_for('main.see_reaction_list'))

    return render_template('insert_data.html', title='Add reaction', form=form, header='Add reaction', data_list=data_list)
