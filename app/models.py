from datetime import datetime
from hashlib import md5
from app import current_app, db, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from time import time
import jwt
import enum

followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
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
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Post {}>'.format(self.body)


reference_inhibition = db.Table('reference_inhibition',
    db.Column('inhibition_id', db.Integer, db.ForeignKey('enzyme_reaction_inhibition.id')),
    db.Column('reference_id', db.Integer, db.ForeignKey('reference.id'))
)

reference_activation = db.Table('reference_activation',
    db.Column('activation_id', db.Integer, db.ForeignKey('enzyme_reaction_activation.id')),
    db.Column('reference_id', db.Integer, db.ForeignKey('reference.id'))
)

reference_effector = db.Table('reference_effector',
    db.Column('effector_id', db.Integer, db.ForeignKey('enzyme_reaction_effector.id')),
    db.Column('reference_id', db.Integer, db.ForeignKey('reference.id'))
)

reference_misc_info = db.Table('reference_misc_info',
    db.Column('misc_info_id', db.Integer, db.ForeignKey('enzyme_reaction_misc_info.id')),
    db.Column('reference_id', db.Integer, db.ForeignKey('reference.id'))
)

reference_mechanism = db.Table('reference_mechanism',
    db.Column('mechanism_id', db.Integer, db.ForeignKey('enzyme_reaction_organism.id')),
    db.Column('reference_id', db.Integer, db.ForeignKey('reference.id'))
)

reference_model_assumptions = db.Table('reference_model_assumptions',
    db.Column('model_assumptions_id', db.Integer, db.ForeignKey('model_assumptions.id')),
    db.Column('reference_id', db.Integer, db.ForeignKey('reference.id'))
)

reference_gibbs_energy = db.Table('reference_gibbs_energy',
    db.Column('gibbs_energy_id', db.Integer, db.ForeignKey('gibbs_energy.id')),
    db.Column('reference_id', db.Integer, db.ForeignKey('reference.id'))
)

reference_author = db.Table('reference_author',
    db.Column('author_id', db.Integer, db.ForeignKey('author.id')),
    db.Column('reference_id', db.Integer, db.ForeignKey('reference.id'))
)



class Author(db.Model):
    __tablename__ = 'author'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String)
    orcid = db.Column(db.String)
    references = db.relationship(
        'Reference', secondary=reference_author,
        primaryjoin=(reference_author.c.author_id == id),
        back_populates='authors')

    def add_reference(self, reference):
        if not self.is_author_of(reference):
            self.references.append(reference)

    def remove_reference(self, reference):
        if self.is_author_of(reference):
            self.references.remove(reference)

    def is_author_of(self, reference):
        return self.references.filter(
            reference_author.c.reference_id == reference.id).count() > 0


class Reference(db.Model):
    __tablename__ = 'reference'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pmid = db.Column(db.Integer)
    doi = db.Column(db.String)
    title = db.Column(db.String)
    link = db.Column(db.String)
    type_id = db.Column(db.Integer, db.ForeignKey('reference_type.id'))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    type = db.relationship('ReferenceType', back_populates='references')
    authors = db.relationship(
        'Author', secondary=reference_author,
        primaryjoin=(reference_author.c.reference_id == id),
        back_populates='references', lazy='dynamic')
    enzyme_reaction_inhibitions = db.relationship(
        'EnzymeReactionInhibition', secondary=reference_inhibition,
        primaryjoin=(reference_inhibition.c.reference_id == id),
        back_populates='references', lazy='dynamic')
    enzyme_reaction_activations = db.relationship(
        'EnzymeReactionActivation', secondary=reference_activation,
        primaryjoin=(reference_activation.c.reference_id == id),
        back_populates='references', lazy='dynamic')
    enzyme_reaction_effectors = db.relationship(
        'EnzymeReactionEffector', secondary=reference_effector,
        primaryjoin=(reference_effector.c.reference_id == id),
        back_populates='references', lazy='dynamic')
    enzyme_reaction_misc_infos = db.relationship(
        'EnzymeReactionMiscInfo', secondary=reference_misc_info,
        primaryjoin=(reference_misc_info.c.reference_id == id),
        back_populates='references', lazy='dynamic')
    enzyme_reaction_mechanisms = db.relationship(
        'EnzymeReactionOrganism', secondary=reference_mechanism,
        primaryjoin=(reference_mechanism.c.reference_id == id),
        back_populates='mechanism_references', lazy='dynamic')
    model_assumptions = db.relationship(
        'ModelAssumptions', secondary=reference_model_assumptions,
        primaryjoin=(reference_model_assumptions.c.reference_id == id),
        back_populates='references', lazy='dynamic')
    gibbs_energies= db.relationship(
        'GibbsEnergy', secondary=reference_gibbs_energy,
        primaryjoin=(reference_gibbs_energy.c.reference_id == id),
        back_populates='references', lazy='dynamic')


    def add_author(self, author):
        if not self.is_authored_by(author):
            self.authors.append(author)

    def remove_author(self, author):
        if self.is_authored_by(author):
            self.authors.remove(author)

    def is_authored_by(self, author):
        return self.references.filter(
            reference_author.c.author_id == author.id).count() > 0


    def add_enzyme_reaction_inhibition(self, enzyme_reaction_inhibition):
        if not self.is_ref_for_inhib(enzyme_reaction_inhibition):
            self.enzyme_reaction_inhibitions.append(enzyme_reaction_inhibition)

    def remove_enzyme_reaction_inhibition(self, enzyme_reaction_inhibition):
        if self.is_ref_for_inhib(enzyme_reaction_inhibition):
            self.enzyme_reaction_inhibitions.remove(enzyme_reaction_inhibition)

    def is_ref_for_inhib(self, enzyme_reaction_inhibition):
        return self.references.filter(
            reference_inhibition.c.inhibition_id == enzyme_reaction_inhibition.id).count() > 0


    def add_enzyme_reaction_activation(self, enzyme_reaction_activation):
        if not self.is_ref_for_activation(enzyme_reaction_activation):
            self.enzyme_reaction_activations.append(enzyme_reaction_activation)

    def remove_enzyme_reaction_activation(self, enzyme_reaction_activation):
        if self.is_ref_for_activation(enzyme_reaction_activation):
            self.enzyme_reaction_activations.remove(enzyme_reaction_activation)

    def is_ref_for_activation(self, enzyme_reaction_activation):
        return self.enzyme_reaction_activations.filter(
            reference_activation.c.activation_id == enzyme_reaction_activation.id).count() > 0


    def add_enzyme_reaction_effector(self, enzyme_reaction_effector):
        if not self.is_ref_for_effector(enzyme_reaction_effector):
            self.enzyme_reaction_effectors.append(enzyme_reaction_effector)

    def remove_enzyme_reaction_effector(self, enzyme_reaction_effector):
        if self.is_ref_for_effector(enzyme_reaction_effector):
            self.enzyme_reaction_effectors.remove(enzyme_reaction_effector)

    def is_ref_for_effector(self, enzyme_reaction_effector):
        return self.enzyme_reaction_effectors.filter(
            reference_effector.c.effector_id == enzyme_reaction_effector.id).count() > 0


    def add_enzyme_misc_info(self, enzyme_reaction_misc_info):
        if not self.is_ref_for_misc_info(enzyme_reaction_misc_info):
            self.enzyme_reaction_misc_infos.append(enzyme_reaction_misc_info)

    def remove_enzyme_misc_info(self, enzyme_reaction_misc_info):
        if self.is_ref_for_misc_info(enzyme_reaction_misc_info):
            self.enzyme_reaction_misc_infos.remove(enzyme_reaction_misc_info)

    def is_ref_for_misc_info(self, enzyme_reaction_misc_info):
        return self.enzyme_reaction_misc_infos.filter(
            reference_misc_info.c.misc_info_id == enzyme_reaction_misc_info.id).count() > 0


    def add_reaction_mechanism(self, enzyme_reaction_mechanism):
        if not self.is_ref_for_rxn_mech(enzyme_reaction_mechanism):
            self.enzyme_reaction_mechanisms.append(enzyme_reaction_mechanism)

    def remove_reaction_mechanism(self, enzyme_reaction_mechanism):
        if self.is_ref_for_rxn_mech(enzyme_reaction_mechanism):
            self.enzyme_reaction_mechanisms.remove(enzyme_reaction_mechanism)

    def is_ref_for_rxn_mech(self, enzyme_reaction_mechanism):
        return self.enzyme_reaction_mechanisms.filter(
            reference_mechanism.c.mechanism_id == enzyme_reaction_mechanism.id).count() > 0


    def add_model_assumption(self, model_assumption):
        if not self.is_ref_for_model_assumption(model_assumption):
            self.model_assumptions.append(model_assumption)

    def remove_model_assumption(self, model_assumption):
        if self.is_ref_for_model_assumption(model_assumption):
            self.model_assumptions.remove(model_assumption)

    def is_ref_for_model_assumption(self, model_assumption):
        return self.model_assumptions.filter(
            reference_model_assumptions.c.model_assumptions_id == model_assumption.id).count() > 0


