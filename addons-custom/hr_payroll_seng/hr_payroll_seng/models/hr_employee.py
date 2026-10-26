# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import date, datetime,time
from dateutil.relativedelta import relativedelta
from odoo import fields, models,api, _
from odoo.exceptions import ValidationError
import pytz


class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    _description = 'Employee'


    _CATG= [
        ('NNI', 'Nationaux non imposables'),
        ('NI', 'Nationaux Imposables'),
        ('ENI', 'Expatriés non imposables'),
        ('EI', 'Expatriés Imposables'),
        ('AAC', 'Associes Actifs'),
        ('XI', 'Exploitant Individuel'),
        ('PON', 'Personnel Occasionnel nationaux'),
        ('POE', 'Personnel Occasionnel expatriés'),		
        ('PFCN', 'Personnel en fin de contrat Nationaux'),
        ('PFCE', 'Personnel en fin de contrat Expatriés'),]



    categ_sal = fields.Selection(_CATG, 'Catégorie Salariale', required=True, default='NI')
    birth = fields.Date(string="Date de naissance", related='birthday',required=True)
    cin = fields.Char(string="Numéro CIN")
    nation = fields.Char(string="Nationalité")	
    cpte_bank = fields.Char(string="Compte bancaire",default=0)
    # sit_famille = fields.Selection(related='marital' 'Situation de Famille')
    diplome = fields.Selection([('Ingénieur', 'Ingénieur'), ('Bac+2', 'Bac+2'), ('Bac+4', 'Bac+4'),('Bac+6', 'Bac+6'),('Technicien OFP', 'Technicien OFP'), ('Sans Diplôme', 'Sans Diplôme')], 'Diplôme')	
    titre = fields.Selection([('Monsieur', 'Monsieur'), ('Madame', 'Madame'), ('Mademoiselle', 'Mademoiselle')], 'Titre')	
    matricule_cnss = fields.Char(string="Numéro CSS")
    niveau = fields.Char(string="Niveau")
    coefficient = fields.Char(string="Coéfficient")
    adresse = fields.Char(string="Adresse personnelle")	
    id_fiscal = fields.Char(string="NINEA")
    enf_infirme = fields.Integer(string="Nombre d'enfants infirmes",help="L’enfant  infirme donne droit à une part." )
    indice = fields.Char(string="Indice")
    ifu = fields.Char(string="identifiant fiscal (ifu)")


    jours_t = fields.Integer(string="Nombre de jours de travail",default=26)
    heures_t = fields.Float(string="Nombre d'heures par mois",default=173.33)
    jours_t_an = fields.Integer(string="Nombre de jours  par an",default=312)		

    jrs_trav_cemois = fields.Integer(string="Jours travaillés (mode horaire)",default=26)
    hrs_trav_cemois = fields.Float(string="Heures travaillées (mode horaire)",default=0)
    jrs_trav_cemois_m = fields.Integer(string="Jours travaillés (mode mensuel)",default=26)
    hrs_trav_cemois_m = fields.Float(string="Heures travaillées (mode mensuel)",default=173.33)	
    presence_impor = fields.Boolean(string="Cochez si la présence est gérée par le système", default=False)
    mode_pay = fields.Selection([('monthly', 'Mois'),('hourly', 'Heure'),('day', 'Jour')], string='Type de Paie', index=True, default='monthly')   
    d_point = fields.Selection([('encours', 'Pointeuse mois encours'), ('dernier', 'Pointeuse mois dernier'),('systeme', 'Système'),('manuel', 'Manuel')], string="Type de pointage", default='manuel')

    presence_impor = fields.Boolean(string="Cochez si la présence est gérée par le système", default=False)
    point_impor = fields.Boolean(string="Cochez pour utiliser les données de la pointeuse", default=False)	
    attendance_ids = fields.One2many('hr.attendance', 'employee_id', help='list of attendances for the employee')		
    leave_ids = fields.One2many('hr.leave', 'employee_id', help='list of leaves for the employee')

    hours_this_month = fields.Float(compute='_compute_hours_this_month',string='Pointage en heures')
    hours_this_month_display = fields.Char(compute='_compute_hours_this_month', groups="hr_attendance.group_hr_attendance_user")
    hours_last_m = fields.Float(compute='_compute_hours_last_m',string='Pointage en heures mois dernier')

    days_this_month = fields.Float(compute='_compute_days_this_month',string='Pointage en jours')
    days_last_month = fields.Float(compute='_compute_days_last_month',string='Pointage en jours mois dernier')	
    days_this_month_display = fields.Char(compute='_compute_days_this_month', groups="hr_attendance.group_hr_attendance_user")

    absence_n_j = fields.Integer(string="Absence non justifiée en j")	
    absence_n_h = fields.Float(string="Absence non justifiée en h")	
    conge_maladie_j = fields.Integer(string="Congé Maladie en j", help='non rémunéré ou 2/3')
    conge_maladie_h = fields.Integer(string="Congé Maladie en h", help='non rémunéré ou 2/3')		
    conge_paye = fields.Integer(string="Congé payé en j")
    at_j = fields.Integer(string="jours accidents de travail")	
    sanc_j = fields.Integer(string="jours de sanction")		
    ferie_j = fields.Integer(string="jours fériés")	
    t_conge_maladie = fields.Float(string="Congé Maladie en j",default=1 ,help=' 2/3')		
    conge_pris = fields.Integer(string="Congé pris en j ce mois")	
    conge_circonstance = fields.Integer(string="Congé de circonstance", help='jours remuenées')		
    conge_naissance = fields.Integer(string="Congé de naissance", help='3 jours remmenées')
    conge_evenement = fields.Integer(string="Congé pour événements familiaux", help="Ces absences ne sont payées qu'aux salariés rémunérés au mois.")
    Conge_maternite = fields.Integer(string="Congé maternité", help="La salariée en état de grossesse attesté par certificat médical dispose d'un congé de maternité de 14 semaines")	

    leave = fields.Float(string='Cumul congé par Mois', compute='_get_leave',inverse='_set_leave')
    cpris = fields.Float(string=" Total Congé pris en jours")
    crest = fields.Float(string="Congé restant en jours", compute='_get_crest' )
    jcngpmois = fields.Float(string="Jours de congé par mois travaillé", default=2 )	
    moistrav = fields.Float(string="Nombre de mois à considérer pour le congé",default=0.0)

    show = fields.Boolean(string='Montrez les présences')



    today = fields.Date(default=fields.Date.today)		
    age = fields.Integer(string="Age", compute='_age')	
    part = fields.Float(string="Parts", compute='_part')	
    parts = fields.Float(string="N parts", compute='_parts')		
    image_certificate = fields.Binary('Upload certificate')
    certificate_name = fields.Char('certificate Name')	
    # enfants=fields.Float(string="N enfant", related='children')			
    first_name = fields.Char(string="Prénom", required=False)
    last_name = fields.Char(string="Nom", required=False)
    code2 = fields.Char('Code', default='Autofilled')

    imageemp = fields.Binary(string="Photo" ,related='image_1920')	
    contractn = fields.Binary(string="Photo" ,related='image_1920')		
    cname = fields.Char(string="N° du contrat", related='contract_id.name')
    cstate = fields.Selection(string="Etat du contrat", related='contract_id.state')
    start = fields.Date(string="Date de Début", related='contract_id.date_start')
    end = fields.Date(string="Date de fin", related='contract_id.date_end')

    heure_15 = fields.Integer(string="Heures supplémentaires +15%",default=0)	
    heure_35 = fields.Integer(string="Heures supplémentaires +35%",default=0)
    heure_40 = fields.Integer(string="Heures supplémentaires +40%",default=0)	
    heure_50 = fields.Integer(string="Heures supplémentaires +50%",default=0)
    heure_60 = fields.Integer(string="Heures supplémentaires +60%",default=0)	
    heure_100 = fields.Integer(string="Heures supplémentaires +100%",default=0)
	

    montantpret =fields.Float(string="Montant Initial du prêt",default=0)	
    montatdeduire =fields.Float(string=" Remboursement du mois",compute='_get_pret_rest')		
    mois1 =fields.Float(string="Janvier",default=0)	
    mois2 =fields.Float(string="Février",default=0)		
    mois3 =fields.Float(string="Mars",default=0)	
    mois4 =fields.Float(string="Avril",default=0)	
    mois5 =fields.Float(string="Mai",default=0)	
    mois6 =fields.Float(string="Juin",default=0)	
    mois7 =fields.Float(string="Juillet",default=0)	
    mois8 =fields.Float(string="Août",default=0)	
    mois9 =fields.Float(string="Septembre",default=0)	
    mois10 =fields.Float(string="Octobre",default=0)		
    mois11 =fields.Float(string="Novembre",default=0)
    mois12 =fields.Float(string="Décembre",default=0)	
	
    retenues = fields.Integer(string="Retenues sur salaire du mois",default=0)
    avance = fields.Integer(string="Avance sur salaire du mois",default=0)

    conge_count = fields.Float('Total number of days allocated.', compute='_compute_conge_count')
 
	
    @api.depends('hrs_trav_cemois')
    def jours_travail(self): 
        for s in self:
            s.jrs_trav_cemois = round((s.hrs_trav_cemois*s.jours_t)/s.heures_t )
	

    @api.onchange('first_name', 'last_name') 
    def check_change(self):     

        self.name = (self.first_name or '')+' '+(self.last_name or '')
		
		
		
    @api.model
    def create(self, vals):
        vals['code2'] = self.env['ir.sequence'].next_by_code('employee.code2') 
        code = super(HrEmployee, self).create(vals)
        return code		
		
    @api.depends('moistrav')
    def _get_leave(self):
        for r in self:		
            r.leave=r.moistrav*r.jcngpmois
		

    def _set_leave(self):	
        self.moistrav=self.leave


    @api.depends('leave','cpris')
    def _get_crest(self):
        for d in self: 
            if not d.leave:
                d.crest = 0.0
            else:				
                d.crest=d.leave-d.cpris		
		

			
    @api.depends('birth','today','birthday')
    def _age(self):
        for r in self:
            end = date.today()
            self.age = relativedelta(end,r.birthday).years			
			


    @api.onchange('month1', 'month2','month3', 'month4','month5', 'month6','month7', 'month9','month10', 'month11', 'month12') # if these fields are changed, call method
    def _get_pret_rest(self):
        for r in self:		
            if r.today.month == 1:
                r.montatdeduire = r.mois1              
            if r.today.month == 2:
                r.montatdeduire = r.mois2 
            if r.today.month == 3:
                r.montatdeduire = r.mois3              
            if r.today.month == 4:
                r.montatdeduire = r.mois4 
            if r.today.month == 5:
                r.montatdeduire = r.mois5              
            if r.today.month == 6:
                r.montatdeduire = r.mois6 
            if r.today.month == 7:
                r.montatdeduire = r.mois7              
            if r.today.month == 8:
                r.montatdeduire = r.mois8 
            if r.today.month == 9:
                r.montatdeduire = r.mois9 
            if r.today.month == 10:
                r.montatdeduire = r.mois10              
            if r.today.month == 11:
                r.montatdeduire = r.mois11 		
            if r.today.month == 12:
                r.montatdeduire = r.mois12 




			
			
    @api.depends('marital','children')
    def _part(self):
        self.part = 1	
        for s in self :    
            if (s.marital =='married' and s.children==0) or (s.marital=='single' and s.children==1 )or (s.marital=='divorced' and s.children==1 ): 
                s.part = 1.5 
            if (s.marital =='married'and s.children==1) or (s.marital=='widower' and s.children==1)or (s.marital =='single'  and s.children==2 )or (s.marital=='divorced' and s.children==2): 
                s.part = 2 
            if (s.marital =='married'and s.children==2) or (s.marital=='widower' and s.children==2)or (s.marital =='single'  and s.children==3 )or (s.marital=='divorced' and s.children==3): 
                s.part = 2.5 
            if (s.marital =='married'and s.children==3) or (s.marital=='widower' and s.children==3)or (s.marital =='single'  and s.children==4 )or (s.marital=='divorced' and s.children==4):		
                s.part = 3 
            if (s.marital =='married'and s.children==4) or (s.marital=='widower' and s.children==4)or (s.marital =='single'  and s.children==5 )or (s.marital=='divorced' and s.children==5):		
                s.part = 3.5 
            if (s.marital =='married'and s.children==5) or (s.marital=='widower' and s.children==5)or (s.marital =='single'  and s.children==6 )or (s.marital=='divorced' and s.children==6):		
                s.part = 4 
            if (s.marital =='married'and s.children==6) or (s.marital=='widower' and s.children==6)or (s.marital =='single'  and s.children==7 )or (s.marital=='divorced' and s.children==7):		
                s.part = 4.5 
            if (s.marital =='married'and s.children==7) or (s.marital=='widower' and s.children==7)or (s.marital =='single'  and s.children==8 )or (s.marital=='divorced' and s.children==8):		
                s.part = 5 
            if (s.marital =='married'and s.children>7) or (s.marital=='widower' and s.children>7)or (s.marital =='single'  and s.children>8 )or (s.marital=='divorced' and s.children>8):		
                s.part = 5 


    @api.depends('part','enf_infirme')
    def _parts(self):
        for s in self :
            s.parts = min(( s.part+s.enf_infirme),5)	
			
    @api.depends('hrs_trav_cemois')
    def jours_travail(self): 
        for s in self:
            s.jrs_trav_cemois = round((s.hrs_trav_cemois*26)/173.33)	


			
    def _compute_hours_today(self):
        now = fields.Datetime.now()
        now_utc = pytz.utc.localize(now)
        for employee in self:
       
            tz = pytz.timezone(employee.tz)
            now_tz = now_utc.astimezone(tz)
            start_tz = now_tz + relativedelta(hour=0, minute=0)  # day start in the employee's timezone
            start_naive = start_tz.astimezone(pytz.utc).replace(tzinfo=None)

            attendances = self.env['hr.attendance'].search([
                ('employee_id', '=', employee.id),
                ('check_in', '<=', now),
                '|', ('check_out', '>=', start_naive), ('check_out', '=', False),
            ])
            worked_hours = 0
            attendance_worked_hours = 0
            hours_previously_today = 0

            for attendance in attendances:
                delta = (attendance.check_out or now) - max(attendance.check_in, start_naive)
                attendance_worked_hours = delta.total_seconds() / 3600.0
                worked_hours += attendance_worked_hours
                hours_previously_today += attendance_worked_hours
            employee.last_attendance_worked_hours = attendance_worked_hours
            hours_previously_today -= attendance_worked_hours
            employee.hours_previously_today = hours_previously_today
            employee.hours_today = worked_hours
			
			
			
    def _compute_hours_this_month(self):
        now = fields.Datetime.now()
        now_utc = pytz.utc.localize(now)
        for employee in self:
            tz = pytz.timezone(employee.tz or 'UTC')
            now_tz = now_utc.astimezone(tz)
            start_tz = now_tz + relativedelta(months=0, day=1, hour=0, minute=0, second=0, microsecond=0)
            start_naive = start_tz.astimezone(pytz.utc).replace(tzinfo=None)
            end_tz = now_tz + relativedelta(day=31, hour=0, minute=0, second=0, microsecond=0)
            end_naive = end_tz.astimezone(pytz.utc).replace(tzinfo=None)

            attendances = self.env['hr.attendance'].search([
                ('employee_id', '=', employee.id),
                '&',
                ('check_in', '<=', end_naive),
                ('check_out', '>=', start_naive),
            ])

            hours = 0
            for attendance in attendances:
                check_in = max(attendance.check_in, start_naive)
                check_out = min(attendance.check_out, end_naive)
                hours += (check_out - check_in).total_seconds() / 3600.0

            employee.hours_this_month = round(hours, 0)
            employee.hours_this_month_display = "%g" % employee.hours_this_month			

    @api.depends('hours_last_month')
    def _compute_hours_last_m(self): 
        for s in self:
            s.hours_last_m = round(s.hours_last_month)		

    @api.depends('hours_last_month')
    def _compute_hours_last_m(self): 
        for s in self:
            s.hours_last_m = round(s.hours_last_month)
			
    @api.depends('jrs_trav_cemois_m')
    def _hrs_trav_cemois_m(self): 
        for s in self:
            s.hrs_trav_cemois_m = (s.jrs_trav_cemois_m*s.heures_t)/s.jours_t			
			
    @api.depends('hours_this_month')
    def _compute_days_this_month(self): 
        for s in self:
            s.days_this_month = round((s.hours_this_month*s.jours_t)/s.heures_t)
			
			
    @api.depends('hours_last_month')
    def _compute_days_last_month(self): 
        for s in self:
            s.days_last_month = round((s.hours_last_month*s.jours_t)/s.heures_t)				




    # def _compute_conge_count(self):

        # now = fields.Datetime.now()
        # now_utc = pytz.utc.localize(now)
        # for employee in self:
            # tz = pytz.timezone(employee.tz or 'UTC')
            # now_tz = now_utc.astimezone(tz)
            # start_tz = now_tz + relativedelta(months=0, day=1, hour=0, minute=0, second=0, microsecond=0)
            # start_naive = start_tz.astimezone(pytz.utc).replace(tzinfo=None)
            # end_tz = now_tz + relativedelta(day=31, hour=0, minute=0, second=0, microsecond=0)
            # end_naive = end_tz.astimezone(pytz.utc).replace(tzinfo=None)

        # data = self.env['hr.leave.allocation'].search([
            # ('employee_id', '=', employee.id),
            # ('state', '=', 'validate'),
            # ('date_from', '<=', start_naive),
            # '|',
            # ('date_to', '>=',end_naive),
        # ], ['employee_id'], ['__count', 'number_of_days:sum'])
        # rg_results = {employee.id: (count, days) for employee, count, days in data}
        # for employee in self:
            # count, days = rg_results.get(employee.id, (0, 0))
            # employee.conge_count = float_round(days, precision_digits=2)
            # employee.conge_count = count



			
			
    def action_azero(self):
        for s in self:
            s.write({'avance': 0})	
            s.write({'heure_15': 0})
            s.write({'heure_35': 0})
            s.write({'heure_40': 0})
            s.write({'heure_50': 0})			
            s.write({'heure_60': 0})			
            s.write({'heure_100': 0})			
            s.write({'hrs_trav_cemois': 0})
            s.write({'jrs_trav_cemois': 0})			
            s.write({'conge_maladie_j': 0})
            s.write({'conge_maladie_h': 0})
            s.write({'absence_n_j': 0})
            s.write({'absence_n_h': 0})			
            s.write({'conge_paye': 0})	
            s.write({'conge_pris': 0})
            s.write({'ferie_j': 0})	
            s.write({'at_j': 0})	
            s.write({'sanc_j': 0})			
            s.write({'conge_evenement': 0})	
            s.write({'retenues': 0})			
					
			