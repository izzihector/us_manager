############################################################################
#  Module Name: hr
#  Kelas: employee
#  File Name: hr_employee_user.py
#  Created On: 22/09/2020, 08.38
#  Description:  UX untuk HR Employee
#  Author: Matrica Consulting - (teguh)
#  Snipet: tp_model_inherit_extend
############################################################################


from odoo import fields, models


class employeeUserCreate(models.TransientModel):
    _name = "employee.user.creation"
    _description = "Multiple user creation from Employee"

    # Start - Celsa Add (8 Des 2020)
    def user_from_emp(self):
        employees = self.env['hr.employee'].browse(self._context.get('active_ids', []))

        if employees:
            for employee in employees:
                print ("Create ", employee.name, employee.user_id.id, employee.user_id.name)
                employee.link_to_user()

        return {'type': 'ir.actions.act_window_close'}

    # End - Celsa Add (8 Des 2020)