class ReferenceType(db.Model):
    __tablename__ = 'reference_type'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type = db.Column(db.String)
    references = db.relationship('Reference', back_populates='type')

    def add_reference(self, reference):
        if not self.is_type(reference):
            self.references.append(reference)

    def remove_reference(self, reference):
        if self.is_type(reference):
            self.references.remove(reference)

    def is_type(self, reference):
        return self.references.filter(
            Reference.id == reference.id)


class EnzymeGeneOrganism(db.Model):
    gene_id = db.Column(db.Integer, db.ForeignKey('gene.id'), primary_key=True)
    enzyme_id = db.Column(db.Integer, db.ForeignKey('enzyme.id'), primary_key=True)
    organism_id = db.Column(db.Integer, db.ForeignKey('organism.id'), primary_key=True)
    gene = db.relationship('Gene', back_populates='enzyme_gene_organisms')
    enzyme = db.relationship('Enzyme', back_populates='enzyme_gene_organisms')
    organism = db.relationship('Organism', back_populates='enzyme_gene_organisms')


enzyme_complex_subunit = db.Table('enzyme_complex_subunit',
    db.Column('enzyme_complex_id', db.Integer, db.ForeignKey('enzyme.id')),
    db.Column('enzyme_subunit_id', db.Integer, db.ForeignKey('enzyme.id'))
)


class Enzyme(db.Model):
    __tablename__ = 'enzyme'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String)
    acronym = db.Column(db.String)
    isoenzyme = db.Column(db.String, unique=True)
    ec_number = db.Column(db.String)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    enzyme_structures = db.relationship('EnzymeStructure', back_populates='enzyme', lazy='dynamic')
    enzyme_organisms = db.relationship('EnzymeOrganism', back_populates='enzyme', lazy='dynamic')
    enzyme_reaction_organisms = db.relationship('EnzymeReactionOrganism', back_populates='enzyme', lazy='dynamic')
    enzyme_gene_organisms = db.relationship('EnzymeGeneOrganism', back_populates='enzyme', lazy='dynamic')
    enzyme_subunits = db.relationship(
        'Enzyme', secondary=enzyme_complex_subunit,
        primaryjoin=(enzyme_complex_subunit.c.enzyme_complex_id == id),
        secondaryjoin=(enzyme_complex_subunit.c.enzyme_subunit_id == id),
        backref=db.backref('enzyme_complex_subunit', lazy='dynamic'), lazy='dynamic')


    def __repr__(self):
        return str(self.isoenzyme)


    def add_structure(self, structure):
            if not self.has_structure(structure):
                self.enzyme_structures.append(structure)

    def remove_structures(self, structure):
        if self.has_structure(structure):
            self.enzyme_structures.remove(structure)

    def has_structure(self, structure):
        return self.enzyme_structures.filter(
            EnzymeStructure.id == structure.id)


    def add_enzyme_organism(self, enzyme_organism):
        if not self.is_part_of_enzyme_organism(enzyme_organism):
            self.enzyme_organisms.append(enzyme_organism)

    def remove_enzyme_organism(self, enzyme_organism):
        if self.is_part_of_enzyme_organism(enzyme_organism):
            self.enzyme_organisms.remove(enzyme_organism)

    def is_part_of_enzyme_organism(self, enzyme_organism):
        return self.enzyme_organisms.filter(
            EnzymeOrganism.id == enzyme_organism.id)


    def add_enzyme_reaction_organism(self, enzyme_reaction_organism):
        if not self.is_part_of_enzyme_reaction_organism(enzyme_reaction_organism):
            self.enzyme_reaction_organisms.append(enzyme_reaction_organism)

    def remove_enzyme_reaction_organism(self, enzyme_reaction_organism):
        if self.is_part_of_enzyme_reaction_organism(enzyme_reaction_organism):
            self.enzyme_reaction_organisms.remove(enzyme_reaction_organism)

    def is_part_of_enzyme_reaction_organism(self, enzyme_reaction_organism):
        return self.enzyme_reaction_organisms.filter(
            EnzymeReactionOrganism.id == enzyme_reaction_organism.id)


    def add_subunit(self, enzyme_subunit):
        if not self.has_subunit(enzyme_subunit):
            self.enzyme_subunits.append(enzyme_subunit)

    def remove_subunit(self, enzyme_subunit):
        if self.has_subunit(enzyme_subunit):
            self.enzyme_subunits.remove(enzyme_subunit)

    def has_subunit(self, enzyme_subunit):
        return self.enzyme_subunits.filter(
             enzyme_complex_subunit.c.enzyme_subunit_id == enzyme_subunit.id).count() > 0


