# -*- coding: utf-8 -*-
##############################################################################
#
#    Sales and Account Invoice Discount Management
#    Copyright (C) 2004-2010 BrowseInfo(<http://www.browseinfo.in>).
#    $autor:
#   
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import osv, fields
#from twisted.application.strports import _DEFAULT
import openerp.addons.decimal_precision as dp

class sale_order(osv.osv):
    _inherit = 'sale.order'

    def _amount_all_total(self, cr, uid, ids, field_name, arg, context=None):
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
            disc_amt = order.discount_amount
            disc_method = order.discount_method
            new_amt = 0.0
            for line in order.order_line:
                val1 += line.price_subtotal
                val += self._amount_line_tax(cr, uid, line, context=context)
            if disc_method =='fix':
                new_amt = disc_amt
            if disc_method =='per':
                new_amt = val1 * disc_amt / 100
            res[order.id]['amount_tax'] = cur_obj.round(cr, uid, cur, val)
            res[order.id]['amount_untaxed'] = cur_obj.round(cr, uid, cur, val1)
            res[order.id]['amount_total'] = res[order.id]['amount_untaxed'] + res[order.id]['amount_tax'] - new_amt
            self.write(cr, uid, ids, {'discount_amt': new_amt})
        return res

    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('sale.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()

    _columns = {
        'hide_discount': fields.boolean('Hide Discount'),
        'discount_method': fields.selection([('fix', 'Fixed'),('per', 'Percentage')], 'Discount Method'),
        'discount_amount': fields.float('Discount Amount'),
        'discount_amt': fields.float('- Discount', readonly=True,),
        'order_line': fields.one2many('sale.order.line', 'order_id', 'Order Lines', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}),
        'amount_untaxed': fields.function(_amount_all_total, digits_compute=dp.get_precision('Account'), string='Untaxed Amount',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The amount without tax.", track_visibility='always'),
        'amount_tax': fields.function(_amount_all_total, digits_compute=dp.get_precision('Account'), string='Taxes',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The tax amount."),
        'amount_total': fields.function(_amount_all_total, digits_compute=dp.get_precision('Account'), string='Total',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The total amount."),
    }
    
    def discount_set(self, cr, uid, ids, context=None):
        amount_total = self.browse(cr, uid, ids, context=context)[0].amount_untaxed
        disc_amt = self.browse(cr, uid, ids, context=context)[0].discount_amount
        disc_methd = self.browse(cr, uid, ids, context=context)[0].discount_method
        new_amt = 0.0
        new_amtt = 0.0
        res = {}
        if not disc_amt or disc_amt == 0.0:
            self.write(cr, uid, ids, {'discount_amt': 0.0, 'discount_amount': 0.0, 'hide_discount': False})
            
        if disc_amt:
            if disc_methd =='fix':
                new_amt = amount_total - disc_amt
                new_amtt = disc_amt
                self.write(cr, uid, ids, {'discount_amt': new_amtt, 'hide_discount': True})
            elif disc_methd =='per':
                new_amtt = amount_total * disc_amt / 100
                new_amt = amount_total * (1 - (disc_amt or 0.0) / 100.0)
                self.write(cr, uid, ids, {'discount_amt': new_amtt, 'hide_discount': True})
            else:
                self.write(cr, uid, ids, {'discount_amt': 0.0, 'discount_amount': 0.0, 'hide_discount': False})
            sql = "update sale_order set amount_total=%s where id=%s"
            cr.execute(sql, (new_amt, ids[0]))
        return True

    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        """Prepare the dict of values to create the new invoice for a
           sales order. This method may be overridden to implement custom
           invoice generation (making sure to call super() to establish
           a clean extension chain).

           :param browse_record order: sale.order record to invoice
           :param list(int) line: list of invoice line IDs that must be
                                  attached to the invoice
           :return: dict of value to create() the invoice
        """
        if context is None:
            context = {}
        journal_ids = self.pool.get('account.journal').search(cr, uid,
            [('type', '=', 'sale'), ('company_id', '=', order.company_id.id)],
            limit=1)
        if not journal_ids:
            raise osv.except_osv(_('Error!'),
                _('Please define sales journal for this company: "%s" (id:%d).') % (order.company_id.name, order.company_id.id))
        invoice_vals = {
            'name': order.client_order_ref or '',
            'origin': order.name,
            'type': 'out_invoice',
            'reference': order.client_order_ref or order.name,
            'account_id': order.partner_id.property_account_receivable.id,
            'partner_id': order.partner_invoice_id.id,
            'journal_id': journal_ids[0],
            'invoice_line': [(6, 0, lines)],
            'currency_id': order.pricelist_id.currency_id.id,
            'comment': order.note,
            'payment_term': order.payment_term and order.payment_term.id or False,
            'fiscal_position': order.fiscal_position.id or order.partner_id.property_account_position.id,
            'date_invoice': context.get('date_invoice', False),
            'company_id': order.company_id.id,
            'discount_method': order.discount_method,
            'discount_amount': order.discount_amount,
            'user_id': order.user_id and order.user_id.id or False
        }

        # Care for deprecated _inv_get() hook - FIXME: to be removed after 6.1
        invoice_vals.update(self._inv_get(cr, uid, order, context=context))
        return invoice_vals

sale_order()

class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'
    
    def _amount_line(self, cr, uid, ids, field_name, arg, context=None):
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            price = line.price_unit
            if line.discount_method =='fix':
                price = line.price_unit - line.discount
            if line.discount_method =='per':   
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = tax_obj.compute_all(cr, uid, line.tax_id, price, line.product_uom_qty, line.product_id, line.order_id.partner_id)
            cur = line.order_id.pricelist_id.currency_id
            res[line.id] = cur_obj.round(cr, uid, cur, taxes['total'])
        return res
    
    _columns = {
        'discount_method': fields.selection([('fix', 'Fixed'),('per', 'Percentage')], 'Discount Method'),
        'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute= dp.get_precision('Account')),
        }

sale_order_line()

class account_invoice(osv.osv):
    _inherit = 'account.invoice'

    def _amount_all(self, cr, uid, ids, name, args, context=None):
        res = {}
        for invoice in self.browse(cr, uid, ids, context=context):
            res[invoice.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0
            }
            val1 = 0.0
            for line in invoice.invoice_line:
                val1 += line.price_subtotal
                res[invoice.id]['amount_untaxed'] += line.price_subtotal
            disc_amt = invoice.discount_amount
            disc_method = invoice.discount_method
            new_amt = 0.0
            if disc_method =='fix':
                new_amt = disc_amt
            if disc_method =='per':
                new_amt = val1 * disc_amt / 100

            for line in invoice.tax_line:
                res[invoice.id]['amount_tax'] += line.amount
            res[invoice.id]['amount_total'] = res[invoice.id]['amount_tax'] + res[invoice.id]['amount_untaxed'] - new_amt
            self.write(cr, uid, ids, {'discount_amt': new_amt})
        return res

    def _get_invoice_tax(self, cr, uid, ids, context=None):
        result = {}
        for tax in self.pool.get('account.invoice.tax').browse(cr, uid, ids, context=context):
            result[tax.invoice_id.id] = True
        return result.keys()

    def _get_invoice_line(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('account.invoice.line').browse(cr, uid, ids, context=context):
            result[line.invoice_id.id] = True
        return result.keys()


    _columns = {
        'discount_method': fields.selection([('fix', 'Fixed'),('per', 'Percentage')], 'Discount Method'),
        'discount_amount': fields.float('Discount Amount'),
        'discount_amt': fields.float('- Discount', readonly=True,),
        'amount_untaxed': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Subtotal', track_visibility='always',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
            },
            multi='all'),
        'amount_tax': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Tax',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
            },
            multi='all'),
        'amount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
            },
            multi='all'),
      }

    def discount_set(self, cr, uid, ids, context=None):
        amount_total = self.browse(cr, uid, ids, context=context)[0].amount_untaxed
        disc_amt = self.browse(cr, uid, ids, context=context)[0].discount_amount
        disc_methd = self.browse(cr, uid, ids, context=context)[0].discount_method
        new_amt = 0.0
        new_amtt = 0.0
        if disc_amt:
            if disc_methd =='fix':
                new_amt = amount_total - disc_amt
                new_amtt = disc_amt
            if disc_methd =='per':
                new_amtt = amount_total * disc_amt / 100
                new_amt = amount_total * (1 - (disc_amt or 0.0) / 100.0)
            self.write(cr, uid, ids, {'discount_amt': new_amtt})
            sql = "update account_invoice set amount_total=%s where id=%s"
            cr.execute(sql, (new_amt, ids[0]))
        return True

account_invoice()

class account_invoice_line(osv.osv):
    _inherit = 'account.invoice.line'

    def _amount_line(self, cr, uid, ids, prop, unknow_none, unknow_dict):
        res = {}
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        for line in self.browse(cr, uid, ids):
            print "============line.discount_method======", line.discount_method
            price = line.price_unit
            if line.discount_method =='fix':
                price = line.price_unit - line.discount
            if line.discount_method =='per':
                price = line.price_unit * (1-(line.discount or 0.0)/100.0)
            taxes = tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, price, line.quantity, product=line.product_id, partner=line.invoice_id.partner_id)
            res[line.id] = taxes['total']
            if line.invoice_id:
                cur = line.invoice_id.currency_id
                res[line.id] = cur_obj.round(cr, uid, cur, res[line.id])
        return res

    _columns = {
        'discount_method': fields.selection([('fix', 'Fixed'),('per', 'Percentage')], 'Discount Method'),
         'price_subtotal': fields.function(_amount_line, string='Amount', type="float",
            digits_compute= dp.get_precision('Account'), store=True),
        }
    
account_invoice_line()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
