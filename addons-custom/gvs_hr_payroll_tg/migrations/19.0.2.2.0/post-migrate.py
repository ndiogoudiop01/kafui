# -*- coding: utf-8 -*-
"""
Migration 19.0.2.2.0 — Nettoyage structures + globalisation règles/catégories Togo.

Changements :
  1. Suppression des structures TG_CADRE et TG_NON_CADRE (structure unique TG_MENS).
  2. company_id = NULL sur les règles salariales et catégories Togo (globales).
     !! hr.payroll.structure.company_id est required=True → ne JAMAIS passer à NULL.
     TG_MENS est réassignée à la première société Togo trouvée.
  3. Suppression de la règle TECH_KM (IND_KM devient imposable, ALW, seq 35).
"""
import logging

_logger = logging.getLogger(__name__)

# Relation M2M règles ↔ structures (nom réel de la table intermédiaire)
_RULE_STRUCT_REL = 'hr_payroll_structure_hr_salary_rule_rel'


def _get_togo_company_id(cr):
    """Retourne l'id de la première société Togo (code pays TG), ou None."""
    cr.execute("""
        SELECT rc.id
        FROM res_company rc
        JOIN res_partner p  ON p.id  = rc.partner_id
        JOIN res_country co ON co.id = p.country_id
        WHERE co.code = 'TG'
        ORDER BY rc.id
        LIMIT 1
    """)
    row = cr.fetchone()
    return row[0] if row else None


def _get_module_ids(cr, model):
    """Retourne les res_id du module gvs_hr_payroll_tg pour le modèle donné."""
    cr.execute("""
        SELECT array_agg(res_id)
        FROM ir_model_data
        WHERE module = 'gvs_hr_payroll_tg' AND model = %s
    """, (model,))
    row = cr.fetchone()
    return row[0] or [] if row else []


def migrate(cr, version):
    if not version:
        return

    # ── Étape 1 : supprimer TG_CADRE et TG_NON_CADRE ────────────────────────
    # On supprime d'abord pour éviter toute tentative de mettre leur company_id
    # à NULL (hr_payroll_structure.company_id est NOT NULL dans certains envs).
    for xml_name in ('struct_tg_cadre', 'struct_tg_non_cadre'):
        cr.execute("""
            SELECT res_id FROM ir_model_data
            WHERE module = 'gvs_hr_payroll_tg' AND name = %s
              AND model = 'hr.payroll.structure'
        """, (xml_name,))
        row = cr.fetchone()
        if not row:
            _logger.info('Structure %s : déjà absente', xml_name)
            continue
        struct_id = row[0]
        # Détacher toutes les règles de cette structure
        cr.execute(
            f"DELETE FROM {_RULE_STRUCT_REL} WHERE struct_id = %s",
            (struct_id,)
        )
        # Supprimer la structure
        cr.execute("DELETE FROM hr_payroll_structure WHERE id = %s", (struct_id,))
        # Nettoyer ir.model.data
        cr.execute(
            "DELETE FROM ir_model_data"
            " WHERE module = 'gvs_hr_payroll_tg' AND name = %s",
            (xml_name,)
        )
        _logger.info('Structure supprimée : gvs_hr_payroll_tg.%s', xml_name)

    # ── Étape 2 : globaliser règles et catégories (company_id = NULL) ────────
    rule_ids = _get_module_ids(cr, 'hr.salary.rule')
    if rule_ids:
        cr.execute(
            "UPDATE hr_salary_rule SET company_id = NULL WHERE id = ANY(%s)",
            (rule_ids,)
        )
        _logger.info('Règles TG → globales (%d)', cr.rowcount)

    cat_ids = _get_module_ids(cr, 'hr.salary.rule.category')
    if cat_ids:
        cr.execute(
            "UPDATE hr_salary_rule_category SET company_id = NULL WHERE id = ANY(%s)",
            (cat_ids,)
        )
        _logger.info('Catégories TG → globales (%d)', cr.rowcount)

    # ── Étape 3 : TG_MENS → société Togo (company_id required, pas NULL) ─────
    tg_company_id = _get_togo_company_id(cr)
    if tg_company_id:
        cr.execute("""
            UPDATE hr_payroll_structure
            SET company_id = %s
            WHERE id IN (
                SELECT res_id FROM ir_model_data
                WHERE module = 'gvs_hr_payroll_tg' AND name = 'struct_tg_bulletin_mensuel'
                  AND model = 'hr.payroll.structure'
            )
        """, (tg_company_id,))
        _logger.info('TG_MENS → société Togo id=%s (%d)', tg_company_id, cr.rowcount)
    else:
        _logger.warning(
            'Aucune société Togo (code=TG) trouvée — TG_MENS conserve sa société actuelle'
        )

    # ── Étape 4 : supprimer TECH_KM ──────────────────────────────────────────
    cr.execute("""
        SELECT res_id FROM ir_model_data
        WHERE module = 'gvs_hr_payroll_tg' AND name = 'rule_tg_tech_km'
          AND model = 'hr.salary.rule'
    """)
    row = cr.fetchone()
    if row:
        tech_km_id = row[0]
        cr.execute(
            f"DELETE FROM {_RULE_STRUCT_REL} WHERE rule_id = %s",
            (tech_km_id,)
        )
        cr.execute("DELETE FROM hr_salary_rule WHERE id = %s", (tech_km_id,))
        cr.execute(
            "DELETE FROM ir_model_data"
            " WHERE module = 'gvs_hr_payroll_tg' AND name = 'rule_tg_tech_km'"
        )
        _logger.info('Règle TECH_KM supprimée')
    else:
        _logger.info('Règle TECH_KM : déjà absente')

    _logger.info('Migration gvs_hr_payroll_tg 19.0.2.2.0 : terminée')
