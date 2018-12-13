"""db refactored after load_data

Revision ID: 7ae322ba00eb
Revises: ddfdc6cdce05
Create Date: 2018-12-13 17:31:08.946977

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7ae322ba00eb'
down_revision = 'ddfdc6cdce05'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('enzyme_complex_subunit',
    sa.Column('enzyme_complex_id', sa.Integer(), nullable=True),
    sa.Column('enzyme_subunit_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['enzyme_complex_id'], ['enzyme.id'], ),
    sa.ForeignKeyConstraint(['enzyme_subunit_id'], ['enzyme.id'], )
    )
    op.create_table('enzyme_gene_organism',
    sa.Column('gene_id', sa.Integer(), nullable=False),
    sa.Column('enzyme_id', sa.Integer(), nullable=False),
    sa.Column('organism_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['enzyme_id'], ['enzyme.id'], ),
    sa.ForeignKeyConstraint(['gene_id'], ['gene.id'], ),
    sa.ForeignKeyConstraint(['organism_id'], ['organism.id'], ),
    sa.PrimaryKeyConstraint('gene_id', 'enzyme_id', 'organism_id')
    )
    op.drop_table('enzyme_organism_gene')
    op.add_column('compartment', sa.Column('bigg_id', sa.String(), nullable=True))
    op.drop_constraint('compartment_bigg_acronym_key', 'compartment', type_='unique')
    op.create_unique_constraint(None, 'compartment', ['bigg_id'])
    op.drop_column('compartment', 'bigg_acronym')
    op.create_unique_constraint(None, 'gene', ['name'])
    op.drop_column('gene', 'bigg_id')
    op.add_column('reaction_metabolite', sa.Column('compartment_id', sa.Integer(), nullable=False))
    op.create_foreign_key(None, 'reaction_metabolite', 'compartment', ['compartment_id'], ['id'])
    op.drop_column('reaction_metabolite', 'met_comp_acronym')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('reaction_metabolite', sa.Column('met_comp_acronym', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'reaction_metabolite', type_='foreignkey')
    op.drop_column('reaction_metabolite', 'compartment_id')
    op.add_column('gene', sa.Column('bigg_id', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'gene', type_='unique')
    op.add_column('compartment', sa.Column('bigg_acronym', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'compartment', type_='unique')
    op.create_unique_constraint('compartment_bigg_acronym_key', 'compartment', ['bigg_acronym'])
    op.drop_column('compartment', 'bigg_id')
    op.create_table('enzyme_organism_gene',
    sa.Column('enzyme_organism_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('gene_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['enzyme_organism_id'], ['enzyme_organism.id'], name='enzyme_organism_gene_enzyme_organism_id_fkey'),
    sa.ForeignKeyConstraint(['gene_id'], ['gene.id'], name='enzyme_organism_gene_gene_id_fkey')
    )
    op.drop_table('enzyme_gene_organism')
    op.drop_table('enzyme_complex_subunit')
    # ### end Alembic commands ###
