import json
import re

from flask import render_template, flash, redirect, url_for
from flask import request
from flask_login import login_required

from app import current_app, db
from app.main import bp
from app.main.forms import EnzymeForm, EnzymeActivationForm, EnzymeEffectorForm, EnzymeInhibitionForm, \
    EnzymeMiscInfoForm, GeneForm, ModelAssumptionsForm, ModelForm, OrganismForm, ReactionForm, ModelModifyForm, \
    SelectOrganismForm, SelectIsoenzymeForm, SelectModelForm, MetaboliteForm
from app.main.utils import add_enzyme_structures, add_enzyme_organism, add_enzyme_genes, add_metabolites_to_reaction, \
    add_gibbs_energy, add_mechanism_references, add_references, check_metabolite
from app.models import Compartment, Enzyme, EnzymeReactionOrganism, EnzymeReactionActivation, EnzymeReactionEffector, \
    EnzymeReactionInhibition, EnzymeReactionMiscInfo, EnzymeOrganism, EnzymeStructure, EvidenceLevel, Gene, \
    GibbsEnergy, GibbsEnergyReactionModel, Mechanism, Metabolite, Model, ModelAssumptions, Organism, Reaction, \
    ReactionMetabolite, Reference, EnzymeGeneOrganism, ChebiIds
from app.utils.parsers import ReactionParser, parse_input_list


@bp.route('/modify_enzyme_select_organism/<isoenzyme>', methods=['GET', 'POST'])
@login_required
def modify_enzyme_select_organism(isoenzyme):
    form_organism = SelectOrganismForm()

    if form_organism.validate_on_submit():

        enzyme = Enzyme.query.filter_by(isoenzyme=isoenzyme).first()

        data_form = dict(name=enzyme.name,
                         acronym=enzyme.acronym,
                         isoenzyme=enzyme.isoenzyme,
                         ec_number=enzyme.ec_number)

        if form_organism.organism.data:

            data_form['organism_name'] = form_organism.organism.data.name

            organism = form_organism.organism.data

            if enzyme.enzyme_organisms.count() > 0:

                enz_org_list = enzyme.enzyme_organisms.filter(EnzymeOrganism.organism == organism).all()
                if enz_org_list:
                    uniprot_id_list = []
                    n_active_sites = 0
                    for enz_org in enz_org_list:
                        uniprot_id_list.append(enz_org.uniprot_id)
                        n_active_sites = enz_org.n_active_sites

                    data_form['uniprot_id_list'] = ', '.join(uniprot_id_list)
                    data_form['number_of_active_sites'] = n_active_sites

            if enzyme.enzyme_structures.count() > 0:

                enz_struct_list = enzyme.enzyme_structures.filter(EnzymeStructure.organism == organism).all()
                if enz_struct_list:
                    pdb_id_list = []
                    strain_list = []
                    for enz_struct in enz_struct_list:
                        pdb_id_list.append(enz_struct.pdb_id)
                        strain_list.append(enz_struct.strain)

                    data_form['pdb_structure_ids'] = ', '.join(pdb_id_list)
                    data_form['strain'] = ', '.join(strain_list)

            if enzyme.enzyme_gene_organisms.count() > 0:
                enz_gene_org_list = enzyme.enzyme_gene_organisms.filter(EnzymeGeneOrganism.organism == organism).all()
                if enz_gene_org_list:
                    gene_list = []
                    for enz_gene_org in enz_gene_org_list:
                        gene_list.append(enz_gene_org.gene.name)

                    data_form['gene_names'] = ', '.join(gene_list)

        return redirect(url_for('main.modify_enzyme', isoenzyme=isoenzyme, data_form=data_form))

    return render_template('insert_data.html', title='Modify enzyme', form=form_organism, header='Modify enzyme')


