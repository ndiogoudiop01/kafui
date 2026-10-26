# -*- coding: utf-8 -*-
# relation_ids et relation.famille sont maintenant dans gvs_hr_payroll_base.
# Ce fichier conserve les champs et calculs spécifiques au Sénégal.

from datetime import datetime
from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # ── Visibilité onglet Famille Sénégal ────────────────────────────────────
    is_sn_payroll = fields.Boolean(
        compute='_compute_is_sn_payroll',
        help="Vrai si la société de l'employé est configurée au Sénégal (code pays 'SN').",
    )

    def _compute_is_sn_payroll(self):
        for emp in self:
            emp.is_sn_payroll = (emp.company_id.country_id.code == 'SN')

    # Champs spécifiques Sénégal
    matricule_cnss = fields.Char('Matricule CNSS')
    ipres = fields.Char('Numéro IPRES')
    mutuelle = fields.Char('Numéro mutuelle')
    compte = fields.Char('Compte contribuable')
    num_chezemployeur = fields.Char("Numéro chez l'employeur")

    # Calcul IR / TRIMF (spécifique Sénégal)
    ir = fields.Float(
        'Nombre de parts IR',
        compute="get_ir_trimf",
        store=True,
        default=1,
    )
    trimf = fields.Float(
        'Nombre de parts TRIMF',
        compute="get_ir_trimf",
        store=True,
        default=1,
    )
    ir_changed = fields.Integer(default=0)
    worked_days_per_years = fields.One2many(
        'employee.worked.days', 'employee_id', 'Jours travaillés'
    )

    def process_scheduler_check_employee_child_grown(self):
        for empl_obj in self.env['hr.employee'].search([]):
            empl_obj.get_ir_trimf()

    @api.depends('relation_ids')
    def get_ir_trimf(self):
        for value in self:
            value.ir = 1
            value.trimf = 1
            nbj_sup = 0
            status = 'single'
            conjoint = False
            for line in value.relation_ids:
                if line.type == 'enfant' and line.birth:
                    now = datetime.now()
                    dur = now - datetime.combine(line.birth, datetime.min.time())
                    if dur.days < 7670:
                        value.ir += 0.5
                    if dur.days <= 5114:
                        nbj_sup += 1

                if line.type == 'conjoint':
                    if not conjoint:
                        if line.salari == 0:
                            value.ir += 1
                            value.trimf += 1
                        else:
                            value.ir += 0.5
                        conjoint = True
                    status = 'married'

            value.marital = status

            version = value.version_id
            if version and hasattr(version, 'nbj_sup'):
                old_nbj_sup = version.nbj_sup
                if nbj_sup > old_nbj_sup:
                    version.write({'nbj_sup': nbj_sup})

            if value.ir >= 5:
                value.ir = 5
            if value.trimf >= 5:
                value.trimf = 5


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    matricule_cnss = fields.Char(readonly=True)
    ipres = fields.Char(readonly=True)
    mutuelle = fields.Char(readonly=True)
    compte = fields.Char(readonly=True)
    num_chezemployeur = fields.Char(readonly=True)
    ir = fields.Float(readonly=True)
    trimf = fields.Float(readonly=True)
    ir_changed = fields.Integer(readonly=True)
    worked_days_per_years = fields.One2many(
        'employee.worked.days', 'employee_id', readonly=True
    )


class EmployeeWorkDays(models.Model):
    _name = 'employee.worked.days'
    _description = "Historique des jours travaillés par année"

    year = fields.Char('Année')
    worked_days = fields.Integer('Jours travaillés')
    employee_id = fields.Many2one('hr.employee')
