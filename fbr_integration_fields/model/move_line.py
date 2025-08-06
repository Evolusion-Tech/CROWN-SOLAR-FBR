from odoo import _, api, fields, models,Command
from odoo.exceptions import ValidationError, UserError
from odoo.tools.float_utils import float_round
from collections import defaultdict
from odoo.tools.misc import clean_context, formatLang
import requests
from decimal import Decimal, ROUND_HALF_UP
import re



    # @api.onchange('hs_code')
    # def onchange_hs_code(self):
    #     for rec in self:
    #         if rec.hs_code:
    #             if not re.match(r'^\d{4}\.\d{4}$', rec.hs_code):
    #                 raise ValidationError(
    #                     "HS Code must be in the format 0000.0000 (4 digits, decimal, 4 digits)"
    #                 )
    #             config = self.env['fbr.config'].search([], order='id DESC', limit=1)
    #             formatted_hs_code = Decimal(str(rec.hs_code)).quantize(
    #                 Decimal('0.0000'),
    #                 rounding=ROUND_HALF_UP
    #             )
    #             # hs_code_without_commas = str(rec.hsCode).replace(',', '')
    #             url = "https://gw.fbr.gov.pk/pdi/v2/HS_UOM?hs_code=" + str(formatted_hs_code) + "&annexure_id=3"
    #             headers = {
    #                 "Content-Type": "application/json",
    #                 "Authorization": "Bearer " + config.token + ""
    #             }
    #
    #             response = requests.get(url, headers=headers, timeout=10)
    #             response.raise_for_status()
    #             uom = response.json()
    #             if uom:
    #                 uom_desc = uom[0]['description']
    #                 rec.fbr_unit_of_measure = uom_desc



class Product(models.Model):
    _inherit = 'product.template'

    hs_code = fields.Char(required=True, string="HS Code")
    purchase_request = fields.Boolean(string="Purchase Request")
    sale_type_id = fields.Many2one('sale.type', string="Sale Type")



    fbr_unit_of_measure = fields.Char()
    taxes_id = fields.Many2many('account.tax', 'product_taxes_rel', 'prod_id', 'tax_id',
                                help="Default taxes used when selling the product.", string='Customer Taxes',
                                domain=[('type_tax_use', '=', 'sale')],
                                default=lambda
                                    self: self.env.companies.account_sale_tax_id or self.env.companies.root_id.sudo().account_sale_tax_id,
                                required=True
                                )

    supplier_taxes_id = fields.Many2many('account.tax', 'product_supplier_taxes_rel', 'prod_id', 'tax_id',
                                         string='Vendor Taxes', help='Default taxes used when buying the product.',
                                         domain=[('type_tax_use', '=', 'purchase')],
                                         default=lambda
                                             self: self.env.companies.account_purchase_tax_id or self.env.companies.root_id.sudo().account_purchase_tax_id,
                                         required=True
                                         )
    is_fed = fields.Boolean()
    fed_per = fields.Float('Fed %')

    def fetch_fbr_uom(self):
        import re
        import requests
        from decimal import Decimal, ROUND_HALF_UP
        from odoo.exceptions import ValidationError

        for rec in self:
            if rec.hs_code:
                if not re.match(r'^\d{4}\.\d{4}$', rec.hs_code):
                    raise ValidationError("HS Code must be in the format 0000.0000 (4 digits, decimal, 4 digits)")

                config = self.env['fbr.config'].search([], order='id DESC', limit=1)
                if not config or not config.token:
                    raise ValidationError("FBR config or token not set.")

                formatted_hs_code = Decimal(str(rec.hs_code)).quantize(
                    Decimal('0.0000'),
                    rounding=ROUND_HALF_UP
                )

                url = f"https://gw.fbr.gov.pk/pdi/v2/HS_UOM?hs_code={formatted_hs_code}&annexure_id=3"
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {config.token}"
                }

                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()

                uom_data = response.json()
                if uom_data:
                    rec.fbr_unit_of_measure = uom_data[0].get('description')
    # @api.onchange('hs_code')
    # def onchange_hs_code(self):
    #     for rec in self:
    #         if rec.hs_code:
    #             config = self.env['fbr.config'].search([], order='id DESC', limit=1)
    #             formatted_hs_code = Decimal(str(rec.hs_code)).quantize(
    #                 Decimal('0.0000'),
    #                 rounding=ROUND_HALF_UP
    #             )
    #             # hs_code_without_commas = str(rec.hsCode).replace(',', '')
    #             url = "https://gw.fbr.gov.pk/pdi/v2/HS_UOM?hs_code=" + str(formatted_hs_code) + "&annexure_id=3"
    #             headers = {
    #                 "Content-Type": "application/json",
    #                 "Authorization": "Bearer " + config.token + ""
    #             }
    #
    #             response = requests.get(url, headers=headers, timeout=10)
    #             response.raise_for_status()
    #             uom = response.json()
    #             if uom:
    #                 uom_desc = uom[0]['description']
    #                 rec.fbr_unit_of_measure = uom_desc


