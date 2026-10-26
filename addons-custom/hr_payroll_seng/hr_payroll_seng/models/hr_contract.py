# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import date
from dateutil.relativedelta import relativedelta


from odoo import fields, models,api, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import ValidationError


class HrContract(models.Model):
    """
    Employee contract based on the visa, work permits
    allows to configure different Salary structure
    """
    _inherit = 'hr.contract'




    pay_period = fields.Selection(string="Type de Paie(voir employé)",  related='employee_id.mode_pay')	
    # mode_pay = fields.Selection([('monthly', 'Mois'),('hourly', 'Heure'),('day', 'Jour')], string='Type de Paie', index=True, default='monthly')   
    struct_id = fields.Many2one('hr.payroll.structure', string='Salary Structure')	
    resource_calendar_id = fields.Many2one(required=True, help="Employee's working schedule.")
    start_date = fields.Date(string="Date d'embauche", related='date_start')
    prime_saliss = fields.Integer(string="Prime Salissure",default=0)
    prime_bilan = fields.Integer(string="Prime du bilan",default=0,help="Prime annuelle taxable")	
    paid_hourly = fields.Boolean(string="Paid Hourly", default=False)	
    prime_vest = fields.Integer(string="Primes de travail dans des conditions particulières",default=0,help="(profondeur, hauteur, poussière, boue, outils pneumatiques, etc.")
    prime_rend = fields.Integer(string="Prime de rendement",default=0,help="Prime taxable")
    prorata = fields.Boolean(string="Appliquer le prorata sur indemnités", default=True)
    prime_tax = fields.Integer(string="Autre prime taxable",default=0,help="Autres primes taxables")
    prime_ntax = fields.Integer(string="Autre prime non taxable",default=0,help="Utiliser pour des primes occasionnelles non taxables")	
    prime_annut = fields.Integer(string="Autre prime annuelle taxable",default=0,help="Utiliser pour autres primes annuelles taxables")	
    prime_panier = fields.Integer(string="Prime de panier",default=0,)
    prime_nuit = fields.Integer(string="Prime de nuit",default=0,help="Prime taxable pour le travail de nuit")	
    situation = fields.Selection([('SO', 'SO'), ('DE', 'DE'), ('IT', 'IT'), ('IL', 'IL'), ('AT', 'AT'), ('CS', 'CS'), ('MS', 'MS'), ('MP', 'MP')], 'Situation CNSS')	
    anciennete = fields.Float(string="Ancienneté", compute='_anciennete')	
    end_date = fields.Date(string="Date de Fin", related='date_end')	
    today = fields.Date(default=fields.Date.today)
    ccn = fields.Char(string="Convention Collective")
    type_ctr = fields.Selection([('CDI', 'CDI'), ('CDD', 'CDD'),('CTT', 'CTT'), ('Expat', 'Expatrié'), ('Stage', 'Stage'), ('Autre', 'Autres')], 'Type de contrat',required=True)

    niveau = fields.Char(string="Niveau")	
    motif= fields.Selection([('Démission', 'Démission'), ('Licenciement', 'Licenciement'), ('Fin de contrat', 'Find de contrat'), ('Fermeture', 'Fermeture')], 'Motif de départ')
    warningval = fields.Char(default='Attention ce  contrat a expiré !')
    hours = fields.Float(string='Nombre Heures de T',default=173.33)
    days = fields.Integer(string='Nombre Jours de T',default=26)
    jours_t = fields.Integer(string="Nombre de jours  par an",default=312)		
    leave = fields.Float(string='Cumul du Congé ')
    cpris = fields.Float(string="Congé pris en jours")
    crest = fields.Float(string="Congé restant en jours", compute='_get_crest' )
    com =fields.Integer(string="Commission sur ventes",default=0,help=" Taxable")
    congmois = fields.Float(string="Jours de congé légal par mois",default=1.5)	
    leave = fields.Float(string='Mois de trvail',compute='_get_leave' )
    conge = fields.Float(string='Jours de Conge acquis',compute='_get_conge' )	
    t_ded_formpro = fields.Float(string="Taux déduction Formation Professionnelle",default=20)		
    prime_ann = fields.Boolean(string="Prime 13 ième mois",help="Prime annuelle taxable")	

    prime_bol = fields.Boolean(string="Cochez pour afficher le tableau de saisie  des primes ou indemnités")	
    anciennet_bol = fields.Boolean(string="Activez la prime d'ancienneté", default=False)

	# Mali primes et alloc. exonérées
	
    aide_medicale = fields.Float(string="Aide médicale",default=0,help="Frais médicaux doivent être dûment justifiés par des factures probante")		
    prime_panier = fields.Float(string="Prime de panier",default=0,help="Le montant est égal à trois fois le salaire horaire minimum de sa catégorie (conventionnel)")	
    prime_vestm = fields.Float(string="Prime Vestimentaire",default=0,help="(Au cas où l’ouvrier n’aurait pas de tenue de travail")   
    prime_laitp = fields.Float(string="Prime de Poussière/lait",default=0,help="")
    prime_depl = fields.Float(string="Prime de Déplacement",default=0,help="")
    prime_salis = fields.Float(string="Prime de Salissure",default=0,help="")	
    prime_loge = fields.Float(string="Indemnité de logement",default=0,help="")	
    prime_trsp = fields.Float(string="Indemnité de transport",default=0,help="")	
    prime_nuise	= fields.Float(string="Prime de Nuisance",default=0,help="")	
    indem_caisse = fields.Float(string="Indemnités de Caisse et de Gestion",default=0,help="Accordées aux agents chargés du maniement des deniers ou de la gestion des matières, ayant de ce fait une responsabilité pécuniaire effective et personnelle et, ne pouvantexcéder 10 % du traitement de base")		
    prime_repr = fields.Float(string="Indemnité de responsabilité",default=0,help="Maximum 10% salaire de base Octroyée uniquement aux aux cadres occupant des emplois supérieurs")	
    prime_trav = fields.Float(string="Primes de travail dans des conditions particulières",default=0,help="(profondeur, hauteur, poussière, boue, outils pneumatiques, etc.")	
    prime_outil = fields.Float(string="Indemnité d’Équipement",default=0,help="Allouée à titre exceptionnel en début de carrière ou à des périodes régulières, à des agents pour l’usage  d’articles d’équipement non-fournis par l’employeur")   
    indem_depl = fields.Float(string="Indemnité de déplacement",default=0,help=" A condition que le déplacement soit réel, justifié par la fonction du bénéficiaire et en rapport avec ses obligations professionnelles")
    indem_transp = fields.Float(string="Indemnité de transport",default=0,help="Attribuées aux salariés en raison de l’éloignement du lieu de travail de leur domicile, à condition que le salarié ne bénéficie pas du transport par l’entreprise et, que le montant ne dépasse pas 10 % du traitement de base	")    
    indem_demena = fields.Float(string="Indemnités de Déménagement",default=0,help="Lorsque cette situation est imposée par l’employeur pour nécessité de service, à l’exclusion du déménagement effectué pour les convenances personnelles du salarié")		
    indem_depays = fields.Float(string="Indemnités de Dépaysement",default=0,help="15 % des émoluments, exclusion faite des allocations familiales, des indemnités destinées à couvrir les frais inhérents à la fonction ou à l’emploi et des avantages en nature. Les cadres expatriés résidant depuis plus de dix ans au Mali, ne peuvent bénéficier de cette indemnité.")		
    indem_voyage = fields.Float(string="Frais de voyage",default=0,help="Frais de voyage de congé pour se rendre dans le pays d’origine pour le personnel étranger, lorsqu’elle est prévue par convention contractuelle, dans la limite d’un voyage effectif une fois par an")
    indem_licen = fields.Float(string="Indemnité de licenciement",default=0,help="dans la limite des montants fixés par le Code du travail")
    indem_depart = fields.Float(string="Indemnité de départ ou mise à la retraite",default=0,help="dans la limite des montants fixés par le Code du travail")
    alloc_stage = fields.Float(string="Allocations de stage",default=0,help="accordées conformément au décret n°92-128/PM-RM du 18 Avril 1992 fixant les modalités d’application du stage de formation des Jeunes Diplômés sans Emploi")
    frais_fonc = fields.Float(string="Frais inhérents à la fonction",default=0,help="80.000 FCFA par mois pour les dirigeants salariés des entreprises dont le chiffre d’affaires annuel dépasse250.000.000 FCFA ;60.000 FCFA par mois, pour les dirigeants salariés des autres entreprises")
    frais_loge = fields.Float(string="Frais de logement",default=0,help="Logement y compris le matériel et le mobilier:imposables pour 50 % de leur valeur intrinsèque et réelle soit 50 % de la valeur locative brute ayant servi de base à l’établissement de l’impôt sur lesrevenus fonciers.")
    frais_conso1= fields.Float(string="Frais eau et électricité",default=0,help="Factures eau et électricité:imposables pour 50 % de leur valeur intrinsèque et réelle")
    frais_conso2= fields.Float(string="Frais Téléphone et Internet",default=0,help="Factures téléphone:imposables pour 50 % de leur valeur intrinsèque et réelle")
    frais_conso3= fields.Float(string="Frais de domesticité",default=0,help="gardiens, jardiniers, cuisiniers, nourrices:imposables pour 50 % de leur valeur intrinsèque et réelle")
    frais_conso4= fields.Float(string="Impôts personnels",default=0,help="Paiement Impôts personnels:imposables pour 50 % de leur valeur intrinsèque et réelle")
    frais_conso5= fields.Float(string="Transport et carburant",default=0,help="y compris les dotations en carburant, à l’exception des transports en commun:imposables pour 50 % de leur valeur intrinsèque et réelle")
    monture = fields.Float(string="Indemnités de Monture Personnelle",default=0, help="Indemnité forfaitaire allouée aux agents qui font régulièrementusage, pour les besoins du Service ou de l’Entreprise, d’un moyen de transport personnel")

    majoration= fields.Float(string="Taux de majoration à appliquer selon la catégorie",default=0)
    prime_nature= fields.Float(string="Autres primes en nature)",default=0)	
    maj_bool= fields.Boolean(string="Cochez si cet employé bénéficie de la majoration ")
    viechere	= fields.Integer(string="Vie chère",default=0,help=" ")	
   
    sursal = fields.Float(string="Sur salaire",default=0)
    qualification= fields.Selection([('Cadre', 'Cadre'),('Ncadre', 'Non Cadre'),('Ouvrier', 'Ouvrier'),('Autre', 'Autre')], 'Qualification')
    categorie= fields.Selection([('1', '1'),('2', '2'),('3', '3'),('4', '4'),('5', '5'),('6', '6'),('7A', '7A'),('7B', '7B'),('8A', '8A'),('8B', '8B'),('8C', '8C'),('9A', '9A'),('9B', '9B'),('10A', '10A'),('10B', '10B'),('10C', '10C'),('11A', '11A'),('11B', '11B')], 'Catégorie')	
    name = fields.Char('Contract Reference', default='/')
    payment_mode_id = fields.Many2one(string="Mode de paiement", comodel_name="hr.payment.mode")
    payment_mode = fields.Selection([('Virement', 'Virement'), ('Espece', 'Espèce'), ('Cheque', 'Chèque')], "Mode de paiement",default= 'Virement')	
    qualification_id = fields.Many2one(string="Qualification", comodel_name="hr.qualif.mode")
    qualification_amount = fields.Many2one(string="Prime de la Solidarité 1991", comodel_name="hr.qualif.mode")	
    categorie_id = fields.Many2one(string="Catégorie", comodel_name="hr.catego.mode")	
    categorie_taux = fields.Many2one(string="Taux de majoration pour cette catégorie", comodel_name="hr.catego.mode")		
    convention_id = fields.Many2one(string="Convention Collective", comodel_name="hr.conv.mode")	
    schedule_pay = fields.Selection([('monthly', 'Mensuel'),('hourly', 'Horaire'),], string='Période de Paie', index=True, default='monthly')	
    wageh = fields.Float('Salaire horaire',  tracking=True, help="Taux horaire",default=333.8)	
    waged = fields.Float('Salaire Journalier',  tracking=True, help="Taux journalier",default=2670)	
    wagecalc= fields.Float('Salaire horaire', help="Total",compute='_get_wage_cal',store=True)
    employee_id = fields.Many2one('hr.employee', 'Employee')
	
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('contract.ref') 
        ref = super(HrContract, self).create(vals)
        return ref	


    @api.depends('start_date','today','date_start')
    def _anciennete(self):
        if self.date_start:
          
            end = date.today()
            self.anciennete = relativedelta(end,self.date_start).years

    @api.depends('today')
    def _get_deduction(self):
        for r in self:
            if not r.interet:
                r.interet=((fields.Datetime.from_string(self.today).month))

    @api.depends('start_date','today','date_start','congmois')
    def _get_leave(self):
        for r in self:
            if r.date_start:
                end = date.today()
                self.leave = relativedelta(end,r.date_start).months 
		


    @api.depends('leave','congmois')
    def _get_conge(self):
        for d in self: 
            if not d.congmois:
                d.conge = 0.0
            else:				
                d.conge = d.leave*d.congmois 
				
    @api.depends('leave','cpris')
    def _get_crest(self):
        for d in self: 
            if not d.leave:
                d.crest = 0.0
            else:				
                d.crest=d.leave-d.cpris	


    @api.depends('wage','pay_period','wageh','waged')
    def _get_wage_cal(self):
        for w in self: 
            if w.pay_period == 'hourly':
                w.wagecalc = w.wageh
            if w.pay_period == 'monthly':				
                w.wagecalc = w.wage/173.33 
            if w.pay_period == 'day':
                w.wagecalc = w.waged/8



    state = fields.Selection([
        ('draft', 'New'),
        ('open', 'Running'),
        ('close', 'Expired'),
        ('cancel', 'Cancelled')
    ], string='Status', group_expand='_expand_states', copy=False,
       tracking=True, help='Status of the contract', default='open')			


