from app.main.forms import  EnzymeForm, GeneForm, ModelForm, OrganismForm, ReactionForm
from flask import render_template, flash, redirect, url_for, request
from flask_login import  login_required
from app import current_app, db
from app.models import  Compartment, Enzyme, EnzymeReactionOrganism, EnzymeOrganism, EnzymeStructure, EvidenceLevel, Gene, \
    GibbsEnergy, Mechanism, Metabolite, Model, Organism, Reaction, ReactionMetabolite, Reference
from app.main import bp
from flask import Markup



@bp.route('/see_enzyme_list')
@login_required
def see_enzyme_list():
    tab_status = {"enzymes": "active", "metabolites": "#",  "models": "#", "organisms": "#", "reactions": "#"}
    header = Markup("<th>Name</th> <th>Acronym</th> <th>Isoenzyme</th> <th>EC number</th>")

    #enzyme_header = Enzyme.__table__.columns.keys()
    page = request.args.get('page', 1, type=int)
    enzymes = Enzyme.query.order_by(Enzyme.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.see_enzyme_list', page=enzymes.next_num) \
        if enzymes.has_next else None
    prev_url = url_for('main.see_enzyme_list', page=enzymes.prev_num) \
        if enzymes.has_prev else None
    return render_template("see_data.html", title='See enzymes', data=enzymes.items,
                           data_type='enzyme', tab_status=tab_status, header=header,
                           next_url=next_url, prev_url=prev_url)



@bp.route('/see_enzyme/<isoenzyme>')
@login_required
def see_enzyme(isoenzyme):
    tab_status = {"enzymes": "active", "metabolites": "#",  "models": "#", "organisms": "#", "reactions": "#"}
    header = Markup("<th>Name</th> <th>Acronym</th> <th>Isoenzyme</th> <th>EC number</th>")
    print('aaalooooo')
    enzyme = Enzyme.query.filter_by(isoenzyme=isoenzyme).first()
    print(enzyme)


    return render_template("see_data_element.html", title='See enzymes', data_point=enzyme,
                           data_type='enzyme')




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
    header = ''

    page = request.args.get('page', 1, type=int)
    metabolites = Metabolite.query.order_by(Metabolite.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.see_metabolite_list', page=metabolites.next_num) \
        if metabolites.has_next else None
    prev_url = url_for('main.see_metabolite_list', page=metabolites.prev_num) \
        if metabolites.has_prev else None
    return render_template("see_data.html", title='See metabolites', data=metabolites.items,
                           data_type='metabolite', tab_status=tab_status, header=header,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/see_model_list')
@login_required
def see_model_list():
    tab_status = {"enzymes": "#", "metabolites": "#",  "models": "active", "organisms": "#", "reactions": "#"}
    header = ''

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


@bp.route('/see_organism_list')
@login_required
def see_organism_list():
    tab_status = {"enzymes": "#", "metabolites": "#",  "models": "#", "organisms": "active", "reactions": "#"}
    header = ''

    page = request.args.get('page', 1, type=int)
    organisms = Organism.query.order_by(Organism.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.see_organism_list', page=organisms.next_num) \
        if organisms.has_next else None
    prev_url = url_for('main.see_organism_list', page=organisms.prev_num) \
        if organisms.has_prev else None
    return render_template("see_data.html", title='See organisms', data=organisms.items,
                           data_type='organism', tab_status=tab_status, header=header,
                           next_url=next_url, prev_url=prev_url)



@bp.route('/see_reaction_list')
@login_required
def see_reaction_list():
    tab_status = {"enzymes": "#", "metabolites": "#",  "models": "#", "organisms": "#", "reactions": "active"}
    header = ''

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

