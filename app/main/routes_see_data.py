from app.main.forms import  EnzymeForm, GeneForm, ModelForm, OrganismForm, ReactionForm, ModifyData
from flask import render_template, flash, redirect, url_for, request
from flask_login import  login_required
from app import current_app, db
from app.models import  Compartment, Enzyme, EnzymeReactionOrganism, EnzymeReactionInhibition, EnzymeReactionActivation, \
    EnzymeReactionEffector, EnzymeReactionMiscInfo, EnzymeOrganism, EnzymeStructure, EvidenceLevel, Gene, \
    GibbsEnergy, Mechanism, Metabolite, Model, Organism, Reaction, ReactionMetabolite, Reference
from app.main.forms import OrganismForm
from app.main import bp
from flask import Markup



@bp.route('/see_enzyme_list')
@login_required
def see_enzyme_list():
    tab_status = {"enzymes": "active", "metabolites": "#",  "models": "#", "organisms": "#", "reactions": "#"}
    header = Markup("<th>Name</th> \
                    <th>Acronym</th> \
                    <th>Isoenzyme</th> \
                    <th>EC number</th>")

    #enzyme_header = Enzyme.__table__.columns.keys()
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

    organism_ids_set = set(enzyme_structures_organism_list + enzyme_organisms_organism_list + enzyme_reaction_organisms_organism_list)

    organisms = [organism.name for organism in Organism.query.filter(Organism.id.in_(organism_ids_set)).all()]
    data.append({'field_name': 'Organisms', 'data': ', '.join(organisms) if organisms else 'NA'})

    enz_rxn_org_models = [enz_rxn_org.models for enz_rxn_org in enzyme_reaction_organism]
    models = [item.name for sublist in enz_rxn_org_models for item in sublist]
    data.append({'field_name': 'Models', 'data': ', '.join(models) if models else 'NA'})

    reactions_ids = [enz_rxn_org.reaction_id for enz_rxn_org in enzyme_reaction_organism]
    reactions = [str(reaction) for reaction in Reaction.query.filter(Reaction.id.in_(reactions_ids)).all()]
    data_nested.append({'field_name': 'Reactions', 'data': reactions})

    enz_rxn_org_id_list = [enz_rxn_org.id for enz_rxn_org in enzyme_reaction_organism]

    inhibitors = EnzymeReactionInhibition.query.filter(EnzymeReactionInhibition.enz_rxn_org_id.in_(enz_rxn_org_id_list)).all()
    data_nested.append({'field_name': 'Inhibitors', 'data': inhibitors})

    activators = EnzymeReactionActivation.query.filter(EnzymeReactionActivation.enz_rxn_org_id.in_(enz_rxn_org_id_list)).all()
    data_nested.append({'field_name': 'Activators', 'data': activators})

    effectors = EnzymeReactionEffector.query.filter(EnzymeReactionEffector.enz_rxn_org_id.in_(enz_rxn_org_id_list)).all()
    data_nested.append({'field_name': 'Effectors', 'data': effectors})

    misc_infos = EnzymeReactionMiscInfo.query.filter(EnzymeReactionMiscInfo.enz_rxn_org_id.in_(enz_rxn_org_id_list)).all()
    data_nested.append({'field_name': 'Misc info', 'data': misc_infos})

    # TODO: add encoding genes

    uniprot_ids = [enz_org.uniprot_id for enz_org in enzyme_organism]
    data.append({'field_name': 'Uniprot IDs', 'data': ', '.join(uniprot_ids) if uniprot_ids else 'NA' })
    pdb_ids = [structure.pdb_id for structure in enzyme_structures]
    data.append({'field_name': 'PDB IDs', 'data': ', '.join(pdb_ids) if pdb_ids else 'NA' })

    form = ModifyData()
    if form.validate_on_submit():
        return redirect(url_for('main.modify_enzyme', isoenzyme=isoenzyme))

    return render_template("see_data_element.html", title='See enzyme', data_name=isoenzyme,  data_type='enzyme',
                           data_list=data, data_list_nested=data_nested, form=form)


