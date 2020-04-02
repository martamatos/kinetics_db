import os

from flask import current_app
from flask import render_template, flash, redirect, url_for
from flask_login import login_required
from werkzeug.utils import secure_filename

from app import db
from app.load_data.import_grasp_model import get_model_name, get_model_stoichiometry, get_model_enzymes, get_model_subunits, \
    get_model_mechanisms, get_model_inhibitors, get_model_activators, get_model_effectors, get_model_gibbs_energies
from app.main import bp
from app.main.forms import EnzymeForm, EnzymeActivationForm, EnzymeEffectorForm, EnzymeInhibitionForm, \
    EnzymeMiscInfoForm, GeneForm, ModelAssumptionsForm, ModelForm, OrganismForm, ReactionForm, ModelFormBase, \
    MetaboliteForm, UploadModelForm
from app.main.utils import add_enzyme_structures, add_enzyme_organism, add_enzyme_genes, add_metabolites_to_reaction, \
    add_gibbs_energy, add_references, check_metabolite, set_binding_release_order, \
    add_enzyme_organism_subunits_only, add_effector
from app.models import Compartment, Enzyme, EnzymeReactionOrganism, EnzymeReactionActivation, \
    EnzymeReactionEffector, EnzymeReactionInhibition, EnzymeReactionMiscInfo, EnzymeStructure, \
    Gene, Metabolite, Model, ModelAssumptions, Mechanism, GibbsEnergy, \
    Organism, Reaction, ChebiIds, GibbsEnergyReactionModel
from app.utils.parsers import parse_input_list


@bp.route('/add_enzyme', methods=['GET', 'POST'])
@login_required
def add_enzyme():
    """
    Adds an enzyme to the database.

    First generates the list of gene bigg ids and strains so that these fields can be autocompleted.

    After validating the form where the enzyme data is inserted:
     - creates the enzyme object and adds it to the DB
     - if the organism was specified:
        - adds the genes that encode for the enzyme, if those are specified
        - adds the pdb ids, if those are specified
        - adds the uniprot ids, if those are specified

    Returns:
        url_for insert data with EnzymeForm before form validation
        url_for see_enzyme_list after form validation
    """

    form = EnzymeForm()

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

        flash('Your enzyme is now live!')
        return redirect(url_for('main.see_enzyme_list'))
    return render_template('insert_data.html', title='Add enzyme', form=form, header='Add enzyme', data_list=data_list)


@bp.route('/add_enzyme_inhibition', methods=['GET', 'POST'])
@login_required
def add_enzyme_inhibition():
    """
    Adds an enzyme inhibition entry to the database.

    Starts by creating a list of all metabolite bigg ids to use in the form auto completion.

    After the form validation:
     - checks if the inhibitor metabolite is in the DB and if not adds and returns the instance
     - checks if the affected metabolite is in the DB and if not adds and returns the instance
     - queries the database to get the respective EnzymeReactionOrganism entry
     -  - if it doesn't exist, it is addded
     - creates and adds the EnzymeReactionInhibition object to the DB
     - associates the EnzymeReactionInhibition to the specified models in the form
     - adds the references specified in the form.


    Returns:
        url_for insert data with EnzymeInhibitionForm before form validation
        url_for see_enzyme_inhibitor after form validation
    """

    form = EnzymeInhibitionForm()

    metabolites = Metabolite.query.all()
    metabolite_list = {'id_value': '#metabolite_list', 'input_data': [{'field1': metabolite.bigg_id} for metabolite in
                                                                      metabolites] if metabolites else []}
    data_list = [metabolite_list]

    if form.validate_on_submit():

        inhib_met = check_metabolite(form.inhibitor_met.data)
        affected_met = check_metabolite(form.affected_met.data)
        inhibition_evidence_level_id = form.inhibition_evidence_level.data.id if form.inhibition_evidence_level.data else None

        enz_rxn_org = EnzymeReactionOrganism.query.filter_by(enzyme_id=form.enzyme.data.id,
                                                             reaction_id=form.reaction.data.id,
                                                             organism_id=form.organism.data.id).first()

        if not enz_rxn_org:
            enz_rxn_org = EnzymeReactionOrganism(id=EnzymeReactionOrganism.query.count()+1,
                                                 enzyme_id=form.enzyme.data.id,
                                                 reaction_id=form.reaction.data.id,
                                                 organism_id=form.organism.data.id)
            db.session.add(enz_rxn_org)
            db.session.commit()

        enz_rxn_inhib = EnzymeReactionInhibition(enz_rxn_org_id=enz_rxn_org.id,
                                                 inhibitor_met_id=inhib_met.id,
                                                 affected_met_id=affected_met.id,
                                                 inhibition_constant=form.inhibition_constant.data,
                                                 inhibition_type=form.inhibition_type.data,
                                                 evidence_level_id=inhibition_evidence_level_id,
                                                 comments=form.comments.data)
        db.session.add(enz_rxn_inhib)

        if form.models.data:
            for model in form.models.data:
                enz_rxn_inhib.add_model(model)

        if form.references.data:
            add_references(form.references.data, enz_rxn_inhib)
            #for ref_db in ref_db_list:
            #    enz_rxn_inhib.add_reference(ref_db)

        db.session.commit()

        flash('Your enzyme inhibition is now live!', 'success')
        return redirect(url_for('main.see_enzyme_inhibitor', inhibitor_id=enz_rxn_inhib.id))

    return render_template('insert_data.html', title='Add enzyme inhibition', form=form, header='Add enzyme inhibition',
                           data_list=data_list)


