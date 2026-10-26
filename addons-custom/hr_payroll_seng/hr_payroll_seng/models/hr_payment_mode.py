# -*- coding: utf-8 -*-

from odoo import models, fields

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
		
class Payment_mode(models.Model):
    _name = "hr.payment.mode"
    name = fields.Char(string="Mode de paiemet")

class Qualif_mode(models.Model):
    _name = "hr.qualif.mode"
    name = fields.Char(string="Qualification")
    montant=fields.Integer(string="Montant ", help="")

    _order = 'name'
    _sql_constraints = [
        ('name_uniq', 'unique (name)', ' Existe ! La qualification doit être unique')]

class Catego_mode(models.Model):
    _name = "hr.catego.mode"
    name = fields.Char(string="Catégorie", help="Selon les conventions collectives ")
    taux=fields.Float(string="Taux de majoration", help="1ère catégorie : salaire minimum inter professionnel garanti (SMIG)- 2ème catégorie : SMIG majoré de 5% 3ème catégorie : SMIG majoré de 18% 4ème catégorie : SMIG majoré de 23%5ème catégorie : SMIG majoré de 30% 6ème catégorie : SMIG majoré de 63% 7ème catégorie : SMIG majoré de 100%")

    _order = 'name'
    _sql_constraints = [
        ('name_uniq', 'unique (name)', ' Existe !  doit être unique')]
		
class Conv_mode(models.Model):
    _name = "hr.conv.mode"
    name = fields.Char(string="Convention Collective", help="La convention collective du secteur de l'entreprise")


    _order = 'name'
    _sql_constraints = [
        ('name_uniq', 'unique (name)', ' Existe ! doit être unique')]	
		
		
class Interet_mode(models.Model):
    _name = "hr.interest"


    def _get_year(self):
	
        START_YEAR = 2010
        STOP_YEAR = 2030
        STEP_YEAR = 1


        seq_year = seq(START_YEAR, STOP_YEAR, STEP_YEAR )
        seq_year = [str( i ) for i in seq_year]
        seq_year.reverse()
        year_selection = zip( seq_year, seq_year )
        return tuple( year_selection )
		