class Gene(db.Model):
    __tablename__ = 'gene'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, unique=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    enzyme_gene_organisms = db.relationship('EnzymeGeneOrganism', back_populates='gene', lazy='dynamic')

    def __repr__(self):
        return str(self.name)


metabolite_compartment = db.Table('metabolite_compartment',
    db.Column('metabolite_id', db.Integer, db.ForeignKey('metabolite.id')),
    db.Column('compartment_id', db.Integer, db.ForeignKey('compartment.id'))
)


class Compartment(db.Model):
    __tablename__ = 'compartment'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, unique=True, index=True)
    name = db.Column(db.String, unique=True, index=False)
    bigg_id = db.Column(db.String, unique=True, index=False)
    metanetx_id = db.Column(db.String, unique=True, index=False)
    reactions = db.relationship('Reaction', back_populates='compartment', lazy='dynamic')

    metabolites = db.relationship(
        'Metabolite', secondary=metabolite_compartment,
        primaryjoin=(metabolite_compartment.c.compartment_id == id),
        back_populates='compartments', lazy='dynamic')

    def __repr__(self):
        return str([self.name, self.bigg_id])

    def __str__(self):
        return str(self.bigg_id)

    def add_metabolite(self, metabolite):
        if not self.met_in_compartment(metabolite):
            self.metabolites.append(metabolite)

    def remove_metabolite(self, metabolite):
        if self.met_in_compartment(metabolite):
            self.metabolites.remove(metabolite)

    def met_in_compartment(self, metabolite):
        return self.metabolites.filter(
            metabolite_compartment.c.metabolite_id == metabolite.id).count() > 0


    def add_reaction(self, reaction):
        if not self.reaction_in_compartment(reaction):
            self.reactions.append(reaction)

    def remove_reaction(self, reaction):
        if self.reaction_in_compartment(reaction):
            self.reactions.remove(reaction)

    def reaction_in_compartment(self, reaction):
        return self.reactions.filter(
            Reaction.id == reaction.id).count() > 0


metabolite_chebi = db.Table('metabolite_chebi',
    db.Column('metabolite_id', db.Integer, db.ForeignKey('metabolite.id')),
    db.Column('chebi_id', db.Integer, db.ForeignKey('chebi_ids.id'))
)


class ReactionMetabolite(db.Model):
    __tablename__ = 'reaction_metabolite'
    reaction_id = db.Column(db.Integer, db.ForeignKey('reaction.id'), primary_key=True)
    metabolite_id = db.Column(db.Integer, db.ForeignKey('metabolite.id'), primary_key=True)
    compartment_id = db.Column(db.Integer, db.ForeignKey('compartment.id'), primary_key=True)
    stoich_coef = db.Column(db.Integer)
    metabolite = db.relationship('Metabolite', back_populates='reactions')
    reaction = db.relationship('Reaction', back_populates='metabolites')
    compartment = db.relationship('Compartment')

    def __repr__(self):
        return str((self.reaction.bigg_id, self.stoich_coef, self.metabolite.bigg_id, self.compartment.bigg_id))


class Metabolite(db.Model):
    __tablename__ = 'metabolite'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    grasp_id = db.Column(db.String, unique=True)
    name = db.Column(db.String)
    bigg_id = db.Column(db.String, unique=True)
    metanetx_id = db.Column(db.String)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    #enzyme_inhibition_inhib_met = db.relationship('EnzymeReactionInhibition', foreign_keys=[inhibitor_met_id], back_populates='inhibitor_met')
    #enzyme_inhibition_affected_met = db.relationship('EnzymeReactionInhibition', back_populates='affected_met')
    reactions = db.relationship('ReactionMetabolite', back_populates='metabolite', lazy='dynamic')
    chebis = db.relationship(
        'ChebiIds', secondary=metabolite_chebi,
        primaryjoin=(metabolite_chebi.c.metabolite_id == id),
        back_populates='metabolites', lazy='dynamic')
    compartments = db.relationship(
        'Compartment', secondary=metabolite_compartment,
        primaryjoin=(metabolite_compartment.c.metabolite_id == id),
        back_populates='metabolites', lazy='dynamic')


    def __repr__(self):
        return str([self.bigg_id, self.name])

    def __str__(self):
        return str(self.bigg_id)

    def add_chebi_id(self, chebi_id):
        if not self.met_involved_in_reaction(chebi_id):
            self.chebis.append(chebi_id)

    def remove_chebi_id(self, chebi_id):
        if self.met_involved_in_reaction(chebi_id):
            self.chebis.remove(chebi_id)

    def has_chebi_id(self, chebi_id):
        return self.metabolite_chebi.filter(
            metabolite_chebi.c.chebi_id == chebi_id.id).count() > 0


    def add_reaction(self, reaction):
        if not self.met_involved_in_reaction(reaction):
            self.reactions.append(reaction)

    def remove_reaction(self, reaction):
        if self.met_involved_in_reaction(reaction):
            self.reactions.remove(reaction)

    def met_involved_in_reaction(self, reaction):
        return self.reactions.filter(
            ReactionMetabolite.reaction_id == reaction.id).count() > 0


    def add_compartment(self, compartment):
        if not self.met_in_compartment(compartment):
            self.compartments.append(compartment)

    def remove_metabolite(self, compartment):
        if self.met_in_compartment(compartment):
            self.compartments.remove(compartment)

    def met_in_compartment(self, compartment):
        return self.compartments.filter(
            Compartment.id == compartment.id).count() > 0


class ChebiIds(db.Model):
    __tablename__ = 'chebi_ids'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    chebi_id = db.Column(db.Integer)
    inchi = db.Column(db.String)
    metabolites = db.relationship(
        'Metabolite', secondary=metabolite_chebi,
        primaryjoin=(metabolite_chebi.c.chebi_id == id),
        back_populates='chebis', lazy='dynamic')

    def __repr__(self):
        return str(self.chebi_id, self.inchi)

    def __str__(self):
        return str(self.chebi_id, self.inchi)

    def add_metabolite(self, metabolite):
        if not self.is_met_associated_to_chebi(metabolite):
            self.metabolites.append(metabolite)

    def remove_metabolite(self, metabolite):
        if self.is_met_associated_to_chebi(metabolite):
            self.metabolites.remove(metabolite)

    def is_met_associated_to_chebi(self, metabolite):
        return self.reactions.filter(
            metabolite_chebi.c.metabolite_id == metabolite.id).count() > 0


