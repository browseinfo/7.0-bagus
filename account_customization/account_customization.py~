from openerp.osv import fields, osv

class invoice_type(osv.osv):
    _name = "invoice.type"
    _description = "Bank Journal Report"

    _columns = {
        'journal_id': fields.many2one('account.journal', string='Journals', required=True),
        'name': fields.char("Name" , required=True),
        'type': fields.selection([('normal', 'Normal'), ('tax', 'Tax')]),
    }
    
    _sql_constraints = [
        ('type_invoice_unique','unique(journal_id)','Journal must be unique per invoice type.!'),
    ]
invoice_type()

class account_invoice1(osv.osv):
    _inherit = "account.invoice"

    _columns = {
        'invoice_type_id': fields.many2one('invoice.type', 'Invoice Type' , required=True),
    }
    
    def onchange_invoice_type(self, cr, uid, ids, invoice_type_id, context=None):
       res = {}
       res['value'] = {}
       if not invoice_type_id:
           return {'value' : {'journal_id':False}}
       for rec in self.pool.get('invoice.type').browse(cr, uid, [invoice_type_id]):
           res['value'] = {'journal_id':rec.journal_id and rec.journal_id.id or False}
           print "Journal Value" , res , rec.journal_id
       return res

account_invoice1()
