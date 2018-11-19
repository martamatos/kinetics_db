from datetime import datetime

from app.main.forms import EditProfileForm, PostForm, EnzymeForm, GeneForm
from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_required

from app import current_app, db
from app.models import User, Post, Enzyme, Gene
from app.main import bp
import json


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

data_in =[
                {"character": "", "realName": ""},
                {"character": "Wolverine6", "realName": "James Howlett6"},
                {"character": "Cyclops", "realName": "Scott Summers"},
                {"character": "Professor X", "realName": "Charles Francis Xavier"},
                {"character": "Mystique", "realName": "Raven Darkholme"},
                {"character": "Magneto", "realName": "Max Eisenhardt"},
                {"character": "Storm", "realName": "Ororo Monroe"},
                {"character": "Wolverine", "realName": "James Howlett"},
                {"character": "Mystique1", "realName": "Raven Darkholme1"},
                {"character": "Magneto1", "realName": "Max Eisenhardt1"},
                {"character": "Storm1", "realName": "Ororo Monroe1"},
                {"character": "Wolverine1", "realName": "James Howlett1"}
            ]

@bp.route('/add_enzyme', methods=['GET', 'POST'])
@login_required
def add_enzyme():
    form = EnzymeForm()
    genes = Gene.query.all()
    gene_data = [{'name': gene.name, 'bigg_id':gene.bigg_id} for gene in genes]

    if form.validate_on_submit():
        enzyme = Enzyme(name=form.name.data,
                        acronym=form.acronym.data,
                        isoenzyme=form.isoenzyme.data,
                        ec_number=form.ec_number.data)
        db.session.add(enzyme)

        gene = Gene(name=form.gene_name.data,
                    bigg_id=form.gene_bigg_id.data)
        db.session.add(gene)
        enzyme.add_encoding_genes(gene)

        db.session.commit()
        flash('Your enzyme is now live!')
        return redirect(url_for('main.see_enzymes'))
    return render_template('add_data.html', title='Add enzyme', form=form, header='enzyme', data=gene_data)


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

