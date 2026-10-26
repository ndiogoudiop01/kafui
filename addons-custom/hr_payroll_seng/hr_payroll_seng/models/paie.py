# -*- coding: utf-8 -*-

import calendar
import logging

# from . import get_date_interval, get_years_from

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
		
		
class PAIE(models.Model):
    _name = 'hr.paie'
    _description = 'paie'
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
		
    def _get_default_day(self):
        date = fields.Date.from_string(fields.Date.today())
        return date.strftime('%d')			


    def _get_default_month(self):
        date = fields.Date.from_string(fields.Date.today())
        return date.strftime('%m')
		
    def _get_default_year(self):
        date = fields.Date.from_string(fields.Date.today())
        return date.strftime('%Y')
		
    @api.onchange('month','date_from','year')    
    def _get_default_start_date(self):	
        mois = int(self.month)
        year = int(self.year)		
        self.date_from= date(year, mois , 1)
 
    @api.onchange('month','date_to','year')		
    def _get_default_end_date(self):
        for s in self:		
            year = int(s.year)	
            mois = int(s.month)
            value1 =  int(mois/12)	 
            value2 =  mois%12+1	
            s.date_to = date(year+value1,value2,1)- timedelta(days=1)
	
	

    date_from = fields.Date(string='Date de début ', required=True, compute='_get_default_start_date')
    date_to = fields.Date(string='Date de début ', required=True, compute='_get_default_end_date')	
    name = fields.Char(string='Déclaration N°', size=64, readonly=True, required=True, default=lambda *a: '...')
    company_id = fields.Many2one('res.company', 'Société', required=True, default=lambda self: self.env.user.company_id)
    year = fields.Selection(_get_year, 'Année', required=True, default=_get_default_year)
    month = fields.Selection(_MONTH, 'Mois', index=True, required=True, default=_get_default_month)	
    day = fields.Integer('Jour du mois' ,default=_get_default_day)
		
    mode_pay = fields.Selection([('month', 'Mois')], string='Période de Paie', index=True, default='month')
    date_document = fields.Date('Date du document', default=lambda *a: date.today())		
    # payment_mode = fields.Selection([('Virement', 'Virement'), ('Espece', 'Espèce'), ('Cheque', 'Chèque')], "Mode de paiement",default= 'Espece')		
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('waiting', 'A payer'),
        ('done', 'Payée'), ], 'État', index=True, default='draft', readonly=True, copy=False)
    paie_lines = fields.One2many('hr.paie.line', 'paie_id', 'paie')

    # total_paie_worker = fields.Float(compute='_get_total_paie_sal',string="paie EMPLOYE", digits=(8, 2))

    brut_total = fields.Float( string="Brut total", compute='_get_total_brut')
    net_total_m = fields.Float( string="Net total", compute='_get_total_net_m')	
    net_total = fields.Float( string="Net total", compute='_get_total_net')	
    net_total_espece = fields.Float( string="Net total espèce", compute='_get_total_net_espece')		
    base_total = fields.Float( string="Net total", compute='_get_total_base')		

    totheures_m = fields.Integer("Nbre d'heures - Total",compute='_get_total_heures_m')	
    totdays = fields.Integer("Nbre de jours",compute='_get_total_days')
    tothours = fields.Integer("Nbre d'heures",compute='_get_total_hours')	
    nemployem = fields.Integer("Total employés M",compute='_compute_employeem_count')	
    total_50 = fields.Integer("Billets de 50",compute='_get_total_50')
    total_100 = fields.Integer("Billets de 100",compute='_get_total_100')
    total_500 = fields.Integer("Billets de 500",compute='_get_total_500')
    total_1000 = fields.Integer("Billets de 1000",compute='_get_total_1000')
    total_2000= fields.Integer("Billets de 2000",compute='_get_total_2000')	
    total_5000 = fields.Integer("Billets de 5000",compute='_get_total_5000')	
    total_10000 = fields.Integer("Billets de 10 000",compute='_get_total_10000')	
	


    @api.depends('mode_pay')
    def _compute_employeem_count(self):
        for p in self:
            p.nemployem = 0		
            for line in p.paie_lines:						
                p.nemployem += len(line.paie_id)

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('paie')or '///...'
        declar = super(PAIE, self).create(vals)
        return declar

    @api.depends('paie_lines')           
    def _get_total_hours(self):       
        for p in self: 
            p.tothours = 0
            for line in p.paie_lines:		
                p.tothours += (line.hours)

    @api.depends('paie_lines')   		
    def _get_total_days(self):       
        for p in self: 
            p.totdays = 0				
            for line in p.paie_lines:	
                p.totdays += (line.days)


    @api.depends('paie_lines')           
    def _get_total_brut(self):       
        for p in self: 
            p.brut_total = 0
            for line in p.paie_lines:			
                p.brut_total += (line.brut)


    @api.depends('paie_lines')           
    def _get_total_base(self):       
        for p in self: 
            p.base_total = 0
            for line in p.paie_lines:			
                p.base_total += (line.base)



    @api.depends('paie_lines')           
    def _get_total_net(self):       
        for p in self: 
            p.net_total = 0
            for line in p.paie_lines:			
                p.net_total += (line.net)

    @api.depends('paie_lines')           
    def _get_total_net_espece(self):       
        for p in self: 
            p.net_total_espece = 0
            for line in p.paie_lines:			
                p.net_total_espece += (line.net_espece)
					
    @api.depends('paie_lines')           
    def _get_total_10000(self): 
        for p in self: 	
            p.total_10000 = 0
            for line in p.paie_lines:			
                p.total_10000 += (line.mt_10000)


    @api.depends('paie_lines')           
    def _get_total_5000(self):       
        for p in self: 
            p.total_5000 = 0
            for line in p.paie_lines:			
                p.total_5000 += (line.mt_5000)

    @api.depends('paie_lines')           
    def _get_total_2000(self):       
        for p in self: 
            p.total_2000 = 0
            for line in p.paie_lines:			
                p.total_2000 += (line.mt_2000)

    @api.depends('paie_lines')           
    def _get_total_1000(self):       
        for p in self: 
            p.total_1000 = 0
            for line in p.paie_lines:			
                p.total_1000 += (line.mt_1000)


    @api.depends('paie_lines')           
    def _get_total_500(self):       
        for p in self: 
            p.total_500 = 0
            for line in p.paie_lines:			
                p.total_500 += (line.mt_500)

    @api.depends('paie_lines')           
    def _get_total_100(self):       
        for p in self: 
            p.total_100 = 0
            for line in p.paie_lines:			
                p.total_100 += (line.mt_100)

    @api.depends('paie_lines')           
    def _get_total_50(self):       
        for p in self: 
            p.total_50 = 0
            for line in p.paie_lines:			
                p.total_50 += (line.mt_50)





    @api.depends('paie_lines')           
    def _get_total_net_m(self):       
        for p in self: 
            p.net_total_m = 0
            for line in p.paie_lines:
                if p.mode_pay == 'month' :				
                    p.net_total_m += (line.net)


    @api.depends('paie_lines')   		
    def _get_total_heures_m(self):       
        for p in self: 
            p.totheures_m = 0				
            for line in p.paie_lines:
                if p.mode_pay == 'month' :	
                    p.totheures_m += (line.hours)



    @api.onchange('month')
    def onchange_trismestre(self):
        line_obj = self.env['hr.paie.line']
        lines_ids = line_obj.search([('paie_id', 'in', self.id)])
        lines_ids.unlink()
		
    def paie_confirm(self):
        return self.write({'state': 'waiting'})

    def paie_payed(self):
        return self.write({'state': 'done'})
		
    def print_report(self):
        return self.env.ref('hr_payroll_seng.action_report_paie_dec').report_action(self)

    def print_report_selonm(self):
        return self.env.ref('hr_payroll_seng.action_mode_paie_selon').report_action(self)


    def paie_generate(self):
        f_line_obj = self.env['hr.paie.line']
        slip_obj = self.env['hr.payslip']
        slip_line_obj = self.env['hr.payslip.line']
        paie_lines = []
        for o in self:
            old_f_lines = f_line_obj.search([('paie_id', '=', o.id)])
            if old_f_lines:
                old_f_lines.unlink()
            date_from= o.date_from
            date_to= o.date_to	
            month = o.month if len(str(o.month)) == 1 else '0' + str(o.month)
			
			
            employee_ids = self.env['hr.employee'].search([['contract_id.state', 'in',['close', 'open']]]).mapped('id')
		
		
			
            slip_ids = slip_obj.search([
                ('date_from', '>=', date_from),
                ('date_to', '<=', date_to),
                ('employee_id', 'in', employee_ids),
                ])
				
            employee_ids = []
			
            for slip in slip_ids:
                if slip.employee_id.id not in employee_ids:
                    employee_ids.append(slip.employee_id.id)
            # for each employee
            for e in employee_ids:

                hours = 0
                days = 0
                base = 0				
                brut = 0
                net = 0	
	

                date_from_temp = datetime.strptime(str(date_from), "%Y-%m-%d").date()
                month_t = date_from_temp.month
                date_to = date_from_temp.replace(day=calendar.monthrange(date_from_temp.year, date_from_temp.month)[1])
                slip_id = slip_obj.search([
                    ('id', 'in', slip_ids.mapped('id')),
                    ('employee_id', '=', e),
                    ('date_from', '>=', date_from_temp),
                    ('date_to', '<=', date_to)]).mapped('id')
                domain_slip_id = ('slip_id', 'in', slip_id)
                val = slip_line_obj.search([domain_slip_id, ('code', '=', 'BASE')], limit=1)
                base = val.total or 0.0

                val = slip_line_obj.search([domain_slip_id, ('code', '=', 'BRUT')], limit=1)
                brut = val.total or 0.0

                val = slip_line_obj.search([domain_slip_id, ('code', '=', 'NETM')], limit=1)
                net = val.total or 0.0


                val = slip_line_obj.search([domain_slip_id, ('code', '=', 'WHOURS')], limit=1)
                hours = val.total or 0.0

                val = slip_line_obj.search([domain_slip_id, ('code', '=', 'WDAYS')], limit=1)
                days= val.total or 0.0

                paie_lines.append((0, 0, {
                    'paie_id': o.id,
                    'employee_id': e,
                    'base': base,
                    'brut': brut,					
                    'net': net,					
                    'hours': hours,
                    'days': days,	
                }))
            o.write({'paie_lines': paie_lines})
        return True
		
			

