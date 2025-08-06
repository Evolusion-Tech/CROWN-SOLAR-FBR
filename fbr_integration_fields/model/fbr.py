import requests
from odoo import models, fields,api
import logging
from odoo.exceptions import ValidationError


_logger = logging.getLogger(__name__)


from odoo import models, fields, api
from odoo.exceptions import ValidationError


class FbrScenario(models.Model):
    _name = 'fbr.scenario'

    name = fields.Char()

class FbrConfig(models.Model):
    _name = 'fbr.config'

    state = fields.Selection([('sandbox', 'Sandbox'), ('live', 'Live')])
    token = fields.Char()

    @api.model
    def create(self, vals):
        existing = self.search([], limit=1)
        if existing:
            raise ValidationError("Only one FBR Config record is allowed.")
        return super(FbrConfig, self).create(vals)

    def write(self, vals):
        # Allow updates to existing record, no issue
        return super(FbrConfig, self).write(vals)
class FbrUom(models.Model):
    _name = 'fbr.uom'

    uom_id = fields.Char()
    description = fields.Char()

    @api.model
    def fetch_uom_from_fbr(self):
        # config = self.env['fbr.config'].search([] , order='id DESC',limit=1)
        # url = "https://gw.fbr.gov.pk/pdi/v1/uom"
        # headers = {
        #     "Content-Type": "application/json",
        #     "Authorization": "Bearer "+config.token+""
        # }
        config = self.env['fbr.config'].search([], order='id DESC', limit=1)
        if not config or not config.token or not config.token.strip():
            raise ValidationError("FBR Token is not configured. Please set it in FBR Configuration.")

        url = "https://gw.fbr.gov.pk/pdi/v1/uom"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + config.token.strip()
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            item_codes = response.json()

            for item in item_codes:
                uom_id = str(item.get('uoM_ID'))
                desc = str(item.get('description'))

                existing = self.search([('uom_id', '=', uom_id)], limit=1)
                if existing:
                    # Only update if description has changed
                    if existing.description != desc:
                        existing.write({'description': desc})
                        _logger.info(f"Updated item code: {uom_id} - {desc}")
                else:
                    self.create({
                        'uom_id': uom_id,
                        'description': desc
                    })
                    _logger.info(f"Created new uom: {uom_id} - {desc}")

            _logger.info("FBR uom sync completed.")

        except Exception as e:
            _logger.error(f"Error fetching uom from FBR: {e}")



class FbrItemCode(models.Model):
    _name = 'fbr.item.code'

    hs_code = fields.Char()
    description = fields.Char()

    @api.model
    def fetch_item_code_from_fbr(self):
        # config = self.env['fbr.config'].search([], order='id DESC',limit=1)
        config = self.env['fbr.config'].search([], order='id DESC', limit=1)
        if not config or not config.token or not config.token.strip():
            raise ValidationError("FBR Token is not configured. Please set it in FBR Configuration.")
        url = "https://gw.fbr.gov.pk/pdi/v1/itemdesccode"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer "+config.token+""
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            item_codes = response.json()

            for item in item_codes:
                hs_code = str(item.get('Hs_Code'))
                desc = str(item.get('description'))

                existing = self.search([('hs_code', '=', hs_code)], limit=1)
                if existing:
                    # Only update if description has changed
                    if existing.description != desc:
                        existing.write({'description': desc})
                        _logger.info(f"Updated item code: {hs_code} - {desc}")
                else:
                    self.create({
                        'hs_code': hs_code,
                        'description': desc
                    })
                    _logger.info(f"Created new hs code: {hs_code} - {desc}")

            _logger.info("FBR Document Type sync completed.")

        except Exception as e:
            _logger.error(f"Error fetching document type from FBR: {e}")

class FbrDocumentType(models.Model):
    _name = 'fbr.document.type'

    doc_type_id = fields.Char()
    doc_description = fields.Char()

    @api.model
    def fetch_doc_type_from_fbr(self):
        # config = self.env['fbr.config'].search([], order='id DESC', limit=1)
        config = self.env['fbr.config'].search([], order='id DESC', limit=1)
        if not config or not config.token or not config.token.strip():
            raise ValidationError("FBR Token is not configured. Please set it in FBR Configuration.")

        url = " https://gw.fbr.gov.pk/pdi/v1/doctypecode"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer "+config.token+""
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            doc_types = response.json()

            for doc in doc_types:
                doc_type_id = str(doc.get('docTypeId'))
                desc = str(doc.get('docDescription'))

                existing = self.search([('doc_type_id', '=', doc_type_id)], limit=1)
                if existing:
                    # Only update if description has changed
                    if existing.doc_description != desc:
                        existing.write({'doc_description': desc})
                        _logger.info(f"Updated doc type: {doc_type_id} - {desc}")
                else:
                    self.create({
                        'doc_type_id': doc_type_id,
                        'doc_description': desc
                    })
                    _logger.info(f"Created new document type: {doc_type_id} - {desc}")

            _logger.info("FBR Document Type sync completed.")

        except Exception as e:
            _logger.error(f"Error fetching document type from FBR: {e}")


class FbrProvince(models.Model):
    _name = 'fbr.province'
    _rec_name = 'state_province_desc'

    state_province_code = fields.Char()
    state_province_desc = fields.Char()

    @api.model
    def fetch_provinces_from_fbr(self):
        # config = self.env['fbr.config'].search([], order='id DESC', limit=1)
        config = self.env['fbr.config'].search([], order='id DESC', limit=1)
        if not config or not config.token or not config.token.strip():
            raise ValidationError("FBR Token is not configured. Please set it in FBR Configuration.")

        url = "https://gw.fbr.gov.pk/pdi/v1/provinces"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer "+config.token+""
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            provinces = response.json()

            for prov in provinces:
                code = str(prov.get('stateProvinceCode'))
                desc = prov.get('stateProvinceDesc')

                existing = self.search([('state_province_code', '=', code)], limit=1)
                if existing:
                    # Only update if description has changed
                    if existing.state_province_desc != desc:
                        existing.write({'state_province_desc': desc})
                        _logger.info(f"Updated province: {code} - {desc}")
                else:
                    self.create({
                        'state_province_code': code,
                        'state_province_desc': desc
                    })
                    _logger.info(f"Created new province: {code} - {desc}")

            _logger.info("FBR provinces sync completed.")

        except Exception as e:
            _logger.error(f"Error fetching provinces from FBR: {e}")


