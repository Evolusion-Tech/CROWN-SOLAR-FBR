/** @odoo-module **/

import { patch } from '@web/core/utils/patch';
import { TaxTotalsComponent } from '@account/components/tax_totals/tax_totals';
import { formatMonetary } from "@web/views/fields/formatters";
import {
    Component,
    onPatched,
    onWillUpdateProps,
    onWillRender,
    toRaw,
    useRef,
    useState,
} from "@odoo/owl";

patch(TaxTotalsComponent.prototype, {
    /**
     * @override
     */

    formatData(props) {
    let totals = JSON.parse(JSON.stringify(toRaw(props.record.data[this.props.name])));
    if (!totals) {
        return;
    }
    const currencyFmtOpts = { currencyId: props.record.data.currency_id && props.record.data.currency_id[0] };
    console.log()
    let amount_untaxed = totals.amount_untaxed;
    let amount_tax = 0;
    let subtotals = [];
    for (let subtotal_title of totals.subtotals_order) {
        let amount_total = amount_untaxed + amount_tax;
        subtotals.push({
            'name': subtotal_title,
            'amount': amount_total,
            'formatted_amount': formatMonetary(amount_total, currencyFmtOpts),
        });
        let group = totals.groups_by_subtotal[subtotal_title];
        for (let i in group) {
            amount_tax = amount_tax + group[i].tax_group_amount;
        }
    }
    totals.subtotals = subtotals;
    let rounding_amount = totals.display_rounding && totals.rounding_amount || 0;
    let amount_total = amount_untaxed + amount_tax + rounding_amount - totals.sales_tax_withheld_total + totals.extra_tax + totals.further_tax + totals.fedPayable;
    totals.amount_total = amount_total;
    totals.formatted_amount_total = formatMonetary(amount_total, currencyFmtOpts);

    // Format the withheld tax total
    if (totals.sales_tax_withheld_total !== undefined) {
        totals.formatted_sales_tax_withheld_total = formatMonetary(totals.sales_tax_withheld_total, currencyFmtOpts);
    }
    if (totals.extra_tax !== undefined) {
        totals.formatted_extra_tax_total = formatMonetary(totals.extra_tax, currencyFmtOpts);
    }
    if (totals.further_tax !== undefined) {
        totals.formatted_further_tax_total = formatMonetary(totals.further_tax, currencyFmtOpts);
    }
     if (totals.fedPayable !== undefined) {
        totals.formatted_fedPayable_total = formatMonetary(totals.fedPayable, currencyFmtOpts);
    }

    for (let group_name of Object.keys(totals.groups_by_subtotal)) {
        let group = totals.groups_by_subtotal[group_name];
        for (let key in group) {
            group[key].formatted_tax_group_amount = formatMonetary(group[key].tax_group_amount, currencyFmtOpts);
            group[key].formatted_tax_group_base_amount = formatMonetary(group[key].tax_group_base_amount, currencyFmtOpts);
        }
    }
    this.totals = totals;
}
});