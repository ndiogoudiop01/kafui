# -*- coding: utf-8 -*-

import calendar
import logging

# from . import get_date_interval, get_years_from
from dateutil.relativedelta import relativedelta
from datetime import date, datetime, timedelta
from odoo import api, fields, models

_logger = logging.getLogger(__name__)

def seq( start, stop, step = 1 ):
    """Return a list of float
    return eg : [2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0]
    with start=2 ; end=10; step =0.5
    """
    n = int( round( ( stop - start ) / float( step ) ) )
    if n > 1:
        return( [start + step * i for i in range( n + 1 )] ) 
    else:
        return( [] )
		
		
class CNSS(models.Model):
    _name = 'hr.cnss'
    _description = 'CNSS'
    _order = "company_id, year"
	
	
    def _get_year(self):
	
        START_YEAR = 2010
        STOP_YEAR = 2030
        STEP_YEAR = 1


        seq_year = seq(START_YEAR, STOP_YEAR, STEP_YEAR )
        seq_year = [str( i ) for i in seq_year]
        seq_year.reverse()
        year_selection = zip( seq_year, seq_year )
        return tuple( year_selection )


    _REGIME = [
        ('MENS', 'Mensuel'),
       ]		



    _MONTH = [
        ('01', 'Janvier'),
        ('02', 'Février'),
        ('03', 'Mars'),
        ('04', 'Avril'),
        ('05', 'Mai'),
        ('06', 'Juin'),
        ('07', 'Juillet'),
        ('08', 'Août'),
        ('09', 'Septembre'),
        ('10', 'Octobre'),
        ('11', 'Novembre'),
        ('12', 'Décembre')]


    _TRIMESTRE = [
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4')]
		

    def _get_default_quarter(self):
        date=datetime.now()
        return str((date.month - 1) // 3 + 1)	


    def _get_default_month(self):
        date = fields.Date.from_string(fields.Date.today())
        return date.strftime('%m')
		
    def _get_default_year(self):
        date = fields.Date.from_string(fields.Date.today())
        return date.strftime('%Y')
		
    @api.depends('regime','trimestre','date_from','year','month')    
    def _get_default_start_date(self):
        for s in self: 
            trim = int(s.trimestre)
            year = int(s.year)
            mois = int(s.month)		
            if s.regime =='TRIM':		
                s.date_from= date(year, 3*(trim)-2 , 1)
            elif s.regime =='MENS':	
                s.date_from= date(year, mois , 1)		
            elif s.regime =='YEAR':	
                s.date_from= date(year, 1, 1)
 
    @api.depends('regime','trimestre','date_to','year','month')		
    def _get_default_end_date(self):
        for s in self: 
            trim = int(s.trimestre)
            year = int(s.year)
            mois = int(s.month)
            value1 =  int(mois/12)	 
            value2 =  mois%12+1	
            if s.regime =='TRIM':		
                s.date_to = date(year, 1+3*(trim-1) , 1)+ relativedelta(months=3, days=-1)	
            elif s.regime =='MENS':		
                s.date_to = date(year+value1,value2,1)- timedelta(days=1)
            elif s.regime =='YEAR':		
                s.date_to = date(year, 12,31)



    @api.depends('month','year')		
    def _get_default_paie_date(self):
        for p in self:	
            year = int(p.year)
            mois = int(p.month)		
            value1 =  int(mois/12)	 
            value2 =  mois%12+1		
            p.paiem_date = date(year+value1,value2,1)+ timedelta(days=15) 	
	

    date_from = fields.Date(string='Date de début ', required=True, compute='_get_default_start_date')
    date_to = fields.Date(string='Date de fin  ',required=True, compute='_get_default_end_date')
    name = fields.Char(string='Déclaration N°', size=64, readonly=True, required=True, default=lambda *a: '...')
    company_id = fields.Many2one('res.company', 'Société', required=True, default=lambda self: self.env.user.company_id)
    year = fields.Selection(_get_year, 'Année', required=True, default=_get_default_year)
    month = fields.Selection(_MONTH, 'Mois', required=True, default=_get_default_month)	
    trimestre = fields.Selection(_TRIMESTRE, 'Trimestre', index=True, required=True,default=_get_default_quarter)
    date_document = fields.Date('Date du document', default=lambda *a: date.today())
    paiem_date = fields.Date(string='Date de paiement', compute='_get_default_paie_date')
    regime     = fields.Selection(_REGIME, 'Régime ',   index=True, required=True, default='MENS')	
	
    payment_mode = fields.Selection([
        ('Espèce', 'Espèce'),
        ('Chèque', 'Chèque'),
        ('Mandat', 'Mandat'),], 'Mode de paiement', default='Espèce', required=True)
    cheque_number = fields.Char('N° Chèque ou Mandat ', size=40)	
    bank_transfer = fields.Char('Virement Bancaire N°', size=40)
    bank = fields.Char('Banque', size=40)
    voucher_number_1 = fields.Char('Numéro récipissé déclaration', size=40)
    voucher_number_2 = fields.Char('Numéro reçu de paiement', size=40)
    voucher_number_date = fields.Date('du')	
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('waiting', 'A payer'),
        ('done', 'Payée'), ], 'État', index=True, default='draft', readonly=True, copy=False)
    cnss_lines = fields.One2many('hr.cnss.line', 'cnss_id', 'cnss')
	
    total_cnss = fields.Float(compute='_get_total_cnss',string="Total Cotisations à payer", digits=(8, 2))
    # total_cnss_worker = fields.Float(compute='_get_total_cnss_sal',string="CNSS EMPLOYE", digits=(8, 2))

    brut_total = fields.Float( string="Masse salariale", compute='_get_total_brut')
    brut_total_catA = fields.Float( string="Masse salariale sup à 63000", compute='_get_total_brut_catA')	
    brut_total_catB = fields.Float( string="Masse salariale inf à 63000", compute='_get_total_brut_catB')	
    brut_total_catC = fields.Float( string="Masse salariale horaire", compute='_get_total_brut_catC')		
    cnss_total_PF = fields.Float( string="Total PF CSS", compute='_get_total_pf')
    cnss_total_AT = fields.Float( string="Total AT  CSS", compute='_get_total_at')	
	
    majoration = fields.Float(string="Majoration de retard ", digits=(8, 2))
    solde_previous = fields.Float(string="Solde période antérieure non payé", digits=(8, 2))
    vers_mois1 = fields.Float(string="Cotisation versé au mois 1 du trimestre", digits=(8, 2))
    vers_mois2 = fields.Float(string="Cotisation versé au mois 2 du trimestre", digits=(8, 2))	
    a_deduire = fields.Float(string="Trop perçu antérieure à déduire", digits=(8, 2))
    # net_total = fields.Float(compute='_get_total_net', string="Net à payer à la css", digits=(8, 2))	
    nemploye = fields.Integer("Nbre employee +63000",compute='_compute_employee_count')	
    nemploye2 = fields.Integer("Nbre employee - 63000",compute='_compute_employee_count2')
    nemploye3 = fields.Integer("Nbre employee - Horaire",compute='_compute_employee_count3')
    nemployes = fields.Integer("Nbre employee - Total",compute='_compute_employee_total')	
    totheures = fields.Integer("Nbre d'heures - Total",compute='_get_total_heures')	
	
    # _sql_constraints = [
        # ('name_company_uniq', 'unique(name, company_id)', 'Ce document existe déjà!'),]

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('cnss')or '/...'
        decla = super(CNSS, self).create(vals)
        return decla
		
    @api.depends('cnss_lines')
    def _compute_employee_total(self):
        for p in self:
            for line in p.cnss_lines:		
                p.nemployes = len(line.cnss_id)
		
    @api.depends('cnss_lines')
    def _compute_employee_count(self):
        for p in self:
            p.nemploye = 0		
            for line in p.cnss_lines:
                p.nemploye += line.nemploye
				

    @api.depends('cnss_lines')
    def _compute_employee_count2(self):
        for p in self:
            p.nemploye2 = 0		
            for line in p.cnss_lines:
                p.nemploye2 += line.nemploye2

    @api.depends('cnss_lines')
    def _compute_employee_count3(self):
        for p in self:
            p.nemploye3 = 0			
            for line in p.cnss_lines:
                p.nemploye3 += line.nemploye3
					
    @api.depends('cnss_lines')           
    def _get_total_brut(self):       
        for p in self: 
            p.brut_total = 0
            for line in p.cnss_lines:			
                p.brut_total += (line.month_1)


    @api.depends('cnss_lines')   		
    def _get_total_heures(self):       
        for p in self: 
            p.totheures = 0				
            for line in p.cnss_lines:
                if line.employee_id.contract_id.schedule_pay == 'hourly':
                    p.totheures += (line.tt1)
	
		
		

    def _get_total_brut_catB(self):
        for p in self:
            p.brut_total_catB = 0		
            for line in p.cnss_lines:		
                if line.month_1 <= p.company_id.plafond1:
                    p.brut_total_catB += (line.month_1)	





    def _get_total_brut_catC(self):
        for p in self:
            p.brut_total_catC		
            for line in p.cnss_lines:		
                if line.employee_id.contract_id.schedule_pay == 'hourly':
                    p.brut_total_catC += (line.month_1)	

					

    def _get_total_brut_catA(self):
        for p in self:
            p.brut_total_catA = 0		
            for line in p.cnss_lines:		
                if line.month_1 > p.company_id.plafond1:
                    p.brut_total_catA += (line.month_1)	




    def _get_total_pf(self):       
        for p in self: 
            p.cnss_total_PF = 0
            for line in p.cnss_lines:			
                p.cnss_total_PF += line.cnss_PF



    def _get_total_at(self):       
        for p in self: 
            p.cnss_total_AT
            for line in p.cnss_lines:			
                p.cnss_total_AT += line.cnss_AT
 

    def _get_total_cnss(self):       
        for p in self: 
            p.total_cnss = p.cnss_total_PF + p.cnss_total_AT		





    @api.onchange('month')
    def onchange_trismestre(self):
        line_obj = self.env['hr.cnss.line']
        lines_ids = line_obj.search([('cnss_id', 'in', self.id)])
        lines_ids.unlink()
		
    def cnss_confirm(self):
        return self.write({'state': 'waiting'})

    def cnss_payed(self):
        return self.write({'state': 'done'})
	
		
    def print_report(self):
        return self.env.ref('hr_payroll_seng.action_report_etat_cnss').report_action(self)

    def print_mensuelle_tab(self):
        return self.env.ref('hr_payroll_seng.action_report_tab').report_action(self)



    def cnss_generate(self):
        f_line_obj = self.env['hr.cnss.line']
        slip_obj = self.env['hr.payslip']
        slip_line_obj = self.env['hr.payslip.line']
        cnss_lines = []
        for o in self:
            old_f_lines = f_line_obj.search([('cnss_id', '=', o.id)])
            if old_f_lines:
                old_f_lines.unlink()
            date_from= o.date_from
            date_to= o.date_to	
            month = o.month if len(str(o.month)) == 1 else '0' + str(o.month)
			
            employee_ids = self.env['hr.employee'].search([['contract_id.state', 'in',['done', 'open']]]).mapped('id')

			
            slip_ids = slip_obj.search([
                ('date_from', '>=', date_from),
                ('date_to', '<=', date_to),
                ('employee_id', 'in', employee_ids),
                ])
				
				
            employee_ids = []
			
            for slip in slip_ids:
                if slip.employee_id.id not in employee_ids:
                    employee_ids.append(slip.employee_id.id)
            # for each 
			
            for e in employee_ids:
                tt1 = 0
           
                cnss_AT = 0
                cnss_PF = 0
                cnss_IPRESC = 0
                cnss_IPRERG = 0				
                date_from_temp = datetime.strptime(str(date_from), "%Y-%m-%d").date()
                month_t = date_from_temp.month
                date_to = date_from_temp.replace(day=calendar.monthrange(date_from_temp.year, date_from_temp.month)[1])
                slip_id = slip_obj.search([
                    ('id', 'in', slip_ids.mapped('id')),
                    ('employee_id', '=', e),
                    ('date_from', '>=', date_from_temp),
                    ('date_to', '<=', date_to)]).mapped('id')
                domain_slip_id = ('slip_id', 'in', slip_id)
                brute = slip_line_obj.search([domain_slip_id, ('code', '=', 'BRUT')], limit=1)
                month_1 = brute.total or 0.0
                if month_1 :
                    tt = slip_line_obj.search([domain_slip_id, ('code', '=', 'WHOURS')], limit=1)
                    tt1 = tt.total or 0.0

                    temp_obj = slip_line_obj.search([domain_slip_id, ('code', '=', 'CSSAT')])
                    cnss_AT += temp_obj.total or 0.0

                    temp_obj = slip_line_obj.search([domain_slip_id, ('code', '=', 'CSSPF')])
                    cnss_PF += temp_obj.total or 0.0

                    temp_obj = slip_line_obj.search([domain_slip_id, ('code', '=', 'TIPRESC')])
                    cnss_IPRESC += temp_obj.total or 0.0

                    temp_obj = slip_line_obj.search([domain_slip_id, ('code', '=', 'TIPRERG')])
                    cnss_IPRERG += temp_obj.total or 0.0



                brute_total = month_1 
				
                cnss_lines.append((0, 0, {
                    'cnss_id': o.id,
                    'employee_id': e,
                    'month_1': month_1,
                    'tt1': tt1,
                    'brute_total': brute_total,
                    'cnss_AT': cnss_AT,
                    'cnss_PF': cnss_PF,
                    'cnss_IPRESC': cnss_IPRESC,
                    'cnss_IPRERG': cnss_IPRERG,                 				
                }))
            o.write({'cnss_lines': cnss_lines})
        return True
		


