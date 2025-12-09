"""
Migration: Add Quote Sheet template for Saudi Arabia route
Date: 2024-12-06
Description: Creates the Quote Sheet - White Collar template for Saudi Arabia
             with all cost estimation sections including Employee Contract Info,
             Employee Cash Benefits, Employee Cost, Family Cost, Government Charges,
             and Mobilization Cost.
"""

from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Quote Sheet - White Collar (Saudi Arabia) HTML Template
QUOTE_SHEET_TEMPLATE = """
<div style="font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; font-size: 11px;">
    <!-- Header -->
    <div style="text-align: center; margin-bottom: 20px;">
        <h1 style="color: #1a5f7a; font-size: 18px; margin: 0 0 5px 0;">Cost Estimation Sheet - White Collar</h1>
        <p style="color: #666; font-size: 10px; margin: 0;">Minimum Contract Period is 12 Months</p>
        <p style="color: #666; font-size: 10px; margin: 5px 0 0 0;">Issued Date: {{issued_date}}</p>
    </div>

    <!-- (A) Employee Contract Information -->
    <div style="margin-bottom: 15px;">
        <div style="background-color: #1a5f7a; color: white; padding: 6px 10px; font-weight: bold; font-size: 11px;">(A). Employee Contract Information</div>
        <table style="width: 100%; border-collapse: collapse; font-size: 10px;">
            <tr>
                <td style="border: 1px solid #ddd; padding: 6px; background-color: #f5f5f5; width: 30%; font-weight: bold;">Name</td>
                <td style="border: 1px solid #ddd; padding: 6px; width: 25%;">{{employee_name}}</td>
                <td style="border: 1px solid #ddd; padding: 6px; width: 45%; color: #666;">{{company_name}}</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 6px; background-color: #f5f5f5; font-weight: bold;">Role</td>
                <td style="border: 1px solid #ddd; padding: 6px;">{{role}}</td>
                <td style="border: 1px solid #ddd; padding: 6px; color: #666;">According to Client Policy</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 6px; background-color: #f5f5f5; font-weight: bold;">Date of Hiring</td>
                <td style="border: 1px solid #ddd; padding: 6px;">{{date_of_hiring}}</td>
                <td style="border: 1px solid #ddd; padding: 6px; color: #666;"></td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 6px; background-color: #f5f5f5; font-weight: bold;">Nationality</td>
                <td style="border: 1px solid #ddd; padding: 6px;">{{nationality}}</td>
                <td style="border: 1px solid #ddd; padding: 6px; color: #666;"></td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 6px; background-color: #f5f5f5; font-weight: bold;">Status Single or Family</td>
                <td style="border: 1px solid #ddd; padding: 6px;">{{family_status}}</td>
                <td style="border: 1px solid #ddd; padding: 6px; color: #666;">According to Client Policy</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 6px; background-color: #f5f5f5; font-weight: bold;">No. of Children Below 18 Years of Age</td>
                <td style="border: 1px solid #ddd; padding: 6px;">{{num_children}}</td>
                <td style="border: 1px solid #ddd; padding: 6px; color: #666;">According to Client Policy</td>
            </tr>
        </table>
    </div>

    <!-- (B) Employee Cash Benefits -->
    <div style="margin-bottom: 15px;">
        <div style="background-color: #1a5f7a; color: white; padding: 6px 10px; font-weight: bold; font-size: 11px;">(B). Employee Cash Benefits</div>
        <table style="width: 100%; border-collapse: collapse; font-size: 10px;">
            <thead>
                <tr style="background-color: #e8e8e8;">
                    <th style="border: 1px solid #ddd; padding: 6px; text-align: left; width: 40%;"></th>
                    <th style="border: 1px solid #ddd; padding: 6px; text-align: right; width: 20%;">AMOUNT IN SAR</th>
                    <th style="border: 1px solid #ddd; padding: 6px; text-align: left; width: 40%;">REMARKS</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 6px; background-color: #f5f5f5; font-weight: bold;">Basic Salary</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{basic_salary}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; color: #666;">Salary is variable as per the categories</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 6px; background-color: #f5f5f5; font-weight: bold;">Transport Allowance</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{transport_allowance}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; color: #666;">According to Client Policy</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 6px; background-color: #f5f5f5; font-weight: bold;">Housing Allowance</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{housing_allowance}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; color: #666;">According to Client Policy</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 6px; background-color: #f5f5f5; font-weight: bold;">Rate Per Day</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{rate_per_day}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; color: #666;">According to Client Policy</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 6px; background-color: #f5f5f5; font-weight: bold;">Working Days / Month</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{working_days_month}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; color: #666;">According to Client Policy</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 6px; background-color: #f5f5f5; font-weight: bold;">AED to SAR</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{aed_to_sar}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; color: #666;">According to Client Policy</td>
                </tr>
                <tr style="background-color: #e8f4e8;">
                    <td style="border: 1px solid #ddd; padding: 6px; font-weight: bold;">Employee Monthly Total Cash Benefits</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right; font-weight: bold;">{{gross_salary}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; font-weight: bold;">Gross Salary</td>
                </tr>
            </tbody>
        </table>
    </div>

    <!-- (C) Employee Cost -->
    <div style="margin-bottom: 15px;">
        <div style="background-color: #1a5f7a; color: white; padding: 6px 10px; font-weight: bold; font-size: 11px;">(C). Employee Cost (Charges in SAR)</div>
        <table style="width: 100%; border-collapse: collapse; font-size: 10px;">
            <thead>
                <tr style="background-color: #e8e8e8;">
                    <th style="border: 1px solid #ddd; padding: 6px; text-align: left; width: 40%;"></th>
                    <th style="border: 1px solid #ddd; padding: 6px; text-align: right; width: 12%;">One Time</th>
                    <th style="border: 1px solid #ddd; padding: 6px; text-align: right; width: 12%;">Annual</th>
                    <th style="border: 1px solid #ddd; padding: 6px; text-align: right; width: 12%;">Monthly</th>
                    <th style="border: 1px solid #ddd; padding: 6px; text-align: left; width: 24%;">Remarks</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 6px; background-color: #f5f5f5;">Cost of Annual Vacation 30 Calendar Days for Employee</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{vacation_one_time}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{vacation_annual}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{vacation_monthly}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; color: #666;">12 Month Contract</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 6px; background-color: #f5f5f5;">Cost of Annual Flight Tickets for Employee</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{flight_one_time}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{flight_annual}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{flight_monthly}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; color: #666;">As Per Actuals / After 1 Year</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 6px; background-color: #f5f5f5;">Monthly Cost of EOSB of Employee</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{eosb_one_time}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{eosb_annual}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{eosb_monthly}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; color: #666;">Monthly</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 6px; background-color: #f5f5f5;">Monthly Cost of GOSI of Employee</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{gosi_one_time}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{gosi_annual}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{gosi_monthly}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; color: #666;">Monthly</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 6px; background-color: #f5f5f5;">Annual Medical Insurance for Employee (A1 Class)</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{medical_one_time}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{medical_annual}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{medical_monthly}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; color: #666;">As per actuals</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 6px; background-color: #f5f5f5;">Exit Re-Entry Charges of Employee</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{exit_reentry_one_time}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{exit_reentry_annual}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{exit_reentry_monthly}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; color: #666;">As per actuals</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 6px; background-color: #f5f5f5;">Salary Transfer (Monthly)</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{salary_transfer_one_time}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{salary_transfer_annual}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{salary_transfer_monthly}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; color: #666;">Monthly</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 6px; background-color: #f5f5f5;">Sick Leave and Public Holiday Cost</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{sick_leave_one_time}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{sick_leave_annual}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{sick_leave_monthly}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; color: #666;">As per actuals</td>
                </tr>
                <tr style="background-color: #fff3cd;">
                    <td style="border: 1px solid #ddd; padding: 6px; font-weight: bold;">Total of Employee Cost</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right; font-weight: bold;">{{employee_cost_one_time_total}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right; font-weight: bold;">{{employee_cost_annual_total}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right; font-weight: bold;">{{employee_cost_monthly_total}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px;"></td>
                </tr>
            </tbody>
        </table>
    </div>

    <!-- (D) Family Cost -->
    <div style="margin-bottom: 15px;">
        <div style="background-color: #1a5f7a; color: white; padding: 6px 10px; font-weight: bold; font-size: 11px;">(D). Family Cost (Charges in SAR)</div>
        <table style="width: 100%; border-collapse: collapse; font-size: 10px;">
            <thead>
                <tr style="background-color: #e8e8e8;">
                    <th style="border: 1px solid #ddd; padding: 6px; text-align: left; width: 40%;"></th>
                    <th style="border: 1px solid #ddd; padding: 6px; text-align: right; width: 12%;">One Time</th>
                    <th style="border: 1px solid #ddd; padding: 6px; text-align: right; width: 12%;">Annual</th>
                    <th style="border: 1px solid #ddd; padding: 6px; text-align: right; width: 12%;">Monthly</th>
                    <th style="border: 1px solid #ddd; padding: 6px; text-align: left; width: 24%;">Remarks</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 6px; background-color: #f5f5f5;">Annual Medical Insurance for Family</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{family_medical_one_time}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{family_medical_annual}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{family_medical_monthly}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; color: #666;">{{family_medical_remarks}}</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 6px; background-color: #f5f5f5;">Annual Flight Tickets for Family</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{family_flight_one_time}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{family_flight_annual}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{family_flight_monthly}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; color: #666;">{{family_flight_remarks}}</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 6px; background-color: #f5f5f5;">Exit Re-Entry charges for Family</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{family_exit_one_time}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{family_exit_annual}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{family_exit_monthly}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; color: #666;">{{family_exit_remarks}}</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 6px; background-color: #f5f5f5;">Joining Flight Tickets for Family (One Time)</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{family_joining_one_time}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{family_joining_annual}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{family_joining_monthly}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; color: #666;">{{family_joining_remarks}}</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 6px; background-color: #f5f5f5;">Visa Cost for Family (One Time)</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{family_visa_one_time}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{family_visa_annual}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{family_visa_monthly}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; color: #666;">{{family_visa_remarks}}</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 6px; background-color: #f5f5f5;">Family Levy Cost</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{family_levy_one_time}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{family_levy_annual}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{family_levy_monthly}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; color: #666;">{{family_levy_remarks}}</td>
                </tr>
                <tr style="background-color: #fff3cd;">
                    <td style="border: 1px solid #ddd; padding: 6px; font-weight: bold;">Total of Family Cost</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right; font-weight: bold;">{{family_cost_one_time_total}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right; font-weight: bold;">{{family_cost_annual_total}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right; font-weight: bold;">{{family_cost_monthly_total}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px;"></td>
                </tr>
            </tbody>
        </table>
    </div>

    <!-- (E) Government Related Charges -->
    <div style="margin-bottom: 15px;">
        <div style="background-color: #1a5f7a; color: white; padding: 6px 10px; font-weight: bold; font-size: 11px;">(E). Government Related Charges (In SAR)</div>
        <table style="width: 100%; border-collapse: collapse; font-size: 10px;">
            <thead>
                <tr style="background-color: #e8e8e8;">
                    <th style="border: 1px solid #ddd; padding: 6px; text-align: left; width: 40%;"></th>
                    <th style="border: 1px solid #ddd; padding: 6px; text-align: right; width: 12%;">One Time</th>
                    <th style="border: 1px solid #ddd; padding: 6px; text-align: right; width: 12%;">Annual</th>
                    <th style="border: 1px solid #ddd; padding: 6px; text-align: right; width: 12%;">Monthly</th>
                    <th style="border: 1px solid #ddd; padding: 6px; text-align: left; width: 24%;">Remarks</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 6px; background-color: #f5f5f5;">SCE Charges</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{sce_one_time}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{sce_annual}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{sce_monthly}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; color: #666;">As per actuals</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 6px; background-color: #f5f5f5;">Medical Test (Iqama) (One Time)</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{medical_test_one_time}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{medical_test_annual}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{medical_test_monthly}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; color: #666;">{{medical_test_remarks}}</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 6px; background-color: #f5f5f5;">Cost of Visa (One Time)</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{visa_cost_one_time}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{visa_cost_annual}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{visa_cost_monthly}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; color: #666;">As per actuals</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 6px; background-color: #f5f5f5;">E-wakala Charge (One Time)</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{ewakala_one_time}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{ewakala_annual}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{ewakala_monthly}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; color: #666;">{{ewakala_remarks}}</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 6px; background-color: #f5f5f5;">Chamber &amp; Mofa (One Time)</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{chamber_mofa_one_time}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{chamber_mofa_annual}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{chamber_mofa_monthly}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; color: #666;">{{chamber_mofa_remarks}}</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 6px; background-color: #f5f5f5;">Yearly Cost of Iqama (Annual)</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{iqama_one_time}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{iqama_annual}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{iqama_monthly}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; color: #666;">As per actuals</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 6px; background-color: #f5f5f5;">Saudi Admin Cost</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{saudi_admin_one_time}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{saudi_admin_annual}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{saudi_admin_monthly}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; color: #666;">Monthly - Subject to Change</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 6px; background-color: #f5f5f5;">Ajeer Cost</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{ajeer_one_time}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{ajeer_annual}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{ajeer_monthly}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; color: #666;">Monthly</td>
                </tr>
                <tr style="background-color: #fff3cd;">
                    <td style="border: 1px solid #ddd; padding: 6px; font-weight: bold;">Total of Government Related Charges</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right; font-weight: bold;">{{govt_cost_one_time_total}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right; font-weight: bold;">{{govt_cost_annual_total}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right; font-weight: bold;">{{govt_cost_monthly_total}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px;"></td>
                </tr>
            </tbody>
        </table>
    </div>

    <!-- (F) Mobilization Cost -->
    <div style="margin-bottom: 15px;">
        <div style="background-color: #1a5f7a; color: white; padding: 6px 10px; font-weight: bold; font-size: 11px;">(F). Mobilization Cost (Charges in SAR)</div>
        <table style="width: 100%; border-collapse: collapse; font-size: 10px;">
            <thead>
                <tr style="background-color: #e8e8e8;">
                    <th style="border: 1px solid #ddd; padding: 6px; text-align: left; width: 40%;"></th>
                    <th style="border: 1px solid #ddd; padding: 6px; text-align: right; width: 12%;">One Time</th>
                    <th style="border: 1px solid #ddd; padding: 6px; text-align: right; width: 12%;">Annual</th>
                    <th style="border: 1px solid #ddd; padding: 6px; text-align: right; width: 12%;">Monthly</th>
                    <th style="border: 1px solid #ddd; padding: 6px; text-align: left; width: 24%;">Remarks</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 6px; background-color: #f5f5f5;">Visa Processing Charges (One Time)</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{visa_processing_one_time}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{visa_processing_annual}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{visa_processing_monthly}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; color: #666;">{{visa_processing_remarks}}</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 6px; background-color: #f5f5f5;">Recruitment Fee (One Time)</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{recruitment_one_time}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{recruitment_annual}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{recruitment_monthly}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; color: #666;">{{recruitment_remarks}}</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 6px; background-color: #f5f5f5;">Joining Ticket (One Time)</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{joining_ticket_one_time}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{joining_ticket_annual}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{joining_ticket_monthly}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; color: #666;">{{joining_ticket_remarks}}</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 6px; background-color: #f5f5f5;">Relocation Cost (One Time)</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{relocation_one_time}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{relocation_annual}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{relocation_monthly}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; color: #666;">As per Actuals</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 6px; background-color: #f5f5f5;">Other Cost</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{other_cost_one_time}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{other_cost_annual}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">{{other_cost_monthly}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; color: #666;">As per Actuals</td>
                </tr>
                <tr style="background-color: #fff3cd;">
                    <td style="border: 1px solid #ddd; padding: 6px; font-weight: bold;">Total of Mobilization Cost</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right; font-weight: bold;">{{mobilization_one_time_total}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right; font-weight: bold;">{{mobilization_annual_total}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px; text-align: right; font-weight: bold;">{{mobilization_monthly_total}}</td>
                    <td style="border: 1px solid #ddd; padding: 6px;"></td>
                </tr>
            </tbody>
        </table>
    </div>

    <!-- Grand Totals -->
    <div style="margin-bottom: 15px;">
        <table style="width: 100%; border-collapse: collapse; font-size: 10px;">
            <tr style="background-color: #d4edda;">
                <td style="border: 1px solid #ddd; padding: 8px; font-weight: bold; width: 40%;">Total Cost</td>
                <td style="border: 1px solid #ddd; padding: 8px; text-align: right; font-weight: bold; width: 12%;">{{total_one_time}}</td>
                <td style="border: 1px solid #ddd; padding: 8px; text-align: right; font-weight: bold; width: 12%;">{{total_annual}}</td>
                <td style="border: 1px solid #ddd; padding: 8px; text-align: right; font-weight: bold; width: 12%;">{{total_monthly}}</td>
                <td style="border: 1px solid #ddd; padding: 8px; width: 24%; color: #666;">Payroll Benefits + Monthly Cost</td>
            </tr>
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; background-color: #f5f5f5; font-weight: bold;">FNRCO Service Charge</td>
                <td style="border: 1px solid #ddd; padding: 8px; text-align: right;"></td>
                <td style="border: 1px solid #ddd; padding: 8px; text-align: right;"></td>
                <td style="border: 1px solid #ddd; padding: 8px; text-align: right; font-weight: bold;">{{fnrco_service_charge}}</td>
                <td style="border: 1px solid #ddd; padding: 8px; color: #666;">Per Person Per Month</td>
            </tr>
            <tr style="background-color: #1a5f7a; color: white;">
                <td style="border: 1px solid #ddd; padding: 10px; font-weight: bold; font-size: 12px;">Total Invoice Amount</td>
                <td style="border: 1px solid #ddd; padding: 10px; text-align: right;"></td>
                <td style="border: 1px solid #ddd; padding: 10px; text-align: right;"></td>
                <td style="border: 1px solid #ddd; padding: 10px; text-align: right; font-weight: bold; font-size: 12px;">{{total_invoice_amount}}</td>
                <td style="border: 1px solid #ddd; padding: 10px;">Monthly</td>
            </tr>
        </table>
    </div>
</div>
"""


