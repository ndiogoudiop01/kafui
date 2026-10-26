# -*- coding: utf-8 -*-
import logging

from odoo import models, api, _, fields
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class HrLeave(models.Model):
    _inherit = "hr.leave"

    def _action_validate(self, check_state=True):
        """
        Override internal validation hook.
        Called by action_approve() / action_validate() in v19.
        After standard validation, update nbj_pris on the employee's version.
        """
        result = super(HrLeave, self)._action_validate(check_state=check_state)

        # Update taken leave days on the employee's current version (contract)
        for holiday in self.filtered(
            lambda h: h.holiday_type == 'employee' and h.employee_id
        ):
            version = holiday.employee_id.version_id
            if version:
                new_val = version.nbj_pris + holiday.number_of_days_display
                version.write({'nbj_pris': new_val})

        return result

    def action_refuse(self):
        """
        Override: after refusing a validated leave, restore nbj_pris.
        """
        # Capture validated leaves before the state changes
        previously_validated = self.filtered(lambda h: h.state == 'validate')

        result = super(HrLeave, self).action_refuse()

        # Restore nbj_pris for leaves that were validated
        for holiday in previously_validated.filtered(
            lambda h: h.holiday_type == 'employee' and h.employee_id
        ):
            version = holiday.employee_id.version_id
            if version:
                new_val = version.nbj_pris - holiday.number_of_days_display
                version.write({'nbj_pris': max(new_val, 0.0)})

        return result


class HrLeaveType(models.Model):
    _inherit = "hr.leave.type"

    paid_legal_leave = fields.Boolean('Congé légal payé')
