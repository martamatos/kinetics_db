from datetime import datetime
from app.main.forms import EditProfileForm, PostForm, EnzymeForm, GeneForm, ModelForm, OrganismForm, ReactionForm
from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_required
from app import current_app, db
from app.models import User, Post, Compartment, Enzyme, EnzymeReactionModel, EnzymeOrganism, EnzymeStructure, EvidenceLevel, Gene, \
    GibbsEnergy, Mechanism, Metabolite, Model, Organism, Reaction, ReactionMetabolite, Reference
from app.main import bp
from app.utils.parsers import ReactionParser, parse_input_list
import re


@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.index', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title='Home', form=form,
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url)


@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.user', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.user', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)


@bp.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('main.index'))
    if user == current_user:
        flash('You cannot follow yourself!')
        return redirect(url_for('main.user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash('You are following {}!'.format(username))
    return redirect(url_for('main.user', username=username))


@bp.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('main.index'))
    if user == current_user:
        flash('You cannot unfollow yourself!')
        return redirect(url_for('main.user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash('You are not following {}.'.format(username))
    return redirect(url_for('main.user', username=username))


@bp.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.explore', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template("index.html", title='Explore', posts=posts.items,
                           next_url=next_url, prev_url=prev_url)

def _add_enzyme_organism(enzyme, organism_id, uniprot_id_list, gene_bigg_ids, number_of_active_sites):
    for uniprot_id in uniprot_id_list:
        enzyme_organism_db = EnzymeOrganism.query.filter_by(uniprot_id=uniprot_id).first()
        if not enzyme_organism_db:
            enzyme_organism_db = EnzymeOrganism(enzyme_id=enzyme.id,
                                                organism_id=organism_id,
                                                uniprot_id=uniprot_id,
                                                n_active_sites=number_of_active_sites)
            db.session.add(enzyme_organism_db)
        enzyme.add_enzyme_organism(enzyme_organism_db)

        # populate genes
        if gene_bigg_ids:
            gene_bigg_ids_list = parse_input_list(gene_bigg_ids)
            for gene_id in gene_bigg_ids_list:
                gene_id_db = Gene.query.filter_by(bigg_id=gene_id).first()
                if not gene_id_db:
                    gene_id_db = Gene(bigg_id=gene_id)
                    db.session.add(gene_id_db)

                enzyme_organism_db.add_encoding_genes(gene_id_db)


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
    gene_bigg_ids = {'id_value': '#gene_bigg_ids', 'input_data': [{'field1': gene.bigg_id} for gene in genes] if genes else []}

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

            # populate enzyme_structure
            if form.pdb_structure_ids.data:
                pdb_id_list = parse_input_list(form.pdb_structure_ids.data)
                strain_list = parse_input_list(form.strain.data)
                _add_enzyme_structures(enzyme, organism_id, pdb_id_list, strain_list)

            # populate enzyme_organism
            if form.uniprot_id_list.data:
                uniprot_id_list = parse_input_list(form.uniprot_id_list.data)
                _add_enzyme_organism(enzyme, organism_id, uniprot_id_list, form.gene_bigg_ids.data, form.number_of_active_sites.data)


        db.session.commit()
        flash('Your enzyme is now live!')
        return redirect(url_for('main.see_enzymes'))
    return render_template('add_data.html', title='Add enzyme', form=form, header='enzyme', data_list=data_list)


@bp.route('/add_gene', methods=['GET', 'POST'])
@login_required
def add_gene():
    form = GeneForm()
    if form.validate_on_submit():
        gene = Enzyme(name=form.name.data,
                      bigg_id=form.bigg_id.data)
        db.session.add(gene)
        db.session.commit()
        flash('Your enzyme is now live!')
        return redirect(url_for('main.see_enzymes'))
    return render_template('add_data.html', title='Add gene', form=form, header='gene')


@bp.route('/add_model', methods=['GET', 'POST'])
@login_required
def add_model():
    form = ModelForm()

    organisms = Organism.query.all()
    organism_name = {'id_value': '#organism_name', 'input_data': [{'field1': organism.name} for organism in organisms] if organisms else []}
    data_list = [organism_name]

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

        flash('Your model is now live!')
        return redirect(url_for('main.see_models'))
    # return render_template('add_data.html', title='Add model', form=form, header='model', data_id_list=id_list, data_list=organism_data)
    return render_template('add_data.html', title='Add model', form=form, header='model', data_list=data_list)


@bp.route('/add_organism', methods=['GET', 'POST'])
@login_required
def add_organism():
    form = OrganismForm()

    if form.validate_on_submit():
        organism = Organism(name=form.name.data)
        db.session.add(organism)
        db.session.commit()

        flash('Your organism is now live!', 'success')

        return redirect(url_for('main.see_organisms'))
    return render_template('add_data.html', title='Add organism', form=form, header='organism')


def add_metabolites_to_reaction(reaction, reaction_string):
    reversible, stoichiometry = ReactionParser().parse_reaction(reaction_string)
    # (True, OrderedDict([('m_pep_c', -1.0), ('m_adp_c', -1.5), ('m_pyr_c', 1.0), ('m_atp_m', 2.0)]))

    for met, stoich_coef in stoichiometry.items():
        try:
            bigg_id = re.findall('(\w+)_(?:\S+)', met)[0]
        except IndexError:
                print('Did you specify all metabolites in the reaction as met_compartment?', 'danger')
                return redirect(url_for('main.add_reactions'))

        met_db = Metabolite.query.filter_by(bigg_id=bigg_id).first()

        if not met_db:
            try:
                compartment_acronym = re.findall('(?:\S+)_(\w+)', met)[0]
            except IndexError:
                print('Did you specify all metabolites in the reaction as met_compartment?', 'danger')
                return redirect(url_for('main.add_reactions'))


            met_db = Metabolite(bigg_id=bigg_id,
                                grasp_id=bigg_id,
                                compartment_acronym=compartment_acronym)

            db.session.add(met_db)

            reaction.add_metabolite(met_db, stoich_coef)

    return reaction

def _add_gibbs_energy(standard_dg, standard_dg_std, standard_dg_ph, standard_dg_is, std_gibbs_energy_references, enzyme_reaction_model):

    gibbs_energy_db = GibbsEnergy.query.filter_by(standard_dg=standard_dg,
                                                  standard_dg_std=standard_dg_std,
                                                  ph=standard_dg_ph,
                                                  ionic_strength=standard_dg_is).first()

    if not gibbs_energy_db:
        gibbs_energy_db = GibbsEnergy(standard_dg=standard_dg,
                                      standard_dg_std=standard_dg_std,
                                      ph=standard_dg_ph,
                                      ionic_strength=standard_dg_is)

        db.session.add(gibbs_energy_db)
        db.session.commit()

    if enzyme_reaction_model:
        enzyme_reaction_model.gibbs_energy_id = gibbs_energy_db.id

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
    Entity EnzymeReactionModel() is only created if either isoenzymes or model_id are provided besides the reaction.

    :return:
    """

    form = ReactionForm()

    enzymes = Enzyme.query.all()
    isoenzyme_list = {'id_value': '#isoenzyme_acronyms', 'input_data': [{'field1': enzyme.isoenzyme} for enzyme in enzymes] if enzymes else []}
    data_list = [isoenzyme_list]


    if form.validate_on_submit():

        compartment_name = form.compartment_name.data.name if form.compartment_name.data else ''
        reaction = Reaction(name=form.name.data,
                            acronym=form.acronym.data,
                            metanetx_id=form.metanetx_id.data,
                            bigg_id=form.bigg_id.data,
                            kegg_id=form.kegg_id.data,
                            compartment_name=compartment_name)

        db.session.add(reaction)

        add_metabolites_to_reaction(reaction, form.reaction_string.data)

        if form.compartment_name.data:
            compartment = Compartment.query.filter_by(name=compartment_name).first()
            compartment.add_reaction(reaction)

        model_id = form.model_name.data.id if form.model_name.data else ''
        mechanism_id = form.mechanism.data.id if form.mechanism.data else ''
        mech_evidence_level_id = form.mechanism_evidence_level.data.id if form.mechanism_evidence_level.data else ''
        included_in_model = True if form.model_name.data else False

        if form.isoenzyme_acronyms.data:
            isoenzyme_list = parse_input_list(form.isoenzyme_acronyms.data)

            for isoenzyme in isoenzyme_list:
                enzyme_db = Enzyme.query.filter_by(isoenzyme=isoenzyme).first()


                enzyme_reaction_model = EnzymeReactionModel(enzyme_id=enzyme_db.id,
                                                            reaction_id = reaction.id,
                                                            model_id=model_id,
                                                            mechanism_id= mechanism_id,
                                                            mech_evidence_level_id=mech_evidence_level_id,
                                                            grasp_id=form.grasp_id.data,
                                                            included_in_model=included_in_model,
                                                            subs_binding_order=form.subs_binding_order.data,
                                                            prod_release_order=form.prod_release_order.data)
                db.session.add(enzyme_reaction_model)

                if form.mechanism_references.data:
                    _add_mechanism(form.mechanism_references.data, enzyme_reaction_model)

                if form.std_gibbs_energy.data:
                    _add_gibbs_energy(form.std_gibbs_energy.data, form.std_gibbs_energy_std.data, form.std_gibbs_energy_ph.data, form.std_gibbs_energy_ionic_strength.data, form.std_gibbs_energy_references.data, enzyme_reaction_model)

        elif model_id:
            enzyme_reaction_model = EnzymeReactionModel(enzyme_id='',
                                                        reaction_id = reaction.id,
                                                        model_id=model_id,
                                                        mechanism_id=mechanism_id,
                                                        mech_evidence_level_id=mech_evidence_level_id,
                                                        grasp_id=form.grasp_id.data,
                                                        included_in_model=included_in_model,
                                                        subs_binding_order=form.subs_binding_order.data,
                                                        prod_release_order=form.prod_release_order.data)
            db.session.add(enzyme_reaction_model)

            if form.mechanism_references.data:
                    _add_mechanism(form.mechanism_references.data, enzyme_reaction_model)

            if form.std_gibbs_energy.data:
                _add_gibbs_energy(form.std_gibbs_energy.data, form.std_gibbs_energy_std.data, form.std_gibbs_energy_ph.data, form.std_gibbs_energy_ionic_strength.data, form.std_gibbs_energy_references.data, enzyme_reaction_model)

        db.session.commit()


        flash('Your reaction is now live!', 'success')

        return redirect(url_for('main.see_reactions'))
    return render_template('add_data.html', title='Add reaction', form=form, header='reaction', data_list=data_list)



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


