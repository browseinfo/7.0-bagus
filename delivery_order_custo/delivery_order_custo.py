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

from dateutil.relativedelta import relativedelta
from openerp.tools.float_utils import float_round
from openerp.osv import fields, osv
from datetime import datetime

class stock_picking(osv.osv):
    _inherit = 'stock.picking'

    _columns = {
        'vessal': fields.char('Vessal'),
        'from_to': fields.char('From'),
        'to': fields.char('To'),
        'trade_terms': fields.text('Trade Terms'),
        'issue_date': fields.date('Issue Date'),
        'consignee': fields.char('Consignee'),
        'lc_no': fields.char('L/C no'),
        'lc_issue_bank': fields.char('L/C issueing bank'),
        'type_select': fields.selection([('surat', 'Surat Jalan'), ('credit', 'Credit Note')], 'Type Select'),

    }

stock_picking()

class stock_picking_out(osv.osv):
    _inherit = "stock.picking.out"
    
    _columns = {
        'vessal': fields.char('Vessal'),
        'from_to': fields.char('From'),
        'to': fields.char('To'),
        'trade_terms': fields.text('Trade Terms'),
        'issue_date': fields.date('Issue Date'),
        'consignee': fields.char('Consignee'),
        'lc_no': fields.char('L/C no'),
        'lc_issue_bank': fields.char('L/C issueing bank'),
    }


stock_picking_out()


class sale_order(osv.osv):
    _inherit = "sale.order"

    def _prepare_order_picking(self, cr, uid, order, context=None):
        pick_name = self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.out')
        return {
            'name': pick_name,
            'origin': order.name,
            'date': self.date_to_datetime(cr, uid, order.date_order, context),
            'type': 'out',
            'type_select': 'surat',
            'state': 'auto',
            'move_type': order.picking_policy,
            'sale_id': order.id,
            'partner_id': order.partner_shipping_id.id,
            'note': order.note,
            'invoice_state': (order.order_policy=='picking' and '2binvoiced') or 'none',
            'company_id': order.company_id.id,
        }

sale_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