@bp.route('/add_enzyme_activation', methods=['GET', 'POST'])
@login_required
def add_enzyme_activation():
    """
    Adds an enzyme activation entry to the database.

    Starts by creating a list of all metabolite bigg ids to use in the form auto completion.

    After the form validation:
     - checks if the activator metabolite is in the DB and if not adds and returns the instance
     - queries the database to get the respective EnzymeReactionOrganism entry
     -  - if it doesn't exist, it is addded
     - creates and adds the EnzymeReactionActivation object to the DB
     - associates the EnzymeReactionActivation to the specified models in the form
     - adds the references specified in the form.


    Returns:
        url_for insert data with EnzymeActivationForm before form validation
        url_for see_enzyme_activator after form validation
    """

    form = EnzymeActivationForm()

    metabolites = Metabolite.query.all()
    metabolite_list = {'id_value': '#metabolite_list', 'input_data': [{'field1': metabolite.bigg_id} for metabolite in
                                                                      metabolites] if metabolites else []}
    data_list = [metabolite_list]

    if form.validate_on_submit():

        activator_met = check_metabolite(form.activator_met.data)
        activation_evidence_level_id = form.activation_evidence_level.data.id if form.activation_evidence_level.data else None

        enz_rxn_org = EnzymeReactionOrganism.query.filter_by(enzyme_id=form.enzyme.data.id,
                                                             reaction_id=form.reaction.data.id,
                                                             organism_id=form.organism.data.id).first()

        if not enz_rxn_org:
            enz_rxn_org = EnzymeReactionOrganism(id=EnzymeReactionOrganism.query.count()+1,
                                                 enzyme_id=form.enzyme.data.id,
                                                 reaction_id=form.reaction.data.id,
                                                 organism_id=form.organism.data.id)
            db.session.add(enz_rxn_org)
            db.session.commit()

        enz_rxn_activation = EnzymeReactionActivation(enz_rxn_org_id=enz_rxn_org.id,
                                                      activator_met_id=activator_met.id,
                                                      activation_constant=form.activation_constant.data,
                                                      evidence_level_id=activation_evidence_level_id,
                                                      comments=form.comments.data)
        db.session.add(enz_rxn_activation)
        db.session.commit()

        if form.models.data:
            for model in form.models.data:
                enz_rxn_activation.add_model(model)

        if form.references.data:
            add_references(form.references.data, enz_rxn_activation)
            #for ref_db in ref_db_list:
            #    enz_rxn_activation.add_reference(ref_db)

        db.session.commit()

        flash('Your enzyme activation is now live!', 'success')

        return redirect(url_for('main.see_enzyme_activator', activator_id=enz_rxn_activation.id))
    return render_template('insert_data.html', title='Add enzyme activation', form=form, header='Add enzyme activation',
                           data_list=data_list)


