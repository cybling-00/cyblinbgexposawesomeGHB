# -*- coding: utf-8 -*-
# Copyright (c) 2020, Youssef Restom and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import json
import frappe
from frappe.utils import nowdate, flt, cstr, getdate
from frappe import _
from erpnext.accounts.doctype.sales_invoice.sales_invoice import get_bank_cash_account

@frappe.whitelist()
def get_bank_chart_of_account(company=None):
    filters = {
        "is_group": 0,
        "disabled": 0,
        "account_type": "Bank"
    }
    if company:
        filters["company"] = company
    account = frappe.db.get_all(
        "Account",
        filters= filters,
        fields=["name"],
        pluck="name"
    )
    return account

def get_cash_account(pos_profile, company):
    cash_mop = None 
    cash_account = None 
    if pos_profile.posa_cash_mode_of_payment:
        cash_mop = pos_profile.posa_cash_mode_of_payment
    elif pos_profile.payments:
        mop_cash_list = []
        for i in pos_profile.payments:
            mop_type = frappe.db.get_value("Mode of Payment", i.mode_of_payment)
            if "cash" in i.mode_of_payment.lower() and mop_type == "Cash":
                mop_cash_list.append(i.mode_of_payment)
        if len(mop_cash_list) > 0:
            cash_mop = mop_cash_list[0]
    if cash_mop:
        cash_account = get_bank_cash_account(cash_mop, company)
    return cash_account
        
@frappe.whitelist()
def get_cash_transit_data(user):
    open_vouchers = frappe.db.get_all(
    "POS Opening Shift",
    filters={
        "user": user,
        "pos_closing_shift": ["in", ["", None]],
        "docstatus": 1,
        "status": "Open",
    },
    fields=["name", "pos_profile"],
    order_by="period_start_date desc",
    )
    data = ""
    if len(open_vouchers) > 0:
        data = {}
        data["pos_profile"] = frappe.get_doc("POS Profile", open_vouchers[0]["pos_profile"])
        data["company"] = frappe.get_doc("Company", data["pos_profile"].company)
        data["bank_chart_of_account"] = get_bank_chart_of_account(data["company"].name)
        cash_account = get_cash_account(data["pos_profile"], data["company"].name)
        if cash_account:
            data["cash_account"] = cash_account.get("account")
    return data

@frappe.whitelist()
def make_transit_type_journal_entry(data):
    data = json.loads(data)
    je = frappe.new_doc("Journal Entry")
    je.posting_date = getdate()
    je.company = data.get("company")
    je.custom_pos_profile = data.get("pos_profile")
    je.voucher_type = "Journal Entry"
    credit_account = None
    debit_account = None
    bank_account = data.get("bank_account")
    cash_account = data.get("cash_account")
    transit_type = data.get("transit_type")
    je.custom_pos_cash_transit_type = transit_type
    amount = flt(data.get("amount"))
    if transit_type == "Deposit":
        debit_account = bank_account
        credit_account = cash_account
    elif transit_type == "Widthdrawal":
        debit_account = cash_account
        credit_account = bank_account
    if credit_account:je.append("accounts", {"account": credit_account, "credit_in_account_currency": amount})
    if debit_account:je.append("accounts", {"account": debit_account, "debit_in_account_currency": amount})
    je.flags.ignore_permissions = True
    # je.flags.ignore_mandatory = True
    je.save()
    je.submit()
    return je.name