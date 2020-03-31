import os
import numpy as np
import pandas as pd
from flask import current_app
from flask import render_template, flash, redirect, url_for
from werkzeug.utils import secure_filename
import flask_sqlalchemy

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



def _add_enzyme(i, rxn, enzyme_list, form, subunit_dict):

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

    return enzyme_db


def _add_mechanism(i, rxn, enz_rxn_org, rxn_strings, mechanisms_dict):

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


def _add_inhibitors(rxn, enz_rxn_org, model, inhibitors_dict):
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

        if inhibitors_dict[rxn][1]:
            try:
                if len(inhibitors_dict[rxn][1]) > 1:
                    add_references(inhibitors_dict[rxn][1][inhib_met_i], enz_inhib_db)
                else:
                    add_references(inhibitors_dict[rxn][1][0], enz_inhib_db)
            except IndexError:
                print(f'Number of references is wrong for inhibitor {inhib_met} from reaction {rxn}. '
                      f'These references won\'t be added.'
                      f'There should be either a single reference for all inhibitors, or one for each.')


def _add_activators(rxn, enz_rxn_org, model, activators_dict):
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
        if activators_dict[rxn][1]:
            try:
                if len(activators_dict[rxn][1]) > 1:
                    add_references(activators_dict[rxn][1][activ_met_i], enz_activ_db)
                else:
                    add_references(activators_dict[rxn][1][0], enz_activ_db)
            except IndexError:
                print(f'Number of references is wrong for inhibitor {activ_met} from reaction {rxn}. '
                      f'These references won\'t be added.'
                      f'There should be either a single reference for all inhibitors, or one for each.')


def _add_gibbs_energies(rxn, reaction_db, model, gibbs_energies_dict):

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


#TODO: add metabolite names to metabolites
#TODO: add reaction names to reactions