class Reaction(db.Model):
    __tablename__ = 'reaction'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String)
    acronym = db.Column(db.String, unique=True)
    metanetx_id = db.Column(db.String)
    bigg_id = db.Column(db.String)
    kegg_id = db.Column(db.String)
    compartment_name = db.Column(db.String, db.ForeignKey(Compartment.name))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    compartment = db.relationship('Compartment', back_populates='reactions')
    enzyme_reaction_organisms = db.relationship('EnzymeReactionOrganism', back_populates='reaction', lazy='dynamic')
    metabolites = db.relationship('ReactionMetabolite', back_populates='reaction', lazy='dynamic')
    gibbs_energy_reaction_models = db.relationship('GibbsEnergyReactionModel', back_populates='reaction', lazy='dynamic')

    def __repr__(self):
        reaction_string = ''
        reaction_string += ' + '.join([str(-met.stoich_coef) + ' ' + str(met.metabolite) + '_' + str(met.compartment)
                                        for met in self.metabolites if met.stoich_coef < 0])
        reaction_string += ' <-> '
        reaction_string += ' + '.join([str(met.stoich_coef) + ' ' + str(met.metabolite) + '_' + str(met.compartment)
                                         for met in self.metabolites if met.stoich_coef > 0])
        return reaction_string

    def __str__(self):
        reaction_string = ''
        reaction_string += ' + '.join([str(-met.stoich_coef) + ' ' + str(met.metabolite) + '_' + str(met.compartment)
                                        for met in self.metabolites if met.stoich_coef < 0])
        reaction_string += ' <-> '
        reaction_string += ' + '.join([str(met.stoich_coef) + ' ' + str(met.metabolite) + '_' + str(met.compartment)
                                         for met in self.metabolites if met.stoich_coef > 0])
        return ': '.join([self.acronym, reaction_string])


    def add_metabolite(self, metabolite, stoich_coef, compartment):
        self.metabolites.append(ReactionMetabolite(reaction_id=self.id, metabolite_id=metabolite.id,
                                                   stoich_coef=stoich_coef, compartment=compartment))

    """def remove_metabolite(self, metabolite, stoich_coef, compartment_acronym):
        if self.met_involved_in_reaction(metabolite):
            row = ReactionMetabolite.query.filter_by(reaction_id=self.id, metabolite_id=metabolite.id,
                                                     met_comp_acronym=compartment_acronym).first()
            # delete the row from db session if it exists
            if row is not None:
                db.session.delete(row)
                db.session.commit()
            self.metabolites.remove(row)"""



    def add_enzyme_organism(self, enzyme_organism):
        if not self.is_part_of_enzyme_organism(enzyme_organism):
            self.enzyme_organisms.append(enzyme_organism)

    def remove_enzyme_organism(self, enzyme_organism):
        if self.is_part_of_enzyme_organism(enzyme_organism):
            self.enzyme_organisms.remove(enzyme_organism)

    def is_part_of_enzyme_organism(self, enzyme_organism):
        return self.enzyme_organisms.filter(
            EnzymeOrganism.id == enzyme_organism.id).count() > 0


    def add_enzyme_reaction_organism(self, enzyme_reaction_organism):
        if not self.is_part_of_enzyme_reaction_organism(enzyme_reaction_organism):
            self.enzyme_reaction_organisms.append(enzyme_reaction_organism)

    def remove_enzyme_reaction_organism(self, enzyme_reaction_organism):
        if self.is_part_of_enzyme_reaction_organism(enzyme_reaction_organism):
            self.enzyme_reaction_organisms.remove(enzyme_reaction_organism)

    def is_part_of_enzyme_reaction_organism(self, enzyme_reaction_organism):
        return self.enzyme_reaction_organisms.filter(
            EnzymeReactionOrganism.id == enzyme_reaction_organism.id).count() > 0


class Organism(db.Model):
    __tablename__ = 'organism'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, unique=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    enzyme_structures = db.relationship('EnzymeStructure', back_populates='organism', lazy='dynamic')
    models = db.relationship('Model', back_populates='organism', lazy='dynamic')
    enzyme_organisms = db.relationship('EnzymeOrganism', back_populates='organism', lazy='dynamic')
    enzyme_reaction_organisms = db.relationship('EnzymeReactionOrganism', back_populates='organism')
    enzyme_gene_organisms = db.relationship('EnzymeGeneOrganism', back_populates='organism', lazy='dynamic')

    def __repr__(self):
        return str(self.name)

    def add_enzyme_organism(self, enzyme_organism):
        if not self.is_part_of_enzyme_organism(enzyme_organism):
            self.enzyme_organisms.append(enzyme_organism)

    def remove_enzyme_organism(self, enzyme_organism):
        if self.is_part_of_enzyme_organism(enzyme_organism):
            self.enzyme_organisms.remove(enzyme_organism)

    def is_part_of_enzyme_organism(self, enzyme_organism):
        return self.enzyme_organisms.filter(
            EnzymeOrganism.id == enzyme_organism.id).count() > 0


    def add_model(self, model):
        if not self.has_model(model):
            self.models.append(model)

    def remove_model(self, model):
        if self.has_model(model):
            self.models.remove(model)

    def has_model(self, model):
        return self.models.filter(
            Model.id == model.id).count() > 0


    def add_structure(self, structure):
        if not self.has_structure(structure):
            self.structures.append(structure)

    def remove_structures(self, structure):
        if self.has_structure(structure):
            self.structures.remove(structure)

    def has_structure(self, structure):
        return self.enzyme_structures.filter(
             EnzymeStructure.id == structure.id).count() > 0


enzyme_reaction_organism_model = db.Table('enzyme_reaction_organism_model',
    db.Column('model_id', db.Integer, db.ForeignKey('model.id')),
    db.Column('enzyme_reaction_organism_id', db.Integer, db.ForeignKey('enzyme_reaction_organism.id'))
)

enzyme_reaction_inhibition_model = db.Table('enzyme_reaction_inhibition_model',
    db.Column('model_id', db.Integer, db.ForeignKey('model.id')),
    db.Column('inhibition_id', db.Integer, db.ForeignKey('enzyme_reaction_inhibition.id'))
)

enzyme_reaction_activation_model = db.Table('enzyme_reaction_activation_model',
    db.Column('model_id', db.Integer, db.ForeignKey('model.id')),
    db.Column('activation_id', db.Integer, db.ForeignKey('enzyme_reaction_activation.id'))
)

enzyme_reaction_effector_model = db.Table('enzyme_reaction_effector_model',
    db.Column('model_id', db.Integer, db.ForeignKey('model.id')),
    db.Column('effector_id', db.Integer, db.ForeignKey('enzyme_reaction_effector.id'))
)

enzyme_reaction_misc_info_model = db.Table('enzyme_reaction_misc_info_model',
    db.Column('model_id', db.Integer, db.ForeignKey('model.id')),
    db.Column('misc_info_id', db.Integer, db.ForeignKey('enzyme_reaction_misc_info.id'))
)