@bp.route('/see_gene_list')
@login_required
def see_gene_list():
    tab_status = {"enzymes": "#", "metabolites": "#",  "models": "active", "organisms": "#", "reactions": "#"}
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
    tab_status = {"enzymes": "#", "metabolites": "active",  "models": "#", "organisms": "#", "reactions": "#"}
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
    data.append({'field_name': 'Compartment', 'data': ' ,'.join([str(compartment) for compartment in metabolite.compartments])})

    chebi_list = [str(chebi.chebi_id) for chebi in metabolite.chebis]
    data.append({'field_name': 'ChEBIs', 'data': chebi_list if chebi_list else ''})
    inchi_list = [str(chebi.inchi) for chebi in metabolite.chebis]
    data.append({'field_name': 'InChis', 'data': inchi_list if inchi_list else ''})

    data_nested.append({'field_name': 'Reactions', 'data': [str(rxn_met.reaction) for rxn_met in metabolite.reactions]})


    return render_template("see_data_element.html", title='See metabolite', data_name=metabolite,  data_type='metabolite',
                           data_list=data, data_list_nested=data_nested)


@bp.route('/see_model_list')
@login_required
def see_model_list():
    tab_status = {"enzymes": "#", "metabolites": "#",  "models": "active", "organisms": "#", "reactions": "#"}
    header = Markup("<th>Name</th> \
                    <th>Organism</th> \
                    <th>Strain</th>")


    page = request.args.get('page', 1, type=int)
    models = Model.query.order_by(Model.timestamp.desc()).paginate(
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
    data.append({'field_name': 'Comment', 'data': model.comments})

    assumptions = [assumption for assumption in model.model_assumptions]
    data_nested.append({'field_name': 'Assumptions', 'data': [', '.join(assumptions)] if assumptions else ['NA']})

    reaction_ids = [enz_rxn_org.reaction_id for enz_rxn_org in model.enzyme_reaction_organisms]
    reactions = [str(reaction) for reaction in Reaction.query.filter(Reaction.id.in_(reaction_ids))]
    data_nested.append({'field_name': 'Reactions', 'data': [', '.join(reactions)] if reactions else ['NA']})


    return render_template("see_data_element.html", title='See model', data_name=model.name,  data_type='model',
                           data_list=data, data_list_nested=data_nested)


@bp.route('/see_organism_list')
@login_required
def see_organism_list():
    tab_status = {"enzymes": "#", "metabolites": "#",  "models": "#", "organisms": "active", "reactions": "#"}
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

    form = ModifyData()
    if form.validate_on_submit():
        return redirect(url_for('main.modify_organism', organism_name=organism_name))

    return render_template("see_data_element.html", title='See organism', data_name=organism.name,  data_type='organism',
                           data_list=data, data_list_nested=data_nested, form=form)


@bp.route('/see_reaction_list')
@login_required
def see_reaction_list():
    tab_status = {"enzymes": "#", "metabolites": "#",  "models": "#", "organisms": "#", "reactions": "active"}
    header = Markup("<th>Name</th> \
                    <th>Acronym</th> \
                    <th>Reaction</th> \
                    <th>MetanetX ID</th> \
                    <th>Bigg ID</th> \
                    <th>KEGG ID</th> \
                    <th>Compartment</th>")


    page = request.args.get('page', 1, type=int)
    reactions = Reaction.query.order_by(Reaction.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.reactions', page=reactions.next_num) \
        if reactions.has_next else None
    prev_url = url_for('main.reactions', page=reactions.prev_num) \
        if reactions.has_prev else None
    return render_template("see_data.html", title='See reactions', data=reactions.items,
                           data_type='reaction', tab_status=tab_status,  header=header,
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

    gibbs_energies = [str(gibbs_energy_rxn_model.gibbs_energy) + ' (' + str(gibbs_energy_rxn_model.model.name) + ')' for gibbs_energy_rxn_model in reaction.gibbs_energy_reaction_models]
    data_nested.append({'field_name': 'Gibbs energies', 'data': gibbs_energies if gibbs_energies else 'NA'})

    enz_rxn_org_models = [enz_rxn_org.models for enz_rxn_org in reaction.enzyme_reaction_organisms]
    models = [item.name for sublist in enz_rxn_org_models for item in sublist]
    data.append({'field_name': 'Models', 'data': ', '.join(models) if models else 'NA'})

    organisms = [enz_rxn_org.organism.name for enz_rxn_org in reaction.enzyme_reaction_organisms]
    data.append({'field_name': 'Organisms', 'data': ', '.join(organisms) if organisms else 'NA'})

    form = ModifyData()
    if form.validate_on_submit():
        return redirect(url_for('main.modify_reaction', reaction_acronym=reaction_acronym))


    return render_template("see_data_element.html", title='See reaction', data_name=reaction.acronym,  data_type='reaction',
                           data_list=data, data_list_nested=data_nested, form=form)
