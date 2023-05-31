from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import float_compare, float_round

from calendar import monthrange


class HRContract(models.Model):
    _inherit = 'hr.contract'

    # ----------- Payslip Methods Start------------ #

    def get_single_day_wage(self, pay_date_from, pay_date_to):
        """
        This is to find single day wage. Useful in all rules which need single day pay
        :param pay_date_from:
        :param pay_date_to:
        :return:
        """

        if (pay_date_from.year != pay_date_to.year) or (pay_date_from.month != pay_date_to.month):
            raise ValidationError(_("Payslip date range must be on a same month"))

        days_in_this_month = monthrange(pay_date_from.year, pay_date_from.month)[1]
        return self.env.company.currency_id.round(self.wage / days_in_this_month)
    def get_single_day_wage_26_to_25(self, pay_date_from, pay_date_to):
        """
        This is to find single day wage. Useful in all rules which need single day pay
        :param pay_date_from:
        :param pay_date_to:
        :return:
        """
        days_in_this_month = monthrange(pay_date_from.year, pay_date_from.month)[1]
        days = (pay_date_to - pay_date_from).days + 1
        return self.env.company.currency_id.round(self.wage / days)
    def get_single_day_wage_india(self, pay_date_from, pay_date_to):
        """
        This is to find single day wage. Useful in all rules which need single day pay
        :param pay_date_from:
        :param pay_date_to:
        :return:
        """
        if (pay_date_from.year != pay_date_to.year) or (pay_date_from.month != pay_date_to.month):
            raise ValidationError(_("Payslip date range must be on a same month"))

        days_in_this_month = monthrange(pay_date_from.year, pay_date_from.month)[1]
        return self.env.company.currency_id.round(self.gross_salary / days_in_this_month)

    def get_single_day_wage_with_percentage_cut(self, pay_date_from, pay_date_to, unpaid_percenatge):
        """
        This is to find single day wage after cutting some percentage of amount
        :param pay_date_from:
        :param pay_date_to:
        :return: how much amount to cut per day in payslip
        """
        if (pay_date_from.year != pay_date_to.year) or (pay_date_from.month != pay_date_to.month):
            raise ValidationError(_("Payslip date range must be on a same month"))

        days_in_this_month = monthrange(pay_date_from.year, pay_date_from.month)[1]
        one_day_wage_full = self.env.company.currency_id.round(self.wage / days_in_this_month)
        return (one_day_wage_full * unpaid_percenatge / 100) if one_day_wage_full else 0

    def get_single_day_wage_with_percentage_cut_26_to_25(self, pay_date_from, pay_date_to, unpaid_percenatge):
        """
        This is to find single day wage after cutting some percentage of amount
        :param pay_date_from:
        :param pay_date_to:
        :return: how much amount to cut per day in payslip
        """
        # if (pay_date_from.year != pay_date_to.year) or (pay_date_from.month != pay_date_to.month):
        #     raise ValidationError(_("Payslip date range must be on a same month"))

        days_in_this_month = monthrange(pay_date_from.year, pay_date_from.month)[1]
        days = (pay_date_to - pay_date_from).days + 1
        one_day_wage_full = self.env.company.currency_id.round(self.wage / days)
        return (one_day_wage_full * unpaid_percenatge / 100) if one_day_wage_full else 0

    def get_one_hour_wage(self, pay_date_from, pay_date_to):
        """
        This is to find one hour wage. Useful in all rules which need one hour
        :param pay_date_from:
        :param pay_date_to:
        :return:
        """
        one_day_wage = self.get_single_day_wage(pay_date_from, pay_date_to)
        hours_in_a_day = self.resource_calendar_id.hours_per_day
        if hours_in_a_day:
            return self.env.company.currency_id.round(one_day_wage / hours_in_a_day)
        else:
            return 0

    def get_basic_pay(self, pay_date_from, pay_date_to):
        """
        Even though the payslip dates are wide in a month.
        The payroll will generate as per the contract only. --- USED IN BASIC
        :param pay_date_from:
        :param pay_date_to:
        :return:
        """
        if (pay_date_from.year != pay_date_to.year) or (pay_date_from.month != pay_date_to.month):
            raise ValidationError(_("Payslip date range must be on a same month"))

        # Check for contract end date. We have to check if the contract already ends
        contract_start_date = self.date_start
        contract_end_date = self.date_end
        payslip_start_date = pay_date_from
        payslip_end_date = pay_date_to
        full_salary_flag = False

        """
                        Payslip Start               Payslip End
            -----------------||                         ||---------------
            
        Contract Start  Contract End
        |--------------------|
        Contract Start          Contract End
        |--------------------------------|
        Contract Start                          Contract End
        |-----------------------------------------------|
        Contract Start                                              Contract End
        |------------------------------------------------------------|
        Contract Start
        |----------------------------------
                    Contract Start
                            |---------------------------|
                                    Contract Start
                                    |---------------------------------------------        
        """
        if contract_end_date:
            if contract_start_date <= payslip_start_date and contract_end_date <= payslip_end_date and contract_end_date >= payslip_start_date:
                days_as_per_contract = (contract_end_date - payslip_start_date).days + 1
            if contract_start_date >= payslip_start_date and contract_end_date >= payslip_end_date and contract_start_date >= payslip_end_date:
                days_as_per_contract = (payslip_end_date - contract_start_date).days + 1
            if contract_start_date > payslip_start_date and contract_end_date < payslip_end_date:
                days_as_per_contract = (payslip_end_date - payslip_start_date).days + 1
            if contract_start_date <= payslip_start_date and contract_end_date >= payslip_end_date:
                # Full salary
                full_salary_flag = True
                days_as_per_contract = (payslip_end_date - payslip_start_date).days + 1
        else:
            if contract_start_date <= payslip_start_date:
                # Full salary
                full_salary_flag = True
                days_as_per_contract = (payslip_end_date - payslip_start_date).days + 1
            if contract_start_date >= payslip_start_date and contract_start_date <= payslip_end_date:
                days_as_per_contract = (payslip_end_date - contract_start_date).days + 1

        if full_salary_flag:
            return self.wage

        basic_salary = self.get_single_day_wage(pay_date_from, pay_date_to) * days_as_per_contract

        basic_salary = float_round(basic_salary, precision_digits=0, rounding_method='DOWN')

        return self.env.company.currency_id.round(basic_salary)

    def get_basic_pay_for_26_to_25(self, pay_date_from, pay_date_to):

        """
        Even though the payslip dates are wide in a month.
        The payroll will generate as per the contract only. --- USED IN BASIC
        :param pay_date_from:
        :param pay_date_to:
        :return:
        """
        # if (pay_date_from.year != pay_date_to.year) or (pay_date_from.month != pay_date_to.month):
        #     raise ValidationError(_("Payslip date range must be on a same month"))

        # Check for contract end date. We have to check if the contract already ends
        contract_start_date = self.date_start
        contract_end_date = self.date_end
        payslip_start_date = pay_date_from
        payslip_end_date = pay_date_to
        full_salary_flag = False

        """
                        Payslip Start               Payslip End
            -----------------||                         ||---------------

        Contract Start  Contract End
        |--------------------|
        Contract Start          Contract End
        |--------------------------------|
        Contract Start                          Contract End
        |-----------------------------------------------|
        Contract Start                                              Contract End
        |------------------------------------------------------------|
        Contract Start
        |----------------------------------
                    Contract Start
                            |---------------------------|
                                    Contract Start
                                    |---------------------------------------------        
        """
        if contract_end_date:
            if contract_start_date <= payslip_start_date and contract_end_date <= payslip_end_date and contract_end_date >= payslip_start_date:
                days_as_per_contract = (contract_end_date - payslip_start_date).days + 1
            if contract_start_date >= payslip_start_date and contract_end_date >= payslip_end_date and contract_start_date >= payslip_end_date:
                days_as_per_contract = (payslip_end_date - contract_start_date).days + 1
            if contract_start_date > payslip_start_date and contract_end_date < payslip_end_date:
                days_as_per_contract = (payslip_end_date - payslip_start_date).days + 1
            if contract_start_date <= payslip_start_date and contract_end_date >= payslip_end_date:
                # Full salary
                full_salary_flag = True
                days_as_per_contract = (payslip_end_date - payslip_start_date).days + 1
        else:
            if contract_start_date <= payslip_start_date:
                # Full salary
                full_salary_flag = True
                days_as_per_contract = (payslip_end_date - payslip_start_date).days + 1
            if contract_start_date >= payslip_start_date and contract_start_date <= payslip_end_date:
                days_as_per_contract = (payslip_end_date - contract_start_date).days + 1
        if full_salary_flag:
            print("yyyyyyyyyyyyyyyyyyyy", pay_date_from, pay_date_to)
            return self.wage

        basic_salary = self.get_single_day_wage(pay_date_from, pay_date_to) * days_as_per_contract

        basic_salary = float_round(basic_salary, precision_digits=0, rounding_method='DOWN')

        return self.env.company.currency_id.round(basic_salary)

    def get_net_pay(self, net_amount):
        """
        Just for rounding purpose only
        :param net_amount:
        :return:
        """
        net_amount = float_round(net_amount, precision_digits=0, rounding_method='DOWN')
        return self.env.company.currency_id.round(net_amount)

    # ----------- Payslip Methods End ------------- #

    employee_contribution_perc = fields.Monetary(string="Employee Contribution %")
    employer_contribution_perc = fields.Monetary(string="Employer Contribution %")



