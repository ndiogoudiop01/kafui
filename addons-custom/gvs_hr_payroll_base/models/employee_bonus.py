# -*- coding: utf-8 -*-
import calendar as _calendar
from datetime import datetime, time as t
from dateutil import relativedelta
from odoo.tools.misc import format_date
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class EmployeeBonus(models.Model):
    """Élément variable salarié lié au contrat (hr.version).

    L'utilisateur saisit les montants UNE FOIS sur le contrat, avec un type
    de durée (montant unique / limité / illimité).  À la génération du
    bulletin, _get_payslip_lines lit ces enregistrements et applique le
    montant sur la règle salariale correspondante, sans jamais écrire sur
    l'enregistrement partagé hr.salary.rule.

    Types de durée :
      • Montant unique (one_time)  : appliqué uniquement sur le mois courant
                                     (date_from et date_to auto-renseignées).
      • Limité(e) (limited)        : appliqué sur une période définie
                                     (date_from et date_to obligatoires).
      • Illimité(e) (unlimited)    : appliqué chaque mois à partir de
                                     date_from, sans date de fin.
    """
    _name = 'hr.employee.bonus'
    _description = 'Élément variable salarial'

    name = fields.Char(readonly=True, compute='_get_name', store=True)
    salary_rule = fields.Many2one(
        'hr.salary.rule', string='Rubrique salariale', required=True,
    )
    employee_id = fields.Many2one('hr.employee', string='Employé')
    amount = fields.Float(string='Montant', required=True)

    duration_type = fields.Selection([
        ('one_time', 'Montant unique'),
        ('limited', 'Limité(e)'),
        ('unlimited', 'Illimité(e)'),
    ], default='one_time', required=True, string='Durée',
        help=(
            "• Montant unique : appliqué uniquement sur le mois courant"
            " (dates auto-renseignées).\n"
            "• Limité(e) : appliqué sur une période définie (date de début"
            " et date de fin obligatoires).\n"
            "• Illimité(e) : appliqué chaque mois à partir de la date de"
            " début, sans date de fin."
        ),
    )

    date_from = fields.Date(
        string='Du',
        default=lambda self: fields.Date.today(),
        required=True,
    )
    date_to = fields.Date(
        string='Au',
        required=False,
        default=lambda self: (
            datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1)
        ).date(),
    )

    note = fields.Text(
        string='Note',
        help='Raison ou référence facultative (décision, lettre, accord…)',
    )

    state = fields.Selection(
        [('active', 'Actif'), ('expired', 'Expiré')],
        default='active',
        string='État',
        compute='_get_status',
        store=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Société',
        required=True,
        default=lambda self: self.env.company,
    )
    version_id = fields.Many2one('hr.version', string='Contrat')

    # ── Nom automatique ──────────────────────────────────────────────────────

    @api.depends('employee_id', 'date_from')
    def _get_name(self):
        for rec in self:
            if rec.employee_id:
                rec.name = 'Élément variable %s — %s' % (
                    rec.employee_id.name or '',
                    format_date(rec.env, rec.date_from, date_format='MMMM y')
                    if rec.date_from else '',
                )
                if rec.employee_id.version_id and not rec.version_id:
                    rec.version_id = rec.employee_id.version_id
            else:
                if not rec.name:
                    rec.name = False

    # ── État (actif / expiré) ────────────────────────────────────────────────

    @api.depends('date_from', 'date_to', 'duration_type')
    def _get_status(self):
        now = datetime.now()
        for rec in self:
            if rec.duration_type == 'unlimited':
                # Illimité : actif dès la date de début
                if rec.date_from:
                    rec.state = (
                        'active'
                        if datetime.combine(rec.date_from, t.min) <= now
                        else 'expired'
                    )
                else:
                    rec.state = 'active'
            elif rec.date_from and rec.date_to:
                if (datetime.combine(rec.date_from, t.min)
                        <= now
                        <= datetime.combine(rec.date_to, t.max)):
                    rec.state = 'active'
                else:
                    rec.state = 'expired'
            else:
                rec.state = 'active'

    # ── Onchange durée : pré-remplissage des dates ───────────────────────────

    @api.onchange('duration_type')
    def _onchange_duration_type(self):
        today = fields.Date.today()
        if self.duration_type == 'one_time':
            # Auto-set to first and last day of current month
            first_day = today.replace(day=1)
            last_day = today.replace(
                day=_calendar.monthrange(today.year, today.month)[1]
            )
            self.date_from = first_day
            self.date_to = last_day
        elif self.duration_type == 'unlimited':
            # Conserver date_from, effacer date_to
            self.date_to = False

    # ── Contraintes ──────────────────────────────────────────────────────────

    @api.constrains('duration_type', 'date_from', 'date_to')
    def _check_dates(self):
        for rec in self:
            if rec.duration_type == 'limited' and not rec.date_to:
                raise ValidationError(
                    _("La date de fin est obligatoire pour un élément variable"
                      " de durée limitée.")
                )
            if rec.date_from and rec.date_to and rec.date_to < rec.date_from:
                raise ValidationError(
                    _("La date de fin doit être postérieure ou égale à la"
                      " date de début.")
                )


class RelationFamille(models.Model):
    """Relations familiales de l'employé (conjoint, enfants, autres)."""
    _name = 'relation.famille'
    _description = 'Relation familiale'

    type = fields.Selection([
        ('conjoint', 'Conjoint(e)'),
        ('enfant', 'Enfant'),
        ('autre', 'Autre parent'),
    ], string='Type de relation')
    nom = fields.Char('Nom')
    prenom = fields.Char('Prénom')
    birth = fields.Date('Date de naissance')
    date_mariage = fields.Date('Date de mariage')
    salari = fields.Boolean('Salarié(e)', default=False)
    employee_id = fields.Many2one('hr.employee', string='Employé')
