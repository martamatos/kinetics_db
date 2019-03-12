import os

from flask import current_app
from flask import render_template, flash, redirect, url_for
from werkzeug.utils import secure_filename

from app import db
from app.load_data.import_grasp_model import get_model_name, get_model_stoichiometry, get_model_enzymes, \
    get_model_subunits, \
    get_model_mechanisms, get_model_inhibitors, get_model_activators, get_model_effectors, get_model_gibbs_energies
from app.main import bp
from app.main.forms import UploadModelForm
from app.main.utils import add_enzyme_structures, add_enzyme_organism, add_metabolites_to_reaction, \
    add_references, check_metabolite, set_binding_release_order, \
    add_enzyme_organism_subunits_only, add_effector
from app.models import Enzyme, EnzymeReactionOrganism, EnzymeReactionActivation, \
    EnzymeReactionInhibition, Model, Mechanism, GibbsEnergy, \
    Reaction, GibbsEnergyReactionModel
from app.utils.parsers import parse_input_list


@bp.route('/upload_model', methods=['GET', 'POST'])
# @login_required
def upload_model():
    """

    :return:
    """

    form = UploadModelForm()

    if form.validate_on_submit():

        f_in = form.model.data
        filename = secure_filename(f_in.filename)
        file_path = os.path.join(current_app.upload_path, filename)
        f_in.save(file_path)

        # create new model
        model_name = get_model_name(file_path, 'general')
        model = Model(name=model_name)
        db.session.add(model)

        mets, rxns, rxn_strings = get_model_stoichiometry(file_path, 'stoic')
        enzyme_list = get_model_enzymes(file_path, 'enzyme_reaction')
        subunit_dict = get_model_subunits(file_path, 'kinetics1')
        gibbs_energies_dict = get_model_gibbs_energies(file_path, 'thermoRxns')
        mechanisms_dict = get_model_mechanisms(file_path, 'kinetics1')
        inhibitors_dict = get_model_inhibitors(file_path, 'kinetics1')
        activators_dict = get_model_activators(file_path, 'kinetics1')
        neg_effectors_dict, pos_effectors_dict = get_model_effectors(file_path, 'kinetics1')

        for i, rxn in enumerate(rxns):

            # add enzyme
            if enzyme_list[i]['isoenzyme']:
                enzyme_db = Enzyme.query.filter_by(isoenzyme=enzyme_list[i]['isoenzyme']).first()
                if not enzyme_db:
                    enzyme_db = Enzyme(name=enzyme_list[i]['enzyme_name'],
                                       acronym=enzyme_list[i]['enzyme_acronym'],
                                       isoenzyme=enzyme_list[i]['isoenzyme'],
                                       ec_number=enzyme_list[i]['ec_number'])
                    db.session.add(enzyme_db)

                    # add uniprot and subunit info
                    if enzyme_list[i]['uniprot_ids']:
                        uniprot_id_list = parse_input_list(enzyme_list[i]['uniprot_ids'])
                        add_enzyme_organism(enzyme_db, form.organism.data.id, uniprot_id_list, subunit_dict[rxn])
                    else:
                        add_enzyme_organism_subunits_only(enzyme_db, form.organism.data.id, subunit_dict[rxn])

                    # add structure info
                    if enzyme_list[i]['pdb_ids']:
                        pdb_id_list = parse_input_list(enzyme_list[i]['pdb_ids'])
                        pdb_strains_list = parse_input_list(enzyme_list[i]['strain'])

                        add_enzyme_structures(enzyme_db, form.organism.data.id, pdb_id_list, pdb_strains_list)

                db.session.commit()

            elif rxn.startswith('EX_') or rxn.startswith('IN_'):
                enzyme_db = Enzyme.query.filter_by(isoenzyme='EX_enz').first()

            else:
                flash('An isoenzyme must be defined for every enzymatic reaction.')
                return render_template('upload_model.html', title='Upload model', form=form, header='Upload model')

            # add reaction
            reaction_db = Reaction.query.filter_by(acronym=rxn).first()
            if not reaction_db:
                reaction_db = Reaction(acronym=rxn,
                                       bigg_id=rxn)
                db.session.add(reaction_db)

                add_metabolites_to_reaction(reaction_db, rxn_strings[i])

            # add enzyme_reaction_organism
            enz_rxn_org = EnzymeReactionOrganism(id=EnzymeReactionOrganism.query.count() + 1,
                                                 enzyme_id=enzyme_db.id,
                                                 reaction_id=reaction_db.id,
                                                 organism_id=form.organism.data.id,
                                                 grasp_id=rxn)
            db.session.add(enz_rxn_org)
            db.session.commit()
            enz_rxn_org.add_model(model)

            # add mechanism
            mechanism_type = None
            for db_mech_type in Mechanism.query.all():
                if mechanisms_dict[rxn][0].lower().find(db_mech_type.name.lower()) != -1:
                    mechanism_type = db_mech_type.name
                    break

            if mechanism_type:
                mechanism_db = Mechanism.query.filter_by(grasp_name=mechanisms_dict[rxn][0]).first()
                if not mechanism_db:

                    mechanism_db = Mechanism(name=mechanism_type,
                                             grasp_name=mechanisms_dict[rxn][0])
                    db.session.add(mechanism_db)
                    enz_rxn_org.mechanism = mechanism_db
                    mechanism_db.add_enzyme_reaction_organism(enz_rxn_org)

                    if mechanisms_dict[rxn][2]:
                        add_references(mechanisms_dict[rxn][2], enz_rxn_org, mechanism_ref=True)

                if mechanisms_dict[rxn][1]:
                    set_binding_release_order(rxn, rxn_strings[i], enz_rxn_org, mechanisms_dict)

            # add inhibitors
            for inhib_met_i, inhib_met in enumerate(inhibitors_dict[rxn][0]):

                inhib_met_db = check_metabolite(inhib_met)

                enz_inhib_db = EnzymeReactionInhibition.query.filter_by(affected_met=None,
                                                                        inhibition_type=None,
                                                                        inhibition_constant=None,
                                                                        inhibitor_met=inhib_met_db).first()

                if not enz_inhib_db:
                    enz_inhib_db = EnzymeReactionInhibition(inhibitor_met=inhib_met_db)
                    db.session.add(enz_inhib_db)

                enz_inhib_db.add_model(model)
                enz_rxn_org.add_enzyme_reaction_inhibition(enz_inhib_db)

                if inhibitors_dict[rxn][1] and inhibitors_dict[rxn][1][inhib_met_i]:
                    add_references(inhibitors_dict[rxn][1][inhib_met_i], enz_inhib_db)

            # add activators
            for activ_met_i, activ_met in enumerate(activators_dict[rxn][0]):
                activ_met_db = check_metabolite(activ_met)

                enz_activ_db = EnzymeReactionActivation.query.filter_by(activation_constant=None,
                                                                        activator_met=activ_met_db).first()

                if not enz_activ_db:
                    enz_activ_db = EnzymeReactionActivation(activator_met=activ_met_db)
                    db.session.add(enz_activ_db)

                enz_rxn_org.add_enzyme_reaction_activation(enz_activ_db)
                enz_activ_db.add_model(model)

                if activators_dict[rxn][1] and activators_dict[rxn][1][activ_met_i]:
                    add_references(activators_dict[rxn][1][activ_met_i], enz_activ_db)

            # add negative effectors
            add_effector(neg_effectors_dict, rxn, 'Inhibiting', model, enz_rxn_org)
            add_effector(pos_effectors_dict, rxn, 'Activating', model, enz_rxn_org)

            # add gibbs energies
            gibbs_energy_db = GibbsEnergy.query.filter_by(standard_dg=gibbs_energies_dict[rxn][0],
                                                          standard_dg_std=gibbs_energies_dict[rxn][1]).first()
            if not gibbs_energy_db:
                gibbs_energy_db = GibbsEnergy(standard_dg=gibbs_energies_dict[rxn][0],
                                              standard_dg_std=gibbs_energies_dict[rxn][1])
                db.session.add(gibbs_energy_db)

                gibbs_energy_rxn_model_db = GibbsEnergyReactionModel(model=model,
                                                                     reaction=reaction_db,
                                                                     gibbs_energy=gibbs_energy_db)
                db.session.add(gibbs_energy_rxn_model_db)

                add_references(gibbs_energies_dict[rxn][2], gibbs_energy_db)

        flash('Your model is now live!', 'success')

        return redirect(url_for('main.see_model_list'))

    return render_template('upload_model.html', title='Upload model', form=form, header='Upload model')
