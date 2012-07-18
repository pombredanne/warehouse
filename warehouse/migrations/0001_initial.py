# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Classifier'
        db.create_table('warehouse_classifier', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('trove', self.gf('django.db.models.fields.CharField')(unique=True, max_length=350)),
        ))
        db.send_create_signal('warehouse', ['Classifier'])

        # Adding model 'Project'
        db.create_table('warehouse_project', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('model_utils.fields.AutoCreatedField')(default=datetime.datetime.now)),
            ('modified', self.gf('model_utils.fields.AutoLastModifiedField')(default=datetime.datetime.now)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=150)),
            ('uris', self.gf('warehouse.fields.dbarray.TextArrayField')(blank=True)),
            ('normalized', self.gf('django.db.models.fields.CharField')(unique=True, max_length=150)),
            ('downloads', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
        ))
        db.send_create_signal('warehouse', ['Project'])

        # Adding model 'Version'
        db.create_table('warehouse_version', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(related_name='versions', to=orm['warehouse.Project'])),
            ('version', self.gf('django.db.models.fields.CharField')(max_length=512)),
            ('created', self.gf('model_utils.fields.AutoCreatedField')(default=datetime.datetime.now, db_index=True)),
            ('modified', self.gf('model_utils.fields.AutoLastModifiedField')(default=datetime.datetime.now)),
            ('order', self.gf('django.db.models.fields.IntegerField')(default=0, db_index=True)),
            ('yanked', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('metadata_version', self.gf('django.db.models.fields.CharField')(max_length=5)),
            ('summary', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('author', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('author_email', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('maintainer', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('maintainer_email', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('license', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('platforms', self.gf('warehouse.fields.dbarray.TextArrayField')(blank=True)),
            ('supported_platforms', self.gf('warehouse.fields.dbarray.TextArrayField')(blank=True)),
            ('keywords', self.gf('warehouse.fields.dbarray.TextArrayField')(blank=True)),
            ('uris', self.gf('django_hstore.fields.DictionaryField')(db_index=True, blank=True)),
            ('requires_python', self.gf('django.db.models.fields.CharField')(max_length=25, blank=True)),
            ('requires_external', self.gf('warehouse.fields.dbarray.TextArrayField')(blank=True)),
            ('downloads', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
        ))
        db.send_create_signal('warehouse', ['Version'])

        # Adding unique constraint on 'Version', fields ['project', 'version']
        db.create_unique('warehouse_version', ['project_id', 'version'])

        # Adding M2M table for field classifiers on 'Version'
        db.create_table('warehouse_version_classifiers', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('version', models.ForeignKey(orm['warehouse.version'], null=False)),
            ('classifier', models.ForeignKey(orm['warehouse.classifier'], null=False))
        ))
        db.create_unique('warehouse_version_classifiers', ['version_id', 'classifier_id'])

        # Adding model 'VersionFile'
        db.create_table('warehouse_versionfile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('version', self.gf('django.db.models.fields.related.ForeignKey')(related_name='files', to=orm['warehouse.Version'])),
            ('created', self.gf('model_utils.fields.AutoCreatedField')(default=datetime.datetime.now, db_index=True)),
            ('modified', self.gf('model_utils.fields.AutoLastModifiedField')(default=datetime.datetime.now)),
            ('yanked', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=25)),
            ('file', self.gf('django.db.models.fields.files.FileField')(max_length=512)),
            ('python_version', self.gf('django.db.models.fields.CharField')(max_length=25, blank=True)),
            ('digests', self.gf('django_hstore.fields.DictionaryField')(db_index=True)),
            ('comment', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('filename', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('filesize', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('downloads', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
        ))
        db.send_create_signal('warehouse', ['VersionFile'])

        # Adding model 'Require'
        db.create_table('warehouse_require', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=150)),
            ('version', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('environment', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('project_version', self.gf('django.db.models.fields.related.ForeignKey')(related_name='requires', to=orm['warehouse.Version'])),
        ))
        db.send_create_signal('warehouse', ['Require'])

        # Adding unique constraint on 'Require', fields ['project_version', 'name']
        db.create_unique('warehouse_require', ['project_version_id', 'name'])

        # Adding model 'Provide'
        db.create_table('warehouse_provide', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=150)),
            ('version', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('environment', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('project_version', self.gf('django.db.models.fields.related.ForeignKey')(related_name='provides', to=orm['warehouse.Version'])),
        ))
        db.send_create_signal('warehouse', ['Provide'])

        # Adding unique constraint on 'Provide', fields ['project_version', 'name']
        db.create_unique('warehouse_provide', ['project_version_id', 'name'])

        # Adding model 'Obsolete'
        db.create_table('warehouse_obsolete', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=150)),
            ('version', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('environment', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('project_version', self.gf('django.db.models.fields.related.ForeignKey')(related_name='obsoletes', to=orm['warehouse.Version'])),
        ))
        db.send_create_signal('warehouse', ['Obsolete'])

        # Adding unique constraint on 'Obsolete', fields ['project_version', 'name']
        db.create_unique('warehouse_obsolete', ['project_version_id', 'name'])


    def backwards(self, orm):
        # Removing unique constraint on 'Obsolete', fields ['project_version', 'name']
        db.delete_unique('warehouse_obsolete', ['project_version_id', 'name'])

        # Removing unique constraint on 'Provide', fields ['project_version', 'name']
        db.delete_unique('warehouse_provide', ['project_version_id', 'name'])

        # Removing unique constraint on 'Require', fields ['project_version', 'name']
        db.delete_unique('warehouse_require', ['project_version_id', 'name'])

        # Removing unique constraint on 'Version', fields ['project', 'version']
        db.delete_unique('warehouse_version', ['project_id', 'version'])

        # Deleting model 'Classifier'
        db.delete_table('warehouse_classifier')

        # Deleting model 'Project'
        db.delete_table('warehouse_project')

        # Deleting model 'Version'
        db.delete_table('warehouse_version')

        # Removing M2M table for field classifiers on 'Version'
        db.delete_table('warehouse_version_classifiers')

        # Deleting model 'VersionFile'
        db.delete_table('warehouse_versionfile')

        # Deleting model 'Require'
        db.delete_table('warehouse_require')

        # Deleting model 'Provide'
        db.delete_table('warehouse_provide')

        # Deleting model 'Obsolete'
        db.delete_table('warehouse_obsolete')


    models = {
        'warehouse.classifier': {
            'Meta': {'object_name': 'Classifier'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'trove': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '350'})
        },
        'warehouse.obsolete': {
            'Meta': {'unique_together': "(('project_version', 'name'),)", 'object_name': 'Obsolete'},
            'environment': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'project_version': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'obsoletes'", 'to': "orm['warehouse.Version']"}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'})
        },
        'warehouse.project': {
            'Meta': {'object_name': 'Project'},
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'downloads': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '150'}),
            'normalized': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '150'}),
            'uris': ('warehouse.fields.dbarray.TextArrayField', [], {'blank': 'True'})
        },
        'warehouse.provide': {
            'Meta': {'unique_together': "(('project_version', 'name'),)", 'object_name': 'Provide'},
            'environment': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'project_version': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'provides'", 'to': "orm['warehouse.Version']"}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'})
        },
        'warehouse.require': {
            'Meta': {'unique_together': "(('project_version', 'name'),)", 'object_name': 'Require'},
            'environment': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'project_version': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'requires'", 'to': "orm['warehouse.Version']"}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'})
        },
        'warehouse.version': {
            'Meta': {'unique_together': "(('project', 'version'),)", 'object_name': 'Version'},
            'author': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'author_email': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'classifiers': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'releases'", 'blank': 'True', 'to': "orm['warehouse.Classifier']"}),
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now', 'db_index': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'downloads': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'keywords': ('warehouse.fields.dbarray.TextArrayField', [], {'blank': 'True'}),
            'license': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'maintainer': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'maintainer_email': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'metadata_version': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'platforms': ('warehouse.fields.dbarray.TextArrayField', [], {'blank': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'versions'", 'to': "orm['warehouse.Project']"}),
            'requires_external': ('warehouse.fields.dbarray.TextArrayField', [], {'blank': 'True'}),
            'requires_python': ('django.db.models.fields.CharField', [], {'max_length': '25', 'blank': 'True'}),
            'summary': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'supported_platforms': ('warehouse.fields.dbarray.TextArrayField', [], {'blank': 'True'}),
            'uris': ('django_hstore.fields.DictionaryField', [], {'default': '{}', 'db_index': 'True', 'blank': 'True'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'yanked': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'warehouse.versionfile': {
            'Meta': {'object_name': 'VersionFile'},
            'comment': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now', 'db_index': 'True'}),
            'digests': ('django_hstore.fields.DictionaryField', [], {'default': '{}', 'db_index': 'True'}),
            'downloads': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '512'}),
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'filesize': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'python_version': ('django.db.models.fields.CharField', [], {'max_length': '25', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
            'version': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'files'", 'to': "orm['warehouse.Version']"}),
            'yanked': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        }
    }

    complete_apps = ['warehouse']
