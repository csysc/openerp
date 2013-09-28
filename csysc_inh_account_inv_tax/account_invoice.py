# -*- coding: utf-8 -*-
from osv import fields, osv
import decimal_precision as dp
import time
import datetime
from tools.translate import _
from report import report_sxw

		
# put the invoice exchange date into the database
class csysc_account_invoice_huf_exchange(osv.osv):
	_name = "csysc.account.invoice.huf.exchange"
	_description = 'Huf daily exhange info'	
	_columns = {
		'name': fields.char('Currency name', size=64, help = "Name of the currency"),
		'value': fields.float('Verification Total', digits_compute=dp.get_precision('Account'), help = "1 actual currency how many Ft"),
		'resourche': fields.char('Currency name', size=64, help = "Exchange ratio sourch, example MNB, Citygroup..etc"), 
		'exchng_date': fields.date('Echange Date', readonly=True, select=True, help="Date of the exchange valiadtion"),
			}	
	
	
csysc_account_invoice_huf_exchange()

class account_invoice(osv.osv):
	
	# check the invoice type, if invoice type is reconcile, this case you nedd to select by Storno
	# boolean field >> Modificator invoice or Storno invoice according to Hungarian law. 
	# is_storn is true the checkbox will be show on the form.
	def _is_storno(self,cr,uid,id,x,y,context):
		result = {}		
		for r in self.browse(cr, uid, id, context=context):
			inv_type = r.type # get the invoice type
			if inv_type == 'out_refund':	# refund out case
			 	result[r.id] = True
			else:
			 	result[r.id] = False				
			
			if inv_type == 'in_refund':	# refund in case ex from supplyer
			 	result[r.id] = True			
			
		return result		
	
	# if the currency is not huf the exchange field must be visible
	def _is_huf(self, cr, uid, id,x,y, context):
		result = {}
		for r in self.browse(cr, uid, id, context=context):
			inv_curr_id = r.currency_id
			
			cur_obj = self.pool.get('res.currency')
			for k in cur_obj.search(cr, uid,[('name','=','HUF')],context=context):
				curr_id = k
			cur_obj1 = self.pool.get('res.currency')
			if curr_id:				
			 l = cur_obj1.browse(cr, uid, curr_id, context=context)	
			 id_fk = l.id
			 if inv_curr_id.id == id_fk:
			 	result[r.id] = True
			 else:
			 	result[r.id] = False			 		
		
		return result
			
	""" Sztornós számla képzés felűlírása """		
	def refund(self, cr, uid, ids, date=None, period_id=None, description=None, journal_id=None, context=None):
		invoice_obj = self.pool.get('account.invoice')
		"""
		A stronós számla létrehozása után kikapjuk az új id-t, majd az originba töltjük az adatot.  
		"""
		new_ids = super(account_invoice, self).refund(cr, uid, ids, date, period_id, description, journal_id)

		for refund_id ,invoice in zip(new_ids, self.browse(cr, uid, ids)):
			self.write(cr, uid, refund_id, {'origin': invoice.internal_number})

		return new_ids


	def action_move_create(self, cr, uid, ids, context=None):
		"""Creates invoice related analytics and financial move lines"""
		ait_obj = self.pool.get('account.invoice.tax')
		cur_obj = self.pool.get('res.currency')
		period_obj = self.pool.get('account.period')
		payment_term_obj = self.pool.get('account.payment.term')
		journal_obj = self.pool.get('account.journal')
		move_obj = self.pool.get('account.move')
		if context is None:
			context = {}
		for inv in self.browse(cr, uid, ids, context=context):
			if not inv.journal_id.sequence_id:
				raise osv.except_osv(_('Error !'), _('Please define sequence on the journal related to this invoice.'))
			if not inv.invoice_line:
				raise osv.except_osv(_('No Invoice Lines !'), _('Please create some invoice lines.'))
			if inv.move_id:
				continue
			
			ctx = context.copy()
			ctx.update({'lang': inv.partner_id.lang})
			if not inv.date_invoice:
				self.write(cr, uid, [inv.id], {'date_invoice': fields.date.context_today(self,cr,uid,context=context)}, context=ctx)
			company_currency = inv.company_id.currency_id.id
			# create the analytical lines
			# one move line per invoice line
			iml = self._get_analytic_lines(cr, uid, inv.id, context=ctx)
			# check if taxes are all computed
			compute_taxes = ait_obj.compute(cr, uid, inv.id, context=ctx)
			self.check_tax_lines(cr, uid, inv, compute_taxes, ait_obj)

			# I disabled the check_total feature
			#if inv.type in ('in_invoice', 'in_refund') and abs(inv.check_total - inv.amount_total) >= (inv.currency_id.rounding/2.0):
			#	raise osv.except_osv(_('Bad total !'), _('Please verify the price of the invoice !\nThe real total does not match the computed total.'))

			if inv.payment_term:
				total_fixed = total_percent = 0
				for line in inv.payment_term.line_ids:
					if line.value == 'fixed':
						total_fixed += line.value_amount
					if line.value == 'procent':
						total_percent += line.value_amount
				total_fixed = (total_fixed * 100) / (inv.amount_total or 1.0)
				if (total_fixed + total_percent) > 100:
					raise osv.except_osv(_('Error !'), _("Can not create the invoice !\nThe related payment term is probably misconfigured as it gives a computed amount greater than the total invoiced amount. The latest line of your payment term must be of type 'balance' to avoid rounding issues."))

			# one move line per tax line
			iml += ait_obj.move_line_get(cr, uid, inv.id)

			entry_type = ''
			if inv.type in ('in_invoice', 'in_refund'):
				ref = inv.reference
				entry_type = 'journal_pur_voucher'
				if inv.type == 'in_refund':
					entry_type = 'cont_voucher'
			else:
				ref = self._convert_ref(cr, uid, inv.number)
				entry_type = 'journal_sale_vou'
				if inv.type == 'out_refund':
					entry_type = 'cont_voucher'

			diff_currency_p = inv.currency_id.id <> company_currency
			# create one move line for the total and possibly adjust the other lines amount
			total = 0
			total_currency = 0
			total, total_currency, iml = self.compute_invoice_totals(cr, uid, inv, company_currency, ref, iml)
			acc_id = inv.account_id.id

			name = inv['name'] or '/'
			totlines = False
			if inv.payment_term:
				totlines = payment_term_obj.compute(cr,
						uid, inv.payment_term.id, total, inv.date_invoice or False, context=ctx)
			if totlines:
				res_amount_currency = total_currency
				i = 0
				ctx.update({'date': inv.date_invoice})
				for t in totlines:
					if inv.currency_id.id != company_currency:
						amount_currency = cur_obj.compute(cr, uid, company_currency, inv.currency_id.id, t[1], context=ctx)
					else:
						amount_currency = False

					# last line add the diff
					res_amount_currency -= amount_currency or 0
					i += 1
					if i == len(totlines):
						amount_currency += res_amount_currency

					iml.append({
						'type': 'dest',
						'name': name,
						'price': t[1],
						'account_id': acc_id,
						'date_maturity': t[0],
						'amount_currency': diff_currency_p \
								and amount_currency or False,
						'currency_id': diff_currency_p \
								and inv.currency_id.id or False,
						'ref': ref,
					})
			else:
				iml.append({
					'type': 'dest',
					'name': name,
					'price': total,
					'account_id': acc_id,
					'date_maturity': inv.date_due or False,
					'amount_currency': diff_currency_p \
							and total_currency or False,
					'currency_id': diff_currency_p \
							and inv.currency_id.id or False,
					'ref': ref
			})

			date = inv.date_invoice or time.strftime('%Y-%m-%d')
			part = inv.partner_id.id

			line = map(lambda x:(0,0,self.line_get_convert(cr, uid, x, part, date, context=ctx)),iml)

			line = self.group_lines(cr, uid, iml, line, inv)

			journal_id = inv.journal_id.id
			journal = journal_obj.browse(cr, uid, journal_id, context=ctx)
			if journal.centralisation:
				raise osv.except_osv(_('UserError'),
						_('You cannot create an invoice on a centralised journal. Uncheck the centralised counterpart box in the related journal from the configuration menu.'))

			line = self.finalize_invoice_move_lines(cr, uid, inv, line)

			move = {
				'ref': inv.reference and inv.reference or inv.name,
				'line_id': line,
				'journal_id': journal_id,
				'date': date,
				'narration':inv.comment
			}
			period_id = inv.period_id and inv.period_id.id or False
			ctx.update(company_id=inv.company_id.id,
					   account_period_prefer_normal=True)
			if not period_id:
				period_ids = period_obj.find(cr, uid, inv.date_invoice, context=ctx)
				period_id = period_ids and period_ids[0] or False
			if period_id:
				move['period_id'] = period_id
				for i in line:
					i[2]['period_id'] = period_id

			move_id = move_obj.create(cr, uid, move, context=ctx)
			new_move_name = move_obj.browse(cr, uid, move_id, context=ctx).name
			# make the invoice point to that move
			self.write(cr, uid, [inv.id], {'move_id': move_id,'period_id':period_id, 'move_name':new_move_name}, context=ctx)
			# Pass invoice in context in method post: used if you want to get the same
			# account move reference when creating the same invoice after a cancelled one:
			ctx.update({'invoice':inv})
			move_obj.post(cr, uid, [move_id], context=ctx)
		self._log_event(cr, uid, ids)
		return True
	
	def tax_in_huf(self, cr, uid, ids,x,y,context):
		result = {}
		invoices = self.browse(cr,uid,ids,context=context)
		for inv in invoices:
			exchange 	= inv.exchng_value
			tax 		= inv.amount_tax 
			result[inv.id] = exchange * tax
		return result

	_inherit = "account.invoice"
	_description = 'account.invoice'

	_columns = {
			#	'units_id': fields.many2one('csyscunit.type', 'unit' ,help='Unit of the dimension '),  
			'curr_exc_id':fields.many2one('csysc.account.invoice.huf.exchange', 'csysc.account.invoice.huf.exchange' ,help='Actually Exchange to HUF'),  
			'exchng_value': fields.float('Exchange value', digits_compute=dp.get_precision('Account'), help = "1 actual currency how many Ft"),	
			'is_huf':fields.function(_is_huf, type='boolean',store = True, string='Is Huf', method=True),
			'printed':fields.char('printed', size=64, help="The partner reference of this invoice."),
			'Tax_amount_huf':fields.function(tax_in_huf,type='float',digits_compute=dp.get_precision('Account'),store = True, help = 'The Tax in Huf'),
			'Cash_accounting':fields.boolean('Cash accounting',help = 'if your invoice according to Cash accounting rule, check it'),
			'exec_date':fields.date('Execution date',help = 'The date when your service/trade is executed'),
			'is_storno':fields.function(_is_storno, type='boolean',store = True, string='Is Storno', method=True),
			'Storno':fields.boolean('Storno',help = 'Érvénytelenítő számla?')
			}	
	_defaults = {
		'printed': lambda *a: 'Blank',
		'is_storno': lambda *a: 'False',		
	}	
	
	# get the workflow function
	def action_date_assign(self, cr, uid, ids, *args):
		for inv in self.browse(cr, uid, ids):
			res = self.onchange_payment_term_date_invoice(cr, uid, inv.id, inv.payment_term.id, inv.date_invoice)
			if res and res['value']:
				self.write(cr, uid, [inv.id], res['value'])
			# check the invoice date
			print inv.date_invoice
			print inv.type
			now = datetime.datetime.now()
			today = now.strftime("%Y-%m-%d")
			if inv.date_invoice <> today:
				raise osv.except_osv(_('Error !'), _('The invoice date is wrong, must today!'))			
			if inv.exec_date == False:
				if inv.type <> 'out_refund': 
					if inv.type <>'in_refund':
						raise osv.except_osv(_('Error !'), _('The execute date is empty!'))
			if inv.currency_id.name <> 'HUF':
				if inv.exchng_value == '0.0':
					raise osv.except_osv(_('Error !'), _('Please input today exchange value!'))
				if inv.exchng_value == False:
					if inv.type <> 'out_refund': 
						if inv.type <>'in_refund':					
							raise osv.except_osv(_('Error !'), _('Please input today exchange value!'))			
			
				
		return True	
	
		
