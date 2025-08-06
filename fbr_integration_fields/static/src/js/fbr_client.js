/** @odoo-module */

import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

class FBRBackgroundClient extends Component {
setup() {
        this.actions = useService("action");
    }
}

FBRBackgroundClient.template = "fbr_integration_fields.fbr_template";

registry.category("actions").add("fbr_template", FBRBackgroundClient);