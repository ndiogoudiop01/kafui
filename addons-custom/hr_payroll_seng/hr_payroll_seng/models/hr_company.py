# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing det


from odoo import fields, models,api, _
from odoo.addons import decimal_precision as dp



	
class Res_company(models.Model):
    _inherit = 'res.company'

   

    nombre_employes = fields.Integer(string="Nombre d'employés")
    cotisation_prevoyance = fields.Float(string="Cotisation Patronale Prévoyance")
    org_ss = fields.Char(string="Identifiant CSS")
    conv_coll = fields.Char(string='Convention collective')	
    patente = fields.Char(string="Numéro de la patente")
    idfiscal = fields.Char(string="Identifiant Fiscal")
    ice = fields.Char(string="Identifiant Commun (ICE)")
	
    t_pfam = fields.Float(string="Prestations familiales",default=7,required=True,help="7")	
    accid_trv = fields.Float(string="Accident de travail",default=3,required=True, help="1,3 ou 5 ")
    t_ipres_s = fields.Float(string="Taux IPRES Salarial",default=5.6,required=True,help="5.6")		
    t_ipres_pc = fields.Float(string="Taux IPRES patronal Complémentaire",default=3.6,help="3.6",required=True)
    t_ipres_sc = fields.Float(string="Taux IPRES Salarial Complémentaire ",default=2.4,required=True,help="2.4")
    actv_ipres = fields.Boolean(string="Activer IPRES  Complémentaire", default=False)	
    t_ipres_p = fields.Float(string="Taux IPRES patronal",default=8.4,help="8.4",required=True)
    t_amos = fields.Float(string="Taux AMO salarial",default=2,help="entre 2 et 7.5%",required=True)
    t_amop = fields.Float(string="Taux AMO patronal",default=2,help="entre 2 et 7.5%",required=True)	
    t_ipm = fields.Float(string="Cotisation IPM/CMU",default=5000)
    tot_pat = fields.Float(string="Total IPRES Patronal",compute='_get_total_ipresp')	
    tot_sal = fields.Float(string="Total IPRES Salarial",compute='_get_total_ipress')	
    tot_css = fields.Float(string="Total IPRES Salarial",compute='_get_total_css')	

    smig = fields.Integer(string="SMIG",default=55000)
    hours = fields.Float(string="Nombre Heures par mois",default=173.33)
    days = fields.Integer(string="Nombre Jours par mois",default=26)
    nom = fields.Char(string="Nom (p.physique)")	
    prenom = fields.Char(string="Prénom (p.physique)")
    numeroCIN = fields.Char(string="Numéro CIN ", size=20)
    numeroCE = fields.Char(string="Numéro Carte étranger")
    numeroRC = fields.Char(string="Numéro Registre commerce")
    identifiantTP = fields.Char(string="Identifiant TP")
    nbrPersoPermanent = fields.Integer(string="Nombre des permanents ")
    nbrPersoOccasionnel = fields.Integer(string="Nombre des occasionnels ")
    nbrStagiaires = fields.Integer(string="Nombre de stagiaires ")
    formeJ = fields.Selection([('SARL', 'SARL'), ('SA', 'SA'), ('SAS', 'SAS'), ('SNC', 'SNC'), ('PP', 'PP'), ('Autoentrepreneur', 'Autoentrepreneur')], "Forme juridique de l'entreprise")
    capital = fields.Char(string="Capital Social")	
    taux_bol = fields.Boolean(string="Cochez pour afficher le tableau des taux CSS,IR... (ATTENTION!!! Ne changer rien dans les taux )")	
    t_tcf = fields.Float(string="La Contribution Forfaitaire à la Charge de l’Employeur(CFCE)",default=3,help="3") 
	
    bol_tcf = fields.Boolean(string="Activer la Taxe de la Contribution Forfaitaire(CFCE) ",help=".")		
    signataire = fields.Char(string="Nom du signataire")
    fonc_signat= fields.Char(string="Fonction du signataire")
    plafond1 = fields.Integer(string="Plafond Prestations familiales et accidents de T",default=63000,required=True)
    plafond2 = fields.Integer(string="Vieillesse (IPRES)",default=432000,required=True)
    plafond3 = fields.Integer(string="Vieillesse complémentaire",default=1296000,required=True)
    plafond4 = fields.Integer(string="AMO",default=250000,required=True)
    actv_amo = fields.Boolean(string="Activer l'AMO", default=False)

	