@bp.route('/add_enzyme_effector', methods=['GET', 'POST'])
@login_required
def add_enzyme_effector():
    """
    Adds an enzyme effector entry to the database.

    The difference between an effector and an inhibitor/activator is that the former is assumed to be an allosteric
    effector, while an inhibitor is assumed to be a competitive/noncompetitive/uncompetitive inhibitor.
    Activators/Inhibitors are modeled differently than an effector. Also, an effector can be either activating or
    inhibiting.

    Starts by creating a list of all metabolite bigg ids to use in the form auto completion.

    After the form validation:
     - checks if the effector metabolite is in the DB and if not adds and returns the instance
     - queries the database to get the respective EnzymeReactionOrganism entry
     -  - if it doesn't exist, it is addded
     - creates and adds the EnzymeReactionEffector object to the DB
     - associates the EnzymeReactionEffector to the specified models in the form
     - adds the references specified in the form.


    Returns:
        url_for insert data with EnzymeEffectorForm before form validation
        url_for see_enzyme_effector after form validation
    """
    form = EnzymeEffectorForm()

    metabolites = Metabolite.query.all()
    metabolite_list = {'id_value': '#metabolite_list', 'input_data': [{'field1': metabolite.bigg_id} for metabolite in
                                                                      metabolites] if metabolites else []}
    data_list = [metabolite_list]

    if form.validate_on_submit():
        effector_met = check_metabolite(form.effector_met.data)
        effector_evidence_level_id = form.effector_evidence_level.data.id if form.effector_evidence_level.data else None

        enz_rxn_org = EnzymeReactionOrganism.query.filter_by(enzyme_id=form.enzyme.data.id,
                                                             reaction_id=form.reaction.data.id,
                                                             organism_id=form.organism.data.id).first()

        if not enz_rxn_org:
            enz_rxn_org = EnzymeReactionOrganism(id=EnzymeReactionOrganism.query.count()+1,
                                                 enzyme_id=form.enzyme.data.id,
                                                 reaction_id=form.reaction.data.id,
                                                 organism_id=form.organism.data.id)
            db.session.add(enz_rxn_org)
            db.session.commit()

        enz_rxn_effector = EnzymeReactionEffector(enz_rxn_org_id=enz_rxn_org.id,
                                                  effector_met_id=effector_met.id,
                                                  effector_type=form.effector_type.data,
                                                  evidence_level_id=effector_evidence_level_id,
                                                  comments=form.comments.data)
        db.session.add(enz_rxn_effector)

        if form.models.data:
            for model in form.models.data:
                enz_rxn_effector.add_model(model)

        if form.references.data:
            add_references(form.references.data, enz_rxn_effector)
            #for ref_db in ref_db_list:
            #    enz_rxn_effector.add_reference(ref_db)

        db.session.commit()
        flash('Your enzyme effector is now live!', 'success')

        return redirect(url_for('main.see_enzyme_effector', effector_id=enz_rxn_effector.id))
    return render_template('insert_data.html', title='Add enzyme effector', form=form, header='Add enzyme effector',
                           data_list=data_list)


@bp.route('/add_enzyme_misc_info', methods=['GET', 'POST'])
@login_required
def add_enzyme_misc_info():
    """
     Adds miscellaneous info to the database.
     It is used to store info that doesn't fit in any of the other existing categories, but is still deemed important.

     After the form validation:
      - queries the database to get the respective EnzymeReactionOrganism entry
      -  - if it doesn't exist, it is addded
      - creates and adds the EnzymeReactionMiscInfo object to the DB
      - associates the EnzymeReactionMiscInfo to the specified models in the form
      - adds the references specified in the form.


     Returns:
         url_for insert data with EnzymeMiscInfoForm before form validation
         url_for see_enzyme_misc_info after form validation
     """
    form = EnzymeMiscInfoForm()

    if form.validate_on_submit():

        evidence_level_id = form.evidence_level.data.id if form.evidence_level.data else None

        enz_rxn_org = EnzymeReactionOrganism.query.filter_by(enzyme_id=form.enzyme.data.id,
                                                             reaction_id=form.reaction.data.id,
                                                             organism_id=form.organism.data.id).first()
        if not enz_rxn_org:
            enz_rxn_org = EnzymeReactionOrganism(id=EnzymeReactionOrganism.query.count()+1,
                                                 enzyme_id=form.enzyme.data.id,
                                                 reaction_id=form.reaction.data.id,
                                                 organism_id=form.organism.data.id)
            db.session.add(enz_rxn_org)
            db.session.commit()

        enz_rxn_misc_info = EnzymeReactionMiscInfo(enz_rxn_org_id=enz_rxn_org.id,
                                                   topic=form.topic.data,
                                                   description=form.description.data,
                                                   evidence_level_id=evidence_level_id,
                                                   comments=form.comments.data)
        db.session.add(enz_rxn_misc_info)

        if form.models.data:
            for model in form.models.data:
                enz_rxn_misc_info.add_model(model)

        if form.references.data:
            add_references(form.references.data, enz_rxn_misc_info)
            #for ref_db in ref_db_list:
            #    enz_rxn_misc_info.add_reference(ref_db)

        db.session.commit()

        flash('Your enzyme misc info is now live!', 'success')

        return redirect(url_for('main.see_enzyme_misc_info', misc_info_id=enz_rxn_misc_info.id))
    return render_template('insert_data.html', title='Add enzyme misc info', form=form, header='Add enzyme misc info')