class Model(db.Model):
    __tablename__ = 'model'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, unique=True)
    organism_name = db.Column(db.String, db.ForeignKey(Organism.name))
    strain = db.Column(db.String)
    comments = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    organism = db.relationship('Organism', back_populates='models')
    model_assumptions = db.relationship('ModelAssumptions', back_populates='model', lazy='dynamic')
    gibbs_energy_reaction_models = db.relationship('GibbsEnergyReactionModel', back_populates='model', lazy='dynamic')


    enzyme_reaction_inhibitions = db.relationship(
        'EnzymeReactionInhibition', secondary=enzyme_reaction_inhibition_model,
        primaryjoin=(enzyme_reaction_inhibition_model.c.model_id == id),
        back_populates='models', lazy='dynamic')

    enzyme_reaction_activations = db.relationship(
        'EnzymeReactionActivation', secondary=enzyme_reaction_activation_model,
        primaryjoin=(enzyme_reaction_activation_model.c.model_id == id),
        back_populates='models', lazy='dynamic')

    enzyme_reaction_effectors = db.relationship(
        'EnzymeReactionEffector', secondary=enzyme_reaction_effector_model,
        primaryjoin=(enzyme_reaction_effector_model.c.model_id == id),
        back_populates='models', lazy='dynamic')

    enzyme_reaction_misc_infos = db.relationship(
        'EnzymeReactionMiscInfo', secondary=enzyme_reaction_misc_info_model,
        primaryjoin=(enzyme_reaction_misc_info_model.c.model_id == id),
        back_populates='models', lazy='dynamic')

    enzyme_reaction_organisms = db.relationship(
        'EnzymeReactionOrganism', secondary=enzyme_reaction_organism_model,
        primaryjoin=(enzyme_reaction_organism_model.c.model_id == id),
        back_populates='models', lazy='dynamic')

    def __repr__(self):
        return str(self.name)

    def add_enzyme_reaction_organism(self, enzyme_reaction_organism):
        if not self.is_part_of_enzyme_reaction_organism(enzyme_reaction_organism):
            self.enzyme_reaction_organisms.append(enzyme_reaction_organism)

    def remove_enzyme_reaction_organism(self, enzyme_reaction_organism):
        if self.is_part_of_enzyme_reaction_organism(enzyme_reaction_organism):
            self.enzyme_reaction_organisms.remove(enzyme_reaction_organism)

    def is_part_of_enzyme_reaction_organism(self, enzyme_reaction_organism):
        return self.enzyme_reaction_organisms.filter(
            EnzymeReactionOrganism.id == enzyme_reaction_organism.id).count() > 0


    def add_model_assumption(self, model_assumption):
        if not self.has_model_assumption(model_assumption):
            self.model_assumptions.append(model_assumption)

    def remove_model_assumption(self, model_assumption):
        if self.has_model_assumption(model_assumption):
            self.model_assumptions.remove(model_assumption)

    def has_model_assumption(self, model_assumption):
        return self.model_assumptions.filter(
            ModelAssumptions.id == model_assumption.id).count() > 0


class GibbsEnergy(db.Model):
    __tablename__ = 'gibbs_energy'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    standard_dg = db.Column(db.Float)
    standard_dg_std = db.Column(db.Float)
    ph = db.Column(db.Float)
    ionic_strength = db.Column(db.Float)

    gibbs_energy_reaction_models = db.relationship('GibbsEnergyReactionModel', back_populates='gibbs_energy', lazy='dynamic')
    references = db.relationship(
        'Reference', secondary=reference_gibbs_energy,
        primaryjoin=(reference_gibbs_energy.c.gibbs_energy_id == id),
        back_populates='gibbs_energies', lazy='dynamic')

    def __repr__(self):
        return ''.join([str(self.standard_dg), ' +- ', str(self.standard_dg_std), ' kJ/mol, pH: ', str(self.ph), ', IS: ', str(self.ionic_strength)])

    def __str__(self):
        return ''.join([str(self.standard_dg), ' +- ', str(self.standard_dg_std), ' kJ/mol, pH: ', str(self.ph), ', IS: ', str(self.ionic_strength)])

    def add_reference(self, reference):
        if not self.has_reference(reference):
            self.references.append(reference)

    def remove_reference(self, reference):
        if self.has_reference(reference):
            self.references.remove(reference)

    def has_reference(self, reference):
        return self.references.filter(
            reference_gibbs_energy.c.reference_id == reference.id).count() > 0


class GibbsEnergyReactionModel(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    gibbs_energy_id = db.Column(db.Integer, db.ForeignKey(GibbsEnergy.id))
    model_id = db.Column(db.Integer, db.ForeignKey(Model.id))
    reaction_id = db.Column(db.Integer, db.ForeignKey(Reaction.id))
    model = db.relationship('Model', back_populates='gibbs_energy_reaction_models')
    reaction = db.relationship('Reaction', back_populates='gibbs_energy_reaction_models')
    gibbs_energy = db.relationship('GibbsEnergy', back_populates='gibbs_energy_reaction_models')


class EnzymeStructure(db.Model):
    __tablename__ = 'enzyme_structure'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    enzyme_id = db.Column(db.Integer, db.ForeignKey(Enzyme.id))
    organism_id = db.Column(db.Integer, db.ForeignKey(Organism.id))
    pdb_id = db.Column(db.String, unique=True)
    strain = db.Column(db.String)

    organism = db.relationship('Organism', back_populates='enzyme_structures')
    enzyme = db.relationship('Enzyme', back_populates='enzyme_structures')


class Mechanism(db.Model):
    __tablename__ = 'mechanism'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String)
    enzyme_reaction_organisms = db.relationship('EnzymeReactionOrganism', back_populates='mechanism', lazy='dynamic')

    def __repr__(self):
        return str(self.name)

    def add_enzyme_reaction_organism(self, enzyme_reaction_organism):
        if not self.has_mechanism(enzyme_reaction_organism):
            self.enzyme_reaction_organisms.append(enzyme_reaction_organism)

    def remove_enzyme_reaction_organisml(self, enzyme_reaction_organism):
        if self.has_mechanism(enzyme_reaction_organism):
            self.enzyme_reaction_organisms.remove(enzyme_reaction_organism)

    def has_mechanism(self, enzyme_reaction_organism):
        return self.enzyme_reaction_organisms.filter(
            EnzymeReactionOrganism.id == enzyme_reaction_organism.id).count() > 0


class EnzymeOrganism(db.Model):
    __tablename__ = 'enzyme_organism'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    enzyme_id = db.Column(db.Integer, db.ForeignKey(Enzyme.id))
    organism_id = db.Column(db.Integer, db.ForeignKey(Organism.id))
    uniprot_id = db.Column(db.String, unique=True)
    n_active_sites = db.Column(db.Integer)

    enzyme = db.relationship('Enzyme', back_populates='enzyme_organisms')
    organism = db.relationship('Organism', back_populates='enzyme_organisms')


