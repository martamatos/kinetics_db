from datetime import datetime
from hashlib import md5
from app import current_app, db, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from time import time
import jwt

followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    def followed_posts(self):
        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)).filter(
                followers.c.follower_id == self.id)
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.timestamp.desc())

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Post {}>'.format(self.body)


enzyme_gene = db.Table('enzyme_gene',
    db.Column('enzyme_id', db.Integer, db.ForeignKey('enzyme.id')),
    db.Column('gene_id', db.Integer, db.ForeignKey('gene.id'))
)

class Enzyme(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    acronym = db.Column(db.String)
    isoenzyme = db.Column(db.String)
    ec_number = db.Column(db.String)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    #enzyme_structures = db.relationship('EnzymeStructure', back_populates='enzyme')
    genes = db.relationship(
        'Gene', secondary=enzyme_gene,
        primaryjoin=(enzyme_gene.c.enzyme_id == id),
        back_populates='enzymes', lazy='dynamic')

    def add_encoding_genes(self, gene):
        if not self.is_encoded_by(gene):
            self.genes.append(gene)

    def remove_encoding_genes(self, gene):
        if self.is_encoded_by(gene):
            self.genes.remove(gene)

    def is_encoded_by(self, gene):
        return self.genes.filter(
            enzyme_gene.c.gene_id == gene.id).count() > 0


class Gene(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    bigg_id = db.Column(db.String)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    enzymes = db.relationship(
        'Enzyme', secondary=enzyme_gene,
        primaryjoin=(enzyme_gene.c.gene_id == id),
        back_populates='genes', lazy='dynamic')



"""
class Metabolite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    grasp_id = db.Column(db.String)
    name = db.Column(db.String)
    bigg_id = db.Column(db.String)
    metanetx_id = db.Column(db.String)
    kegg_id = db.Column(db.String)
    compartment_id = db.Column(db.Integer, db.ForeignKey('compartment.id'))
    compartment = db.relationship('Compartment', back_populates='metabolites')
    reactions = db.relationship('ReactionMetabolite', back_populates='metabolite')
    chebis = db.relationship(
        'ChebiIds', secondary=metabolite_chebi,
        primaryjoin=(metabolite_chebi.metabolite_id == id),
        back_populates='metabolites')


class Compartment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    abbreviation = db.Column(db.String)
    metabolites = db.relationship('Metabolite', back_populates='compartment')
    reactions = db.relationship('Reactions', back_populates='compartment')


class Reaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Integer)
    metanetx_id = db.Column(db.Integer)
    reactome_id = db.Column(db.Integer)
    bigg_id = db.Column(db.Integer)
    kegg_id = db.Column(db.Integer)
    compartment_id = db.Column(db.Integer, db.ForeignKey('compartment.id'))
    gibbs_energy_id = db.Column(db.Integer, db.ForeignKey('gibbsenergy.id'))
    metabolites = db.relationship('ReactionMetabolite', back_populates='reaction')


class ReactionMetabolite(db.Model):
    reaction_id = db.Column(db.Integer, db.ForeignKey('reaction.id'), primary_key=True)
    metabolite_id = db.Column(db.Integer, db.ForeignKey('metabolite.id'), primary_key=True)
    stoich_coef = db.Column(db.Integer)
    metabolite = db.relationship('Metabolite', back_populates='reactions')
    reaction = db.relationship('Reaction', back_populates='metabolites')

class Organism(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    enzyme_structures = db.relationship('EnzymeStructure', back_populates='organism')
    models = db.relationship('Model', back_populates='organism')


class Model(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    organism_id = db.Column(db.Integer, db.ForeignKey('Organism.id'))
    organism = db.relationship('Organism', back_populates='models')


class GibbsEnergy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    standard_dg = db.Column(db.Float)
    standard_dg_std = db.Column(db.Float)
    ph = db.Column(db.Float)
    ionic_strength = db.Column(db.Float)
    reference_id = db.Column(db.Integer, db.ForeignKey('reference.id'))
    reactions = db.relationship('Reactions', back_populates='gibbsenergy')


class EnzymeStructure(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pdb_id = db.Column(db.String)
    enzyme_id = db.Column(db.String, db.ForeignKey('enzyme.id'))
    enzyme = db.relationship('Enzyme', back_populates='enzyme_structures')
    organism_id = db.Column(db.String, db.ForeignKey('organism.id'))
    organism = db.relationship('Organism', back_populates='enzyme_structures')
    strain = db.Column(db.String)


class ChebiIds(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chebi_id = db.Column(db.Integer)
    inchi = db.Column(db.String)
    chebis = db.relationship(
        'ChebiIds', secondary=metabolite_chebi,
        primaryjoin=(metabolite_chebi.chebi_id == id),
        back_populates='chebis')


metabolite_chebi = db.Table('metabolite_chebi',
    db.Column('metabolite_id', db.Integer, db.ForeignKey('metabolite.id')),
    db.Column('chebi_id', db.Integer, db.ForeignKey('chebiids.id'))
)


class ReferenceType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String)
    references = db.relationship('Reference', back_populates='type')


class Reference(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pmid = db.Column(db.Integer)
    doi = db.Column(db.String)
    title = db.Column(db.String)
    link = db.Column(db.String)
    type_id = db.Column(db.String, db.ForeignKey('referencetype.id'))
    type = db.relationship('ReferenceType', back_populates='references')
    authors = db.relationship(
        'Author', secondary=reference_author,
        primaryjoin=(reference_author.reference_id == id),
        back_populates='references')


class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    orcid = db.Column(db.String)
    references = db.relationship(
        'Reference', secondary=reference_author,
        primaryjoin=(reference_author.author_id == id),
        back_populates='authors')


reference_author = db.Table('reference_author',
    db.Column('author_id', db.Integer, db.ForeignKey('author.id')),
    db.Column('reference_id', db.Integer, db.ForeignKey('reference.id'))
)

"""