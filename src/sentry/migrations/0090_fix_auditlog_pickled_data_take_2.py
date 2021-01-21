# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2020-07-15 21:50
from __future__ import unicode_literals

from django.db import migrations

from sentry.utils.query import RangeQuerySetWrapperWithProgressBar


def cleanup_audit_log_data(apps, schema_editor):
    """
    Fix `AuditLogEntry` rows that have pickled `Team` models in their `data` field.

    We originally had fixed this in [0], but we missed some types. This is
    basically the same migration, but without the audit log entry type gaurd.

    [0]: https://github.com/getsentry/sentry/pull/17545
    """
    AuditLogEntry = apps.get_model("sentry", "AuditLogEntry")
    for audit_log in RangeQuerySetWrapperWithProgressBar(AuditLogEntry.objects.all()):
        teams = audit_log.data.get("teams")
        if teams and hasattr(teams[0], "id"):
            # We have a team in here rather than just the expected data
            audit_log.data["teams"] = [team.id for team in teams]
            audit_log.data["teams_slugs"] = [team.slug for team in teams]
            audit_log.save()


class Migration(migrations.Migration):
    # This flag is used to mark that a migration shouldn't be automatically run in
    # production. We set this to True for operations that we think are risky and want
    # someone from ops to run manually and monitor.
    # General advice is that if in doubt, mark your migration as `is_dangerous`.
    # Some things you should always mark as dangerous:
    # - Large data migrations. Typically we want these to be run manually by ops so that
    #   they can be monitored. Since data migrations will now hold a transaction open
    #   this is even more important.
    # - Adding columns to highly active tables, even ones that are NULL.
    is_dangerous = True

    # This flag is used to decide whether to run this migration in a transaction or not.
    # By default we prefer to run in a transaction, but for migrations where you want
    # to `CREATE INDEX CONCURRENTLY` this needs to be set to False. Typically you'll
    # want to create an index concurrently when adding one to an existing table.
    atomic = False

    dependencies = [("sentry", "0089_rule_level_fields_backfill")]

    operations = [
        migrations.RunPython(code=cleanup_audit_log_data, reverse_code=migrations.RunPython.noop)
    ]