class CNSSLine(models.Model):
    _name = 'hr.cnss.line'
    _description = 'CNSS'

    def _name_get(self):
        res = {}
        for record in self:
            res[record.id] = 'CNSS' + str(record.cnss_id.id) + '-' + str(record.employee_id.id) + '-' + str(record.id)
        return res

    name = fields.Char(compute='_name_get', type="char", string='Name', store=True)
    cnss_id = fields.Many2one('hr.cnss', 'CNSS', required=True, ondelete='cascade', index=True)
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True)
    month_1 = fields.Float('Month 1')
    brute_plaf	= fields.Float('plafond',compute='_compute_plaf')
    brute_plaf2	= fields.Float('plafond',compute='_compute_plaf2')
    brute_plaf3	= fields.Float('plafond',compute='_compute_plaf3')	
    company_id = fields.Many2one('res.company', 'Société', required=True, default=lambda self: self.env.user.company_id)
    tt1 = fields.Integer('Heures Travaillées')
    nemploye = fields.Integer("Nbre employee +63000",compute='_compute_employee_count')	
    nemploye2 = fields.Integer("Nbre employee - 63000",compute='_compute_employee_count2')
    nemploye3 = fields.Integer("Nbre employee - Horaire",compute='_compute_employee_count3')	
    brute_total = fields.Float('Salaire Brut', digits=(8, 2))
    cnss_AT = fields.Float('CSS ATMP', required=True)
    cnss_PF = fields.Float('CSS PF',  required=True)
    cnss_IPRESC = fields.Float('IPRES RCC',  required=True)
    cnss_IPRERG = fields.Float('IPRES RG',  required=True)	
    observation = fields.Char('Observation', size=120)



    @api.depends('month_1')
    def _compute_plaf(self):
        for p in self:	
            val1 = p.month_1	
            val2 = p.company_id.plafond1			
            p.brute_plaf = min(val1,val2)

    @api.depends('month_1')
    def _compute_plaf2(self):
        for p in self:
            p.brute_plaf2 =0
            if p.employee_id .contract_id.type_ctr !='Stage' :	
                val1 = p.month_1	
                val2 = p.company_id.plafond2			
                p.brute_plaf2 = min(val1,val2)

			
    @api.depends('month_1')
    def _compute_plaf3(self):
        for p in self:	
            p.brute_plaf3 =0		
            if p.employee_id .contract_id.type_ctr !='Stage' and p.brute_total > 432000:	
                val1 = p.month_1	
                val2 = p.company_id.plafond3			
                p.brute_plaf3 = min(val1,val2)			
			

    @api.depends('month_1')
    def _compute_employee_count(self):
        for p in self:
            p.nemploye = 0	
            val1 = p.month_1	
            val2 = p.company_id.plafond1			
            if val1 > val2:
                p.nemploye = len(p.cnss_id)


    @api.depends('month_1')
    def _compute_employee_count2(self):
        for p in self:
            p.nemploye2 = 0			
            val1 = p.month_1	
            val2 = p.company_id.plafond1
            val3 = p.employee_id.contract_id.pay_period 			
            if val1 <= val2 and val3 != 'hourly':
                p.nemploye2 = len(p.cnss_id)

    @api.depends('employee_id')
    def _compute_employee_count3(self):
        for p in self:
            p.nemploye3 = 0			
            val3 = p.employee_id.contract_id.pay_period 			
            if val3 == 'hourly':
                p.nemploye3 = len(p.cnss_id)