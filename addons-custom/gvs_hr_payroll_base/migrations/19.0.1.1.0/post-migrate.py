# -*- coding: utf-8 -*-
"""
Migration 19.0.1.1.0 — Initialisation de duration_type sur hr.employee.bonus

Nouveau champ duration_type (Sélection : one_time / limited / unlimited).
Les enregistrements existants ont tous date_to renseigné (ancien required=True),
donc on les migre vers 'limited'.  Les éventuels enregistrements sans date_to
(ne devraient pas exister) sont migrés vers 'unlimited'.
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Initialiser duration_type sur les bonus existants."""
    if not version:
        return

    # Enregistrements avec date_to → limité
    cr.execute("""
        UPDATE hr_employee_bonus
           SET duration_type = 'limited'
         WHERE duration_type IS NULL
           AND date_to IS NOT NULL
    """)
    _logger.info(
        'hr.employee.bonus: %d enregistrement(s) migrés → limited',
        cr.rowcount,
    )

    # Enregistrements sans date_to (cas théorique) → illimité
    cr.execute("""
        UPDATE hr_employee_bonus
           SET duration_type = 'unlimited'
         WHERE duration_type IS NULL
           AND date_to IS NULL
    """)
    _logger.info(
        'hr.employee.bonus: %d enregistrement(s) migrés → unlimited',
        cr.rowcount,
    )