class EvidenceLevel(db.Model):
    __tablename__ = 'evidence_level'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String)
    description = db.Column(db.Text)
    enzyme_reaction_inhibitors = db.relationship('EnzymeReactionInhibition', back_populates='evidence', lazy='dynamic')
    enzyme_reaction_activators = db.relationship('EnzymeReactionActivation', back_populates='evidence', lazy='dynamic')
    enzyme_reaction_effectors = db.relationship('EnzymeReactionEffector', back_populates='evidence', lazy='dynamic')
    enzyme_reaction_misc_infos = db.relationship('EnzymeReactionMiscInfo', back_populates='evidence', lazy='dynamic')
    model_assumptions = db.relationship('ModelAssumptions', back_populates='evidence', lazy='dynamic')
    enz_mechanisms = db.relationship('EnzymeReactionOrganism', back_populates='mech_evidence', lazy='dynamic')

    def __repr__(self):
        return str(self.name)

    def add_enzyme_reaction_inhibitor(self, enzyme_reaction_inhibitor):
        if not self.is_evidence_for_inhib(enzyme_reaction_inhibitor):
            self.enzyme_reaction_inhibitors.append(enzyme_reaction_inhibitor)

    def remove_enzyme_reaction_inhibitor(self, enzyme_reaction_inhibitor):
        if self.is_evidence_for_inhib(enzyme_reaction_inhibitor):
            self.enzyme_reaction_inhibitors.remove(enzyme_reaction_inhibitor)

    def is_evidence_for_inhib(self, enzyme_reaction_inhibitor):
        return self.enzyme_reaction_inhibitors.filter(
            EnzymeReactionInhibition.id == enzyme_reaction_inhibitor.id).count() > 0


    def add_enzyme_reaction_activator(self, enzyme_reaction_activator):
        if not self.is_evidence_for_activation(enzyme_reaction_activator):
            self.enzyme_reaction_activators.append(enzyme_reaction_activator)

    def remove_enzyme_reaction_activator(self, enzyme_reaction_activator):
        if self.is_evidence_for_activation(enzyme_reaction_activator):
            self.enzyme_reaction_activators.remove(enzyme_reaction_activator)

    def is_evidence_for_activation(self, enzyme_reaction_activator):
        return self.enzyme_reaction_activators.filter(
            EnzymeReactionActivation.id == enzyme_reaction_activator.id).count() > 0


    def add_enzyme_reaction_effector(self, enzyme_reaction_effector):
        if not self.is_evidence_for_effector(enzyme_reaction_effector):
            self.enzyme_reaction_effectors.append(enzyme_reaction_effector)

    def remove_enzyme_reaction_effector(self, enzyme_reaction_effector):
        if self.is_evidence_for_effector(enzyme_reaction_effector):
            self.enzyme_reaction_effectors.remove(enzyme_reaction_effector)

    def is_evidence_for_effector(self, enzyme_reaction_effector):
        return self.enzyme_reaction_effectors.filter(
            EnzymeReactionEffector.id == enzyme_reaction_effector.id).count() > 0


    def add_enzyme_reaction_misc_info(self, enzyme_reaction_misc_info):
        if not self.is_evidence_for_misc_info(enzyme_reaction_misc_info):
            self.enzyme_reaction_misc_infos.append(enzyme_reaction_misc_info)

    def remove_enzyme_reaction_misc_info(self, enzyme_reaction_misc_info):
        if self.is_evidence_for_misc_info(enzyme_reaction_misc_info):
            self.enzyme_reaction_misc_infos.remove(enzyme_reaction_misc_info)

    def is_evidence_for_misc_info(self, enzyme_reaction_misc_info):
        return self.enzyme_reaction_misc_infos.filter(
            EnzymeReactionMiscInfo.id == enzyme_reaction_misc_info.id).count() > 0


    def add_model_assumption(self, model_assumption):
        if not self.is_evidence_for_model_assumption(model_assumption):
            self.model_assumptions.append(model_assumption)

    def remove_model_assumption(self, model_assumption):
        if self.is_evidence_for_model_assumption(model_assumption):
            self.model_assumptions.remove(model_assumption)

    def is_evidence_for_model_assumption(self, model_assumption):
        return self.model_assumptions.filter(
            ModelAssumptions.id == model_assumption.id).count() > 0


    def add_enz_mechanism(self, enz_mechanism):
        if not self.is_evidence_for_enz_mechanism(enz_mechanism):
            self.enz_mechanisms.append(enz_mechanism)

    def remove_enz_mechanism(self, enz_mechanism):
        if self.is_evidence_for_enz_mechanism(enz_mechanism):
            self.enz_mechanisms.remove(enz_mechanism)

    def is_evidence_for_enz_mechanism(self, enz_mechanism):
        return self.enz_mechanisms.filter(
            Mechanism.id == enz_mechanism.id).count() > 0