""" @api.onchange('hs_code')
    def onchange_hs_code(self):
        for rec in self:
            if rec.hs_code:
                config = self.env['fbr.config'].search([], order='id DESC', limit=1)
                if not config or not config.token:
                    raise ValidationError("FBR token is missing. Please configure it first in FBR Configuration.")

                formatted_hs_code = Decimal(str(rec.hs_code)).quantize(
                    Decimal('0.0000'),
                    rounding=ROUND_HALF_UP
                )
                url = "https://gw.fbr.gov.pk/pdi/v2/HS_UOM?hs_code=" + str(formatted_hs_code) + "&annexure_id=3"
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer " + config.token
                }

                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                uom = response.json()
                if uom:
                    uom_desc = uom[0]['description']
                    rec.fbr_unit_of_measure = uom_desc"""


class BuyerType(models.Model):
    _name = 'buyer.type'

    name = fields.Char()

class Partner(models.Model):
    _inherit = 'res.partner'

    bussiness_name = fields.Char()
    street = fields.Char(required=True)
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict',
                               domain="[('country_id', '=?', country_id)]",required=True)
    vat = fields.Char(string='Tax ID', index=True,required=True,
                      help="The Tax Identification Number. Values here will be validated based on the country format. You can use '/' to indicate that the partner is not subject to tax.")
    buyer_type = fields.Selection([('Registered','Registered'),('unregistered','Unregistered')])
    buyer_type_id = fields.Many2one('buyer.type')
    province_id = fields.Many2one('fbr.province')