@bp.route('/modify_enzyme/<isoenzyme>', methods=['GET', 'POST'])
@login_required
def modify_enzyme(isoenzyme):
    data_form = request.args.get('data_form')
    data_form = json.loads(data_form.replace("'", "\""))

    if 'organism_name' in data_form:
        data_form['organism_name'] = Organism.query.filter_by(name=data_form['organism_name']).first()

    form = EnzymeForm(data=data_form, flag='modify')

    genes = Gene.query.all()
    gene_bigg_ids = {'id_value': '#gene_bigg_ids',
                     'input_data': [{'field1': gene.name} for gene in genes] if genes else []}

    enzyme_structures = EnzymeStructure.query.all()
    enzyme_structure_strains = set(
        [enzyme_structure.strain for enzyme_structure in enzyme_structures]) if enzyme_structures else []
    strain = {'id_value': '#strain', 'input_data': [{'field1': strain} for strain in
                                                    enzyme_structure_strains] if enzyme_structures else []}

    data_list = [gene_bigg_ids, strain]

    if form.validate_on_submit():
        enzyme = Enzyme.query.filter_by(isoenzyme=isoenzyme).first()

        enzyme.name = form.name.data
        enzyme.acronym = form.acronym.data
        enzyme.isoenzyme = form.isoenzyme.data
        enzyme.ec_number = form.ec_number.data

        if form.organism_name.data:
            # organism_db = Organism.query.filter_by(name=form.organism_name.data.name).first()
            organism_id = form.organism_name.data.id
            enzyme.empty_enzyme_gene_organisms(organism_id)
            enzyme.empty_structures(organism_id)
            enzyme.empty_enzyme_organisms(organism_id)

            if form.gene_names.data:
                add_enzyme_genes(form.gene_names.data, enzyme, organism_id)

            # populate enzyme_structure
            if form.pdb_structure_ids.data:
                pdb_id_list = parse_input_list(form.pdb_structure_ids.data)
                strain_list = parse_input_list(form.strain.data)
                add_enzyme_structures(enzyme, organism_id, pdb_id_list, strain_list)

            # populate enzyme_organism
            if form.uniprot_id_list.data:
                uniprot_id_list = parse_input_list(form.uniprot_id_list.data)
                add_enzyme_organism(enzyme, organism_id, uniprot_id_list, form.number_of_active_sites.data)

        db.session.commit()

        flash('Your enzyme has been modified.')
        return redirect(url_for('main.see_enzyme', isoenzyme=form.isoenzyme.data))

    return render_template('insert_data.html', title='Modify enzyme', form=form, header='Modify enzyme',
                           data_list=data_list)


@bp.route('/modify_enzyme_inhibitor/<inhibitor_id>', methods=['GET', 'POST'])
@login_required
def modify_enzyme_inhibitor(inhibitor_id):
    """
    Enzyme inhibitions can only be added to models through this view, not removed, so that a given user doesn't mess
    around with other users models.

    :param inhibitor_id:
    :return:
    """

    metabolites = Metabolite.query.all()
    metabolite_list = {'id_value': '#metabolite_list', 'input_data': [{'field1': metabolite.bigg_id} for metabolite in
                                                                      metabolites] if metabolites else []}
    data_list = [metabolite_list]

    enz_inhibitor = EnzymeReactionInhibition.query.filter_by(id=inhibitor_id).first()
    enz_inhibitor_refs = ', '.join([ref.doi for ref in enz_inhibitor.references]) if enz_inhibitor.references else ''

    form = EnzymeInhibitionForm(enzyme=enz_inhibitor.enzyme_reaction_organism.enzyme,
                                reaction=enz_inhibitor.enzyme_reaction_organism.reaction,
                                organism=enz_inhibitor.enzyme_reaction_organism.organism,
                                models=enz_inhibitor.models,
                                inhibitor_met=enz_inhibitor.inhibitor_met.bigg_id,
                                affected_met=enz_inhibitor.affected_met.bigg_id,
                                inhibition_type=enz_inhibitor.inhibition_type,
                                inhibition_constant=enz_inhibitor.inhibition_constant,
                                inhibition_evidence_level=enz_inhibitor.evidence,
                                references=enz_inhibitor_refs,
                                comments=enz_inhibitor.comments)

    if form.validate_on_submit():

        if not (form.enzyme.data.id == enz_inhibitor.enzyme_reaction_organism.enzyme.id and
                        form.reaction.data.id == enz_inhibitor.enzyme_reaction_organism.reaction.id and
                        form.organism.data.id == enz_inhibitor.enzyme_reaction_organism.organism.id):

            enz_rxn_org = EnzymeReactionOrganism.query.filter_by(enzyme_id=form.enzyme.data.id,
                                                                 reaction_id=form.reaction.data.id,
                                                                 organism_id=form.organism.data.id).first()

            if not enz_rxn_org:
                enz_rxn_org = EnzymeReactionOrganism(id=EnzymeReactionOrganism.query.count() + 1,
                                                     enzyme_id=form.enzyme.data.id,
                                                     reaction_id=form.reaction.data.id,
                                                     organism_id=form.organism.data.id)

                db.session.add(enz_rxn_org)
                db.session.commit()

            enz_inhibitor.enzyme_reaction_organism = enz_rxn_org

        inhibitor_met = check_metabolite(form.inhibitor_met.data)
        enz_inhibitor.inhibitor_met = inhibitor_met
        affected_met = check_metabolite(form.affected_met.data)
        enz_inhibitor.affected_met = affected_met
        enz_inhibitor.inhibition_type = form.inhibition_type.data
        enz_inhibitor.inhibition_constant = form.inhibition_constant.data

        inhibition_evidence_level_id = form.inhibition_evidence_level.data.id if form.inhibition_evidence_level.data else None
        enz_inhibitor.evidence_level_id = inhibition_evidence_level_id

        enz_inhibitor.comments = form.comments.data

        if form.models.data:
            # enz_inhibitor.empty_models()
            for model in form.models.data:
                enz_inhibitor.add_model(model)

        if form.references.data:
            enz_inhibitor.empty_references()

            add_references(form.references.data, enz_inhibitor)
            #for ref_db in ref_db_list:
            #    enz_inhibitor.add_reference(ref_db)
        db.session.commit()

        flash('Your enzyme inhibition has been modified.', 'success')

        return redirect(url_for('main.see_enzyme_inhibitor', inhibitor_id=inhibitor_id))

    return render_template('insert_data.html', title='Modify enzyme inhibitor', form=form,
                           header='Modify enzyme inhibitor', data_list=data_list)


