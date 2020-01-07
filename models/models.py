# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import pdb
import time
from odoo.tools import float_compare, float_is_zero

SESSION_STATES =[('draft','Draft'),('confirm','Running')]

class deffered(models.Model):
	_name = 'vit.deffered'
	_inherit = 'mail.thread'

	entry_count 		= fields.Integer(compute='_entry_count', string='# Asset Entries')
	name                = fields.Char(string="Name", required=True, default='New')
	account_asset_id    = fields.Many2one('vit.deffered.category', string='Defferal Category')
	entry               = fields.Date(string="Entry Date", required=False, 
						default=lambda self:time.strftime("%Y-%m-%d"))
	currency_id         = fields.Many2one(string='Currency',comodel_name='res.currency',)
	company_id          = fields.Many2one(string='Company',comodel_name='res.company',)
	value               = fields.Float(string="Value")
	salvage             = fields.Float(string="Salvage Value")
	residual            = fields.Float(string="Residual Value", compute='_compute_residual')
	partner             = fields.Many2one(comodel_name="res.partner", string="Partner")
	time_metode         = fields.Many2one('vit.deffered.category',string="Time Method")
	number_of_defferal  = fields.Integer(string="Number of Defferal")
	number_of_month     = fields.Integer(string="Number of Months in a Period")
	ending_date         = fields.Date(string="Ending Date", required=False, default=lambda self:time.strftime("%Y-%m-%d"))
	description         = fields.Char(string="Description")
	state               = fields.Selection(selection=SESSION_STATES, string="Status", required=False,
						readonly=True, default=SESSION_STATES[0][0], help="")
	deffered_line_ids	= fields.One2many('vit.deffered.line','line_id',"Line")
	code 				= fields.Char(string='Reference', size=32, readonly=False, states={'draft': [('readonly', False)]})

	@api.depends('deffered_line_ids')
	def _compute_residual(self):
		for line in self.deffered_line_ids[0]:
			self.residual = line.remaining_value

	@api.multi
	@api.depends('deffered_line_ids.move_id')
	def _entry_count(self):
		for line in self:
			res = self.env['vit.deffered.line'].search_count([('line_id', '=', line.id), ('move_id', '!=', False)])
			line.entry_count = res or 0

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
			self.write({'deffered_line_ids' : line_data})

	@api.multi
	def open_entries(self):
		move_ids = []
		for line in self:
			for depreciation_line in line.deffered_line_ids:
				if depreciation_line.move_id:
					move_ids.append(depreciation_line.move_id.id)
		return {
			'name': ('Journal Entries'),
			'view_type': 'form',
			'view_mode': 'tree,form',
			'res_model': 'account.move',
			'view_id': False,
			'type': 'ir.actions.act_window',
			'domain': [('id', 'in', move_ids)],
		}

class defferedCategory(models.Model):
	_name = 'vit.deffered.category'

	name 				= fields.Char(string="Deffered Category")
	journal_id 			= fields.Many2one('account.journal', string='Journal', required=True)
	account_asset_id 	= fields.Many2one('account.account', string='Deffered Account', required=True, domain=[('internal_type','=','other'), ('deprecated', '=', False)], help="Account used to record the purchase of the asset at its original price.")
	account_depreciation_expense_id = fields.Many2one('account.account', string='Depreciation Entries: Expense Deffered', required=True, domain=[('internal_type','=','other'), ('deprecated', '=', False)], oldname='account_income_recognition_id', help="Account used in the periodical entries, to record a part of the asset as expense.")
	method_number 		= fields.Integer(string='Number of Depreciations', default=5, help="The number of depreciations needed to depreciate your asset")
	method_period 		= fields.Integer(string='Period Length', default=1, help="State here the time between 2 depreciations, in months", required=True)
	open_asset 			= fields.Boolean(string='Auto-Confirm Assets', help="Check this if you want to automatically confirm the assets of this category when created by invoices.")

