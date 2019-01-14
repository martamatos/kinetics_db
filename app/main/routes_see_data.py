from flask import Markup
from flask import render_template, flash, redirect, url_for, request
from flask_login import login_required

from app import current_app, db
from app.main import bp
from app.main.forms import EnzymeForm, GeneForm, ModelForm, OrganismForm, ReactionForm, ModifyDataForm
from app.main.forms import OrganismForm
from app.models import Compartment, Enzyme, EnzymeReactionOrganism, EnzymeReactionInhibition, EnzymeReactionActivation, \
    EnzymeReactionEffector, EnzymeReactionMiscInfo, EnzymeOrganism, EnzymeStructure, EvidenceLevel, Gene, \
    GibbsEnergy, Mechanism, Metabolite, Model, Organism, Reaction, ReactionMetabolite, Reference, ModelAssumptions


@bp.route('/see_enzyme_list')
@login_required
def see_enzyme_list():
    tab_status = {"enzymes": "active", "metabolites": "#", "models": "#", "organisms": "#", "reactions": "#",
                  "enzyme_inhibitors:": "#", "enzyme_activators:": "#", "enzyme_effectors:": "#",
                  "enzyme_misc_info:": "#", "model_assumptions": "#"}
    header = Markup("<th>Name</th> \
                    <th>Acronym</th> \
                    <th>Isoenzyme</th> \
                    <th>EC number</th>")

    # enzyme_header = Enzyme.__table__.columns.keys()
    page = request.args.get('page', 1, type=int)
    enzymes = Enzyme.query.order_by(Enzyme.isoenzyme.asc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.see_enzyme_list', page=enzymes.next_num) \
        if enzymes.has_next else None
    prev_url = url_for('main.see_enzyme_list', page=enzymes.prev_num) \
        if enzymes.has_prev else None
    return render_template("see_data.html", title='See enzymes', data=enzymes.items,
                           data_type='enzyme', tab_status=tab_status, header=header,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/see_enzyme/<isoenzyme>', methods=['GET', 'POST'])
@login_required
def see_enzyme(isoenzyme):
    enzyme = Enzyme.query.filter_by(isoenzyme=isoenzyme).first()

    data = []
    data_nested = []

    data.append({'field_name': 'Name', 'data': enzyme.name})
    data.append({'field_name': 'Acronym', 'data': enzyme.acronym})
    data.append({'field_name': 'Isoenzyme', 'data': enzyme.isoenzyme})
    data.append({'field_name': 'EC number', 'data': enzyme.ec_number})

    enzyme_structures = EnzymeStructure.query.filter_by(enzyme_id=enzyme.id).all()
    enzyme_structures_organism_list = [structure.organism_id for structure in enzyme_structures]

    enzyme_organism = EnzymeOrganism.query.filter_by(enzyme_id=enzyme.id).all()
    enzyme_organisms_organism_list = [enz_org.organism_id for enz_org in enzyme_organism]

    enzyme_reaction_organism = EnzymeReactionOrganism.query.filter_by(enzyme_id=enzyme.id)
    enzyme_reaction_organisms_organism_list = [enz_rxn_org.organism_id for enz_rxn_org in enzyme_reaction_organism]

    organism_ids_set = set(
        enzyme_structures_organism_list + enzyme_organisms_organism_list + enzyme_reaction_organisms_organism_list)

    organisms = [organism.name for organism in Organism.query.filter(Organism.id.in_(organism_ids_set)).all()]
    data.append({'field_name': 'Organisms', 'data': ', '.join(organisms) if organisms else 'NA'})

    enz_rxn_org_models = [enz_rxn_org.models for enz_rxn_org in enzyme_reaction_organism]
    models = [item.name for sublist in enz_rxn_org_models for item in sublist]
    data.append({'field_name': 'Models', 'data': ', '.join(models) if models else 'NA'})

    reactions_ids = [enz_rxn_org.reaction_id for enz_rxn_org in enzyme_reaction_organism]
    reactions = [str(reaction) for reaction in Reaction.query.filter(Reaction.id.in_(reactions_ids)).all()]
    data_nested.append({'field_name': 'Reactions', 'data': reactions})

    enz_rxn_org_id_list = [enz_rxn_org.id for enz_rxn_org in enzyme_reaction_organism]

    inhibitors = EnzymeReactionInhibition.query.filter(
        EnzymeReactionInhibition.enz_rxn_org_id.in_(enz_rxn_org_id_list)).all()
    data_nested.append({'field_name': 'Inhibitors', 'data': inhibitors})

    activators = EnzymeReactionActivation.query.filter(
        EnzymeReactionActivation.enz_rxn_org_id.in_(enz_rxn_org_id_list)).all()
    data_nested.append({'field_name': 'Activators', 'data': activators})

    effectors = EnzymeReactionEffector.query.filter(
        EnzymeReactionEffector.enz_rxn_org_id.in_(enz_rxn_org_id_list)).all()
    data_nested.append({'field_name': 'Effectors', 'data': effectors})

    misc_infos = EnzymeReactionMiscInfo.query.filter(
        EnzymeReactionMiscInfo.enz_rxn_org_id.in_(enz_rxn_org_id_list)).all()
    data_nested.append({'field_name': 'Misc info', 'data': misc_infos})

    # TODO: add encoding genes

    uniprot_ids = [enz_org.uniprot_id for enz_org in enzyme_organism]
    data.append({'field_name': 'Uniprot IDs', 'data': ', '.join(uniprot_ids) if uniprot_ids else 'NA'})
    pdb_ids = [structure.pdb_id for structure in enzyme_structures]
    data.append({'field_name': 'PDB IDs', 'data': ', '.join(pdb_ids) if pdb_ids else 'NA'})

    form = ModifyDataForm()
    if form.validate_on_submit():
        return redirect(url_for('main.modify_enzyme_select_organism', isoenzyme=isoenzyme))

    return render_template("see_data_element.html", title='See enzyme', data_name=isoenzyme, data_type='enzyme',
                           data_list=data, data_list_nested=data_nested, form=form)


@bp.route('/see_enzyme_inhibitors_list')
@login_required
def see_enzyme_inhibitors_list():
    tab_status = {"enzymes": "#", "metabolites": "#", "models": "#", "organisms": "#", "reactions": "#",
                  "enzyme_inhibitors:": "active", "enzyme_activators:": "#", "enzyme_effectors:": "#",
                  "enzyme_misc_info:": "#", "model_assumptions": "#"}
    header = Markup("<th>ID</th> \
                    <th>Inhibitor</th> \
                    <th>Inhibition type</th> \
                    <th>Affected metabolite</th> \
                    <th>Enzyme</th> \
                    <th>Reaction</th> \
                    <th>Organism</th>")

    # enzyme_header = Enzyme.__table__.columns.keys()
    page = request.args.get('page', 1, type=int)
    enzyme_inhibitors = EnzymeReactionInhibition.query.order_by(EnzymeReactionInhibition.id.asc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.see_enzyme_inhibitors_list', page=enzyme_inhibitors.next_num) \
        if enzyme_inhibitors.has_next else None
    prev_url = url_for('main.see_enzyme_inhibitors_list', page=enzyme_inhibitors.prev_num) \
        if enzyme_inhibitors.has_prev else None
    return render_template("see_data.html", title='See enzyme inhibitors', data=enzyme_inhibitors.items,
                           data_type='enzyme_inhibitors', tab_status=tab_status, header=header,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/see_enzyme_inhibitor/<inhibitor_id>', methods=['GET', 'POST'])
@login_required
def see_enzyme_inhibitor(inhibitor_id):
    enz_inhib = EnzymeReactionInhibition.query.filter_by(id=inhibitor_id).first()

    data = []
    data_nested = []

    data.append({'field_name': 'Isoenzyme', 'data': enz_inhib.enzyme_reaction_organism.enzyme.isoenzyme})
    data.append({'field_name': 'Reaction', 'data': enz_inhib.enzyme_reaction_organism.reaction})
    data.append({'field_name': 'Organism', 'data': enz_inhib.enzyme_reaction_organism.organism})
    data.append({'field_name': 'Inhibiting metabolite', 'data': enz_inhib.inhibitor_met.name})
    data.append({'field_name': 'Inhibition type', 'data': enz_inhib.inhibition_type})
    data.append({'field_name': 'Affected metabolite', 'data': enz_inhib.affected_met.name})
    data.append({'field_name': 'Inhibition constant', 'data': enz_inhib.inhibition_constant})
    data.append({'field_name': 'Evidence level', 'data': enz_inhib.evidence})
    data.append({'field_name': 'Comments', 'data': enz_inhib.comments})

    models = [model.name for model in enz_inhib.models]
    data_nested.append({'field_name': 'Models', 'data': models if models else ['NA']})

    references = [ref.doi for ref in enz_inhib.references]
    data_nested.append({'field_name': 'References', 'data': references if references else ['NA']})

    form = ModifyDataForm()
    if form.validate_on_submit():
        return redirect(url_for('main.modify_enzyme_inhibitor', inhibitor_id=inhibitor_id))

    return render_template("see_data_element.html", title='See enzyme inhibitor', data_name='Inhibitor',
                           data_type='inhibitor', data_list=data, data_list_nested=data_nested, form=form)


@bp.route('/see_enzyme_activators_list')
@login_required
def see_enzyme_activators_list():
    tab_status = {"enzymes": "#", "metabolites": "#", "models": "#", "organisms": "#", "reactions": "#",
                  "enzyme_inhibitors:": "#", "enzyme_activators:": "active", "enzyme_effectors:": "#",
                  "enzyme_misc_info:": "#", "model_assumptions": "#"}
    header = Markup("<th>ID</th> \
                    <th>Activator</th> \
                    <th>Enzyme</th> \
                    <th>Reaction</th> \
                    <th>Organism</th>")

    # enzyme_header = Enzyme.__table__.columns.keys()
    page = request.args.get('page', 1, type=int)
    enzyme_activators = EnzymeReactionActivation.query.order_by(EnzymeReactionActivation.id.asc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.see_enzyme_activators_list', page=enzyme_activators.next_num) \
        if enzyme_activators.has_next else None
    prev_url = url_for('main.see_enzyme_activatorslist', page=enzyme_activators.prev_num) \
        if enzyme_activators.has_prev else None
    return render_template("see_data.html", title='See enzyme activators', data=enzyme_activators.items,
                           data_type='enzyme_activators', tab_status=tab_status, header=header,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/see_enzyme_activator/<activator_id>', methods=['GET', 'POST'])
@login_required
def see_enzyme_activator(activator_id):
    enz_activator = EnzymeReactionActivation.query.filter_by(id=activator_id).first()

    data = []
    data_nested = []

    data.append({'field_name': 'Isoenzyme', 'data': enz_activator.enzyme_reaction_organism.enzyme.isoenzyme})
    data.append({'field_name': 'Reaction', 'data': enz_activator.enzyme_reaction_organism.reaction})
    data.append({'field_name': 'Organism', 'data': enz_activator.enzyme_reaction_organism.organism})
    data.append({'field_name': 'Activating metabolite', 'data': enz_activator.activator_met.name})
    data.append({'field_name': 'Activation constant', 'data': enz_activator.activation_constant})
    data.append({'field_name': 'Evidence level', 'data': enz_activator.evidence})
    data.append({'field_name': 'Comments', 'data': enz_activator.comments})

    models = [model.name for model in enz_activator.models]
    data_nested.append({'field_name': 'Models', 'data': models if models else ['NA']})

    references = [ref.doi for ref in enz_activator.references]
    data_nested.append({'field_name': 'References', 'data': references if references else ['NA']})

    form = ModifyDataForm()
    if form.validate_on_submit():
        return redirect(url_for('main.modify_enzyme_activator', activator_id=activator_id))

    return render_template("see_data_element.html", title='See enzyme activator', data_name='Activator',
                           data_type='activator', data_list=data, data_list_nested=data_nested, form=form)


@bp.route('/see_enzyme_effectors_list')
@login_required
def see_enzyme_effectors_list():
    tab_status = {"enzymes": "#", "metabolites": "#", "models": "#", "organisms": "#", "reactions": "#",
                  "enzyme_inhibitors:": "#", "enzyme_activators:": "#", "enzyme_effectors:": "active",
                  "enzyme_misc_info:": "#", "model_assumptions": "#"}
    header = Markup("<th>ID</th> \
                    <th>Effector</th> \
                    <th>Type</th> \
                    <th>Enzyme</th> \
                    <th>Reaction</th> \
                    <th>Organism</th>")

    # enzyme_header = Enzyme.__table__.columns.keys()
    page = request.args.get('page', 1, type=int)
    enzyme_effector_list = EnzymeReactionEffector.query.order_by(EnzymeReactionEffector.id.asc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.see_enzyme_effector_list', page=enzyme_effector_list.next_num) \
        if enzyme_effector_list.has_next else None
    prev_url = url_for('main.see_enzyme_effector_list', page=enzyme_effector_list.prev_num) \
        if enzyme_effector_list.has_prev else None
    return render_template("see_data.html", title='See enzyme effectors', data=enzyme_effector_list.items,
                           data_type='enzyme_effectors', tab_status=tab_status, header=header,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/see_enzyme_effector/<effector_id>', methods=['GET', 'POST'])
@login_required
def see_enzyme_effector(effector_id):
    enz_effector = EnzymeReactionEffector.query.filter_by(id=effector_id).first()

    data = []
    data_nested = []

    data.append({'field_name': 'Isoenzyme', 'data': enz_effector.enzyme_reaction_organism.enzyme.isoenzyme})
    data.append({'field_name': 'Reaction', 'data': enz_effector.enzyme_reaction_organism.reaction})
    data.append({'field_name': 'Organism', 'data': enz_effector.enzyme_reaction_organism.organism})
    data.append({'field_name': 'Effector metabolite', 'data': enz_effector.effector_met.name})
    data.append({'field_name': 'Effector type', 'data': enz_effector.effector_type})
    data.append({'field_name': 'Evidence level', 'data': enz_effector.evidence})
    data.append({'field_name': 'Comments', 'data': enz_effector.comments})

    models = [model.name for model in enz_effector.models]
    data_nested.append({'field_name': 'Models', 'data': models if models else ['NA']})

    references = [ref.doi for ref in enz_effector.references]
    data_nested.append({'field_name': 'References', 'data': references if references else ['NA']})

    form = ModifyDataForm()

    if form.validate_on_submit():
        print('valid')
        print(form.is_submitted())
        print(url_for('main.modify_enzyme_effector', effector_id=effector_id))
        return redirect(url_for('main.modify_enzyme_effector', effector_id=effector_id))

    return render_template("see_data_element.html", title='See enzyme effector', data_name='Effector',
                           data_type='effector', data_list=data, data_list_nested=data_nested, form=form)


@bp.route('/see_enzyme_misc_info_list')
@login_required
def see_enzyme_misc_info_list():
    tab_status = {"enzymes": "#", "metabolites": "#", "models": "#", "organisms": "#", "reactions": "#",
                  "enzyme_inhibitors:": "#", "enzyme_activators:": "#", "enzyme_effectors:": "#",
                  "enzyme_misc_info:": "active", "model_assumptions": "#"}
    header = Markup("<th>ID</th> \
                    <th>Topic</th> \
                    <th>Enzyme</th> \
                    <th>Reaction</th> \
                    <th>Organism</th>")

    # enzyme_header = Enzyme.__table__.columns.keys()
    page = request.args.get('page', 1, type=int)
    enzyme_misc_info = EnzymeReactionMiscInfo.query.order_by(EnzymeReactionMiscInfo.id.asc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.see_enzyme_misc_info_list', page=enzyme_misc_info.next_num) \
        if enzyme_misc_info.has_next else None
    prev_url = url_for('main.see_enzyme_misc_info_list', page=enzyme_misc_info.prev_num) \
        if enzyme_misc_info.has_prev else None
    return render_template("see_data.html", title='See enzyme misc info', data=enzyme_misc_info.items,
                           data_type='enzyme_misc_info', tab_status=tab_status, header=header,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/see_enzyme_misc_info/<misc_info_id>', methods=['GET', 'POST'])
@login_required
def see_enzyme_misc_info(misc_info_id):
    enz_misc_info = EnzymeReactionMiscInfo.query.filter_by(id=misc_info_id).first()

    data = []
    data_nested = []

    data.append({'field_name': 'Isoenzyme', 'data': enz_misc_info.enzyme_reaction_organism.enzyme.isoenzyme})
    data.append({'field_name': 'Reaction', 'data': enz_misc_info.enzyme_reaction_organism.reaction})
    data.append({'field_name': 'Organism', 'data': enz_misc_info.enzyme_reaction_organism.organism})
    data.append({'field_name': 'Topic', 'data': enz_misc_info.topic})
    data.append({'field_name': 'Description', 'data': enz_misc_info.description})
    data.append({'field_name': 'Evidence level', 'data': enz_misc_info.evidence})
    data.append({'field_name': 'Comments', 'data': enz_misc_info.comments})

    models = [model.name for model in enz_misc_info.models]
    data_nested.append({'field_name': 'Models', 'data': models if models else ['NA']})

    references = [ref.doi for ref in enz_misc_info.references]
    data_nested.append({'field_name': 'References', 'data': references if references else ['NA']})

    form = ModifyDataForm()
    if form.validate_on_submit():
        return redirect(url_for('main.modify_enzyme_misc_info', misc_info_id=misc_info_id))

    return render_template("see_data_element.html", title='See enzyme misc info', data_name='Misc info',
                           data_type='misc_info', data_list=data, data_list_nested=data_nested, form=form)


@bp.route('/see_gene_list')
@login_required
def see_gene_list():
    tab_status = {"enzymes": "#", "metabolites": "#", "models": "active", "organisms": "#", "reactions": "#",
                  "enzyme_inhibitors:": "#", "enzyme_activators:": "#", "enzyme_effectors:": "#",
                  "enzyme_misc_info:": "#", "model_assumptions": "#"}
    header = ''

    page = request.args.get('page', 1, type=int)
    genes = Gene.query.order_by(Gene.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.see_gene_list', page=genes.next_num) \
        if genes.has_next else None
    prev_url = url_for('main.see_gene_list', page=genes.prev_num) \
        if genes.has_prev else None
    return render_template("see_data.html", title='See genes', data=genes.items,
                           data_type='gene', tab_status=tab_status, header=header,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/see_metabolite_list')
@login_required
def see_metabolite_list():
    tab_status = {"enzymes": "#", "metabolites": "active", "models": "#", "organisms": "#", "reactions": "#",
                  "enzyme_inhibitors:": "#", "enzyme_activators:": "#", "enzyme_effectors:": "#",
                  "enzyme_misc_info:": "#", "model_assumptions": "#"}
    header = Markup("<th>GRASP ID</th> \
                    <th>Name</th> \
                    <th>Bigg ID</th> \
                    <th>MetanetX ID</th> \
                    <th>Compartment</th>")

    page = request.args.get('page', 1, type=int)
    metabolites = Metabolite.query.order_by(Metabolite.grasp_id.asc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.see_metabolite_list', page=metabolites.next_num) \
        if metabolites.has_next else None
    prev_url = url_for('main.see_metabolite_list', page=metabolites.prev_num) \
        if metabolites.has_prev else None
    return render_template("see_data.html", title='See metabolites', data=metabolites.items,
                           data_type='metabolite', tab_status=tab_status, header=header,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/see_metabolite/<grasp_id>', methods=['GET', 'POST'])
@login_required
def see_metabolite(grasp_id):
    metabolite = Metabolite.query.filter_by(grasp_id=grasp_id).first()

    data = []
    data_nested = []

    data.append({'field_name': 'Name', 'data': metabolite.name})
    data.append({'field_name': 'GRASP ID', 'data': metabolite.grasp_id})
    data.append({'field_name': 'Bigg ID', 'data': metabolite.bigg_id})
    data.append({'field_name': 'MetanetX ID', 'data': metabolite.metanetx_id})
    data.append(
        {'field_name': 'Compartment', 'data': ' ,'.join([str(compartment) for compartment in metabolite.compartments])})

    chebi_list = [str(chebi.chebi_id) for chebi in metabolite.chebis]
    data.append({'field_name': 'ChEBIs', 'data': chebi_list if chebi_list else ''})
    inchi_list = [str(chebi.inchi) for chebi in metabolite.chebis]
    data.append({'field_name': 'InChis', 'data': inchi_list if inchi_list else ''})

    data_nested.append({'field_name': 'Reactions', 'data': [str(rxn_met.reaction) for rxn_met in metabolite.reactions]})

    form = ModifyDataForm()
    if form.validate_on_submit():
        return redirect(url_for('main.modify_metabolite', grasp_id=metabolite.grasp_id, title='Modify metabolite'))

    return render_template("see_data_element.html", title='See metabolite', data_name=metabolite,
                           data_type='metabolite', form=form,
                           data_list=data, data_list_nested=data_nested)


@bp.route('/see_model_list')
@login_required
def see_model_list():
    tab_status = {"enzymes": "#", "metabolites": "#", "models": "active", "organisms": "#", "reactions": "#",
                  "enzyme_inhibitors:": "#", "enzyme_activators:": "#", "enzyme_effectors:": "#",
                  "enzyme_misc_info:": "#", "model_assumptions": "#"}
    header = Markup("<th>Name</th> \
                    <th>Organism</th> \
                    <th>Strain</th>")

    page = request.args.get('page', 1, type=int)
    models = Model.query.order_by(Model.name.asc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.see_model_list', page=models.next_num) \
        if models.has_next else None
    prev_url = url_for('main.see_model_list', page=models.prev_num) \
        if models.has_prev else None
    return render_template("see_data.html", title='See models', data=models.items,
                           data_type='model', tab_status=tab_status, header=header,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/see_model/<model_name>', methods=['GET', 'POST'])
@login_required
def see_model(model_name):
    model = Model.query.filter_by(name=model_name).first()

    data = []
    data_nested = []

    data.append({'field_name': 'Name', 'data': model.name})
    data.append({'field_name': 'Organism', 'data': model.organism_name})
    data.append({'field_name': 'Strain', 'data': model.strain})
    data.append({'field_name': 'Comments', 'data': model.comments})

    assumptions = [assumption for assumption in model.model_assumptions]
    data_nested.append({'field_name': 'Assumptions', 'data': [', '.join(assumptions)] if assumptions else ['NA']})

    # reaction_ids = [enz_rxn_org.reaction_id for enz_rxn_org in model.enzyme_reaction_organisms]
    # reactions = [str(reaction) for reaction in Reaction.query.filter(Reaction.id.in_(reaction_ids))]

    if model.enzyme_reaction_organisms:
        reaction_data = []
        for enz_rxn_org in model.enzyme_reaction_organisms:
            reaction_data.append(enz_rxn_org)
            for inhibitor in enz_rxn_org.enzyme_reaction_inhibitors:
                if model.has_enzyme_reaction_inhibitor(inhibitor):
                    reaction_data.append('-> ' + str(inhibitor))

            for activator in enz_rxn_org.enzyme_reaction_activators:
                if model.has_enzyme_reaction_activator(activator):
                    reaction_data.append('-> ' + str(activator))

            for effector in enz_rxn_org.enzyme_reaction_effectors:
                if model.has_enzyme_reaction_effector(effector):
                    reaction_data.append('-> ' + str(effector))

            for misc_info in enz_rxn_org.enzyme_reaction_misc_infos:
                if model.has_enzyme_reaction_misc_info(misc_info):
                    reaction_data.append('-> ' + str(misc_info))

        # data_nested.append({'field_name': 'Reactions', 'data': model.enzyme_reaction_organisms if model.enzyme_reaction_organisms else ['NA']})
        data_nested.append({'field_name': 'Reactions', 'data': reaction_data})
    else:
        data_nested.append({'field_name': 'Reactions', 'data': ['NA']})

    form = ModifyDataForm()
    if form.validate_on_submit():
        return redirect(url_for('main.modify_model', model_name=model_name, title='Modify model'))

    return render_template("see_data_element.html", title='See model', data_name=model.name, data_type='model',
                           data_list=data, data_list_nested=data_nested, form=form)


@bp.route('/see_model_assumptions_list')
@login_required
def see_model_assumptions_list():
    tab_status = {"enzymes": "#", "metabolites": "#", "models": "#", "organisms": "#", "reactions": "#",
                  "enzyme_inhibitors:": "#", "enzyme_activators:": "#", "enzyme_effectors:": "#",
                  "enzyme_misc_info:": "#", "model_assumptions": "active"}

    header = Markup("<th>ID</th> \
                    <th>Assumption</th> \
                    <th>Model</th>")

    page = request.args.get('page', 1, type=int)
    model_assumptions = ModelAssumptions.query.order_by(ModelAssumptions.assumption.asc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.see_model_assumptions_list', page=model_assumptions.next_num) \
        if model_assumptions.has_next else None
    prev_url = url_for('main.see_model_assumptions_list', page=model_assumptions.prev_num) \
        if model_assumptions.has_prev else None
    return render_template("see_data.html", title='See model assumptions', data=model_assumptions.items,
                           data_type='model_assumptions', tab_status=tab_status, header=header,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/see_model_assumption/<model_assumption_id>', methods=['GET', 'POST'])
@login_required
def see_model_assumption(model_assumption_id):
    model_assumption = ModelAssumptions.query.filter_by(id=model_assumption_id).first()

    data = []
    data_nested = []

    data.append({'field_name': 'Assumption', 'data': model_assumption.assumption})
    data.append({'field_name': 'Description', 'data': model_assumption.description})
    data.append({'field_name': 'Evidence level', 'data': model_assumption.evidence.name})
    data.append({'field_name': 'Included in model', 'data': model_assumption.included_in_model})
    data.append({'field_name': 'Comments', 'data': model_assumption.comments})

    references = [ref.doi for ref in model_assumption.references]
    data_nested.append({'field_name': 'References', 'data': references if references else ['NA']})

    form = ModifyDataForm()
    if form.validate_on_submit():
        return redirect(url_for('main.modify_model_assumption', model_assumption_id=model_assumption_id))

    return render_template("see_data_element.html", title='See model assumption', data_name=model_assumption,
                           data_type='model_assumption', data_list=data, data_list_nested=data_nested, form=form)


@bp.route('/see_organism_list')
@login_required
def see_organism_list():
    tab_status = {"enzymes": "#", "metabolites": "#", "models": "#", "organisms": "active", "reactions": "#",
                  "enzyme_inhibitors:": "#", "enzyme_activators:": "#", "enzyme_effectors:": "#",
                  "enzyme_misc_info:": "#", "model_assumptions": "#"}
    header = Markup("<th>Name</th>")

    page = request.args.get('page', 1, type=int)
    organisms = Organism.query.order_by(Organism.name.asc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.see_organism_list', page=organisms.next_num) \
        if organisms.has_next else None
    prev_url = url_for('main.see_organism_list', page=organisms.prev_num) \
        if organisms.has_prev else None
    return render_template("see_data.html", title='See organisms', data=organisms.items,
                           data_type='organism', tab_status=tab_status, header=header,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/see_organism/<organism_name>', methods=['GET', 'POST'])
@login_required
def see_organism(organism_name):
    organism = Organism.query.filter_by(name=organism_name).first()

    data = []
    data_nested = []

    data.append({'field_name': 'Name', 'data': organism.name})
    models = [model.name for model in organism.models]
    data_nested.append({'field_name': 'Models', 'data': models if models else ['NA']})

    form = ModifyDataForm()
    if form.validate_on_submit():
        return redirect(url_for('main.modify_organism', organism_name=organism_name))

    return render_template("see_data_element.html", title='See organism', data_name=organism.name, data_type='organism',
                           data_list=data, data_list_nested=data_nested, form=form)


@bp.route('/see_reaction_list')
@login_required
def see_reaction_list():
    tab_status = {"enzymes": "#", "metabolites": "#", "models": "#", "organisms": "#", "reactions": "active",
                  "enzyme_inhibitors:": "#", "enzyme_activators:": "#", "enzyme_effectors:": "#",
                  "enzyme_misc_info:": "#", "model_assumptions": "#"}
    header = Markup("<th>Name</th> \
                    <th>Acronym</th> \
                    <th>Reaction</th> \
                    <th>MetanetX ID</th> \
                    <th>Bigg ID</th> \
                    <th>KEGG ID</th> \
                    <th>Compartment</th>")

    page = request.args.get('page', 1, type=int)
    reactions = Reaction.query.order_by(Reaction.name.asc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.see_reaction_list', page=reactions.next_num) \
        if reactions.has_next else None
    prev_url = url_for('main.see_reaction_list', page=reactions.prev_num) \
        if reactions.has_prev else None
    return render_template("see_data.html", title='See reactions', data=reactions.items,
                           data_type='reaction', tab_status=tab_status, header=header,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/see_reaction/<reaction_acronym>', methods=['GET', 'POST'])
@login_required
def see_reaction(reaction_acronym):
    reaction = Reaction.query.filter_by(acronym=reaction_acronym).first()

    data = []
    data_nested = []

    data.append({'field_name': 'Name', 'data': reaction.name})
    data.append({'field_name': 'Acronym', 'data': reaction.acronym})
    data.append({'field_name': 'Reaction', 'data': str(reaction)})
    data.append({'field_name': 'MetanetX ID', 'data': reaction.metanetx_id})
    data.append({'field_name': 'KEGG id', 'data': reaction.kegg_id})
    data.append({'field_name': 'Compartment', 'data': reaction.compartment_name})

    enzyme_ids = [enz_rxn_org.enzyme_id for enz_rxn_org in reaction.enzyme_reaction_organisms]
    enzymes = [enz.isoenzyme for enz in Enzyme.query.filter(Enzyme.id.in_(enzyme_ids)).all()]
    data.append({'field_name': 'Catalyzing isoenzymes', 'data': ', '.join(enzymes) if enzymes else 'NA'})

    # TODO catalyzing genes

    gibbs_energies = [str(gibbs_energy_rxn_model.gibbs_energy) + ' (' + str(gibbs_energy_rxn_model.model.name) + ')' for
                      gibbs_energy_rxn_model in reaction.gibbs_energy_reaction_models]
    data_nested.append({'field_name': 'Gibbs energies', 'data': gibbs_energies if gibbs_energies else ['NA']})

    enz_rxn_org_models = [enz_rxn_org.models for enz_rxn_org in reaction.enzyme_reaction_organisms]
    models = [item.name for sublist in enz_rxn_org_models for item in sublist]
    data.append({'field_name': 'Models', 'data': ', '.join(models) if models else 'NA'})

    organisms = [enz_rxn_org.organism.name for enz_rxn_org in reaction.enzyme_reaction_organisms]
    data.append({'field_name': 'Organisms', 'data': ', '.join(organisms) if organisms else 'NA'})

    form = ModifyDataForm()
    if form.validate_on_submit():
        return redirect(url_for('main.modify_reaction_select_organism', reaction_acronym=reaction_acronym))

    return render_template("see_data_element.html", title='See reaction', data_name=reaction.acronym,
                           data_type='reaction',
                           data_list=data, data_list_nested=data_nested, form=form)