@bp.route('/modify_enzyme_activator/<activator_id>', methods=['GET', 'POST'])
@login_required
def modify_enzyme_activator(activator_id):
    """
    Enzyme activations can only be added to models through this view, not removed, so that a given user doesn't mess
    around with other users models.

    :param activator_id:
    :return:
    """

    metabolites = Metabolite.query.all()
    metabolite_list = {'id_value': '#metabolite_list', 'input_data': [{'field1': metabolite.bigg_id} for metabolite in
                                                                      metabolites] if metabolites else []}
    data_list = [metabolite_list]

    enz_activator = EnzymeReactionActivation.query.filter_by(id=activator_id).first()
    enz_activator_refs = ', '.join([ref.doi for ref in enz_activator.references]) if enz_activator.references else ''

    form = EnzymeActivationForm(enzyme=enz_activator.enzyme_reaction_organism.enzyme,
                                reaction=enz_activator.enzyme_reaction_organism.reaction,
                                organism=enz_activator.enzyme_reaction_organism.organism,
                                models=enz_activator.models,
                                activator_met=enz_activator.activator_met.bigg_id,
                                activation_constant=enz_activator.activation_constant,
                                activation_evidence_level=enz_activator.evidence,
                                references=enz_activator_refs,
                                comments=enz_activator.comments)

    if form.validate_on_submit():

        if not (form.enzyme.data.id == enz_activator.enzyme_reaction_organism.enzyme.id and
                        form.reaction.data.id == enz_activator.enzyme_reaction_organism.reaction.id and
                        form.organism.data.id == enz_activator.enzyme_reaction_organism.organism.id):

            enz_rxn_org = EnzymeReactionOrganism.query.filter_by(enzyme_id=form.enzyme.data.id,
                                                                 reaction_id=form.reaction.data.id,
                                                                 organism_id=form.organism.data.id).first()

            if not enz_rxn_org:
                enz_rxn_org = EnzymeReactionOrganism(id=EnzymeReactionOrganism.query.count() + 1,
                                                     enzyme_id=form.enzyme.data.id,
                                                     reaction_id=form.reaction.data.id,
                                                     organism_id=form.organism.data.id)

                db.session.add(enz_rxn_org)
                db.session.commit()

            enz_activator.enzyme_reaction_organism = enz_rxn_org

        activator_met = check_metabolite(form.activator_met.data)
        enz_activator.activator_met = activator_met
        enz_activator.activation_constant = form.activation_constant.data

        activation_evidence_level_id = form.activation_evidence_level.data.id if form.activation_evidence_level.data else None
        enz_activator.evidence_level_id = activation_evidence_level_id

        enz_activator.comments = form.comments.data

        if form.models.data:
            # enz_activator.empty_models()
            for model in form.models.data:
                enz_activator.add_model(model)

        if form.references.data:
            enz_activator.empty_references()

            add_references(form.references.data, enz_activator)
            #for ref_db in ref_db_list:
            #    enz_activator.add_reference(ref_db)
        db.session.commit()

        flash('Your enzyme activation has been modified.', 'success')

        return redirect(url_for('main.see_enzyme_activator', activator_id=activator_id))

    return render_template('insert_data.html', title='Modify enzyme activator', form=form,
                           header='Modify enzyme activator', data_list=data_list)