class defferedLine(models.Model):
	_name = 'vit.deffered.line'

	amount 				= fields.Float(string='Depreciation', digits=0, required=True)
	remaining_value 	= fields.Float(string='Residual', digits=0, required=True)
	depreciated_value 	= fields.Float(string='Cumulative Depreciation', required=True)
	depreciation_date 	= fields.Date('Depreciation Date', index=True)
	line_id 			= fields.Many2one('vit.deffered',string='Line')
	move_id 			= fields.Many2one('account.move', string='Depreciation Entry')
	move_check 			= fields.Boolean(compute='_get_move_check', string='Linked', track_visibility='always', store=True)
	move_posted_check 	= fields.Boolean(compute='_get_move_posted_check', string='Posted', track_visibility='always', store=True)
	sequence 			= fields.Integer(required=True)

	@api.multi
	@api.depends('move_id')
	def _get_move_check(self):
		for line in self:
			line.move_check = bool(line.move_id)

	@api.multi
	@api.depends('move_id.state')
	def _get_move_posted_check(self):
		for line in self:
			line.move_posted_check = True if line.move_id and line.move_id.state == 'posted' else False

	@api.multi
	def create_move(self, post_move=True):
		created_moves = self.env['account.move']
		for line in self:
			if line.move_id:
				raise UserError(_('This deffered is already linked to a journal entry. Please post or delete it.'))
			move_vals = self._prepare_move(line)
			move = self.env['account.move'].create(move_vals)
			line.write({'move_id': move.id, 'move_check': True})
			created_moves |= move

		if post_move and created_moves:
			created_moves.filtered(lambda m: any(m.asset_deffered_ids.mapped('line_id.account_asset_id.open_asset'))).post()
		return [x.id for x in created_moves]

	def _prepare_move(self, line):
		account_asset_id = line.line_id.account_asset_id
		depreciation_date = self.env.context.get('depreciation_date') or line.depreciation_date or fields.Date.context_today(self)
		company_currency = line.line_id.company_id.currency_id
		current_currency = line.line_id.currency_id
		prec = company_currency.decimal_places
		amount = current_currency._convert(
			line.amount, company_currency, line.line_id.company_id, depreciation_date)
		asset_name = line.line_id.name + ' (%s/%s)' % (line.sequence, len(line.line_id.deffered_line_ids))
		move_line_1 = {
			'name': asset_name,
			'account_id': account_asset_id.account_asset_id.id,
			'debit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
			'credit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
			'partner_id': line.line_id.partner.id,
			'currency_id': company_currency != current_currency and current_currency.id or False,
			'amount_currency': company_currency != current_currency and - 1.0 * line.amount or 0.0,
		}
		move_line_2 = {
			'name': asset_name,
			'account_id': account_asset_id.account_depreciation_expense_id.id,
			'credit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
			'debit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
			'partner_id': line.line_id.partner.id,
			'currency_id': company_currency != current_currency and current_currency.id or False,
			'amount_currency': company_currency != current_currency and line.amount or 0.0,
		}
		move_vals = {
			'ref': line.line_id.code,
			'date': depreciation_date or False,
			'journal_id': account_asset_id.journal_id.id,
			'line_ids': [(0, 0, move_line_1), (0, 0, move_line_2)],
		}
		return move_vals

class AccountMove(models.Model):
	_inherit = 'account.move'

	asset_deffered_ids = fields.One2many('vit.deffered.line', 'move_id', string='Assets Deffered Lines', ondelete="restrict")

	@api.multi
	def button_cancel(self):
		for move in self:
			for line in move.asset_deffered_ids:
				line.move_posted_check = False
		return super(AccountMove, self).button_cancel()

	@api.multi
	def post(self, invoice=False):
		for move in self:
			for depreciation_line in move.asset_deffered_ids:
				depreciation_line.post_lines_and_close_asset()
		return super(AccountMove, self).post(invoice=invoice)