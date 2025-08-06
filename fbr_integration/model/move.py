import json
import re
import requests
from docutils.nodes import reference

from odoo import _, api, fields, models
import qrcode
import base64
from io import BytesIO
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError



class AccountMove(models.Model):
    _inherit = "account.move"

    sent_to_fbr = fields.Boolean(string="Sent to FBR", default=False)
    fbr_invoice_number = fields.Char('FBR Verified Invoice Number' , readonly=True)
    fbr_qr_code = fields.Binary("FBR QR Code", compute="_compute_fbr_qr_code", store=True)
    scenario_id = fields.Many2one('fbr.scenario')
    show_fbr_sandbox_fields = fields.Boolean(
        compute='_compute_show_fbr_sandbox_fields',
        store=False
    )

    @api.depends()
    def _compute_show_fbr_sandbox_fields(self):
        config = self.env['fbr.config'].search([], limit=1)
        sandbox_mode = config.state == 'sandbox' if config else False
        for record in self:
            record.show_fbr_sandbox_fields = sandbox_mode


    @api.depends('name', 'invoice_date', 'amount_total', 'partner_id.vat')
    def _compute_fbr_qr_code(self):
        for move in self:
            if move.move_type in ['out_invoice', 'out_refund'] and move.fbr_invoice_number:  # Sales Invoices
                data = f"Invoice Number: {move.fbr_invoice_number}\nDate: {move.invoice_date}\nAmount: {move.amount_total}\nCustomer NTN: {move.partner_id.vat or 'N/A'}"
                qr = qrcode.QRCode(version=1, box_size=10, border=5)
                qr.add_data(data)
                qr.make(fit=True)

                img = qr.make_image(fill='black', back_color='white')
                buffer = BytesIO()
                img.save(buffer, format='PNG')
                move.fbr_qr_code = base64.b64encode(buffer.getvalue())
            else:
                move.fbr_qr_code = False

    def button_draft(self):
        res = super().button_draft()
        self.fbr_invoice_number = False
        for line in self.invoice_line_ids:
            line.fbr_invoice_number = False
        return res

    def get_rate(self):
        for rec in self:
            for line in rec.invoice_line_ids:
                rate_data = self._get_fbr_rate_details(
                    line.sale_type_id.type_id,
                    self.invoice_date.strftime('%d-%b-%Y'),
                    self.company_id.partner_id.province_id.state_province_code if self.move_type == 'out_invoice' else self.partner_id.province_id.state_province_code
                )
                line.rate = str(rate_data['rate_desc'])


    def _get_fbr_rate_details(self, trans_type_id, date_str, origination_supplier=1):
        """
        Fetch rate ID, description, value, and corresponding SRO schedule from FBR APIs
        """
        config = self.env['fbr.config'].search([], order='id DESC', limit=1)
        if not config or not config.token:
            raise UserError("FBR Token not configured. Please set it in FBR settings.")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.token}"
        }

        # STEP 1: Fetch Rate Info
        rate_url = (
            f"https://gw.fbr.gov.pk/pdi/v2/SaleTypeToRate"
            f"?date={date_str}&transTypeId={trans_type_id}&originationSupplier={origination_supplier}"
        )

        rate_response = requests.get(rate_url, headers=headers)
        if rate_response.status_code != 200:
            raise UserError(f"Failed to fetch FBR rate. Status: {rate_response.status_code} - {rate_response.text}")

        try:
            rate_data = rate_response.json()
            if not isinstance(rate_data, list) or not rate_data:
                raise UserError("FBR returned empty rate response.")
        except Exception as e:
            raise UserError(f"Invalid rate response from FBR: {str(e)}")

        rate = rate_data[0]
        rate_id = str(rate.get("ratE_ID"))
        rate_value = rate.get("ratE_VALUE")
        rate_desc = rate.get("ratE_DESC")

        # STEP 2: Fetch SRO Schedule based on rate_id
        #sro_url = (
        #    f"https://gw.fbr.gov.pk/pdi/v1/SroSchedule"
        #    f"?rate_id={rate_id}&date={date_str}&orgination_supplier_csv={origination_supplier}"
        #)
        #sro_response = requests.get(sro_url, headers=headers)
        #if sro_response.status_code != 200:
        #    raise UserError(f"Failed to fetch SRO schedule. Status: {sro_response.status_code} - {sro_response.text}")

        #try:
        #    sro_data = sro_response.json()
        #    sro_schedule = sro_data[0]["srO_DESC"] if sro_data else ""
        #except Exception as e:
        #    raise UserError(f"Invalid SRO response from FBR: {str(e)}")

        # Final return
        return {
            "rate_id": rate_id,
            "rate_value": rate_value,
            "rate_desc": rate_desc,
            #"sro_schedule": sro_schedule
        }

    def prepare_fbr_invoice_payload(self):
        self.ensure_one()
        type = False
        reference = False
        fbr_invoice_number = False
        if self.move_type == "out_invoice":
            type = "Sale Invoice"
        elif self.move_type == 'in_invoice':
            type = "Purchase Invoice"
        elif self.move_type == 'out_refund':
            type = "Credit Note"
            match = re.search(r'\bINV/\d{4}/\d{5}\b', self.ref)
            if match:
                reference = match.group()
        elif self.move_type == 'in_refund':
            type = "Debit Note"
            match = re.search(r'\bINV/\d{4}/\d{5}\b', self.ref)
            if match:
                reference = match.group()
        move = self.env['account.move'].search([('name','=',reference)])
        if move:
            fbr_invoice_number = move.fbr_invoice_number
        else:
            fbr_invoice_number = self.name

        data = {
            "invoiceType": type,
            "invoiceDate": str(self.invoice_date),
            # Seller Info
            "sellerNTNCNIC": self.company_id.vat if self.move_type == 'out_invoice' else self.partner_id.vat,
            "sellerBusinessName": self.company_id.partner_id.name if self.move_type == 'out_invoice' else self.partner_id.name,
            "sellerProvince": self.company_id.partner_id.province_id.state_province_desc if self.move_type == 'out_invoice' else self.partner_id.province_id.state_province_desc,
            "sellerAddress": self.company_id.partner_id.street if self.move_type == 'out_invoice' else self.partner_id.street,

            # Buyer Info
            "buyerNTNCNIC": self.partner_id.vat if self.move_type == 'out_invoice' else self.company_id.vat,
            "buyerBusinessName": self.partner_id.name if self.move_type == 'out_invoice' else self.company_id.partner_id.name,
            "buyerProvince": self.partner_id.province_id.state_province_desc if self.move_type == 'out_invoice' else self.company_id.partner_id.province_id.state_province_desc,
            "buyerAddress": self.partner_id.street if self.move_type == 'out_invoice' else self.company_id.partner_id.street,
            "buyerRegistrationType": self.partner_id.buyer_type_id.name if self.move_type == 'out_invoice' else self.company_id.partner_id.buyer_type_id.name,
            #"invoiceRefNo":str(fbr_invoice_number) if self.move_type in ('out_refund', 'in_refund') else "",
            "invoiceRefNo": str(fbr_invoice_number),
            "items": [
                {
                    "hsCode": line.hsCode,
                    "productDescription": line.name,
                    "rate": str(line.tax_ids[0].name) if line.tax_ids else 0,
                    "uoM": str(line.unit_of_measure),  # Adjust as needed
                    "quantity": line.quantity,
                    "totalValues": int(line.price_total),
                    "valueSalesExcludingST": int(line.price_subtotal or 0),
                    "fixedNotifiedValueOrRetailPrice": int(line.mrp*line.quantity or 0),
                    "salesTaxApplicable": int(float(line.salesTaxApplicable)or 0),
                    "salesTaxWithheldAtSource": int(float(line.salesTaxWithheldAtSource) or 0),
                    "extraTax": int(float(line.extraTax)) if line.tax_ids[0].amount >= 17 else "",
                    "furtherTax": int(float(line.furtherTax) or 0),
                    "sroScheduleNo": line.sroScheduleNo,
                    "fedPayable": int(float(line.fedPayable) or 0),
                    "discount": int(line.discount or 0),
                    "saleType": str(line.sale_type_id.name),
                    "sroItemSerialNo": line.sroItemSerialNo or ""
                }
                for line in self.invoice_line_ids

            ]
        }
        if self.show_fbr_sandbox_fields:
            data["scenarioId"] = str(self.scenario_id.name)
        return data


    def action_post(self):
        for rec in self:
            for line in rec.invoice_line_ids:
                item_required_fields = [
                    (line.hsCode, 'HS Code'),
                    (line.name, 'Product Description'),
                    (line.tax_ids, 'Tax Rate'),
                    (line.quantity, 'Quantity'),
                    (line.price_total, 'Total Value'),
                    (line.price_subtotal, 'Sales Value Excluding ST'),
                    (line.salesTaxApplicable, 'Sales Tax Applicable'),
                    (line.salesTaxWithheldAtSource, 'Sales Tax Withheld at Source'),
                    (line.sale_type_id, 'Sale Type')
                ]
                for value, label in item_required_fields:
                    # Check for empty, None, or False
                    if not value:
                        raise ValidationError(
                            f"Missing required field '{label}' in invoice line for product: {line.product_id.display_name or 'Unknown Product'}")

        # Your existing logic here, e.g.:
        return super().action_post()

    def send_to_fbr(self):
        self.ensure_one()

        # Validation for required fields
        required_fields = [
            ('invoice_date', 'Invoice Date'),
            ('company_id.vat', 'Seller NTN/CNIC'),
            ('partner_id.vat', 'Buyer NTN/CNIC'),
            ('company_id.partner_id.name', 'Seller Business Name'),
            ('partner_id.name', 'Buyer Business Name'),
            ('company_id.partner_id.province_id.state_province_desc', 'Seller Province'),
            ('partner_id.province_id.state_province_desc', 'Buyer Province'),
            ('company_id.partner_id.street', 'Seller Address'),
            ('partner_id.street', 'Buyer Address')
        ]

        # Check header level required fields
        missing_fields = []
        for field, label in required_fields:
            if not self._get_field_value(field):
                missing_fields.append(label)

        # Check line items required fields

        for line in self.invoice_line_ids:
            item_required_fields = [
                (line.hsCode, 'HS Code'),
                (line.name, 'Product Description'),
                (line.tax_ids, 'Tax Rate'),
                (line.quantity, 'Quantity'),
                (line.price_total, 'Total Values'),
                (line.price_subtotal, 'Sales Value Excluding ST'),
                (line.salesTaxApplicable, 'Sales Tax Applicable'),
                (line.salesTaxWithheldAtSource, 'Sales Tax Withheld at Source'),
                (line.sale_type_id, 'Sale Type')
            ]

            for field, label in item_required_fields:
                if not field:
                    missing_fields.append(f"{label} (Line: {line.name or 'Unnamed'})")

        if missing_fields:
            raise ValidationError(
                "The following required fields are missing:\n\n• " +
                "\n• ".join(missing_fields) +
                "\n\nPlease fill all required fields before submitting to FBR."
            )
        config = self.env['fbr.config'].search([], order='id DESC',limit=1)
        # Prepare and send payload if validation passes
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer "+config.token+""
        }

        payload = self.prepare_fbr_invoice_payload()
        if config.state == 'sandbox':
            url = "https://gw.fbr.gov.pk/di_data/v1/di/postinvoicedata_sb"
        else:
            url = "https://gw.fbr.gov.pk/di_data/v1/di/postinvoicedata"
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()  # Raises exception for 4XX/5XX responses

            decoded_data = response.json()
            invoice_number = decoded_data.get('invoiceNumber')

            if not invoice_number:
               # raise ValidationError("FBR response did not contain an invoice number")
                  raise ValidationError(str(response.content))
            # Store the invoice number or process the successful response
            self.fbr_invoice_number = invoice_number
            for i in decoded_data.get('validationResponse').get('invoiceStatuses'):
                for line in self.invoice_line_ids:
                    if not line.fbr_invoice_number:
                        line.fbr_invoice_number = i.get('invoiceNo')
                        break
            self.sent_to_fbr = True
            self._compute_fbr_qr_code()



        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to submit invoice to FBR: {str(e)}"
            if hasattr(e, 'response') and e.response.text:
                error_msg += f"\nFBR Response: {e.response.text}"
            raise ValidationError(error_msg)

    def _get_field_value(self, field_path):
        """Helper method to get nested field values safely"""
        obj = self
        for part in field_path.split('.'):
            if not obj:
                return None
            obj = getattr(obj, part, None)
        return obj