@bp.route('/modify_enzyme_effector/<effector_id>', methods=['GET', 'POST'])
@login_required
def modify_enzyme_effector(effector_id):
    """
    Enzyme effectors can only be added to models through this view, not removed, so that a given user doesn't mess
    around with other users models.

    :param effector_id:
    :return:
    """

    metabolites = Metabolite.query.all()
    metabolite_list = {'id_value': '#metabolite_list', 'input_data': [{'field1': metabolite.bigg_id} for metabolite in
                                                                      metabolites] if metabolites else []}
    data_list = [metabolite_list]

    enz_effector = EnzymeReactionEffector.query.filter_by(id=effector_id).first()
    enz_effector_refs = ', '.join([ref.doi for ref in enz_effector.references]) if enz_effector.references else ''

    form = EnzymeEffectorForm(enzyme=enz_effector.enzyme_reaction_organism.enzyme,
                              reaction=enz_effector.enzyme_reaction_organism.reaction,
                              organism=enz_effector.enzyme_reaction_organism.organism,
                              models=enz_effector.models,
                              effector_met=enz_effector.effector_met.bigg_id,
                              effector_type=enz_effector.effector_type,
                              effector_evidence_level=enz_effector.evidence,
                              references=enz_effector_refs,
                              comments=enz_effector.comments)

    if form.validate_on_submit():

        if not (form.enzyme.data.id == enz_effector.enzyme_reaction_organism.enzyme.id and
                        form.reaction.data.id == enz_effector.enzyme_reaction_organism.reaction.id and
                        form.organism.data.id == enz_effector.enzyme_reaction_organism.organism.id):

            enz_rxn_org = EnzymeReactionOrganism.query.filter_by(enzyme_id=form.enzyme.data.id,
                                                                 reaction_id=form.reaction.data.id,
                                                                 organism_id=form.organism.data.id).first()

            enz_effector.enzyme_reaction_organism = enz_rxn_org

            if not enz_rxn_org:
                enz_rxn_org = EnzymeReactionOrganism(id=EnzymeReactionOrganism.query.count() + 1,
                                                     enzyme_id=form.enzyme.data.id,
                                                     reaction_id=form.reaction.data.id,
                                                     organism_id=form.organism.data.id)

                db.session.add(enz_rxn_org)
                db.session.commit()

                enz_effector.enzyme_reaction_organism = enz_rxn_org

        effector_met = check_metabolite(form.effector_met.data)
        enz_effector.effector_met = effector_met
        enz_effector.effector_type = form.effector_type.data

        effector_evidence_level_id = form.effector_evidence_level.data.id if form.effector_evidence_level.data else None
        enz_effector.evidence_level_id = effector_evidence_level_id

        enz_effector.comments = form.comments.data

        if form.models.data:
            # enz_effector.empty_models()
            for model in form.models.data:
                enz_effector.add_model(model)

        if form.references.data:
            enz_effector.empty_references()

            add_references(form.references.data, enz_effector)
            #for ref_db in ref_db_list:
            #    enz_effector.add_reference(ref_db)

        db.session.commit()
        flash('Your enzyme effector has been modified.', 'success')

        return redirect(url_for('main.see_enzyme_effector', effector_id=effector_id))

    return render_template('insert_data.html', title='Modify enzyme effector', form=form,
                           header='Modify enzyme effector', data_list=data_list)