@bp.route('/upload_model', methods=['GET', 'POST'])
# @login_required
def upload_model():
    """
    Takes in the excel input file for GRASP and inserts the following data in the DB:
    Model: a model for the chosen organism is added.
    Enzymes:
    Metabolites:
    Reactions:
    Inhibitions:
    Activations:
    Effectors:
    Gibbs energies:

    :return: None
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
        model.organism = form.organism.data
        db.session.add(model)

        # load input file
        mets, rxns, rxn_strings = get_model_stoichiometry(file_path, 'stoic')
        enzyme_list = get_model_enzymes(file_path, 'enzyme_reaction')
        subunit_dict = get_model_subunits(file_path, 'kinetics1')
        gibbs_energies_dict = get_model_gibbs_energies(file_path, 'thermoRxns')
        mechanisms_dict = get_model_mechanisms(file_path, 'kinetics1')
        inhibitors_dict = get_model_inhibitors(file_path, 'kinetics1')
        activators_dict = get_model_activators(file_path, 'kinetics1')
        neg_effectors_dict, pos_effectors_dict = get_model_effectors(file_path, 'kinetics1')
        print(mechanisms_dict)

        for i, rxn in enumerate(rxns):

            # add enzyme
            enzyme_db = _add_enzyme(i, rxn, enzyme_list, form, subunit_dict)

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

            _add_mechanism(i, rxn, enz_rxn_org, rxn_strings, mechanisms_dict)

            # add inhibitors
            _add_inhibitors(rxn, enz_rxn_org, model, inhibitors_dict)

            # add activators
            _add_activators(rxn, enz_rxn_org, model, activators_dict)

            # add effectors
            add_effector(neg_effectors_dict, rxn, 'Inhibiting', model, enz_rxn_org)
            add_effector(pos_effectors_dict, rxn, 'Activating', model, enz_rxn_org)

            # add gibbs energies
            _add_gibbs_energies(rxn, reaction_db, model, gibbs_energies_dict)

        flash('Your model is now live!', 'success')
        return redirect(url_for('main.see_model_list'))

    return render_template('upload_model.html', title='Upload model', form=form, header='Upload model')


@bp.route('/download_model/<model_name>', methods=['GET', 'POST'])
def download_model(model_name):

    # general sheet: write name only
    general_df = pd.DataFrame()
    general_df.loc[0, 0] = model_name
    general_df.loc[0, 1] = 'HMP'
    general_df.columns = ['General Reaction and Sampling Platform (GRASP)', '']

    # stoic sheet: write all
    model = Model.query.filter_by(name=model_name).first()
    model_reactions = [enz_rxn_org.reaction for enz_rxn_org in model.enzyme_reaction_organisms]
    reaction_metabolites = dict([(enz_rxn_org.grasp_id,
                                  dict([(rxn_met.metabolite.grasp_id + '_' + rxn_met.compartment.bigg_id, rxn_met.stoich_coef) for rxn_met in enz_rxn_org.reaction.metabolites]))
                                 for enz_rxn_org in model.enzyme_reaction_organisms])

    model_metabolites = dict([(rxn_met.metabolite.grasp_id + '_' + rxn_met.compartment.bigg_id, rxn_met.metabolite.name) for reaction in model_reactions for rxn_met in reaction.metabolites])

    stoic_mat = [[reaction_metabolites[rxn][met] if met in reaction_metabolites[rxn].keys() else 0 for met in model_metabolites] for rxn in reaction_metabolites.keys()]
    stoic_df = pd.DataFrame(data=stoic_mat, index=reaction_metabolites.keys(), columns=model_metabolites)
    print(stoic_df)

    # mets sheet: write column names, ID, metabolite_names, balanced
    met_names = []
    balanced_mets = []
    fixed_mets = []
    active_mets = np.repeat(1, len(model_metabolites))

    for met in stoic_df.columns:
        met_names.append(model_metabolites[met])

        if stoic_df[met].gt(0).any() and stoic_df[met].lt(0).any():
            balanced_mets.append(1)
            fixed_mets.append(0)
        else:
            balanced_mets.append(0)
            fixed_mets.append(1)

    col_names = ['metabolite name', 'balanced?', 'active?', 'fixed?']
    mets_df = pd.DataFrame(data=np.array([met_names, balanced_mets, active_mets, fixed_mets]).transpose(), index=model_metabolites, columns=col_names)
    mets_df.index.name = 'ID'

    # rxns sheet:  write column names, D, reaction names

    reaction_names = [rxn.name for rxn in model_reactions]
    col_names = ['reaction name', 'transportRxn?', 'modelled?']
    rxns_df = pd.DataFrame(data=np.array([reaction_names, np.repeat(0, len(model_reactions)), np.repeat(0, len(model_reactions))]).transpose(), index=stoic_df.index, columns=col_names)
    rxns_df.index.name = 'ID'

    # splitRatios: write ID
    split_ratios_df = pd.DataFrame(data=[], index=stoic_df.index)
    split_ratios_df.index.name = 'ID'

    # poolConst: write ID
    pool_const_df = pd.DataFrame(data=[], index=stoic_df.columns)
    pool_const_df.index.name = 'met'


    # thermoIneqConstraints: write ID
    thermo_ineq_const_df = pd.DataFrame(data=[], index=stoic_df.columns)
    thermo_ineq_const_df.index.name = 'met'

    # thermoRxns: write all
    map_rxn_id_grasp_id = dict([(enz_rxn_org.reaction_id, enz_rxn_org.grasp_id) for enz_rxn_org in model.enzyme_reaction_organisms])

    gibbs_energies = dict([(map_rxn_id_grasp_id[gibbs_rxn_model.reaction_id],
                            (gibbs_rxn_model.gibbs_energy.standard_dg - gibbs_rxn_model.gibbs_energy.standard_dg_std,
                             gibbs_rxn_model.gibbs_energy.standard_dg + gibbs_rxn_model.gibbs_energy.standard_dg_std,
                             ' '.join([ref.doi if ref.doi else '' for ref in gibbs_rxn_model.gibbs_energy.references])))

                           for gibbs_rxn_model in model.gibbs_energy_reaction_models])

    thermo_rxns_df = pd.DataFrame(data=list(gibbs_energies.values()), index=gibbs_energies.keys(), columns=['∆Gr\'_min (kJ/mol)', '∆Gr\'_max (kJ/mol)', 'refs'])
    thermo_rxns_df.index.name = 'rxn'

    # thermoMets: write column names and ID
    thermo_mets_df = pd.DataFrame(data=[], index=stoic_df.columns, columns=['min (M)', 'max (M)'])
    thermo_mets_df.index.name = 'met'

    # measRates: write columns names and ID
    meas_rates_df = pd.DataFrame(data=[], columns=['vref_mean', 'vref_std', 'vexp1_mean', 'vexp1_std'])
    meas_rates_df.index.name = 'Fluxes (umol/gCDW/h)'
    print(meas_rates_df)

    # protData: write columns names and ID
    #print(np.repeat([0.99, 1, 1.01], [len(stoic_df.index),3]))
    prot_data_df = pd.DataFrame(data=np.array([np.repeat(0.99, len(stoic_df.index)), np.repeat(1, len(stoic_df.index)), np.repeat(1.01, len(stoic_df.index))]).transpose(), index=stoic_df.index, columns=['MBo10_LB2', 'MBo10_meas2', 'MBo10_UB2'])
    prot_data_df.index.name = 'enzyme/rxn'

    # metsData: write columns names and ID
    met_data_df = pd.DataFrame(data=np.array([np.repeat(0.99, len(stoic_df.columns)), np.repeat(1, len(stoic_df.columns)), np.repeat(1.01, len(stoic_df.columns))]).transpose(), index=stoic_df.columns, columns=['MBo10_LB2', 'MBo10_meas2', 'MBo10_UB2'])
    met_data_df.index.name = 'met'

    # kinetics1: write all
    organism_id = model.organism.id

    mechanisms = [enz_rxn_org.mechanism.name if enz_rxn_org.mechanism else '' for enz_rxn_org in model.enzyme_reaction_organisms]
    order = [' '.join([enz_rxn_org.subs_binding_order, enz_rxn_org.prod_release_order]) if enz_rxn_org.subs_binding_order and enz_rxn_org.prod_release_order else '' for enz_rxn_org in model.enzyme_reaction_organisms]
    promiscuous = ['' for i in range(len(stoic_df.index))]
    inhibitors = [' '.join([inhib.inhibitor_met.bigg_id for inhib in enz_rxn_org.enzyme_reaction_inhibitors]) if enz_rxn_org.enzyme_reaction_inhibitors else '' for enz_rxn_org in model.enzyme_reaction_organisms]
    activators = [' '.join([activ.activator_met.bigg_id for activ in enz_rxn_org.enzyme_reaction_activators]) if enz_rxn_org.enzyme_reaction_activators else '' for enz_rxn_org in model.enzyme_reaction_organisms]
    pos_effectors = [' '.join([effector.effector_met.bigg_id if effector.effector_type == 'Activating' else '' for effector in enz_rxn_org.enzyme_reaction_effectors]) if enz_rxn_org.enzyme_reaction_effectors else '' for enz_rxn_org in model.enzyme_reaction_organisms]
    neg_effectors = [' '.join([effector.effector_met.bigg_id if effector.effector_type == 'Inhibiting' else '' for effector in enz_rxn_org.enzyme_reaction_effectors]) if enz_rxn_org.enzyme_reaction_effectors else '' for enz_rxn_org in model.enzyme_reaction_organisms]
    allosteric = [1 if enz_rxn_org.enzyme_reaction_effectors else 0 for enz_rxn_org in model.enzyme_reaction_organisms]
    subunits = [enz_rxn_org.enzyme.enzyme_organisms.filter_by(organism_id=organism_id).first().n_active_sites if enz_rxn_org.enzyme.enzyme_organisms.filter_by(organism_id=organism_id).first() else 1 for enz_rxn_org in model.enzyme_reaction_organisms]


    mechanisms_refs = [' '.join([ref.doi for ref in enz_rxn_org.mechanism_references]) if enz_rxn_org.mechanism_references else '' for enz_rxn_org in model.enzyme_reaction_organisms]
    inhibitors_refs = ['; '.join([' '.join([ref.doi for ref in inhib.references]) if inhib.references else '' for inhib in enz_rxn_org.enzyme_reaction_inhibitors]) if enz_rxn_org.enzyme_reaction_inhibitors else '' for enz_rxn_org in model.enzyme_reaction_organisms]
    activators_refs = ['; '.join([' '.join([ref.doi for ref in activ.references]) if activ.references else '' for activ in enz_rxn_org.enzyme_reaction_activators]) if enz_rxn_org.enzyme_reaction_activators else '' for enz_rxn_org in model.enzyme_reaction_organisms]
    pos_effectors_refs = ['; '.join([' '.join([ref.doi for ref in effector.references]) if effector.effector_type == 'Activating' and effector.references else '' for effector in enz_rxn_org.enzyme_reaction_effectors]) if enz_rxn_org.enzyme_reaction_effectors else '' for enz_rxn_org in model.enzyme_reaction_organisms]
    neg_effectors_refs = ['; '.join([' '.join([ref.doi for ref in effector.references]) if effector.effector_type == 'Inhibiting' and effector.references else '' for effector in enz_rxn_org.enzyme_reaction_effectors]) if enz_rxn_org.enzyme_reaction_effectors else '' for enz_rxn_org in model.enzyme_reaction_organisms]

    comments = [enz_rxn_org.comments if enz_rxn_org.comments else '' for enz_rxn_org in model.enzyme_reaction_organisms]

    kinetics_df = pd.DataFrame(data=np.array([mechanisms, order, promiscuous, inhibitors, activators, pos_effectors,
                                              neg_effectors, allosteric, subunits, mechanisms_refs, inhibitors_refs,
                                              activators_refs, pos_effectors_refs, neg_effectors_refs, comments]).transpose(),
                               index=stoic_df.index,
                               columns=['kinetic mechanism', 'order', 'promiscuous', 'inhibitors', 'activators',
                                        'negative effectors', 'positive effectors', 'allosteric', 'subunits',
                                        'mechanisms_refs', 'inhibitors_refs', 'activators_refs',
                                        'negative effectors_refs', 'positive effectors_refs', 'comments'])

    kinetics_df.index.name = 'reaction ID'
    print(kinetics_df)

    # enzyme_reaction: write all

    enz_names = []
    enz_acronyms = []
    enz_isoenzymes = []
    enz_ec_numbers = []
    enz_uniprot_ids = []
    enz_pdb_ids = []

    for enz_rxn_org in model.enzyme_reaction_organisms:
        enz_names.append(enz_rxn_org.enzyme.name if enz_rxn_org.enzyme.name else '')
        enz_acronyms.append(enz_rxn_org.enzyme.acronym if enz_rxn_org.enzyme.acronym else '')
        enz_isoenzymes.append(enz_rxn_org.enzyme.isoenzyme if enz_rxn_org.enzyme.isoenzyme else '')
        enz_ec_numbers.append(enz_rxn_org.enzyme.ec_number if enz_rxn_org.enzyme.ec_number else '')

        enz_org_list = enz_rxn_org.enzyme.enzyme_organisms.filter_by(organism_id=organism_id).all()
        enz_uniprot_ids.append(' '.join([enz_org.uniprot_id if enz_org.uniprot_id else '' for enz_org in enz_org_list]) if enz_org_list else '')

        enz_struct_list = enz_rxn_org.enzyme.enzyme_structures.filter_by(organism_id=organism_id).all()
        enz_pdb_ids.append(' '.join([enz_struct.pdb_id if enz_struct.pdb_id else '' for enz_struct in enz_struct_list]) if enz_struct_list else '')

    enzyme_reaction_df = pd.DataFrame(data=np.array([enz_names, enz_acronyms, enz_isoenzymes, enz_ec_numbers, enz_uniprot_ids, enz_pdb_ids]).transpose(),
                                      index=stoic_df.index, columns=['enzyme_name', 'enzyme_acronym', 'isoenzyme', 'ec_number', 'uniprot_ids' 'pdb_ids', 'strain'])
    enzyme_reaction_df.index.name = 'reaction_id'


    with pd.ExcelWriter(os.path.join(current_app.download_path, model_name + '.xlsx'), engine='xlsxwriter') as writer:  # doctest: +SKIP
        general_df.to_excel(writer, sheet_name='general', index=None)
        stoic_df.to_excel(writer, sheet_name='stoic', index=None)
        mets_df.to_excel(writer, sheet_name='mets', index=None)
        rxns_df.to_excel(writer, sheet_name='rxns', index=None)
        split_ratios_df.to_excel(writer, sheet_name='splitRatios', index=None)
        pool_const_df.to_excel(writer, sheet_name='poolConst', index=None)
        thermo_ineq_const_df.to_excel(writer, sheet_name='thermo_ineq_constraints', index=None)
        thermo_rxns_df.to_excel(writer, sheet_name='thermoRxns', index=None)
        thermo_mets_df.to_excel(writer, sheet_name='thermoMets', index=None)
        prot_data_df.to_excel(writer, sheet_name='protData', index=None)
        met_data_df.to_excel(writer, sheet_name='metsData', index=None)
        kinetics_df.to_excel(writer, sheet_name='kinetics1', index=None)
        enzyme_reaction_df.to_excel(writer, sheet_name='enzyme_reaction', index=None)

    return redirect(url_for('static', filename=os.path.join(current_app.download_path, model_name + '.xlsx')))

