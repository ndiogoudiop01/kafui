# -*- coding: utf-8 -*-
# Composants communs (bonus, famille, is_prorata, _get_payslip_lines)
# sont maintenant dans gvs_hr_payroll_base.

from . import convention_collective
from . import employee_bonus       # garde HrPayslipRunInherit + SaveAllocMensuel
from . import hr_contract          # garde les champs Sénégal uniquement
from . import hr_employee          # garde les champs Sénégal uniquement
from . import hr_payslip           # garde override Sénégal (_get_payslip_lines complet SN)
from . import res_company_inherit
from . import res_config_setting_inherit
from . import account_move_extend
from . import employee_compute_pr
from . import hr_payslip_annual_ir
from . import hr_payslip_annual_trimf
from . import hr_holidays