class EnzymeReactionOrganism(db.Model):
    __tablename__ = 'enzyme_reaction_organism'
    id = db.Column(db.Integer, nullable=False)
    enzyme_id = db.Column(db.Integer, db.ForeignKey(Enzyme.id), primary_key=True)
    reaction_id = db.Column(db.Integer, db.ForeignKey(Reaction.id), primary_key=True)
    organism_id = db.Column(db.Integer, db.ForeignKey(Organism.id), primary_key=True)
    mechanism_id = db.Column(db.Integer, db.ForeignKey(Mechanism.id))
    mech_evidence_level_id = db.Column(db.Integer, db.ForeignKey(EvidenceLevel.id))

    grasp_id = db.Column(db.String)
    subs_binding_order = db.Column(db.String)
    prod_release_order = db.Column(db.String)
    comments = db.Column(db.String)

    enzyme = db.relationship('Enzyme', back_populates='enzyme_reaction_organisms')
    reaction = db.relationship('Reaction', back_populates='enzyme_reaction_organisms')
    organism = db.relationship('Organism', back_populates='enzyme_reaction_organisms')
    mechanism = db.relationship('Mechanism', back_populates='enzyme_reaction_organisms')
    mech_evidence = db.relationship('EvidenceLevel', back_populates='enz_mechanisms')

    enzyme_reaction_inhibitors = db.relationship('EnzymeReactionInhibition', back_populates='enzyme_reaction_organism', lazy='dynamic')
    enzyme_reaction_activators = db.relationship('EnzymeReactionActivation', back_populates='enzyme_reaction_organism', lazy='dynamic')
    enzyme_reaction_effectors = db.relationship('EnzymeReactionEffector', back_populates='enzyme_reaction_organism', lazy='dynamic')
    enzyme_reaction_misc_infos = db.relationship('EnzymeReactionMiscInfo', back_populates='enzyme_reaction_organism', lazy='dynamic')

    models = db.relationship(
        'Model', secondary=enzyme_reaction_organism_model,
        primaryjoin=(enzyme_reaction_organism_model.c.enzyme_reaction_organism_id == id),
        back_populates='enzyme_reaction_organisms', lazy='dynamic')

    mechanism_references = db.relationship(
        'Reference', secondary=reference_mechanism,
        primaryjoin=(reference_mechanism.c.mechanism_id == id),
        back_populates='enzyme_reaction_mechanisms', lazy='dynamic')

    def add_enzyme_reaction_inhibition(self, enzyme_reaction_inhibition):
        if not self.has_inhib(enzyme_reaction_inhibition):
            self.enzyme_reaction_inhibitions.append(enzyme_reaction_inhibition)

    def remove_enzyme_reaction_inhibition(self, enzyme_reaction_inhibition):
        if self.has_inhib(enzyme_reaction_inhibition):
            self.enzyme_reaction_inhibitions.remove(enzyme_reaction_inhibition)

    def has_inhib(self, enzyme_reaction_inhibition):
        return self.references.filter(
            EnzymeReactionInhibition.id == enzyme_reaction_inhibition.id).count() > 0


    def add_enzyme_reaction_activation(self, enzyme_reaction_activation):
        if not self.has_activation(enzyme_reaction_activation):
            self.enzyme_reaction_activations.append(enzyme_reaction_activation)

    def remove_enzyme_reaction_activation(self, enzyme_reaction_activation):
        if self.has_activation(enzyme_reaction_activation):
            self.enzyme_reaction_activations.remove(enzyme_reaction_activation)

    def has_activation(self, enzyme_reaction_activation):
        return self.enzyme_reaction_activations.filter(
            EnzymeReactionActivation.id == enzyme_reaction_activation.id).count() > 0


    def add_enzyme_reaction_effector(self, enzyme_reaction_effector):
        if not self.has_effector(enzyme_reaction_effector):
            self.enzyme_reaction_effectors.append(enzyme_reaction_effector)

    def remove_enzyme_reaction_effector(self, enzyme_reaction_effector):
        if self.has_effector(enzyme_reaction_effector):
            self.enzyme_reaction_effectors.remove(enzyme_reaction_effector)

    def has_effector(self, enzyme_reaction_effector):
        return self.enzyme_reaction_effectors.filter(
            EnzymeReactionEffector.id == enzyme_reaction_effector.id).count() > 0


    def add_enzyme_misc_info(self, enzyme_reaction_misc_info):
        if not self.has_misc_info(enzyme_reaction_misc_info):
            self.enzyme_reaction_misc_infos.append(enzyme_reaction_misc_info)

    def remove_enzyme_misc_info(self, enzyme_reaction_misc_info):
        if self.has_misc_info(enzyme_reaction_misc_info):
            self.enzyme_reaction_misc_infos.remove(enzyme_reaction_misc_info)

    def has_misc_info(self, enzyme_reaction_misc_info):
        return self.enzyme_reaction_misc_infos.filter(
            EnzymeReactionMiscInfo.id == enzyme_reaction_misc_info.id).count() > 0


    def add_mechanism_reference(self, reference):
        if not self.has_mechanism_reference(reference):
            self.mechanism_references.append(reference)

    def remove_mechanism_reference(self, reference):
        if self.has_mechanism_reference(reference):
            self.mechanism_references.remove(reference)

    def has_mechanism_reference(self, reference):
        return self.mechanism_references.filter(
            reference_mechanism.c.reference_id == reference.id).count() > 0


    def add_model(self, model):
        if not self.is_in_model(model):
            self.models.append(model)

    def remove_model(self, model):
        if self.is_in_model(model):
            self.models.remove(model)

    def is_in_model(self, model):
        return self.models.filter(
            enzyme_reaction_organism_model.c.model_id == model.id).count() > 0


class EnzymeReactionInhibition(db.Model):
    __tablename__ = 'enzyme_reaction_inhibition'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    enz_rxn_org_id = db.Column(db.Integer, db.ForeignKey(EnzymeReactionOrganism.id))
    inhibitor_met_id = db.Column(db.Integer, db.ForeignKey(Metabolite.id))
    affected_met_id = db.Column(db.Integer, db.ForeignKey(Metabolite.id))

    inhibition_type = db.Column(db.String)
    inhibition_constant = db.Column(db.Float)
    evidence_level_id = db.Column(db.Integer, db.ForeignKey(EvidenceLevel.id))
    comments = db.Column(db.Text)

    enzyme_reaction_organism = db.relationship('EnzymeReactionOrganism', back_populates='enzyme_reaction_inhibitors')
    inhibitor_met = db.relationship('Metabolite', foreign_keys=[inhibitor_met_id])
    affected_met = db.relationship('Metabolite', foreign_keys=[affected_met_id])
    evidence = db.relationship('EvidenceLevel', back_populates='enzyme_reaction_inhibitors')
    references = db.relationship(
        'Reference', secondary=reference_inhibition,
        primaryjoin=(reference_inhibition.c.inhibition_id == id),
        back_populates='enzyme_reaction_inhibitions', lazy='dynamic')

    models = db.relationship(
        'Model', secondary=enzyme_reaction_inhibition_model,
        primaryjoin=(enzyme_reaction_inhibition_model.c.inhibition_id == id),
        back_populates='enzyme_reaction_inhibitions', lazy='dynamic')


    def __repr__(self):
        return ''.join(['Inhibitor: ', str(self.inhibitor_met), ', Affected metabolite: ', str(self.affected_met),
                        ', Inhibition type: ', str(self.inhibition_type),  ', Inhibition constant: ', str(round(self.inhibition_constant, 6)),
                        ', Evidence level: ', str(self.evidence)])

    def __str__(self):
        return ''.join(['Inhibitor: ', str(self.inhibitor_met), ', Affected metabolite: ', str(self.affected_met),
                        ', Inhibition type: ', str(self.inhibition_type),  ', Inhibition constant: ', str(round(self.inhibition_constant, 6)),
                        ', Evidence level: ', str(self.evidence)])


    def add_reference(self, reference):
        if not self.has_reference(reference):
            self.references.append(reference)

    def remove_reference(self, reference):
        if self.has_reference(reference):
            self.references.remove(reference)

    def has_reference(self, reference):
        return self.references.filter(
            reference_inhibition.c.reference_id == reference.id).count() > 0

    def add_model(self, model):
        if not self.is_in_model(model):
            self.models.append(model)

    def remove_model(self, model):
        if self.is_in_model(model):
            self.models.remove(model)

    def is_in_model(self, model):
        return self.models.filter(
            enzyme_reaction_inhibition_model.c.model_id == model.id).count() > 0