account_invoice()

# inherit account_invoice line by standard way for show the tax by invoice row
class account_invoice_line(osv.osv):
	# override this methode to get the tax info's by invoice line	
	def _amount_line(self, cr, uid, ids, prop, unknow_none, unknow_dict):
		#values = super(account_invoice_line, self)._amount_line(self, cr, uid, ids, prop, unknow_none, unknow_dict)
		res = {}
		tax_obj = self.pool.get('account.tax')
		cur_obj = self.pool.get('res.currency')
		for line in self.browse(cr, uid, ids):
			price = line.price_unit * (1-(line.discount or 0.0)/100.0)
			taxes = tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, price, line.quantity, product=line.product_id, address_id=line.invoice_id.address_invoice_id, partner=line.invoice_id.partner_id)
			res[line.id] = taxes['total']
			#-----------------------------------------------------------------------------------
			for r in taxes['taxes']: # listing the result list
				id = r.get('id')	# get id of the taxes		
			tax_percent = self.pool.get('account.tax').browse(cr, uid, id).amount 				
			tax_amount  = taxes['total_included'] -  taxes['total']
			tax_total   = taxes['total_included'] 
			for r in ids:
				id = r
				cr.execute('UPDATE account_invoice_line SET tax_percent = %s  WHERE id=%s', (tax_percent,id,))
				cr.execute('UPDATE account_invoice_line SET Tax_amount = %s  WHERE id=%s', (tax_amount,id,))
				cr.execute('UPDATE account_invoice_line SET Line_total = %s  WHERE id=%s', (tax_total,id,))
				cr.execute('UPDATE account_invoice_line SET line_net_unit_price = %s  WHERE id=%s', (price,id,)) # put the net price	
			#-----------------------------------------------------------------------------------				
			if line.invoice_id:
				cur = line.invoice_id.currency_id
				res[line.id] = cur_obj.round(cr, uid, cur, res[line.id])
		return res	
		
	_inherit= "account.invoice.line"
	_description = "account.invoice.line"  #"Account invoice line set up for the life...."
	
	
	
	_columns = {
		'tax_percent' : fields.float('tax_percent'),	# percentage of the tax	
		'tax_amount' : fields.float('tax_amount'),		# amount of the tax
		'line_total' : fields.float('line_total'),		# calculate line tax + line amount
		'line_net_unit_price' : fields.float('line_net_total'),		# calculate line tax + line amount
		'price_subtotal': fields.function(_amount_line, string='Subtotal', type="float",digits_compute= dp.get_precision('Account'), store=True),		
			}
		

account_invoice_line()






