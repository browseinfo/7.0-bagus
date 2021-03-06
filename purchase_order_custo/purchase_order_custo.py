# -*- coding: utf-8 -*-
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

from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.tools.translate import _

from openerp.osv import fields, osv
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp

from openerp import netsvc
from os.path import join
from tools.translate import _
from xlwt import Workbook, easyxf, Formula
import StringIO
import base64
import xlrd
from xlrd import open_workbook
from xlutils.copy import copy
import addons

class purchase_pay(osv.osv):
    _name = 'purchase.pay'

    def _amount_pay(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        data = self.browse(cr, uid, ids, context=context)
        for x in data:
            res[x.id] = {
                'amount':0.0
            }
            if x.po_id.amount_total and x.percent:
                amount = x.po_id.amount_total*x.percent/100
                res[x.id] = {
                'amount': amount
            }
        
        return res

    _columns = {
        'name': fields.char('Name'),
        'total1':fields.float('Total'),
        'percent': fields.float('   %   '),
        'amount': fields.function(_amount_pay, string='Amount', type="float", multi="payment"),
        'due_date': fields.date('Due Date'),
        'po_id': fields.many2one('purchase.order', 'Order Reference'),
    }

    def onchange_percent(self, cr, uid, ids, percent, context=None):
        v = {}
        res = {}
        if percent:
            data = self.browse(cr, uid, ids, context=context)
            for x in data:
                res[x.id] = {
                    'amount':0.0
                }
                if x.po_id.amount_total and x.percent:
                    v['amount'] = x.po_id.amount_total*x.percent/100
        return {'value': v}

purchase_pay()

class stock_picking_in(osv.osv):
    _inherit = 'stock.picking.in'
    _columns = {
        'project': fields.char('Project'),
            }
stock_picking_in()

class purchase_order(osv.osv):
    _inherit = 'purchase.order'

    _columns = {
        
        'destination_id': fields.many2one('purchase.destination', 'Destination', select=True),
        'cash_mark': fields.char('Cash Mark', size=50),
        'packing_id': fields.many2one('purchase.packaging', 'Packing', select=True),
        'pac_file' : fields.binary('payment lines Document', help="Download document with '.xls' Extension"),
        'delivery_date': fields.datetime('Delivery Date'),
        'delivery_id': fields.many2one('purchase.delivery', 'Delivery', select=True),
        'delivery_mark': fields.char('Delivery Terms', size=50),
        'payment_line': fields.one2many('purchase.pay', 'po_id', 'Order Payments', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}),
        'project': fields.char('Project'),
    }

    def _prepare_order_picking(self, cr, uid, order, context=None):
        return {
            'name': self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.in'),
            'origin': order.name + ((order.origin and (':' + order.origin)) or ''),
            'date': self.date_to_datetime(cr, uid, order.date_order, context),
            'partner_id': order.dest_address_id.id or order.partner_id.id,
            'invoice_state': '2binvoiced' if order.invoice_method == 'picking' else 'none',
            'type': 'in',
            'partner_id': order.dest_address_id.id or order.partner_id.id,
            'purchase_id': order.id,
            'company_id': order.company_id.id,
            'move_lines' : [],
            'project': order.project,
        }


    def action_invoice_create(self, cr, uid, ids, context=None):
        """Generates invoice for given ids of purchase orders and links that invoice ID to purchase order.
        :param ids: list of ids of purchase orders.
        :return: ID of created invoice.
        :rtype: int
        """
        res = False

        journal_obj = self.pool.get('account.journal')
        inv_obj = self.pool.get('account.invoice')
        inv_line_obj = self.pool.get('account.invoice.line')
        purchase_pay = self.pool.get('purchase.pay')
        po_ids = purchase_pay.search(cr, uid, [('po_id', '=', ids[0])], context=context)
        payments = purchase_pay.read(cr, uid, po_ids, ['percent', 'due_date'], context=context)

        if payments:
            for pay in payments:
                for order in self.browse(cr, uid, ids, context=context):
                    pay_acc_id = order.partner_id.property_account_payable.id
                    journal_ids = journal_obj.search(cr, uid, [('type', '=','purchase'),('company_id', '=', order.company_id.id)], limit=1)
                    if not journal_ids:
                        raise osv.except_osv(_('Error!'),
                                         _('Define purchase journal for this company: "%s" (id:%d).') % (order.company_id.name, order.company_id.id))

                    # generate invoice line correspond to PO line and link that to created invoice (inv_id) and PO line
                    inv_lines = []
                    for po_line in order.order_line:
                        acc_id = self._choose_account_from_po_line(cr, uid, po_line, context=context)
                        inv_line_data = self._prepare_inv_line(cr, uid, acc_id, po_line, context=context)
                        inv_line_data['price_unit'] = inv_line_data['price_unit'] * pay['percent'] / 100
                        inv_line_data['name'] += "\n(" + _("Advance of %s %%") % (pay['percent']) + ")"
                        inv_line_id = inv_line_obj.create(cr, uid, inv_line_data, context=context)
                        inv_lines.append(inv_line_id)

                        po_line.write({'invoiced':True, 'invoice_lines': [(4, inv_line_id)]}, context=context)

                        # get invoice data and create invoice
                        inv_data = {
                                'name': order.partner_ref or order.name,
                                'reference': order.partner_ref or order.name,
                                'account_id': pay_acc_id,
                                'type': 'in_invoice',
                                'partner_id': order.partner_id.id,
                                'currency_id': order.pricelist_id.currency_id.id,
                                'journal_id': len(journal_ids) and journal_ids[0] or False,
                                'invoice_line': [(6, 0, inv_lines)],
                                'origin': order.name,
                                'project': order.project,
                                'fiscal_position': order.fiscal_position.id or False,
                                'payment_term': order.payment_term_id.id or False,
                                'company_id': order.company_id.id,
                                'date_due': pay['due_date']
                                }
                        inv_id = inv_obj.create(cr, uid, inv_data, context=context)
                        # compute the invoice
                        inv_obj.button_compute(cr, uid, [inv_id], context=context, set_total=True)
                        # Link this new invoice to related purchase order
                        order.write({'invoice_ids': [(4, inv_id )]}, context=context)
                        res = inv_id
        else:
            for order in self.browse(cr, uid, ids, context=context):
                pay_acc_id = order.partner_id.property_account_payable.id
                journal_ids = journal_obj.search(cr, uid, [('type', '=','purchase'),('company_id', '=', order.company_id.id)], limit=1)
                if not journal_ids:
                    raise osv.except_osv(_('Error!'),
                                         _('Define purchase journal for this company: "%s" (id:%d).') % (order.company_id.name, order.company_id.id))

                # generate invoice line correspond to PO line and link that to created invoice (inv_id) and PO line
                inv_lines = []
                for po_line in order.order_line:
                    acc_id = self._choose_account_from_po_line(cr, uid, po_line, context=context)
                    inv_line_data = self._prepare_inv_line(cr, uid, acc_id, po_line, context=context)
                    inv_line_id = inv_line_obj.create(cr, uid, inv_line_data, context=context)
                    inv_lines.append(inv_line_id)

                    po_line.write({'invoiced':True, 'invoice_lines': [(4, inv_line_id)]}, context=context)

                # get invoice data and create invoice
                inv_data = {
                                'name': order.partner_ref or order.name,
                                'reference': order.partner_ref or order.name,
                                'account_id': pay_acc_id,
                                'type': 'in_invoice',
                                'partner_id': order.partner_id.id,
                                'currency_id': order.pricelist_id.currency_id.id,
                                'journal_id': len(journal_ids) and journal_ids[0] or False,
                                'invoice_line': [(6, 0, inv_lines)],
                                'origin': order.name,
                                'project': order.project,
                                'fiscal_position': order.fiscal_position.id or False,
                                'payment_term': order.payment_term_id.id or False,
                                'company_id': order.company_id.id,
                            }
                inv_id = inv_obj.create(cr, uid, inv_data, context=context)

                # compute the invoice
                inv_obj.button_compute(cr, uid, [inv_id], context=context, set_total=True)

                # Link this new invoice to related purchase order
                order.write({'invoice_ids': [(4, inv_id)]}, context=context)
                res = inv_id

        return res

    def view_invoice(self, cr, uid, ids, context=None):
        '''
        This function returns an action that display existing invoices of given sales order ids. It can either be a in a list or in a form view, if there is only one invoice to show.
        '''
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')

        result = mod_obj.get_object_reference(cr, uid, 'account', 'action_invoice_tree1')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        #compute the number of invoices to display
        inv_ids = []
        for po in self.browse(cr, uid, ids, context=context):
            inv_ids += [invoice.id for invoice in po.invoice_ids]
        #choose the view_mode accordingly
        if len(inv_ids)>1:
            result['domain'] = "[('id','in',["+','.join(map(str, inv_ids))+"])]"
        else:
            res = mod_obj.get_object_reference(cr, uid, 'account', 'invoice_form')
            result['views'] = [(res and res[1] or False, 'form')]
            result['res_id'] = inv_ids and inv_ids[0] or False
        return result  

    def generate_payment_lines (self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        rec_list = ['name','percent','due_date','amount','po_id']
        file_path = join(addons.get_module_resource('purchase_order_custo'),'files')
        record_obj = self.browse(cr, uid, ids[0], context)
        record_ids = record_obj.payment_line
        record_id = []
        po = ''

        for rec_id in record_ids:
            record_id.append(rec_id.id)
        record_line = self.pool.get('purchase.pay').read(cr, uid, record_id, context=context)
        if not record_line:
            raise osv.except_osv(_('Warning!'), _('No payment lines defined!'))

        wb = xlrd.open_workbook(join(file_path,'format.xls'), encoding_override="cp1252", formatting_info=True)

        ws = copy(wb)
        row = 1
        column = 0
        style = easyxf(
                    'align: horizontal left , vertical center;font: bold on;font:height 250;border: right double, bottom double,left double,top double;',
                )
        style1 = easyxf(
                    'align: horizontal center , vertical center;font:height 250;',
                )
        style2 = easyxf(
                    'align: horizontal left , vertical center;font:height 250;',
                )
        style3 = easyxf(
                    'align: horizontal right , vertical center;font:height 250;',
                )

        for rec_line in record_line:
            row +=1 
            column = 1
            for list_item in rec_list:
                if list_item == 'po_id':
                    po = rec_line.get('po_id') and rec_line['po_id'][1]
                    ws.get_sheet(0).write(0, 1, rec_line.get('po_id') and rec_line['po_id'][1], style1)
                elif list_item == 'amount':
                    ws.get_sheet(0).write(row, column, str(rec_line[list_item]), style3)
                elif list_item == 'due_date':
                    ws.get_sheet(0).write(row, column, rec_line[list_item], style1)
                elif list_item == 'percent':
                    ws.get_sheet(0).write(row, column, str(rec_line[list_item]) + '%', style1)
                else:
                    ws.get_sheet(0).write(row, column, rec_line[list_item], style2)
                column += 1
        row = row + 10 
        n = po and ("%s.xls" % po) or 'undefined.xls'
        ws.save(join(file_path, n))
        file = StringIO.StringIO()
        out = ws.save(file)
        self.write(cr, uid, ids, {'pac_file': base64.encodestring(file.getvalue())})
        return True


    def print_quotation(self, cr, uid, ids, context=None):
        '''
        This function prints the request for quotation and mark it as sent, so that we can see more easily the next step of the workflow
        '''
        assert len(ids) == 1, 'This option should only be used for a single id at a time'
        wf_service = netsvc.LocalService("workflow")
        wf_service.trg_validate(uid, 'purchase.order', ids[0], 'send_rfq', cr)
        datas = {
                 'model': 'purchase.order',
                 'ids': ids,
                 'form': self.read(cr, uid, ids[0], context=context),
        }
        return {'type': 'ir.actions.report.xml', 'report_name': 'purchase.order.custo', 'datas': datas, 'nodestroy': True}



purchase_order()

class purchase_delivery(osv.osv):
    _name = 'purchase.delivery'

    _columns = {
        'name': fields.char('Name', required=True,),
        'description': fields.char('Description'),
    }

purchase_delivery()

class purchase_packaging(osv.osv):
    _name = 'purchase.packaging'

    _columns = {
        'name': fields.char('Name', required=True,),
        'description': fields.char('Description'),
    }

purchase_packaging()

class purchase_destination(osv.osv):
    _name = 'purchase.destination'

    _columns = {
        'name': fields.char('Name', required=True,),
        'description': fields.char('Description'),
    }

purchase_destination()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
