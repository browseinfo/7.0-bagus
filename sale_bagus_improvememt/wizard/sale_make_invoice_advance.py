##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from openerp.osv import osv
from openerp.tools.translate import _

class sale_advance_payment_inv(osv.osv_memory):
    _inherit = "sale.advance.payment.inv"

    def create_invoices(self, cr, uid, ids, context=None):
        """ create invoices for the active sales orders """
        sale_obj = self.pool.get('sale.order')
        act_window = self.pool.get('ir.actions.act_window')
        wizard = self.browse(cr, uid, ids[0], context)
        sale_ids = context.get('active_ids', [])
        salepay_obj = self.pool.get('sale.pay')
        salepay_ids = salepay_obj.search(cr, uid, [('so_id', '=', sale_ids[0])])
        reads = salepay_obj.read(cr, uid, salepay_ids, ['percent', 'due_date'], context=context)
        if salepay_ids and wizard.advance_payment_method == 'all':
            inv_ids = []
            for r in reads:
                for sale in sale_obj.browse(cr, uid, sale_ids, context=context):
                    inv_lines = []
                    for line in sale.order_line:
                        inv_line_vals = self.pool.get('sale.order.line')._prepare_order_line_invoice_line(cr, uid, line, False, context=context)
                        inv_line_vals['price_unit'] = inv_line_vals['price_unit'] * r['percent'] / 100
                        inv_line_vals['name'] += "\n(" + _("Advance of %s %%") % (r['percent']) + ")"
                        inv_lines.append((0, 0, inv_line_vals))
                    inv_values = {
                        'name': sale.client_order_ref or sale.name,
                        'origin': sale.name,
                        'type': 'out_invoice',
                        'reference': False,
                        'account_id': sale.partner_id.property_account_receivable.id,
                        'partner_id': sale.partner_invoice_id.id,
                        'invoice_line': inv_lines,
                        'currency_id': sale.pricelist_id.currency_id.id,
                        'comment': '',
                        'payment_term': sale.payment_term.id,
                        'fiscal_position': sale.fiscal_position.id or sale.partner_id.property_account_position.id,
                        'date_due': r['due_date']
                    }
                    inv_ids.append(self._create_invoices(cr, uid, inv_values, sale.id, context=context))
            if context.get('open_invoices', False):
                return sale_obj.action_view_invoice(cr, uid, sale_ids, context=context)
            return {'type': 'ir.actions.act_window_close'}
        if not salepay_ids and wizard.advance_payment_method == 'all':
            res = sale_obj.manual_invoice(cr, uid, sale_ids, context)
            if context.get('open_invoices', False):
                return res
            return {'type': 'ir.actions.act_window_close'}

        if wizard.advance_payment_method == 'lines':
            # open the list view of sales order lines to invoice
            res = act_window.for_xml_id(cr, uid, 'sale', 'action_order_line_tree2', context)
            res['context'] = {
                'search_default_uninvoiced': 1,
                'search_default_order_id': sale_ids and sale_ids[0] or False,
            }
            return res
        assert wizard.advance_payment_method in ('fixed', 'percentage')

        inv_ids = []
        for sale_id, inv_values in self._prepare_advance_invoice_vals(cr, uid, ids, context=context):
            inv_ids.append(self._create_invoices(cr, uid, inv_values, sale_id, context=context))

        if context.get('open_invoices', False):
            return self.open_invoices( cr, uid, ids, inv_ids, context=context)
        return {'type': 'ir.actions.act_window_close'}

sale_advance_payment_inv()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