class AccountTax(models.Model):
    _inherit = 'account.tax'

    def _compute_taxes_for_single_line(self, base_line, handle_price_include=True, include_caba_tags=False,
                                       early_pay_discount_computation=None, early_pay_discount_percentage=None):
        #if base_line['record'].sale_type_id.name != '3rd Schedule Goods':
        orig_price_unit_after_discount = base_line['price_unit'] * (1 - (base_line['discount'] / 100.0))
        #else:
            #orig_price_unit_after_discount = base_line['record'].mrp * (1 - (base_line['discount'] / 100.0))
        price_unit_after_discount = orig_price_unit_after_discount
        taxes = base_line['taxes']._origin
        currency = base_line['currency'] or self.env.company.currency_id
        rate = base_line['rate']

        if early_pay_discount_computation in ('included', 'excluded'):
            remaining_part_to_consider = (100 - early_pay_discount_percentage) / 100.0
            price_unit_after_discount = remaining_part_to_consider * price_unit_after_discount

        if taxes:
            taxes_res = taxes.with_context(**base_line['extra_context']).compute_all(
                price_unit_after_discount,
                currency=currency,
                quantity=base_line['quantity'],
                product=base_line['product'],
                partner=base_line['partner'],
                is_refund=base_line['is_refund'],
                handle_price_include=base_line['handle_price_include'],
                include_caba_tags=include_caba_tags,
            )

            to_update_vals = {
                'tax_tag_ids': [Command.set(taxes_res['base_tags'])],
                'price_subtotal': taxes_res['total_excluded'],
                'price_total': taxes_res['total_included'],
            }

            if early_pay_discount_computation == 'excluded':
                new_taxes_res = taxes.with_context(**base_line['extra_context']).compute_all(
                    orig_price_unit_after_discount,
                    currency=currency,
                    quantity=base_line['quantity'],
                    product=base_line['product'],
                    partner=base_line['partner'],
                    is_refund=base_line['is_refund'],
                    handle_price_include=base_line['handle_price_include'],
                    include_caba_tags=include_caba_tags,
                )
                for tax_res, new_taxes_res in zip(taxes_res['taxes'], new_taxes_res['taxes']):
                    delta_tax = new_taxes_res['amount'] - tax_res['amount']
                    tax_res['amount'] += delta_tax
                    to_update_vals['price_total'] += delta_tax

            tax_values_list = []
            for tax_res in taxes_res['taxes']:
                tax_amount = tax_res['amount'] / rate
                if self.company_id.tax_calculation_rounding_method == 'round_per_line':
                    tax_amount = currency.round(tax_amount)
                tax_rep = self.env['account.tax.repartition.line'].browse(tax_res['tax_repartition_line_id'])
                tax_values_list.append({
                    **tax_res,
                    'tax_repartition_line': tax_rep,
                    'base_amount_currency': tax_res['base'],
                    'base_amount': currency.round(tax_res['base'] / rate),
                    'tax_amount_currency': tax_res['amount'],
                    'tax_amount': tax_amount,
                })

        else:
            price_subtotal = currency.round(price_unit_after_discount * base_line['quantity'])
            to_update_vals = {
                'tax_tag_ids': [Command.clear()],
                'price_subtotal': price_subtotal,
                'price_total': price_subtotal,
            }
            tax_values_list = []

        return to_update_vals, tax_values_list

    @api.model
    def _convert_to_tax_base_line_dict(
            self, base_line,
            partner=None, currency=None, product=None, taxes=None, price_unit=None, quantity=None,
            discount=None, account=None, analytic_distribution=None, price_subtotal=None,
            is_refund=False, rate=None,
            handle_price_include=True,
            extra_context=None,
    ):
        return {
            'record': base_line,
            'partner': partner or self.env['res.partner'],
            'currency': currency or self.env['res.currency'],
            'product': product or self.env['product.product'],
            'taxes': taxes or self.env['account.tax'],
            'price_unit': price_unit or 0.0,
            'quantity': quantity or 0.0,
            'salesTaxWithheldAtSource':float(base_line.salesTaxWithheldAtSource) or 0.0,
            'extratax': float(base_line.extraTax) or 0.0,
            'furtherTax': float(base_line.furtherTax) or 0.0,
            'fedPayable': float(base_line.fedPayable) or 0.0,
            'discount': discount or 0.0,
            'account': account or self.env['account.account'],
            'analytic_distribution': analytic_distribution,
            'price_subtotal': price_subtotal or 0.0,
            'is_refund': is_refund,
            'rate': rate or 1.0,
            'handle_price_include': handle_price_include,
            'extra_context': extra_context or {},
        }

    @api.model
    def _prepare_tax_totals(self, base_lines, currency, tax_lines=None, is_company_currency_requested=False):
        """ Compute the tax totals details for the business documents with custom withheld sales tax total. """

        # ==== Compute the taxes ====

        to_process = []
        for base_line in base_lines:
            to_update_vals, tax_values_list = self._compute_taxes_for_single_line(base_line)
            to_process.append((base_line, to_update_vals, tax_values_list))

        def grouping_key_generator(base_line, tax_values):
            source_tax = tax_values['tax_repartition_line'].tax_id
            return {'tax_group': source_tax.tax_group_id}

        global_tax_details = self._aggregate_taxes(to_process, grouping_key_generator=grouping_key_generator)
        is_3rd_schedule = False
        schedule_tax = 0
        for record in base_lines:
            if record['record'].sale_type_id.name ==  '3rd Schedule Goods':
                is_3rd_schedule = True
                schedule_tax += float(record['record'].salesTaxApplicable)


        tax_group_vals_list = []
        for tax_detail in global_tax_details['tax_details'].values():
            if not is_3rd_schedule:
               schedule_tax = tax_detail['tax_amount_currency']
            tax_group_vals = {
                'tax_group': tax_detail['tax_group'],
                'base_amount': tax_detail['base_amount_currency'],
                'tax_amount': int(float(schedule_tax)),
                'hide_base_amount': all(
                    x['tax_repartition_line'].tax_id.amount_type == 'fixed' for x in tax_detail['group_tax_details']),
            }
            if is_company_currency_requested:
                tax_group_vals['base_amount_company_currency'] = tax_detail['base_amount']
                tax_group_vals['tax_amount_company_currency'] = tax_detail['tax_amount']

            # Handle a manual edition of tax lines.
            if tax_lines is not None:
                matched_tax_lines = [
                    x
                    for x in tax_lines
                    if x['tax_repartition_line'].tax_id.tax_group_id == tax_detail['tax_group']
                ]
                if matched_tax_lines:
                    if base_line['record'].sale_type_id.name != '3rd Schedule Goods':
                       tax_group_vals['tax_amount'] = sum(x['tax_amount'] for x in matched_tax_lines)


            tax_group_vals_list.append(tax_group_vals)

        tax_group_vals_list = sorted(tax_group_vals_list, key=lambda x: (x['tax_group'].sequence, x['tax_group'].id))

        # ==== Partition the tax group values by subtotals ====

        amount_untaxed = global_tax_details['base_amount_currency']
        amount_tax = 0.0

        amount_untaxed_company_currency = global_tax_details['base_amount']
        amount_tax_company_currency = 0.0

        subtotal_order = {}
        groups_by_subtotal = defaultdict(list)
        for tax_group_vals in tax_group_vals_list:
            tax_group = tax_group_vals['tax_group']

            subtotal_title = tax_group.preceding_subtotal or _("Untaxed Amount")
            sequence = tax_group.sequence

            subtotal_order[subtotal_title] = min(subtotal_order.get(subtotal_title, float('inf')), sequence)
            groups_by_subtotal[subtotal_title].append({
                'group_key': tax_group.id,
                'tax_group_id': tax_group.id,
                'tax_group_name': tax_group.name,
                'tax_group_amount': tax_group_vals['tax_amount'],
                'tax_group_base_amount': tax_group_vals['base_amount'],
                'formatted_tax_group_amount': formatLang(self.env, tax_group_vals['tax_amount'], currency_obj=currency),
                'formatted_tax_group_base_amount': formatLang(self.env, tax_group_vals['base_amount'],
                                                              currency_obj=currency),
                'hide_base_amount': tax_group_vals['hide_base_amount'],
            })
            if is_company_currency_requested:
                groups_by_subtotal[subtotal_title][-1]['tax_group_amount_company_currency'] = tax_group_vals[
                    'tax_amount_company_currency']
                groups_by_subtotal[subtotal_title][-1]['tax_group_base_amount_company_currency'] = tax_group_vals[
                    'base_amount_company_currency']

        # ==== Build the final result ====

        subtotals = []
        for subtotal_title in sorted(subtotal_order.keys(), key=lambda k: subtotal_order[k]):
            amount_total = amount_untaxed + amount_tax
            subtotals.append({
                'name': subtotal_title,
                'amount': amount_total,
                'formatted_amount': formatLang(self.env, amount_total, currency_obj=currency),
            })
            if is_company_currency_requested:
                subtotals[-1]['amount_company_currency'] = amount_untaxed_company_currency + amount_tax_company_currency
                amount_tax_company_currency += sum(
                    x['tax_group_amount_company_currency'] for x in groups_by_subtotal[subtotal_title])

            amount_tax += sum(x['tax_group_amount'] for x in groups_by_subtotal[subtotal_title])

        sales_tax_withheld_total = sum(base_line.get('salesTaxWithheldAtSource', 0.0) for base_line in base_lines)
        extra_tax = sum(base_line.get('extratax', 0.0) for base_line in base_lines)
        furtherTax = sum(base_line.get('furtherTax', 0.0) for base_line in base_lines)
        fedPayable = sum(base_line.get('fedPayable', 0.0) for base_line in base_lines)
        amount_total = amount_untaxed + amount_tax - sales_tax_withheld_total + extra_tax + furtherTax + fedPayable
        amount_total_company_currency = amount_untaxed_company_currency + amount_tax_company_currency

        display_tax_base = (len(global_tax_details['tax_details']) == 1 and currency.compare_amounts(
            tax_group_vals_list[0]['base_amount'], amount_untaxed) != 0) \
                           or len(global_tax_details['tax_details']) > 1

        # ==== Compute withheld tax total ====


        result = {
            'amount_untaxed': currency.round(amount_untaxed) if currency else amount_untaxed,
            'amount_total': currency.round(amount_total) if currency else amount_total,
            'formatted_amount_total': formatLang(self.env, amount_total, currency_obj=currency),
            'formatted_amount_untaxed': formatLang(self.env, amount_untaxed, currency_obj=currency),
            'groups_by_subtotal': groups_by_subtotal,
            'subtotals': subtotals,
            'subtotals_order': sorted(subtotal_order.keys(), key=lambda k: subtotal_order[k]),
            'display_tax_base': display_tax_base,
            'sales_tax_withheld_total': float_round(sales_tax_withheld_total, precision_digits=2),
            'extra_tax': float_round(extra_tax, precision_digits=2),
            'further_tax': float_round(furtherTax, precision_digits=2),
            'fedPayable':float_round(fedPayable, precision_digits=2),
            # You can change rounding
        }

        if is_company_currency_requested:
            comp_currency = self.env.company.currency_id
            result['amount_total_company_currency'] = comp_currency.round(amount_total_company_currency)

        return result