@bp.route('/modify_enzyme_misc_info/<misc_info_id>', methods=['GET', 'POST'])
@login_required
def modify_enzyme_misc_info(misc_info_id):
    """
    Enzyme misc info can only be added to models through this view, not removed, so that a given user doesn't mess
    around with other users models.

    :param misc_info_id:
    :return:
    """

    enz_misc_info = EnzymeReactionMiscInfo.query.filter_by(id=misc_info_id).first()
    enz_misc_info_refs = ', '.join([ref.doi for ref in enz_misc_info.references]) if enz_misc_info.references else ''

    form = EnzymeMiscInfoForm(enzyme=enz_misc_info.enzyme_reaction_organism.enzyme,
                              reaction=enz_misc_info.enzyme_reaction_organism.reaction,
                              organism=enz_misc_info.enzyme_reaction_organism.organism,
                              models=enz_misc_info.models,
                              topic=enz_misc_info.topic,
                              description=enz_misc_info.description,
                              evidence_level=enz_misc_info.evidence,
                              references=enz_misc_info_refs,
                              comments=enz_misc_info.comments)

    if form.validate_on_submit():

        if not (form.enzyme.data.id == enz_misc_info.enzyme_reaction_organism.enzyme.id and
                        form.reaction.data.id == enz_misc_info.enzyme_reaction_organism.reaction.id and
                        form.organism.data.id == enz_misc_info.enzyme_reaction_organism.organism.id):

            enz_rxn_org = EnzymeReactionOrganism.query.filter_by(enzyme_id=form.enzyme.data.id,
                                                                 reaction_id=form.reaction.data.id,
                                                                 organism_id=form.organism.data.id).first()

            if not enz_rxn_org:
                enz_rxn_org = EnzymeReactionOrganism(id=EnzymeReactionOrganism.query.count() + 1,
                                                     enzyme_id=form.enzyme.data.id,
                                                     reaction_id=form.reaction.data.id,
                                                     organism_id=form.organism.data.id)

                db.session.add(enz_rxn_org)
                db.session.commit()

            enz_misc_info.enzyme_reaction_organism = enz_rxn_org

        enz_misc_info.topic = form.topic.data
        enz_misc_info.description = form.description.data

        misc_info_evidence_level_id = form.evidence_level.data.id if form.evidence_level.data else None
        enz_misc_info.evidence_level_id = misc_info_evidence_level_id

        enz_misc_info.comments = form.comments.data

        if form.models.data:
            # enz_misc_info.empty_models()
            for model in form.models.data:
                enz_misc_info.add_model(model)

        if form.references.data:
            enz_misc_info.empty_references()

            add_references(form.references.data, enz_misc_info)
            #for ref_db in ref_db_list:
            #    enz_misc_info.add_reference(ref_db)

        db.session.commit()
        flash('Your enzyme misc info has been modified.', 'success')

        return redirect(url_for('main.see_enzyme_misc_info', misc_info_id=misc_info_id))

    return render_template('insert_data.html', title='Modify enzyme misc info', form=form,
                           header='Modify enzyme misc info')


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
    organism_name = {'id_value': '#organism_name',
                     'input_data': [{'field1': organism.name} for organism in organisms] if organisms else []}
    data_list = [organism_name]

    if form.validate_on_submit():

        organism = Model.query.filter_by(name=form.name.data).first()
        if not organism:
            organism = Organism(name=form.organism_name.data)
            db.session.add(organism)

        model.name = form.name.data
        model.organism_name = form.organism_name.data
        model.strain = form.strain.data
        model.comments = form.comments.data

        model.empty_enzyme_reaction_organisms()
        model.emtpy_enzyme_reaction_inhibitions()
        model.emtpy_enzyme_reaction_activations()
        model.emtpy_enzyme_reaction_effectors()
        model.emtpy_enzyme_reaction_misc_infos()
        model.emtpy_model_assumptions()

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

        if form.model_misc_infos.data:
            for model_misc_info in form.model_misc_infos.data:
                model.add_enzyme_reaction_misc_info(model_misc_info)

        if form.model_assumptions.data:
            for model_assumption in form.model_assumptions.data:
                model.add_model_assumption(model_assumption)

        db.session.commit()

        flash('Your model has been modified', 'success')

        return redirect(url_for('main.see_model', model_name=form.name.data))

    return render_template('insert_data.html', title='Modify model', form=form, header='Modify model',
                           data_list=data_list)