# IRR
    igr_bol = fields.Boolean(string="Cochez pour afficher le tableau des tranches du revenu imposable (ATTENTION!!! Ne modifier rien)")	
    rnidu1 = fields.Float(default=0)
    rnidu2 = fields.Float(default=630001)
    rnidu3 = fields.Float(default=1500001)
    rnidu4 = fields.Float(default=4000001)
    rnidu5 = fields.Float(default=8000001)
    rnidu6 = fields.Float(default=13500001)	
    rnidu7 = fields.Float(default=50000001)
	
    rniau1 = fields.Float(default=630000)
    rniau2 = fields.Float(default=1500000)
    rniau3 = fields.Float(default=4000000)
    rniau4 = fields.Float(default=8000000)
    rniau5 = fields.Float(default=13500000)
    rniau6 = fields.Float(default=50000000)
    rniau7 = fields.Float(default=9000000000)

    taux1 = fields.Float(default=0)
    taux2 = fields.Float(default=20)
    taux3 = fields.Float(default=30)
    taux4 = fields.Float(default=35)
    taux5 = fields.Float(default=37)
    taux6 = fields.Float(default=40)
    taux7 = fields.Float(default=43)
	
    deduct1 = fields.Float(default=0)
    deduct2 = fields.Float(default=0)
    deduct3 = fields.Float(default=0)
    deduct4 = fields.Float(default=0)
    deduct5 = fields.Float(default=0)
    deduct6 = fields.Float(default=0)	
    deduct7 = fields.Float(default=0)    
    taux_red = fields.Float(default=30)  


# PARTS


    part1 = fields.Float(default=1)
    part2 = fields.Float(default=1.5)
    part3 = fields.Float(default=2)
    part4 = fields.Float(default=2.5)
    part5 = fields.Float(default=3)
    part6 = fields.Float(default=3.5)	
    part7 = fields.Float(default=4)
    part8 = fields.Float(default=4.5)
    part9 = fields.Float(default=5)	

    tpart1 = fields.Float(default=0)
    tpart2 = fields.Float(default=10)
    tpart3 = fields.Float(default=15)
    tpart4 = fields.Float(default=20)
    tpart5 = fields.Float(default=25)
    tpart6 = fields.Float(default=30)	
    tpart7 = fields.Float(default=35)
    tpart8 = fields.Float(default=40)
    tpart9 = fields.Float(default=45)	

    minpart1 = fields.Float(default=0)
    minpart2 = fields.Float(default=100000)
    minpart3 = fields.Float(default=200000)
    minpart4 = fields.Float(default=300000)
    minpart5 = fields.Float(default=400000)
    minpart6 = fields.Float(default=500000)	
    minpart7 = fields.Float(default=600000)
    minpart8 = fields.Float(default=700000)
    minpart9 = fields.Float(default=800000)
	

    maxpart1 = fields.Float(default=0)
    maxpart2 = fields.Float(default=300000)
    maxpart3 = fields.Float(default=650000)
    maxpart4 = fields.Float(default=1100000)
    maxpart5 = fields.Float(default=1650000)
    maxpart6 = fields.Float(default=2030000)	
    maxpart7 = fields.Float(default=2490000)
    maxpart8 = fields.Float(default=2755000)
    maxpart9 = fields.Float(default=3180000)


# TRIMF


    trimdu1 = fields.Float(default=0)
    trimdu2 = fields.Float(default=600000)
    trimdu3 = fields.Float(default=1000000)
    trimdu4 = fields.Float(default=2000000)
    trimdu5 = fields.Float(default=7000000)
    trimdu6 = fields.Float(default=12000000)	

    trimau1 = fields.Float(default=599999)
    trimau2 = fields.Float(default=999999)
    trimau3 = fields.Float(default=1999999)
    trimau4 = fields.Float(default=6999999)
    trimau5 = fields.Float(default=11999999)
    trimau6 = fields.Float(default=99999999)

    ttrim1 = fields.Float(default=900)
    ttrim2 = fields.Float(default=3600)
    ttrim3 = fields.Float(default=4800)
    ttrim4 = fields.Float(default=12000)
    ttrim5 = fields.Float(default=18000)
    ttrim6 = fields.Float(default=36000)




    @api.depends('t_ipres_pc','t_ipres_p')
    def _get_total_ipresp(self):
        for r in self:
            
            self.tot_sal = self.t_ipres_pc  + self.t_ipres_p 


    @api.depends('t_ipres_sc','t_ipres_s')
    def _get_total_ipress(self):
        for r in self:
            
            self.tot_sal = self.t_ipres_sc  + self.t_ipres_s
			
			
    @api.depends('t_pfam','accid_trv')
    def _get_total_css(self):
        for r in self:
            
            self.tot_css = self.t_pfam  + self.accid_trv			