class AccountMove(models.Model):
    _inherit = 'account.move'

    def create(self, vals_list):
        res = super().create(vals_list)
        for i in res:
            for line in i.invoice_line_ids:
                line._process_tax_lines()
        return res

    def action_post(self):
        res = super().action_post()

        for move in self:
            for line in move.invoice_line_ids:
                if line.product_id:
                    line.sale_type_id = line.product_id.sale_type_id.id  # ← THIS LINE sets sale_type_id directly from product

        return res

    salesTaxWithheldAtSourcetotal = fields.Float('Total Sales tax withheld', compute='get_total_taxes')

    def get_total_taxes(self):
        for rec in self:
            salestax_withheld = 0
            extratax = 0
            furthertax = 0
            for line in rec.invoice_line_ids:
                salestax_withheld += float(line.salesTaxWithheldAtSource)
                extratax += float(line.extraTax)
                furthertax += float(line.furtherTax)
            rec.salesTaxWithheldAtSourcetotal = salestax_withheld


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    fbr_invoice_number = fields.Char(readonly=True)
    hsCode = fields.Char(string="HS Code", compute="_compute_product_details", store=True, readonly=True)
    unit_of_measure = fields.Char(string="UOM", compute="_compute_product_details", store=True, readonly=True)
    valueSalesExcludingST = fields.Char()
    salesTaxApplicable = fields.Char(compute='_compute_sales_tax',string="Sales Tax Applicable")
    salestaxwithheldatsourceper = fields.Float(string="Sales Tax Withheld %")
    salesTaxWithheldAtSource = fields.Char('Sales Tax Withheld')
    extrataxper = fields.Float(string="Extra Tax %")
    extraTax = fields.Char(string="Extra Tax")
    furthertaxper = fields.Float(string="Further Tax %")
    furtherTax = fields.Char(string="Further Tax")
    sroScheduleNo = fields.Char('Sro Schedule No')
    fedPayableper = fields.Float()
    fedPayable = fields.Char('Fed Payable')
    discount_amount = fields.Char('Discount')
    saleType = fields.Char('Sale Type')
    sale_type_id = fields.Many2one('sale.type')
    rate = fields.Char()
    sroItemSerialNo = fields.Char('Sro Item Serial No')
    force_delete = fields.Boolean()
    delete_tax_line = fields.Boolean()
    mrp = fields.Float()












    def write(self, vals):
        res = super(AccountMoveLine, self).write(vals)
        if 'salestaxwithheldatsourceper' in vals or 'extrataxper' in vals or 'furthertaxper' in vals:
           self._process_tax_lines()
       # if 'delete_tax_line' in vals:
       #     if vals['delete_tax_line']:
       #         self.delete_tax_lines()

        return res

    @api.ondelete(at_uninstall=False)
    def _prevent_automatic_line_deletion(self):
        if not self.env.context.get('dynamic_unlink'):
            for line in self:
                if line.display_type == 'tax' and line.move_id.line_ids.tax_ids and not line.force_delete:
                    raise ValidationError(_(
                        "You cannot delete a tax line as it would impact the tax report"
                    ))
                elif line.display_type == 'payment_term':
                    raise ValidationError(_(
                        "You cannot delete a payable/receivable line as it would not be consistent "
                        "with the payment terms"
                    ))


    def _process_tax_lines(self):
        for line in self:
            move = line.move_id
            config = self.env['account.tax.configuration.custom'].search([], limit=1)
            if not config:
                continue

            is_invoice = move.move_type in ('out_invoice', 'out_refund')
            is_bill = move.move_type in ('in_invoice', 'in_refund')

            # Map tax name -> (amount field, configured account)
            tax_amount_map = {
                'salestaxwithheldatsourceper': ('salesTaxWithheldAtSource', config.tax_withheld_account_id),
                'extrataxper': ('extraTax', config.extra_tax_account_id),
                'furthertaxper': ('furtherTax', config.further_tax_account_id),
                'fedPayableper': ('fedPayable', config.fed_payable_account_id),
            }

            total_tax_amount = 0.0

            for tax_field_name, (amount_field_name, account) in tax_amount_map.items():
                tax = getattr(line, tax_field_name)
                amount_str = getattr(line, amount_field_name)

                if account:
                    try:
                        amount = float(amount_str)
                    except ValueError:
                        amount = 0.0
                    line_exits = move.line_ids.filtered(lambda l: l.name == amount_field_name)
                    if amount > 0:
                        if line_exits:
                            line_exits.write({
                                'balance':-amount if is_invoice else amount,'account_id':account.id
                            })
                        else:
                            if move.move_type in ['out_refund','in_invoice']:
                                if amount_field_name != 'salesTaxWithheldAtSource':
                                    amount = amount
                                else:
                                    amount = -amount
                            else:
                                if amount_field_name != 'salesTaxWithheldAtSource':
                                   amount = -amount
                                else:
                                    amount = amount
                            total_tax_amount += amount
                            tax_line_vals = {
                                'move_id': move.id,
                                'name': str(amount_field_name),
                                'display_type':'tax',
                                'account_id': account.id,
                                'quantity': 0.0,
                                'partner_id': move.partner_id.id,
                                'company_id': move.company_id.id,
                                'currency_id': move.currency_id.id,
                                'date': move.date,
                                'balance': amount,
                            }
                            self.env['account.move.line'].create(tax_line_vals)





    def delete_tax_lines(self):
        for rec in self:
            rec.furtherTax = 0.0
            rec.extraTax = 0.0
            rec.salesTaxWithheldAtSource = 0.0

            line_receivable = rec.move_id.line_ids.filtered(
                    lambda l: l.account_id.account_type == 'asset_receivable')
            line_exits_extra_tax = rec.move_id.line_ids.filtered(lambda l: l.name == 'extraTax')
            line_exits_further_tax = rec.move_id.line_ids.filtered(lambda l: l.name == 'furtherTax')
            line_exits_salesTaxWithheldAtSource = rec.move_id.line_ids.filtered(lambda l: l.name == 'salesTaxWithheldAtSource')
            line_exits_fedPayable = rec.move_id.line_ids.filtered(lambda l: l.name == 'fedPayable')
            if line_exits_extra_tax:
                line_exits_extra_tax.write({'force_delete': True})
                line_exits_extra_tax.unlink()
            if line_exits_further_tax:
                line_exits_further_tax.write({'force_delete': True})
                line_exits_further_tax.unlink()
            if line_exits_salesTaxWithheldAtSource:
                line_exits_salesTaxWithheldAtSource.write({'force_delete': True})
                line_exits_salesTaxWithheldAtSource.unlink()
            if line_exits_fedPayable:
                line_exits_fedPayable.write({'force_delete': True})
                line_exits_fedPayable.unlink()



    @api.depends('product_id')
    def _compute_product_details(self):
        for rec in self:
            rec.hsCode = rec.product_id.hs_code
            rec.unit_of_measure = rec.product_id.fbr_unit_of_measure
            rec.sale_type_id = rec.product_id.sale_type_id.id if rec.product_id.sale_type_id else False

    @api.onchange('salestaxwithheldatsourceper', 'extrataxper', 'furthertaxper')
    def _compute_taxes(self):
        for rec in self:
            # Sales Tax Withheld

            if rec.salestaxwithheldatsourceper:
                rec.salesTaxWithheldAtSource = float(rec.salesTaxApplicable)/rec.salestaxwithheldatsourceper
            else:
                rec.salesTaxWithheldAtSource = 0.0
                line_exits_withheld = self.env['account.move.line'].search([('name', '=', 'salesTaxWithheldAtSource')])
                if line_exits_withheld:
                    line_exits_withheld.write({'force_delete': True})
                    line_exits_withheld.unlink()

            if rec.extrataxper:
                rec.extraTax = (rec.price_unit+ float(rec.salesTaxApplicable)) *(rec.extrataxper/100)
            else:
                rec.extraTax = 0.0
                line_exits_extra_tax = rec.move_id.line_ids.filtered(lambda l: l.name == 'extraTax')
                if line_exits_extra_tax:
                    line_exits_extra_tax.write({'delete_tax_line': True,'balance':0})


            if rec.furthertaxper:
                rec.furtherTax = (rec.price_unit + float(rec.salesTaxApplicable))* (rec.furthertaxper/100)
            else:
                rec.furtherTax = 0.0
                line_exits_furtherTax = rec.move_id.line_ids.filtered(lambda l: l.name == 'furtherTax')
                if line_exits_furtherTax:
                    line_exits_furtherTax.write({'force_delete': True})
                    line_exits_furtherTax.unlink()



    @api.depends('tax_ids', 'price_subtotal')
    def _compute_sales_tax(self):
        for line in self:
            tax_amount = 0.0
            if line.tax_ids:
                # Compute tax amount based on subtotal
                for tax in line.tax_ids:
                    if line.sale_type_id.name != '3rd Schedule Goods':
                       tax_amount += (line.price_subtotal * tax.amount) / 100
                    else:
                       mrp_subtotal = line.quantity * line.mrp
                       tax_amount += (mrp_subtotal * tax.amount) / 100
                if line.product_id.is_fed:

                    tax_fed_payable = (line.price_subtotal * line.product_id.fed_per)/100
                else:
                    tax_fed_payable = 0

            line.salesTaxApplicable = str(round(tax_amount, 2)) if tax_amount else '0'
            line.fedPayableper = line.product_id.fed_per
            line.fedPayable = str(round(tax_fed_payable, 2)) if tax_amount else '0'