@bp.route('/modify_metabolite/<grasp_id>', methods=['GET', 'POST'])
@login_required
def modify_metabolite(grasp_id):
    metabolite = Metabolite.query.filter_by(grasp_id=grasp_id).first()

    chebi_id_list = [chebi.chebi_id for chebi in metabolite.chebis]
    chebi_id_list = chebi_id_list if chebi_id_list else ''
    inchi_list = [chebi.inchi for chebi in metabolite.chebis]
    inchi_list = inchi_list if inchi_list else ''

    data_form = dict(grasp_id=metabolite.grasp_id,
                     name=metabolite.name,
                     bigg_id=metabolite.bigg_id,
                     metanetx_id=metabolite.metanetx_id,
                     compartments=metabolite.compartments,
                     chebi_ids=chebi_id_list,
                     inchis=inchi_list)

    form = MetaboliteForm(data=data_form, flag='modify')

    if form.validate_on_submit():

        metabolite.grasp_id = form.grasp_id.data
        metabolite.name = form.name.data
        metabolite.bigg_id = form.bigg_id.data
        metabolite.metanetx_id = form.metanetx_id.data

        metabolite.empty_compartments()
        for compartment in form.compartments.data:
            metabolite.add_compartment(compartment)

        metabolite.empty_chebis()
        chebi_id_list = parse_input_list(form.chebi_ids.data)
        inchi_list = parse_input_list(form.inchis.data, False)
        for chebi_id, inchi_id in zip(chebi_id_list, inchi_list):
            chebi_id_db = ChebiIds(chebi_id=chebi_id,
                                   inchi=inchi_id)

            db.session.add(chebi_id_db)
            metabolite.add_chebi_id(chebi_id_db)

        db.session.commit()

        flash('Your metabolite has been modified', 'success')

        return redirect(url_for('main.see_metabolite', grasp_id=form.grasp_id.data))

    return render_template('insert_data.html', title='Modify metabolite', form=form, header='Modify metabolite')


@bp.route('/modify_model_assumption/<model_assumption_id>', methods=['GET', 'POST'])
@login_required
def modify_model_assumption(model_assumption_id):
    model_assumption = ModelAssumptions.query.filter_by(id=model_assumption_id).first()
    model_assumption_refs = ', '.join(
        [ref.doi for ref in model_assumption.references]) if model_assumption.references else ''

    form = ModelAssumptionsForm(model=model_assumption.model,
                                assumption=model_assumption.assumption,
                                description=model_assumption.description,
                                evidence_level=model_assumption.evidence,
                                included_in_model=model_assumption.included_in_model,
                                references=model_assumption_refs,
                                comments=model_assumption.comments)

    if form.validate_on_submit():

        model_assumption.assumption = form.assumption.data
        model_assumption.description = form.description.data
        model_assumption_evidence_level_id = form.evidence_level.data.id if form.evidence_level.data else None
        model_assumption.evidence_level_id = model_assumption_evidence_level_id
        model_assumption.comments = form.comments.data
        model_assumption.model = form.model.data

        if form.references.data:
            model_assumption.empty_references()

            add_references(form.references.data, model_assumption)
            #for ref_db in ref_db_list:
            #    model_assumption.add_reference(ref_db)

        db.session.commit()
        flash('Your model assumption has been modified.', 'success')

        return redirect(url_for('main.see_model_assumption', model_assumption_id=model_assumption_id))

    return render_template('insert_data.html', title='Modify model assumption', form=form,
                           header='Modify model assumption')


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

    return render_template('insert_data.html', title='Modify organism', form=form, header='Modify organism')


@bp.route('/modify_reaction_select_organism/<reaction_acronym>', methods=['GET', 'POST'])
@login_required
def modify_reaction_select_organism(reaction_acronym):
    form_organism = SelectOrganismForm()

    if form_organism.validate_on_submit():
        if not form_organism.organism.data:
            return render_template('insert_data.html', title='Modify reaction', form=form_organism,
                                   header='Modify reaction',
                                   text='Please select an organism')
        else:
            data_form = dict()
            data_form['organism'] = form_organism.organism.data.name

        return redirect(
            url_for('main.modify_reaction_select_isoenzyme', reaction_acronym=reaction_acronym, data_form=data_form))

    return render_template('insert_data.html', title='Modify reaction', form=form_organism, header='Modify reaction')