def run_migration():
    """Add Quote Sheet template to the database"""

    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        # Check if Quote Sheet template already exists
        result = conn.execute(text("""
            SELECT id, name FROM templates
            WHERE template_type = 'quote_sheet'
            ORDER BY created_at DESC
            LIMIT 1
        """))

        existing = result.fetchone()

        if existing:
            # Update existing Quote Sheet template
            template_id = existing[0]
            template_name = existing[1]

            conn.execute(text("""
                UPDATE templates
                SET content = :content,
                    name = 'Quote Sheet - White Collar (Saudi Arabia)',
                    description = 'Cost Estimation Sheet for Saudi Arabia White Collar contractors with Employee Contract Info, Cash Benefits, Employee Cost, Family Cost, Government Charges, and Mobilization Cost sections',
                    updated_at = NOW()
                WHERE id = :template_id
            """), {"content": QUOTE_SHEET_TEMPLATE.strip(), "template_id": template_id})

            conn.commit()
            print(f"Updated existing Quote Sheet template: {template_name} (ID: {template_id})")
        else:
            # Create new Quote Sheet template
            conn.execute(text("""
                INSERT INTO templates (id, name, template_type, description, content, country, is_active, created_at)
                VALUES (
                    gen_random_uuid(),
                    'Quote Sheet - White Collar (Saudi Arabia)',
                    'quote_sheet',
                    'Cost Estimation Sheet for Saudi Arabia White Collar contractors with Employee Contract Info, Cash Benefits, Employee Cost, Family Cost, Government Charges, and Mobilization Cost sections',
                    :content,
                    'Saudi Arabia',
                    true,
                    NOW()
                )
            """), {"content": QUOTE_SHEET_TEMPLATE.strip()})

            conn.commit()
            print("Created new Quote Sheet template: Quote Sheet - White Collar (Saudi Arabia)")

        print("\nMigration completed successfully!")
        print("The Quote Sheet template includes:")
        print("  - (A) Employee Contract Information: Name, Role, Date of Hiring, Nationality, Family Status, No. of Children")
        print("  - (B) Employee Cash Benefits: Basic Salary, Transport, Housing, Rate Per Day, Working Days, AED to SAR, Gross Salary")
        print("  - (C) Employee Cost: Vacation, Flight Tickets, EOSB, GOSI, Medical Insurance, Exit Re-Entry, Salary Transfer, Sick Leave")
        print("  - (D) Family Cost: Medical Insurance, Flight Tickets, Exit Re-Entry, Joining Flights, Visa Cost, Family Levy")
        print("  - (E) Government Related Charges: SCE, Medical Test, Visa, E-wakala, Chamber & Mofa, Iqama, Saudi Admin, Ajeer")
        print("  - (F) Mobilization Cost: Visa Processing, Recruitment Fee, Joining Ticket, Relocation, Other Cost")
        print("  - Grand Totals: Total Cost, FNRCO Service Charge, Total Invoice Amount")


def rollback_migration():
    """Remove Quote Sheet template (use with caution!)"""
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        conn.execute(text("""
            DELETE FROM templates WHERE template_type = 'quote_sheet'
        """))
        conn.commit()
        print("Removed Quote Sheet template")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        print("Rolling back migration...")
        rollback_migration()
    else:
        print("Running migration to add Quote Sheet template...")
        run_migration()
