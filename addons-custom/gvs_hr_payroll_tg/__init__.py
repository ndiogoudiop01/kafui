# -*- coding: utf-8 -*-
from . import models


def post_init_hook(env):
    """Initialise les données Togo après installation.

    Règles salariales et catégories → globales (company_id = False) :
    visibles par toutes les sociétés, filtrées par structure sur le contrat.

    Structure TG_MENS → société Togo si trouvée, sinon société courante :
    hr.payroll.structure.company_id est required=True, ne peut pas être False.

    Les bulletins, employés et contrats restent liés à leur société.
    """
    # ── Règles salariales → globales ─────────────────────────────────────────
    rule_data = env['ir.model.data'].search([
        ('module', '=', 'gvs_hr_payroll_tg'),
        ('model', '=', 'hr.salary.rule'),
    ])
    if rule_data:
        env['hr.salary.rule'].browse(
            [d.res_id for d in rule_data]
        ).write({'company_id': False})

    # ── Catégories → globales ─────────────────────────────────────────────────
    cat_data = env['ir.model.data'].search([
        ('module', '=', 'gvs_hr_payroll_tg'),
        ('model', '=', 'hr.salary.rule.category'),
    ])
    if cat_data:
        env['hr.salary.rule.category'].browse(
            [d.res_id for d in cat_data]
        ).write({'company_id': False})

    # ── Structure TG_MENS → société Togo (company_id required, jamais False) ──
    # hr.payroll.structure.company_id est required=True dans Odoo : on ne peut
    # pas mettre False. On cherche la première société Togo, sinon société courante.
    tg_country = env['res.country'].search([('code', '=', 'TG')], limit=1)
    tg_company = (
        env['res.company'].search(
            [('partner_id.country_id', '=', tg_country.id)], limit=1
        ) if tg_country else env['res.company']
    )
    target_company = tg_company or env.company
    struct = env.ref(
        'gvs_hr_payroll_tg.struct_tg_bulletin_mensuel', raise_if_not_found=False
    )
    if struct:
        struct.write({'company_id': target_company.id})