@bp.route('/modify_reaction_select_isoenzyme/<reaction_acronym>', methods=['GET', 'POST'])
@login_required
def modify_reaction_select_isoenzyme(reaction_acronym):
    data_form = request.args.get('data_form')
    data_form = json.loads(data_form.replace("'", "\""))

    organism = Organism.query.filter_by(name=data_form['organism']).first()
    reaction = Reaction.query.filter_by(acronym=reaction_acronym).first()
    enzyme_rxn_orgs = EnzymeReactionOrganism.query.filter_by(reaction_id=reaction.id,
                                                             organism_id=organism.id).all()
    enzyme_ids = [enz_rxn_org.enzyme_id for enz_rxn_org in enzyme_rxn_orgs]
    enzymes = Enzyme.query.filter(Enzyme.id.in_(enzyme_ids)).all()
    isoenzyme_data_form = dict(enzyme=enzymes)

    form_isoenzymes = SelectIsoenzymeForm(data=isoenzyme_data_form)

    if form_isoenzymes.validate_on_submit():
        data_form['isoenzyme'] = form_isoenzymes.enzyme.data[0].acronym

        return redirect(
            url_for('main.modify_reaction_select_model', reaction_acronym=reaction_acronym, data_form=data_form))

    return render_template('insert_data.html', title='Modify reaction', form=form_isoenzymes, header='Modify reaction')


@bp.route('/modify_reaction_select_model/<reaction_acronym>', methods=['GET', 'POST'])
@login_required
def modify_reaction_select_model(reaction_acronym):
    data_form = request.args.get('data_form')
    data_form = json.loads(data_form.replace("'", "\""))

    organism = Organism.query.filter_by(name=data_form['organism']).first()
    reaction = Reaction.query.filter_by(acronym=reaction_acronym).first()
    enzyme = Enzyme.query.filter_by(isoenzyme=data_form['isoenzyme']).first()

    enzyme_rxn_org = EnzymeReactionOrganism.query.filter_by(reaction_id=reaction.id,
                                                            organism_id=organism.id,
                                                            enzyme_id=enzyme.id).first()

    form_model = SelectModelForm(data=enzyme_rxn_org.models)

    if form_model.validate_on_submit():
        if form_model.model.data:
            data_form['model'] = form_model.model.data[0].name
        else:
            data_form['model'] = []

        return redirect(url_for('main.modify_reaction', reaction_acronym=reaction_acronym, data_form=data_form))

    return render_template('insert_data.html', title='Modify reaction', form=form_model, header='Modify reaction')