class EnzymeReactionActivation(db.Model):
    __tablename__ = 'enzyme_reaction_activation'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    enz_rxn_org_id = db.Column(db.Integer, db.ForeignKey(EnzymeReactionOrganism.id))
    activator_met_id = db.Column(db.Integer, db.ForeignKey(Metabolite.id))
    activation_constant = db.Column(db.Float)
    evidence_level_id = db.Column(db.Integer, db.ForeignKey(EvidenceLevel.id))
    comments = db.Column(db.Text)

    enzyme_reaction_organism = db.relationship('EnzymeReactionOrganism', back_populates='enzyme_reaction_activators')
    activator_met = db.relationship('Metabolite', foreign_keys=[activator_met_id])
    evidence = db.relationship('EvidenceLevel', back_populates='enzyme_reaction_activators')

    models = db.relationship(
        'Model', secondary=enzyme_reaction_activation_model,
        primaryjoin=(enzyme_reaction_activation_model.c.activation_id == id),
        back_populates='enzyme_reaction_activations', lazy='dynamic')
    references = db.relationship(
        'Reference', secondary=reference_activation,
        primaryjoin=(reference_activation.c.activation_id == id),
        back_populates='enzyme_reaction_activations', lazy='dynamic')

    def __repr__(self):
        return ''.join(['Activator: ', str(self.activator_met),  ', Activation constant: ', str(round(self.activation_constant, 6)),
                        ', Evidence level: ', str(self.evidence)])

    def __str__(self):
        return ''.join(['Activator: ', str(self.activator_met),  ', Activation constant: ', str(round(self.activation_constant, 6)),
                        ', Evidence level: ', str(self.evidence)])


    def add_reference(self, reference):
        if not self.has_reference(reference):
            self.references.append(reference)

    def remove_reference(self, reference):
        if self.has_reference(reference):
            self.references.remove(reference)

    def has_reference(self, reference):
        return self.references.filter(
            reference_activation.c.reference_id == reference.id).count() > 0


    def add_model(self, model):
        if not self.is_in_model(model):
            self.models.append(model)

    def remove_model(self, model):
        if self.is_in_model(model):
            self.models.remove(model)

    def is_in_model(self, model):
        return self.models.filter(
            enzyme_reaction_activation_model.c.model_id == model.id).count() > 0


class EnzymeReactionEffector(db.Model):
    __tablename__ = 'enzyme_reaction_effector'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    enz_rxn_org_id = db.Column(db.Integer, db.ForeignKey(EnzymeReactionOrganism.id))
    effector_met_id = db.Column(db.Integer, db.ForeignKey(Metabolite.id))
    effector_type = db.Column(db.String)
    evidence_level_id = db.Column(db.Integer, db.ForeignKey(EvidenceLevel.id))
    comments = db.Column(db.Text)

    effector_met = db.relationship('Metabolite', foreign_keys=[effector_met_id])
    enzyme_reaction_organism = db.relationship('EnzymeReactionOrganism', back_populates='enzyme_reaction_effectors')
    evidence = db.relationship('EvidenceLevel', back_populates='enzyme_reaction_effectors')
    models = db.relationship(
        'Model', secondary=enzyme_reaction_effector_model,
        primaryjoin=(enzyme_reaction_effector_model.c.effector_id == id),
        back_populates='enzyme_reaction_effectors', lazy='dynamic')
    references = db.relationship(
        'Reference', secondary=reference_effector,
        primaryjoin=(reference_effector.c.effector_id == id),
        back_populates='enzyme_reaction_effectors', lazy='dynamic')


    def __repr__(self):
        return ''.join(['Effector: ', str(self.effector_met),  ', Effector type: ', str(self.effector_type),
                        ', Evidence level: ', str(self.evidence)])

    def __str__(self):
        return ''.join(['Effector: ', str(self.effector_met),  ', Effector type: ', str(self.effector_type),
                        ', Evidence level: ', str(self.evidence)])

    def add_reference(self, reference):
        if not self.has_reference(reference):
            self.references.append(reference)

    def remove_reference(self, reference):
        if self.has_reference(reference):
            self.references.remove(reference)

    def has_reference(self, reference):
        return self.references.filter(
            reference_effector.c.reference_id == reference.id).count() > 0

    def add_model(self, model):
        if not self.is_in_model(model):
            self.models.append(model)

    def remove_model(self, model):
        if self.is_in_model(model):
            self.models.remove(model)

    def is_in_model(self, model):
        return self.models.filter(
            enzyme_reaction_effector_model.c.model_id == model.id).count() > 0


class EnzymeReactionMiscInfo(db.Model):
    __tablename__ = 'enzyme_reaction_misc_info'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    enz_rxn_org_id = db.Column(db.Integer, db.ForeignKey(EnzymeReactionOrganism.id))
    topic = db.Column(db.String)
    description = db.Column(db.Text)
    evidence_level_id = db.Column(db.Integer, db.ForeignKey(EvidenceLevel.id))
    comments = db.Column(db.Text)

    enzyme_reaction_organism = db.relationship('EnzymeReactionOrganism', back_populates='enzyme_reaction_misc_infos')
    evidence = db.relationship('EvidenceLevel', back_populates='enzyme_reaction_misc_infos')

    models = db.relationship(
        'Model', secondary=enzyme_reaction_misc_info_model,
        primaryjoin=(enzyme_reaction_misc_info_model.c.misc_info_id == id),
        back_populates='enzyme_reaction_misc_infos', lazy='dynamic')

    references = db.relationship(
        'Reference', secondary=reference_misc_info,
        primaryjoin=(reference_misc_info.c.misc_info_id == id),
        back_populates='enzyme_reaction_misc_infos', lazy='dynamic')

    def __repr__(self):
        return ''.join(['Topic: ', str(self.topic),  '. Description: ', str(self.description),
                        ' Evidence level:', str(self.evidence)])

    def __str__(self):
        return ''.join(['Topic: ', str(self.topic),  '. Description: ', str(self.description),
                        ' Evidence level:', str(self.evidence)])

    def add_reference(self, reference):
        if not self.has_reference(reference):
            self.references.append(reference)

    def remove_reference(self, reference):
        if self.has_reference(reference):
            self.references.remove(reference)

    def has_reference(self, reference):
        return self.references.filter(
            reference_misc_info.c.reference_id == reference.id).count() > 0

    def add_model(self, model):
        if not self.is_in_model(model):
            self.models.append(model)

    def remove_model(self, model):
        if self.is_in_model(model):
            self.models.remove(model)

    def is_in_model(self, model):
        return self.models.filter(
            enzyme_reaction_misc_info_model.c.model_id == model.id).count() > 0


class ModelAssumptions(db.Model):
    __tablename__ = 'model_assumptions'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    model_id = db.Column(db.Integer, db.ForeignKey(Model.id))
    assumption = db.Column(db.String)
    description = db.Column(db.Text)
    evidence_level_id = db.Column(db.Integer, db.ForeignKey(EvidenceLevel.id))
    included_in_model = db.Column(db.Boolean)
    comments = db.Column(db.Text)

    model = db.relationship('Model', back_populates='model_assumptions')
    evidence = db.relationship('EvidenceLevel', back_populates='model_assumptions')
    references = db.relationship(
        'Reference', secondary=reference_model_assumptions,
        primaryjoin=(reference_model_assumptions.c.model_assumptions_id == id),
        back_populates='model_assumptions', lazy='dynamic')

    def add_reference(self, reference):
        if not self.has_reference(reference):
            self.references.append(reference)

    def remove_reference(self, reference):
        if self.has_reference(reference):
            self.references.remove(reference)

    def has_reference(self, reference):
        return self.references.filter(
            reference_model_assumptions.c.reference_id == reference.id).count() > 0
