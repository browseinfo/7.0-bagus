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

class sale_pay(osv.osv):
    _name = 'sale.pay'

    def _amount_pay(self, cr, uid, ids, field_name, arg, context=None):
        so_obj = self.pool.get('sale.order')
        res = {}
        data = self.browse(cr, uid, ids, context=context)
        for x in data:
            res[x.id] = {
                'amount':0.0
            }
            if x.so_id.amount_total and x.percent:
                amount = x.so_id.amount_total*x.percent/100
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
        'so_id': fields.many2one('sale.order', 'Order Reference'),
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
                if x.so_id.amount_total and x.percent:
                    v['amount'] = x.so_id.amount_total*x.percent/100
        return {'value': v}

sale_pay()

class stock_picking(osv.osv):
    _inherit = 'stock.picking'
    _columns = {
        'project': fields.char('Project'),
            }
stock_picking()


class stock_picking_out(osv.osv):
    _inherit = 'stock.picking.out'
    _columns = {
        'project': fields.char('Project'),
            }
stock_picking_out()

class account_invoice(osv.osv):
    _inherit = 'account.invoice'
    _columns = {
        'project': fields.char('Project'),
            }
account_invoice()

class sale_order(osv.osv):
    _inherit = 'sale.order'

    _columns = {
        'delivery_id': fields.many2one('sale.delivery', 'Delivery', select=True),
        'packing_id': fields.many2one('sale.packaging', 'Packing', select=True),
        'payment_id': fields.many2one('sale.payment', 'Payment', select=True),
        'pac_file' : fields.binary('payment lines Document', help="Download document with '.xls' Extension"),
        'destination_id': fields.many2one('sale.destination', 'Destination', select=True),
        'inspection_id': fields.many2one('sale.inspection', 'Inspection'),
        'validity': fields.char('Validity'),
        'image': fields.binary("Logo", help="This field holds the image used as logo, limited to 1024x1024px."),
        'payment_line': fields.one2many('sale.pay', 'so_id', 'Order Payments', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}),
        'project': fields.char('Project'),
    }

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
            'project': order.project,
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
            'user_id': order.user_id and order.user_id.id or False
        }

        # Care for deprecated _inv_get() hook - FIXME: to be removed after 6.1
        invoice_vals.update(self._inv_get(cr, uid, order, context=context))
        return invoice_vals

    def _prepare_order_picking(self, cr, uid, order, context=None):
        pick_name = self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.out')
        return {
            'name': pick_name,
            'origin': order.name,
            'date': self.date_to_datetime(cr, uid, order.date_order, context),
            'type': 'out',
            'project': order.project,
            'state': 'auto',
            'move_type': order.picking_policy,
            'sale_id': order.id,
            'partner_id': order.partner_shipping_id.id,
            'note': order.note,
            'invoice_state': (order.order_policy=='picking' and '2binvoiced') or 'none',
            'company_id': order.company_id.id,
        }

    def generate_payment_lines (self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        rec_list = ['name','percent','due_date','amount','so_id']
        file_path = join(addons.get_module_resource('sale_bagus_improvememt'),'files')
        record_obj = self.browse(cr, uid, ids[0], context)
        record_ids = record_obj.payment_line
        record_id = []
        so = ''

        for rec_id in record_ids:
            record_id.append(rec_id.id)
        record_line = self.pool.get('sale.pay').read(cr, uid, record_id, context=context)
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
                if list_item == 'so_id':
                    so = rec_line.get('so_id') and rec_line['so_id'][1]
                    ws.get_sheet(0).write(0, 1, rec_line.get('so_id') and rec_line['so_id'][1], style1)
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
        n = so and ("%s.xls" % so) or 'undefined.xls'
        ws.save(join(file_path, n))
        file = StringIO.StringIO()
        out = ws.save(file)
        self.write(cr, uid, ids, {'pac_file': base64.encodestring(file.getvalue())})
        return True

    def print_quotation(self, cr, uid, ids, context=None):
        '''
        This function prints the sales order and mark it as sent, so that we can see more easily the next step of the workflow
        '''
        assert len(ids) == 1, 'This option should only be used for a single id at a time'
        wf_service = netsvc.LocalService("workflow")
        wf_service.trg_validate(uid, 'sale.order', ids[0], 'quotation_sent', cr)
        datas = {
                 'model': 'sale.order',
                 'ids': ids,
                 'form': self.read(cr, uid, ids[0], context=context),
        }
        return {'type': 'ir.actions.report.xml', 'report_name': 'sale.order.bagus', 'datas': datas, 'nodestroy': True}


sale_order()

class sale_delivery(osv.osv):
    _name = 'sale.delivery'

    _columns = {
        'name': fields.char('Name'),
        'description': fields.char('Description'),
    }

sale_delivery()

class sale_packaging(osv.osv):
    _name = 'sale.packaging'

    _columns = {
        'name': fields.char('Name'),
        'description': fields.char('Description'),
    }

sale_packaging()

class sale_payment(osv.osv):
    _name = 'sale.payment'

    _columns = {
        'name': fields.char('Name'),
        'description': fields.char('Description'),
    }

sale_payment()

class sale_destination(osv.osv):
    _name = 'sale.destination'

    _columns = {
        'name': fields.char('Name'),
        'description': fields.char('Description'),
    }

sale_destination()

class sale_inspection(osv.osv):
    _name = 'sale.inspection'

    _columns = {
        'name': fields.char('Name'),
        'description': fields.char('Description'),
    }

sale_inspection()

#######################################################################################
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
