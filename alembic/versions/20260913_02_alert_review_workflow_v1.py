"""PRAHARI Alert System and Officer Review Workflow V1."""
from alembic import op
import sqlalchemy as sa

revision="20260913_02";down_revision="20260909_01";branch_labels=None;depends_on=None

def upgrade():
    bind=op.get_bind();inspector=sa.inspect(bind);project_columns={x['name'] for x in inspector.get_columns('projects')};alert_columns={x['name'] for x in inspector.get_columns('alerts')}
    if 'data_origin' not in project_columns:op.add_column('projects',sa.Column('data_origin',sa.String(32),nullable=False,server_default='HISTORICAL_FLASH_REPORT'))
    if 'ix_projects_data_origin' not in {x['name'] for x in inspector.get_indexes('projects')}:op.create_index('ix_projects_data_origin','projects',['data_origin'])
    additions=[
        sa.Column('alert_type',sa.String(40),nullable=False,server_default='IMPLEMENTATION_PRESSURE'),sa.Column('severity',sa.String(16),nullable=False,server_default='ATTENTION'),sa.Column('data_origin',sa.String(32),nullable=False,server_default='HISTORICAL_FLASH_REPORT'),sa.Column('deduplication_key',sa.String(64)),sa.Column('reason_family',sa.String(40)),sa.Column('trigger_reason_codes',sa.JSON(),nullable=False,server_default='[]'),sa.Column('current_reason_codes',sa.JSON(),nullable=False,server_default='[]'),sa.Column('initial_evidence_snapshot',sa.JSON(),nullable=False,server_default='{}'),sa.Column('latest_evidence_snapshot',sa.JSON(),nullable=False,server_default='{}'),sa.Column('decision_state_at_open',sa.String(40)),sa.Column('decision_state_current',sa.String(40)),sa.Column('data_trust_at_open',sa.JSON(),nullable=False,server_default='{}'),sa.Column('data_trust_current',sa.JSON(),nullable=False,server_default='{}'),sa.Column('opened_at',sa.DateTime(timezone=True)),sa.Column('last_updated_at',sa.DateTime(timezone=True)),sa.Column('resolved_at',sa.DateTime(timezone=True)),sa.Column('reopened_at',sa.DateTime(timezone=True)),sa.Column('first_seen_month',sa.String(7)),sa.Column('last_seen_month',sa.String(7)),sa.Column('consecutive_valid_cycles',sa.Integer(),nullable=False,server_default='1'),sa.Column('watch_policy_version',sa.String(80)),sa.Column('decision_policy_version',sa.String(80)),sa.Column('review_policy_version',sa.String(80),nullable=False,server_default='officer-review-v1.0')]
    for column in additions:
        if column.name not in alert_columns:op.add_column('alerts',column)
    alert_indexes={x['name'] for x in sa.inspect(bind).get_indexes('alerts')}
    if 'uq_alert_deduplication_key' not in alert_indexes and not any(x.get('column_names')==['deduplication_key'] for x in sa.inspect(bind).get_unique_constraints('alerts')):op.create_index('uq_alert_deduplication_key','alerts',['deduplication_key'],unique=True)
    if 'ix_alerts_data_origin' not in alert_indexes:op.create_index('ix_alerts_data_origin','alerts',['data_origin'])
    if 'ix_alert_mode_status_updated' not in alert_indexes:op.create_index('ix_alert_mode_status_updated','alerts',['data_origin','status','last_updated_at'])
    alert_checks={x['name'] for x in sa.inspect(bind).get_check_constraints('alerts')}
    missing_status='ck_alert_workflow_status' not in alert_checks
    missing_severity='ck_alert_severity' not in alert_checks
    if missing_status or missing_severity:
        with op.batch_alter_table('alerts') as batch:
            if missing_status:batch.create_check_constraint('ck_alert_workflow_status',"status IN ('NEW','ACKNOWLEDGED','IN_REVIEW','MONITORING','PERSISTENT','ESCALATED','RESOLVED','DISMISSED','REOPENED')")
            if missing_severity:batch.create_check_constraint('ck_alert_severity',"severity IN ('INFO','ATTENTION','HIGH')")
    from backend.database import Base
    import backend.models
    for name in ('alert_history','officer_reviews','review_notes','review_actions'):Base.metadata.tables[name].create(bind=bind,checkfirst=True)

def downgrade():
    bind=op.get_bind();inspector=sa.inspect(bind);tables=set(inspector.get_table_names())
    for name in ('review_actions','review_notes','officer_reviews','alert_history'):
        if name in tables:op.drop_table(name)
    alert_indexes={x['name'] for x in sa.inspect(bind).get_indexes('alerts')}
    for name in ('ix_alert_mode_status_updated','ix_alerts_data_origin','uq_alert_deduplication_key'):
        if name in alert_indexes:op.drop_index(name,table_name='alerts')
    removable=('review_policy_version','decision_policy_version','watch_policy_version','consecutive_valid_cycles','last_seen_month','first_seen_month','reopened_at','resolved_at','last_updated_at','opened_at','data_trust_current','data_trust_at_open','decision_state_current','decision_state_at_open','latest_evidence_snapshot','initial_evidence_snapshot','current_reason_codes','trigger_reason_codes','reason_family','deduplication_key','data_origin','severity','alert_type')
    existing={x['name'] for x in sa.inspect(bind).get_columns('alerts')}
    checks={x['name'] for x in sa.inspect(bind).get_check_constraints('alerts')}
    with op.batch_alter_table('alerts',recreate='always') as batch:
        for name in ('ck_alert_workflow_status','ck_alert_severity'):
            if name in checks:batch.drop_constraint(name,type_='check')
        for name in removable:
            if name in existing:batch.drop_column(name)
    project_indexes={x['name'] for x in sa.inspect(bind).get_indexes('projects')}
    if 'ix_projects_data_origin' in project_indexes:op.drop_index('ix_projects_data_origin',table_name='projects')
    if 'data_origin' in {x['name'] for x in sa.inspect(bind).get_columns('projects')}:
        with op.batch_alter_table('projects',recreate='always') as batch:batch.drop_column('data_origin')
