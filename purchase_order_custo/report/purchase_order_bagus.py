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

import time

from openerp.report import report_sxw

class purchase_order_custo(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(purchase_order_custo, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time, 
            'show_discount':self._show_discount,
            'date_month':self._date_month,
        })

    def _show_discount(self, uid, context=None):
        cr = self.cr
        try: 
            group_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'sale', 'group_discount_per_so_line')[1]
        except:
            return False
        return group_id in [x.id for x in self.pool.get('res.users').browse(cr, uid, uid, context=context).groups_id]
    def _date_month(self, datedetail):
       date = time.strptime(datedetail,'%Y-%m-%d')
       month = time.strftime('%d %B %Y', date)
       return month

report_sxw.report_sxw('report.purchase.order.custo', 'purchase.order', 'addons/purchase_order_custo/report/purchase_order_custo.rml', parser=purchase_order_custo)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

