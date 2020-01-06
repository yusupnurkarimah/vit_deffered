# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import pdb
import time

SESSION_STATES =[('draft','Draft'),('confirm','Running')]

class deffered(models.Model):
	_name = 'vit.deffered'
	_inherit = 'mail.thread'

	name                = fields.Char(string="Name", required=True, default='New')
	account_asset_id    = fields.Many2one('vit.deffered.category', string='Defferal Category')
	entry               = fields.Date(string="Entry Date", required=False, 
						default=lambda self:time.strftime("%Y-%m-%d"))
	currency_id         = fields.Many2one(string='Currency',comodel_name='res.currency',)
	company_id          = fields.Many2one(string='Company',comodel_name='res.company',)
	value               = fields.Float(string="Value")
	salvage             = fields.Float(string="Salvage Value")
	residual            = fields.Float(string="Residual Value")
	partner             = fields.Many2one(comodel_name="res.partner", string="Partner")
	time_metode         = fields.Many2one('vit.deffered.category',string="Time Method")
	number_of_defferal  = fields.Integer(string="Number of Defferal")
	number_of_month     = fields.Integer(string="Number of Months in a Period")
	ending_date         = fields.Date(string="Ending Date", required=False, default=lambda self:time.strftime("%Y-%m-%d"))
	description         = fields.Char(string="Description")
	state               = fields.Selection(selection=SESSION_STATES, string="Status", required=False,
						readonly=True, default=SESSION_STATES[0][0], help="")
	line_ids			= fields.One2many('vit.deffered.line','line_id',"Line")

	@api.model
	def create(self, vals):
		if not vals.get('name', False) or vals['name'] == 'New':
			vals['name'] = self.env['ir.sequence'].next_by_code('vit.deffered') or 'Error Number!!!'
		return super(deffered, self).create(vals)

	@api.multi
	def action_draft(self):
		self.state = SESSION_STATES[0][0]

	@api.multi
	def action_confirm(self):
		self.state = SESSION_STATES[1][0]

	@api.onchange('account_asset_id')
	def onchange_doc_template_number(self):
		if self.account_asset_id:
			number = self.account_asset_id.method_number
			self.number_of_defferal = number

			return {'domain': {'number_of_defferal': [('method_number', '=', number)]}}
		else:
			self.number_of_defferal = False
			return {'domain': {'number_of_defferal': [('method_number', '!=', False)]}}

	@api.onchange('account_asset_id')
	def onchange_doc_template_period(self):
		if self.account_asset_id:
			period = self.account_asset_id.method_period
			self.number_of_month = period

			return {'domain': {'number_of_month': [('method_period', '=', period)]}}
		else:
			self.number_of_month = False
			return {'domain': {'number_of_month': [('method_period', '!=', False)]}}

	@api.multi
	def compute_defferal_board(self):
		# pdb.set_trace()
		cr=self.env.cr
		sql = "delete from vit_deffered_line where line_id=%s"
		cr.execute(sql, (self.id,) )
		value 				= self.value
		number_of_defferal 	= self.number_of_defferal
		amount 				= self.value / self.number_of_defferal
		entry				= self.entry
		for x in range(number_of_defferal):
			count 	= (x * amount) + amount
			count1	= value - count
			count2	= entry + relativedelta(months=+x)
			line_data = [(0,0,{
				'amount' 			: amount,
				'depreciation_date' : count2,
				'depreciated_value' : count,
				'remaining_value' 	: count1,
				'line_id' 			: self.id,
			})]
			self.write({'line_ids' : line_data})

class defferedCategory(models.Model):
	_name = 'vit.deffered.category'

	name 				= fields.Char(string="Deffered Category")
	journal_id 			= fields.Many2one('account.journal', string='Journal', required=True)
	account_asset_id 	= fields.Many2one('account.account', string='Deffered Account', required=True, domain=[('internal_type','=','other'), ('deprecated', '=', False)], help="Account used to record the purchase of the asset at its original price.")
	account_depreciation_expense_id = fields.Many2one('account.account', string='Depreciation Entries: Expense Deffered', required=True, domain=[('internal_type','=','other'), ('deprecated', '=', False)], oldname='account_income_recognition_id', help="Account used in the periodical entries, to record a part of the asset as expense.")
	method_number 		= fields.Integer(string='Number of Depreciations', default=5, help="The number of depreciations needed to depreciate your asset")
	method_period 		= fields.Integer(string='Period Length', default=1, help="State here the time between 2 depreciations, in months", required=True)

class defferedLine(models.Model):
	_name = 'vit.deffered.line'

	amount 				= fields.Float(string='Depreciation', digits=0, required=True)
	remaining_value 	= fields.Float(string='Residual', digits=0, required=True)
	depreciated_value 	= fields.Float(string='Cumulative Depreciation', required=True)
	depreciation_date 	= fields.Date('Depreciation Date', index=True)
	line_id 			= fields.Many2one('vit.deffered',string='Line')