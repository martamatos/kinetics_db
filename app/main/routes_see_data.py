from app.main.forms import  EnzymeForm, GeneForm, ModelForm, OrganismForm, ReactionForm
from flask import render_template, flash, redirect, url_for, request
from flask_login import  login_required
from app import current_app, db
from app.models import  Compartment, Enzyme, EnzymeReactionOrganism, EnzymeOrganism, EnzymeStructure, EvidenceLevel, Gene, \
    GibbsEnergy, Mechanism, Metabolite, Model, Organism, Reaction, ReactionMetabolite, Reference
from app.main import bp



@bp.route('/see_enzymes')
@login_required
def see_enzymes():
    page = request.args.get('page', 1, type=int)
    enzymes = Enzyme.query.order_by(Enzyme.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.see_enzymes', page=enzymes.next_num) \
        if enzymes.has_next else None
    prev_url = url_for('main.see_enzymes', page=enzymes.prev_num) \
        if enzymes.has_prev else None
    return render_template("see_data.html", title='See enzymes', data=enzymes.items,
                           data_type='enzyme', next_url=next_url, prev_url=prev_url)


@bp.route('/see_genes')
@login_required
def see_genes():
    page = request.args.get('page', 1, type=int)
    genes = Gene.query.order_by(Gene.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.see_genes', page=genes.next_num) \
        if genes.has_next else None
    prev_url = url_for('main.see_genes', page=genes.prev_num) \
        if genes.has_prev else None
    return render_template("see_data.html", title='See genes', data=genes.items,
                           data_type='gene', next_url=next_url, prev_url=prev_url)


@bp.route('/see_models')
@login_required
def see_models():
    page = request.args.get('page', 1, type=int)
    models = Model.query.order_by(Model.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.see_models', page=models.next_num) \
        if models.has_next else None
    prev_url = url_for('main.see_models', page=models.prev_num) \
        if models.has_prev else None
    return render_template("see_data.html", title='See models', data=models.items,
                           data_type='model', next_url=next_url, prev_url=prev_url)


@bp.route('/see_organisms')
@login_required
def see_organisms():
    page = request.args.get('page', 1, type=int)
    organisms = Organism.query.order_by(Organism.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.see_organisms', page=organisms.next_num) \
        if organisms.has_next else None
    prev_url = url_for('main.see_organisms', page=organisms.prev_num) \
        if organisms.has_prev else None
    return render_template("see_data.html", title='See organisms', data=organisms.items,
                           data_type='organism', next_url=next_url, prev_url=prev_url)



@bp.route('/see_reactions')
@login_required
def see_reactions():
    page = request.args.get('page', 1, type=int)
    reactions = Reaction.query.order_by(Reaction.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.reactions', page=reactions.next_num) \
        if reactions.has_next else None
    prev_url = url_for('main.reactions', page=reactions.prev_num) \
        if reactions.has_prev else None
    return render_template("see_data.html", title='See reactions', data=reactions.items,
                           data_type='reaction', next_url=next_url, prev_url=prev_url)