@bp.route('/add_gene', methods=['GET', 'POST'])
@login_required
def add_gene():
    """
     Adds a gene to the database.

     Returns:
         url_for insert data with GeneForm before form validation
         url_for see_enzyme_list after form validation
    """

    form = GeneForm()

    if form.validate_on_submit():
        gene = Gene(name=form.name.data)

        db.session.add(gene)

        db.session.commit()

        flash('Your enzyme is now live!')
        return redirect(url_for('main.see_enzyme_list'))
    return render_template('insert_data.html', title='Add gene', form=form, header='Add gene')


@bp.route('/add_metabolite', methods=['GET', 'POST'])
@login_required
def add_metabolite():
    """
     Adds a metabolite to the database.

     After the form validation:
      - create Metabolite object and adds it to the DB
      - adds all compartments to DB where metabolite can be found (according to the data inserted by the user)
      - parses the lists of chebi IDs and inchis and adds the respective ChebiIds entries to the DB.

     Returns:
         url_for insert data with MetaboliteForm before form validation
         url_for see_metabolite after form validation
    """

    form = MetaboliteForm()

    if form.validate_on_submit():
        metabolite = Metabolite(grasp_id=form.grasp_id.data,
                                name=form.name.data,
                                bigg_id=form.bigg_id.data,
                                metanetx_id=form.metanetx_id.data)
        db.session.add(metabolite)

        for compartment in form.compartments.data:
            metabolite.add_compartment(compartment)

        chebi_id_list = parse_input_list(form.chebi_ids.data)
        inchi_list = parse_input_list(form.inchis.data, False)
        for chebi_id, inchi_id in zip(chebi_id_list, inchi_list):
            chebi_id_db = ChebiIds(chebi_id=chebi_id,
                                   inchi=inchi_id)

            db.session.add(chebi_id_db)
            metabolite.add_chebi_id(chebi_id_db)

        db.session.commit()

        flash('Your metabolite is now live!', 'success')

        return redirect(url_for('main.see_metabolite', grasp_id=form.grasp_id.data))

    return render_template('insert_data.html', title='Add metabolite', form=form, header='Add metabolite')


@bp.route('/add_model', methods=['GET', 'POST'])
@login_required
def add_model():
    """"
     Adds a model to the database.

     The model can either be built from an existing model (base model) or from scratch.

     If the model is to be built from an existing model the user is redirected to modify_model.

     If the model is to be built from scatch:
       - before the form validation a list of organisms is built to be used in the form autocompletion.
       - after the form validation:
          - checks if the organism exists and if not adds it to the DB
          - adds the model
          - adds all the specified enz_rxn_orgs entities to the DB

     Returns:
         url_for insert data with ModelFormBase before form validation
         url_for modify_model after form validation if a base model is specified
         url_for insert data with ModelForm before form validation if a model is to be created from scratch
         url_for see_model_list after form validation and if model is created from scratch
    """

    text = 'If you want to build a model from an existing one, please select the desired model. ' \
           'Otherwise press "Continue".'

    form_base = ModelFormBase()

    if form_base.validate_on_submit():

        if form_base.model_base.data:
            return redirect(url_for('main.modify_model', model_name=form_base.model_base.data.name))

        else:
            organisms = Organism.query.all()
            organism_name = {'id_value': '#organism_name',
                             'input_data': [{'field1': organism.name} for organism in organisms] if organisms else []}
            data_list = [organism_name]

            form = ModelForm()

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

                if form.enz_rxn_orgs.data:
                    for enz_rxn_org in form.enz_rxn_orgs.data:
                        model.add_enzyme_reaction_organism(enz_rxn_org)

                db.session.commit()

                flash('Your model is now live!')
                return redirect(url_for('main.see_model_list'))

            return render_template('insert_data.html', title='Add model', form=form, header='Add model',
                                   data_list=data_list)

    return render_template('insert_data.html', title='Add model', form=form_base, header='Add model', text=text)


