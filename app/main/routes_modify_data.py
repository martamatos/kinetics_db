from app.main.forms import EnzymeForm, EnzymeActivationForm, EnzymeEffectorForm, EnzymeInhibitionForm, \
    EnzymeMiscInfoForm, GeneForm, ModelAssumptionsForm, ModelForm, OrganismForm, ReactionForm, ModelModifyForm
from flask import render_template, flash, redirect, url_for
from flask_login import login_required
from app import current_app, db
from app.models import Compartment, Enzyme, EnzymeReactionOrganism, EnzymeReactionActivation, EnzymeReactionEffector, EnzymeReactionInhibition, EnzymeReactionMiscInfo, EnzymeOrganism, EnzymeStructure, EvidenceLevel, Gene, \
    GibbsEnergy, GibbsEnergyReactionModel, Mechanism, Metabolite, Model, ModelAssumptions, Organism, Reaction, ReactionMetabolite, Reference
from app.main import bp
from app.utils.parsers import ReactionParser, parse_input_list
import re



"""
@bp.route('/modify_enzyme/<isoenzyme>', methods=['GET', 'POST'])
@login_required
def modify_enzyme(isoenzyme):

    data_form = dict(name=organism_name)
    form = OrganismForm(data=data_form)

    if form.validate_on_submit():
        organism = Organism.query.filter_by(name=organism_name).first()
        organism.name = form.name.data
        db.session.commit()

        flash('Your organism has been modified', 'success')

        return redirect(url_for('main.see_organism', organism_name=form.name.data))

    return render_template('insert_data.html', title='Modify organism', form=form, header='organism')

"""
@bp.route('/modify_organism/<organism_name>', methods=['GET', 'POST'])
@login_required
def modify_organism(organism_name):

    data_form = dict(name=organism_name)
    form = OrganismForm(data=data_form)

    if form.validate_on_submit():
        organism = Organism.query.filter_by(name=organism_name).first()
        organism.name = form.name.data
        db.session.commit()

        flash('Your organism has been modified', 'success')

        return redirect(url_for('main.see_organism', organism_name=form.name.data))

    return render_template('insert_data.html', title='Modify organism', form=form, header='Modify organism')\


@bp.route('/modify_model/<model_name>', methods=['GET', 'POST'])
@login_required
def modify_model(model_name):

    model = Model.query.filter_by(name=model_name).first()

    data_form = dict(name=model.name,
                     organism_name=model.organism_name,
                     strain=model.strain,
                     enz_rxn_orgs=model.enzyme_reaction_organisms,
                     model_inhibitions=model.enzyme_reaction_inhibitions,
                     model_activations=model.enzyme_reaction_activations,
                     model_effectors=model.enzyme_reaction_effectors,
                     model_assumptions=model.model_assumptions,
                     comments=model.comments)

    form = ModelModifyForm(data=data_form)

    organisms = Organism.query.all()
    organism_name = {'id_value': '#organism_name', 'input_data': [{'field1': organism.name} for organism in organisms] if organisms else []}
    data_list = [organism_name]

    if form.validate_on_submit():

        organism = Model.query.filter_by(name=form.name.data).first()
        if not organism:
            organism = Organism(name=form.organism_name.data)
            db.session.add(organism)

        model.name = form.name.data
        model.organism_name = form.organism_name.data,
        model.strain = form.strain.data,
        model.comments = form.comments.data
        model.empty_enzyme_reaction_organisms()
        model.emtpy_enzyme_reaction_inhibitions()
        model.emtpy_enzyme_reaction_activations()
        model.emtpy_enzyme_reaction_effectors()
        model.emtpy_enzyme_reaction_misc_infos()
        model.emtpy_model_assumptions()

        db.session.commit()

        if form.enz_rxn_orgs.data:
            for enz_rxn_org in form.enz_rxn_orgs.data:
                model.add_enzyme_reaction_organism(enz_rxn_org)

        if form.model_inhibitions.data:
            for model_inhibitor in form.model_inhibitions.data:
                model.add_enzyme_reaction_inhibitor(model_inhibitor)

        if form.model_activations.data:
            for model_activator in form.model_activations.data:
                model.add_enzyme_reaction_activator(model_activator)

        if form.model_effectors.data:
            for model_effector in form.model_effectors.data:
                model.add_enzyme_reaction_effector(model_effector)

        if form.model_assumptions.data:
            for model_assumption in form.model_assumptions.data:
                model.add_model_assumption(model_assumption)

        db.session.commit()

        flash('Your model has been modified', 'success')

        return redirect(url_for('main.see_model', model_name=form.name.data))

    return render_template('insert_data.html', title='Modify model', form=form, header='Modify model', data_list=data_list)

"""

@bp.route('/modify_enzyme/<reaction_acronym>', methods=['GET', 'POST'])
@login_required
def modify_reaction(reaction_acronym):

    reaction = Reaction.query.filter_by(bigg_acronym=reaction_acronym).first()

    data_form = dict(name=reaction.name,
                    bigg_acronym=reaction.bigg_acronym,
                    grasp_id=,
                    reaction_string=str(reaction),
                    metanetx_id=reaction.metanetx_id,
                    bigg_id=reaction.bigg_id,
                    kegg_id=reaction.kegg_id,

                    compartment=,
                    organism =,
                    models =,
                    enzymes =,

                    mechanism =,
                    mechanism_references =,
                    mechanism_evidence_level =,
                    subs_binding_order =,
                    prod_release_order =,

                    std_gibbs_energy =,
                    std_gibbs_energy_std =,
                    std_gibbs_energy_ph =,
                    std_gibbs_energy_ionic_strength =,
                    std_gibbs_energy_references =,
                    comments=)

    form = ReactionForm(data=data_form)

    if form.validate_on_submit():
        organism = Organism.query.filter_by(name=organism_name).first()
        organism.name = form.name.data
        db.session.commit()

        flash('Your organism has been modified', 'success')

        return redirect(url_for('main.see_reaction', reaction_acronym=form.bigg_acronym.data))

    return render_template('insert_data.html', title='Modify reaction', form=form, header='organism')
"""