from odoo import models, fields,api
from odoo.exceptions import ValidationError
import requests
import logging

_logger = logging.getLogger(__name__)

class SaleType(models.Model):
    _name = 'sale.type'

    type_id = fields.Char()
    name = fields.Char()

    @api.model
    def fetch_transaction_type_from_fbr(self):
        # config = self.env['fbr.config'].search([], order='id DESC', limit=1)
        config = self.env['fbr.config'].search([], order='id DESC', limit=1)
        if not config or not config.token or not config.token.strip():
            raise ValidationError("FBR Token is not configured. Please set it in FBR Configuration.")

        url = "https://gw.fbr.gov.pk/pdi/v1/transtypecode"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + config.token + ""
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            doc_types = response.json()

            for doc in doc_types:
                transaction_type_id = str(doc.get('transactioN_TYPE_ID'))
                desc = str(doc.get('transactioN_DESC'))

                existing = self.search([('type_id', '=', transaction_type_id)], limit=1)
                if existing:
                    # Only update if description has changed
                    if existing.doc_description != desc:
                        existing.write({'doc_description': desc})
                        _logger.info(f"Updated doc type: {transaction_type_id} - {desc}")
                else:
                    self.create({
                        'type_id': transaction_type_id,
                        'name': desc
                    })
                    _logger.info(f"Created new transaction type: {transaction_type_id} - {desc}")

            _logger.info("FBR Transaction Type sync completed.")

        except Exception as e:
            _logger.error(f"Error fetching transaction type from FBR: {e}")





class AccountTaxConfiguration(models.Model):
    _name = 'account.tax.configuration.custom'
    _description = 'Tax Accounts Configuration'

    sales_tax_id = fields.Many2one('account.tax', string='Sales Tax')
    sales_tax_account_id = fields.Many2one('account.account', string='Sales Tax Account')

    tax_withheld_id = fields.Many2one('account.tax', string='Tax Withheld')
    tax_withheld_account_id = fields.Many2one('account.account', string='Tax Withheld Account')

    extra_tax_id = fields.Many2one('account.tax', string='Extra Tax')
    extra_tax_account_id = fields.Many2one('account.account', string='Extra Tax Account')

    further_tax_id = fields.Many2one('account.tax', string='Further Tax')
    further_tax_account_id = fields.Many2one('account.account', string='Further Tax Account')

    fed_payable_account_id = fields.Many2one('account.account', string='Fed Payable Account')