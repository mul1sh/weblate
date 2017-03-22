# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-03-22 10:12
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trans', '0077_auto_20170317_1514'),
    ]

    operations = [
        migrations.AlterField(
            model_name='check',
            name='check',
            field=models.CharField(choices=[('end_space', 'Trailing space'), (b'inconsistent', 'Inconsistent'), ('begin_newline', 'Starting newline'), ('max-length', 'Maximum length of translation'), ('zero-width-space', 'Zero-width space'), ('escaped_newline', 'Mismatched \\n'), ('same', 'Unchanged translation'), ('end_question', 'Trailing question'), (b'angularjs_format', 'AngularJS interpolation string'), (b'python_brace_format', 'Python brace format'), ('end_newline', 'Trailing newline'), (b'c_format', 'C format'), ('end_exclamation', 'Trailing exclamation'), ('end_ellipsis', 'Trailing ellipsis'), ('end_colon', 'Trailing colon'), ('xml-tags', 'XML tags mismatch'), (b'python_format', 'Python format'), (b'plurals', 'Missing plurals'), (b'javascript_format', 'Javascript format'), ('begin_space', 'Starting spaces'), ('bbcode', 'Mismatched BBcode'), (b'php_format', 'PHP format'), ('xml-invalid', 'Invalid XML markup'), (b'same-plurals', 'Same plurals'), (b'translated', 'Has been translated'), ('end_stop', 'Trailing stop')], max_length=50),
        ),
    ]