@bp.route('/add_model_assumption', methods=['GET', 'POST'])
@login_required
def add_model_assumption():
    """"
     Adds a model assumption to the database.

     After form validation:
       - the ModelAssumptions object is created and added to the DB
       - all associated references are also added to the DB

     Returns:
         url_for insert data with ModelAssumptionsForm before form validation
         url_for see_model_list after form validation
    """

    form = ModelAssumptionsForm()

    if form.validate_on_submit():

        evidence_level_id = form.evidence_level.data.id if form.evidence_level.data else None
        included_in_model = True if form.included_in_model.data == 'True' else False

        model_assumption = ModelAssumptions(model_id=form.model.data.id,
                                            assumption=form.assumption.data,
                                            description=form.description.data,
                                            evidence_level_id=evidence_level_id,
                                            included_in_model=included_in_model,
                                            comments=form.comments.data)
        db.session.add(model_assumption)

        if form.references.data:
            add_references(form.references.data, model_assumption)
            #for ref_db in ref_db_list:
            #    model_assumption.add_reference(ref_db)

        db.session.commit()

        flash('Your model assumption is now live!', 'success')

        return redirect(url_for('main.see_model_list'))
    return render_template('insert_data.html', title='Add model assumption', form=form, header='Add model assumption')


@bp.route('/add_organism', methods=['GET', 'POST'])
@login_required
def add_organism():
    """"
     Adds an organism to the database.

     After form validation:
       - the Organism object is created and added to the DB

     Returns:
         url_for insert data with OrganismForm before form validation
         url_for see_organism_list after form validation
    """

    form = OrganismForm()

    if form.validate_on_submit():
        organism = Organism(name=form.name.data)
        db.session.add(organism)
        db.session.commit()

        flash('Your organism is now live!', 'success')

        return redirect(url_for('main.see_organism_list'))
    return render_template('insert_data.html', title='Add organism', form=form, header='Add organism')


@bp.route('/add_reaction', methods=['GET', 'POST'])
@login_required
def add_reaction():
    """"
     Adds a reaction to the database.

     Before form validation builds a list of isoenzymes to be used in the form autocompletion.

     After form validation:
       - the Reaction object is created and added to the DB
       - the metabolites involved in the reaction are associated to the reaction
       - if a compartment is specified, it is associated to the reaction
       - the respective EnzymeReactionOrganism objects are created and added to the DB
       - mechanism references are added to the DB
       - EnzymeReactionOrganism entities are associated to the respective model
       - standard Gibbs energies are added and associated to the reaction

     Returns:
         url_for insert data with ReactionForm before form validation
         url_for see_reaction_list after form validation
    """

    form = ReactionForm()

    enzymes = Enzyme.query.all()
    isoenzyme_list = {'id_value': '#isoenzyme_acronyms',
                      'input_data': [{'field1': enzyme.isoenzyme} for enzyme in enzymes] if enzymes else []}
    data_list = [isoenzyme_list]

    if form.validate_on_submit():

        compartment = form.compartment.data if form.compartment.data else None
        reaction = Reaction(name=form.name.data,
                            acronym=form.acronym.data,
                            metanetx_id=form.metanetx_id.data,
                            bigg_id=form.bigg_id.data,
                            kegg_id=form.kegg_id.data,
                            compartment=compartment)

        db.session.add(reaction)

        add_metabolites_to_reaction(reaction, form.reaction_string.data)

        if compartment:
            compartment = Compartment.query.filter_by(name=compartment.name).first()
            compartment.add_reaction(reaction)

        mechanism_id = form.mechanism.data.id if form.mechanism.data else None
        mech_evidence_level_id = form.mechanism_evidence_level.data.id if form.mechanism_evidence_level.data else None

        for enzyme in form.enzymes.data:
            enzyme_reaction_organism = EnzymeReactionOrganism(id=EnzymeReactionOrganism.query.count() + 1,
                                                              enzyme_id=enzyme.id,
                                                              reaction_id=reaction.id,
                                                              organism_id=form.organism.data.id,
                                                              mechanism_id=mechanism_id,
                                                              mech_evidence_level_id=mech_evidence_level_id,
                                                              grasp_id=form.grasp_id.data,
                                                              subs_binding_order=form.subs_binding_order.data,
                                                              prod_release_order=form.prod_release_order.data,
                                                              comments=form.comments.data)
            db.session.add(enzyme_reaction_organism)

            if form.mechanism_references.data:
                add_references(form.mechanism_references.data, enzyme_reaction_organism, mechanism_ref=True)

            if form.models.data:
                for model in form.models.data:
                    enzyme_reaction_organism.add_model(model)

                    if form.std_gibbs_energy.data:
                        add_gibbs_energy(reaction.id, model.id, form.std_gibbs_energy.data,
                                         form.std_gibbs_energy_std.data,
                                         form.std_gibbs_energy_ph.data, form.std_gibbs_energy_ionic_strength.data,
                                         form.std_gibbs_energy_references.data)

        db.session.commit()

        flash('Your reaction is now live!', 'success')

        return redirect(url_for('main.see_reaction_list'))

    return render_template('insert_data.html', title='Add reaction', form=form, header='Add reaction',
                           data_list=data_list)