class paieLine(models.Model):
    _name = 'hr.paie.line'
    _description = 'paie'

    def _name_get(self):
        res = {}
        for record in self:
            res[record.id] = 'paie' + str(record.paie_id.id) + '-' + str(record.employee_id.id) + '-' + str(record.id)
        return res

    name = fields.Char(compute='_name_get', type="char", string='Name', store=True)
    paie_id = fields.Many2one('hr.paie', 'paie', required=True, ondelete='cascade', index=True)
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True)
    company_id = fields.Many2one('res.company', 'Société', required=True, default=lambda self: self.env.user.company_id)
    hours= fields.Integer('Heures')		
    days= fields.Integer('Jours')
    base= fields.Float('Base')		
    brut= fields.Float('Brut')
    net= fields.Integer('Net')
    net_espece= fields.Integer('Net espèce', compute ='_get_net_especet')	
    mt_50 = fields.Integer("Billets de 50",compute='_get_total_50')
    mt_100 = fields.Integer("Billets de 100",compute='_get_total_100')
    mt_500 = fields.Integer("Billets de 500",compute='_get_total_500')
    mt_1000 = fields.Integer("Billets de 1000",compute='_get_total_1000')
    mt_2000= fields.Integer("Billets de 2000",compute='_get_total_2000')	
    mt_5000 = fields.Integer("Billets de 5000",compute='_get_total_5000')	
    mt_10000 = fields.Integer("Billets de 10 000",compute='_get_total_10000')	

    modepaiement= fields.Char('Mode de paiement',compute='_get_mode_de_paiement')


    def _get_mode_de_paiement(self):
        for p in self:
            p.modepaiement = p.employee_id.contract_id.payment_mode	



    def _get_net_especet(self):
        for p in self:
            p.net_espece = 0		
            if p.modepaiement == 'Espece':			
                p.net_espece = p.net




    @api.depends('net_espece')           
    def _get_total_10000(self):       
        for p in self: 
            p.mt_10000 = p.net_espece/10000


    @api.depends('net_espece','mt_10000')           
    def _get_total_5000(self):       
        for p in self: 
            p.mt_5000 = (p.net_espece-(p.mt_10000*10000))/5000

    @api.depends('net_espece','mt_10000','mt_5000')           
    def _get_total_2000(self):       
        for p in self: 
            p.mt_2000= (p.net_espece-(p.mt_10000*10000)-(p.mt_5000*5000))/2000

    @api.depends('net_espece','mt_10000','mt_5000','mt_2000')           
    def _get_total_1000(self):       
        for p in self: 
            p.mt_1000 = (p.net_espece-(p.mt_10000*10000)-(p.mt_5000*5000)-(p.mt_2000*2000))/1000


    @api.depends('net_espece','mt_10000','mt_5000','mt_2000','mt_1000')           
    def _get_total_500(self):       
        for p in self: 
            p.mt_500 = (p.net_espece-(p.mt_10000*10000)-(p.mt_5000*5000)-(p.mt_2000*2000)-(p.mt_1000*1000))/500

    @api.depends('net_espece','mt_10000','mt_5000','mt_2000','mt_1000','mt_500')           
    def _get_total_100(self):       
        for p in self: 
            p.mt_100 = (p.net_espece-(p.mt_10000*10000)-(p.mt_5000*5000)-(p.mt_2000*2000)-(p.mt_1000*1000)-(p.mt_500*500))/100

    @api.depends('net_espece','mt_10000','mt_5000','mt_2000','mt_1000','mt_500','mt_100')           
    def _get_total_50(self):       
        for p in self: 
            p.mt_50 = (p.net_espece-(p.mt_10000*10000)-(p.mt_5000*5000)-(p.mt_2000*2000)-(p.mt_1000*1000)-(p.mt_500*500)-(p.mt_100*100))/50