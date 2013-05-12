from osv import fields, osv
import time
import datetime
import decimal_precision as dp
from tools.translate import _

# inherit sale.order to read the tax when it calculate
class sale_order(osv.osv):
	_name = 'sale.order'
	_inherit = 'sale.order'
	
	def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
		cur_obj = self.pool.get('res.currency')
		res = {}
		for order in self.browse(cr, uid, ids, context=context):
			res[order.id] = {
				'amount_untaxed': 0.0,
				'amount_tax': 0.0,
				'amount_total': 0.0,
			}
			val = val1 = 0.0
			cur = order.pricelist_id.currency_id
			for line in order.order_line:
				val1 += line.price_subtotal
				k = self._amount_line_tax(cr, uid, line, context=context) # save the tax in k
				self.pool.get('sale.order.line').write(cr, uid,line.id,{'TAX' : k }) # save the k into the record
				val += k
			res[order.id]['amount_tax'] = cur_obj.round(cr, uid, cur, val)
			res[order.id]['amount_untaxed'] = cur_obj.round(cr, uid, cur, val1)
			res[order.id]['amount_total'] = res[order.id]['amount_untaxed'] + res[order.id]['amount_tax']
		return res
sale_order()


class sale_order_line(osv.osv):

	_name = 'sale.order.line'
	_inherit = 'sale.order.line'
	_columns = {
		'TAX_percent' : fields.float('TAX_percent'),	
		'TAX_amount' : fields.float('TAX_amount'),
		'Line_total' : fields.float('Line_total'),		
			}			

sale_order_line()



