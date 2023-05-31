/** @odoo-module **/
var rpc = require('web.rpc');
import { UserMenu } from "@web/webclient/user_menu/user_menu";
import { patch } from "@web/core/utils/patch";
import { registry } from "@web/core/registry";
import { browser } from "@web/core/browser/browser";
import { _lt } from "@web/core/l10n/translation";
import { preferencesItem1 } from "@web/webclient/user_menu/user_menu_items";
const userMenuRegistry = registry.category("user_menuitems");


patch(UserMenu.prototype, "employee_inherits.UserMenu", {
setup() {
this._super.apply(this, arguments);
userMenuRegistry.remove("documentation");
userMenuRegistry.remove("odoo_account");
userMenuRegistry.remove("support");
userMenuRegistry.remove("separator");
userMenuRegistry.remove("shortcuts");
userMenuRegistry.remove("profile");
},
});


export function employeeProfile(env) {
    return {
        type: "item",
        id: "employeeprofile",
        description: env._t("My profile"),
        callback: async function () {
            const actionDescription = await env.services.orm.call("hr.employee", "action_get");
            const currentEmployee = await env.services.orm.call("hr.employee", "emp_id_get");
            actionDescription.res_id = currentEmployee;
            env.services.action.doAction(actionDescription);
        },
        sequence: 50,
    };
}
registry.category("user_menuitems").add("employeeprofile", employeeProfile);
