# -*- coding: utf-8 -*-
"""
Migration 19.0.2.1.0 — Réassociation des données TG à la société Togo.

Problème : lors de l'installation du module gvs_hr_payroll_tg, si la société
active était YourCompany (pays=US), le post_init_hook assignait company_id=1
(YourCompany, pays=US) à toutes les règles salariales, catégories et structures.

Conséquence : l'ir.rule filtrant par pays (country_id=Togo) cachait ces
enregistrements aux utilisateurs de la société Togo → bulletin vide.

Fix : cette migration trouve la première société Togo (pays=TG) et réassigne
tous les enregistrements TG du module à cette société.

Exécution : automatique sur `odoo-bin -u gvs_hr_payroll_tg` quand la version
en base est inférieure à 19.0.2.1.0.
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Réassigne les données TG à la société Togo."""

    # ── Trouver la société Togo (pays = Togo) ────────────────────────────────
    cr.execute("""
        SELECT rc.id, p.name
        FROM res_company rc
        JOIN res_partner p ON p.id = rc.partner_id
        JOIN res_country co ON co.id = p.country_id
        WHERE co.code = 'TG'
        ORDER BY rc.id
        LIMIT 1
    """)
    row = cr.fetchone()

    if not row:
        _logger.warning(
            "Migration gvs_hr_payroll_tg 19.0.2.1.0 : aucune société Togo (code=TG) "
            "trouvée. Réassociation ignorée."
        )
        return

    togo_company_id, togo_company_name = row
    _logger.info(
        "Migration gvs_hr_payroll_tg 19.0.2.1.0 : réassociation à %s (id=%s)",
        togo_company_name, togo_company_id
    )

    # ── Récupérer les IDs des enregistrements du module gvs_hr_payroll_tg ───
    cr.execute("""
        SELECT model, array_agg(res_id) as ids
        FROM ir_model_data
        WHERE module = 'gvs_hr_payroll_tg'
          AND model IN ('hr.salary.rule', 'hr.salary.rule.category',
                        'hr.payroll.structure')
        GROUP BY model
    """)
    records_by_model = {row[0]: row[1] for row in cr.fetchall()}

    # ── Règles salariales ────────────────────────────────────────────────────
    rule_ids = records_by_model.get('hr.salary.rule', [])
    if rule_ids:
        cr.execute(
            "UPDATE hr_salary_rule SET company_id = %s WHERE id = ANY(%s)",
            (togo_company_id, rule_ids)
        )
        _logger.info("  %d règles salariales réassignées", cr.rowcount)

    # ── Catégories de règles ─────────────────────────────────────────────────
    cat_ids = records_by_model.get('hr.salary.rule.category', [])
    if cat_ids:
        cr.execute(
            "UPDATE hr_salary_rule_category SET company_id = %s WHERE id = ANY(%s)",
            (togo_company_id, cat_ids)
        )
        _logger.info("  %d catégories réassignées", cr.rowcount)

    # ── Structures de paie ───────────────────────────────────────────────────
    struct_ids = records_by_model.get('hr.payroll.structure', [])
    if struct_ids:
        cr.execute(
            "UPDATE hr_payroll_structure SET company_id = %s WHERE id = ANY(%s)",
            (togo_company_id, struct_ids)
        )
        _logger.info("  %d structures réassignées", cr.rowcount)

    # ── Invalider le cache ORM pour que country_id soit recalculé ───────────
    # Le champ country_id est stocké (store=True) et calculé depuis company_id.
    # Odoo recalculera automatiquement lors du prochain accès ou via le
    # mécanisme de recomputation des champs stockés.
    cr.execute("""
        UPDATE hr_salary_rule
        SET country_id = (
            SELECT p.country_id
            FROM res_company rc
            JOIN res_partner p ON p.id = rc.partner_id
            WHERE rc.id = %s
        )
        WHERE id = ANY(%s)
    """, (togo_company_id, rule_ids or []))

    cr.execute("""
        UPDATE hr_salary_rule_category
        SET country_id = (
            SELECT p.country_id
            FROM res_company rc
            JOIN res_partner p ON p.id = rc.partner_id
            WHERE rc.id = %s
        )
        WHERE id = ANY(%s) AND company_id IS NOT NULL
    """, (togo_company_id, cat_ids or []))

    cr.execute("""
        UPDATE hr_payroll_structure
        SET country_id = (
            SELECT p.country_id
            FROM res_company rc
            JOIN res_partner p ON p.id = rc.partner_id
            WHERE rc.id = %s
        )
        WHERE id = ANY(%s)
    """, (togo_company_id, struct_ids or []))

    _logger.info(
        "Migration gvs_hr_payroll_tg 19.0.2.1.0 : terminée — "
        "country_id recalculé pour toutes les données TG."
    )
