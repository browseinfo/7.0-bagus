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

class account_invoice1(osv.osv):
    _inherit = 'account.invoice'

    _columns = {
        'vessal': fields.char('Vessal'),
        'formm': fields.char('From'),
        'to': fields.char('To'),
        'trade_terms': fields.text('Trade Terms'),
        'issue_date': fields.date('Issue Date'),
        'consignee': fields.char('Consignee'),
        'lc_no': fields.char('L/C no'),
        'lc_issue_bank': fields.char('L/C issueing bank'),
        'tax_code': fields.char('Tax Code'),
        'account_tax_custo_line': fields.one2many('account.tax.custo', 'invoice_id', 'Tax Report Line', readonly=True, states={'draft': [('readonly', False)]}),
    }

    def invoice_print(self, cr, uid, ids, context=None):
        '''
        This function prints the invoice and mark it as sent, so that we can see more easily the next step of the workflow
        '''
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        self.write(cr, uid, ids, {'sent': True}, context=context)
        datas = {
            'ids': ids,
            'model': 'account.invoice',
            'form': self.read(cr, uid, ids[0], context=context)
        }
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'account.invoice.custo',
            'datas': datas,
            'nodestroy' : True
        }

account_invoice1()

class res_partner_bank1(osv.osv):
    _inherit = 'res.partner.bank'

    _columns = {
        'branch': fields.char('Branch'),
    }

res_partner_bank1()

class account_tax_custo(osv.osv):
    _name = 'account.tax.custo'

    _columns = {
        'tarif': fields.integer('Tarif'),
        'dpp': fields.integer('DPP'),
        'ppn': fields.integer('PPn BM'),
        'invoice_id': fields.many2one('account.invoice', 'Invoice'),
    }

account_tax_custo()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