@bp.route('/modify_reaction/<reaction_acronym>', methods=['GET', 'POST'])
@login_required
def modify_reaction(reaction_acronym):
    """

    The models associated to a given enzyme_reaction_organism are never removed, only added. This is to avoid that user
    2 by mistake removes the association between a given enzyme_reaction_organism and the models from user 1.

    :param reaction_acronym:
    :return:
    """

    data_form = request.args.get('data_form')
    data_form = json.loads(data_form.replace("'", "\""))

    reaction = Reaction.query.filter_by(acronym=reaction_acronym).first()
    organism = Organism.query.filter_by(name=data_form['organism']).first()
    enzyme = Enzyme.query.filter_by(isoenzyme=data_form['isoenzyme']).first()

    enzyme_rxn_org = EnzymeReactionOrganism.query.filter_by(reaction_id=reaction.id,
                                                            organism_id=organism.id,
                                                            enzyme_id=enzyme.id).first()

    mech_references = ', '.join([ref.doi for ref in enzyme_rxn_org.mechanism_references])

    data_form['name'] = reaction.name
    data_form['acronym'] = reaction.acronym
    data_form['grasp_id'] = enzyme_rxn_org.grasp_id
    data_form['reaction_string'] = str(reaction)
    data_form['metanetx_id'] = reaction.metanetx_id
    data_form['bigg_id'] = reaction.bigg_id
    data_form['kegg_id'] = reaction.kegg_id
    data_form['organism'] = organism.name
    data_form['enzymes'] = [enzyme]
    data_form['comments'] = enzyme_rxn_org.comments

    model_names = [model.name for model in enzyme_rxn_org.models]

    if reaction.compartment:
        data_form['compartment'] = reaction.compartment.name

    if enzyme_rxn_org.mechanism:
        data_form['mechanism'] = enzyme_rxn_org.mechanism.name
        data_form['mechanism_references'] = mech_references
        data_form['mechanism_evidence_level'] = enzyme_rxn_org.mech_evidence
        data_form['subs_binding_order'] = enzyme_rxn_org.subs_binding_order
        data_form['prod_release_order'] = enzyme_rxn_org.prod_release_order

    if data_form['model']:
        model = Model.query.filter_by(name=data_form['model']).first()
        data_form['models'] = [model]

        if data_form['model'] in model_names:
            gibbs_energy_rxn_model = GibbsEnergyReactionModel.query.filter_by(model_id=model.id,
                                                                              reaction_id=reaction.id).first()
            gibbs_energy = GibbsEnergy.query.filter_by(id=gibbs_energy_rxn_model.gibbs_energy_id).first()

            data_form['std_gibbs_energy'] = gibbs_energy.standard_dg
            data_form['std_gibbs_energy_std'] = gibbs_energy.standard_dg_std
            data_form['std_gibbs_energy_ph'] = gibbs_energy.ph
            data_form['std_gibbs_energy_ionic_strength'] = gibbs_energy.ionic_strength
            data_form['std_gibbs_energy_references'] = ', '.join(
                [ref.doi if ref.doi is not None else ref.title for ref in
                 gibbs_energy.references.all()]) if gibbs_energy.references else ''

    form = ReactionForm(data=data_form, flag='modify')

    if form.validate_on_submit():

        compartment_name = form.compartment.data.name if form.compartment.data else ''
        reaction.name = form.name.data
        reaction.acronym = form.acronym.data
        reaction.metanetx_id = form.metanetx_id.data
        reaction.bigg_id = form.bigg_id.data
        reaction.kegg_id = form.kegg_id.data
        reaction.compartment_name = compartment_name

        db.session.add(reaction)

        reaction.empty_metabolites()
        add_metabolites_to_reaction(reaction, form.reaction_string.data)

        if compartment_name:
            compartment = Compartment.query.filter_by(name=compartment_name).first()
            compartment.add_reaction(reaction)

        mechanism_id = form.mechanism.data.id if form.mechanism.data else ''
        mech_evidence_level_id = form.mechanism_evidence_level.data.id if form.mechanism_evidence_level.data else ''

        if not (len(form.enzymes.data) == 1 and enzyme_rxn_org.enzyme_id == form.enzymes.data[0].id
                and enzyme_rxn_org.organism_id == form.organism.data.id):

            enzyme_rxn_org = EnzymeReactionOrganism.query.filter_by(enzyme_id=form.enzymes.data[0].id,
                                                                    reaction_id=reaction.id,
                                                                    organism_id=form.organism.data.id).first()

            if not enzyme_rxn_org:
                enzyme_rxn_org = EnzymeReactionOrganism(id=EnzymeReactionOrganism.query.count() + 1,
                                                        enzyme_id=form.enzymes.data[0].id,
                                                        reaction_id=reaction.id,
                                                        organism_id=form.organism.data.id)
                db.session.add(enzyme_rxn_org)
                db.session.commit()

        enzyme_rxn_org.mechanism_id = mechanism_id
        enzyme_rxn_org.mech_evidence_level_id = mech_evidence_level_id
        enzyme_rxn_org.grasp_id = form.grasp_id.data
        enzyme_rxn_org.subs_binding_order = form.subs_binding_order.data
        enzyme_rxn_org.prod_release_order = form.prod_release_order.data
        enzyme_rxn_org.comments = form.comments.data

        if form.mechanism_references.data:
            enzyme_rxn_org.empty_mechanism_references()
            add_references(form.mechanism_references.data, enzyme_rxn_org, mechanism_ref=True)

        if form.models.data:
            for model in form.models.data:
                enzyme_rxn_org.add_model(model)

                if form.std_gibbs_energy.data:
                    add_gibbs_energy(reaction.id, model.id, form.std_gibbs_energy.data, form.std_gibbs_energy_std.data,
                                     form.std_gibbs_energy_ph.data, form.std_gibbs_energy_ionic_strength.data,
                                     form.std_gibbs_energy_references.data)

        db.session.commit()

        flash('Your reaction has been modified', 'success')

        return redirect(url_for('main.see_reaction', reaction_acronym=form.acronym.data))

    return render_template('insert_data.html', title='Modify reaction', form=form, header='Modify reaction')
