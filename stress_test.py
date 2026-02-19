    """
    Comprehensive stress test for ZeroPhix library
    Tests runtime performance and accuracy across 100+ test cases
    """

    import time
    import json
    from typing import List, Dict, Tuple
    from dataclasses import dataclass
    from zerophix.pipelines.redaction import RedactionPipeline
    from zerophix.config import RedactionConfig


    @dataclass
    class TestCase:
        """Single test case with expected entities"""
        text: str
        expected_labels: List[str]  # Labels we expect to find
        description: str
        country: str = "US"


    class StressTest:
        def __init__(self):
            self.results = {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "total_time": 0.0,
                "avg_time": 0.0,
                "by_detector": {},
                "failures": []
            }
            self.test_cases = self._create_test_cases()
        
        def _calculate_metrics(self, true_positives, false_positives, false_negatives):
            """Calculate precision, recall, and F1 score"""
            precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
            recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
            return precision, recall, f1

        def _create_test_cases(self) -> List[TestCase]:
            """Create 200 diverse test cases: 100 US + 100 AU with medical in both"""
            cases = []
            
            # ========== US CASES (100) ==========
            
            # US SSN cases (12)
            us_ssn = [
                TestCase("My SSN is 123-45-6789", ["SSN"], "US SSN basic"),
                TestCase("SSN: 987-65-4321", ["SSN"], "US SSN with label"),
                TestCase("The employee's SSN is 555-12-3456", ["SSN"], "US SSN in sentence"),
                TestCase("123-45-6789 is my SSN", ["SSN"], "US SSN at start"),
                TestCase("SSN format XXX-XX-XXXX: 456-78-9012", ["SSN"], "US SSN after format"),
                TestCase("Tax ID: 321-54-9876, verified", ["SSN"], "US Tax ID as SSN"),
                TestCase("Invalid SSN: 000-00-0000, valid: 234-56-7890", ["SSN"], "US Valid/invalid mix"),
                TestCase("SSN check: 901-23-4567 passed", ["SSN"], "US SSN with context"),
                TestCase("Two SSNs: 345-67-8901 and 765-43-2109", ["SSN"], "US Multiple SSNs"),
                TestCase("Federal ID 111-22-3333", ["SSN"], "US Federal ID"),
                TestCase("Government file 222-33-4444 attached", ["SSN"], "US Gov file SSN"),
                TestCase("Reference: 333-44-5555", ["SSN"], "US Reference SSN"),
            ]
            cases.extend(us_ssn)
            
            # US Email addresses (12)
            us_email = [
                TestCase("Email: john@example.com", ["EMAIL"], "US Email basic"),
                TestCase("Contact me at jane.doe@company.co.uk", ["EMAIL"], "US Email subdomain"),
                TestCase("john.smith_2024@test-domain.org", ["EMAIL"], "US Email complex"),
                TestCase("Multiple: alice@test.com, bob@company.com", ["EMAIL"], "US Multiple emails"),
                TestCase("hello@world.io is my email", ["EMAIL"], "US Email in sentence"),
                TestCase("support@zerophix.dev and info@zerophix.com", ["EMAIL"], "US Company emails"),
                TestCase("user+tag@example.com is valid", ["EMAIL"], "US Email with plus"),
                TestCase("name_123@domain.co.nz", ["EMAIL"], "US Email with numbers"),
                TestCase("Contact: support@organization.com", ["EMAIL"], "US Email context"),
                TestCase("work: admin@corporate.net", ["EMAIL"], "US Work email"),
                TestCase("billing@store.io for invoices", ["EMAIL"], "US Billing email"),
                TestCase("notifications@service.com daily", ["EMAIL"], "US Notification email"),
            ]
            cases.extend(us_email)
            
            # US Phone numbers (12)
            us_phone = [
                TestCase("Call me at (555) 123-4567", ["PHONE_US"], "US Phone standard"),
                TestCase("555-987-6543 is my number", ["PHONE_US"], "US Phone with dashes"),
                TestCase("5551234567 without formatting", ["PHONE_US"], "US Phone no format"),
                TestCase("Phone: 555.123.4567", ["PHONE_US"], "US Phone with dots"),
                TestCase("Multiple: 555-111-2222 or 555-333-4444", ["PHONE_US"], "US Multiple phones"),
                TestCase("Reach: (202) 555-0123 ext. 456", ["PHONE_US"], "US Phone with extension"),
                TestCase("Call 555-0199 for support", ["PHONE_US"], "US Phone in context"),
                TestCase("My home: 555-1234", ["PHONE_US"], "US Short phone"),
                TestCase("Office (555) 867-5309, Mobile 555-123-4567", ["PHONE_US"], "US Multiple types"),
                TestCase("Emergency: (555) 911-0000", ["PHONE_US"], "US Emergency number"),
                TestCase("Main line 555-2000", ["PHONE_US"], "US Main line"),
                TestCase("Direct: (555) 444-5555", ["PHONE_US"], "US Direct number"),
            ]
            cases.extend(us_phone)
            
            # US Credit cards (8)
            us_card = [
                TestCase("Card: 4532-1234-5678-9999", ["CREDIT_CARD"], "US Visa card"),
                TestCase("5105105105105100 is test", ["CREDIT_CARD"], "US Mastercard"),
                TestCase("American Express: 378282246310005", ["CREDIT_CARD"], "US Amex"),
                TestCase("Card numbers: 6011111111111117, 4532123456789", ["CREDIT_CARD"], "US Multiple cards"),
                TestCase("4024 0071 4597 4932 format", ["CREDIT_CARD"], "US Card formatted"),
                TestCase("My card is 5105-1051-0510-5100", ["CREDIT_CARD"], "US Partial card"),
                TestCase("5555555555554444 test", ["CREDIT_CARD"], "US Test Mastercard"),
                TestCase("Discover: 6011000990139424", ["CREDIT_CARD"], "US Discover card"),
            ]
            cases.extend(us_card)
            
            # US Medical cases (16)
            us_medical = [
                TestCase("Patient MRN: 123456", ["MEDICAL_RECORD"], "US Medical record number"),
                TestCase("Patient MRN: 654321", ["MEDICAL_RECORD"], "US MRN second"),
                TestCase("Record #999888", ["MEDICAL_RECORD"], "US Record ID"),
                TestCase("Chart: MRN 555777", ["MEDICAL_RECORD"], "US Chart MRN"),
                TestCase("ICD-10 code: E11.9 for Diabetes", [], "US Medical condition (context only)"),
                TestCase("Diagnosis: Type 2 Diabetes, hypertension", [], "US Multiple conditions (context only)"),
                TestCase("Treated with Metformin 500mg daily", [], "US Medication (context only)"),
                TestCase("HbA1c: 7.5%, glucose: 145 mg/dL", [], "US Lab values (context only)"),
                TestCase("Blood pressure: 120/80 mmHg", [], "US Vital signs (context only)"),
                TestCase("Allergy: Penicillin (severe)", [], "US Allergy info (context only)"),
                TestCase("Hospitalized 03/15/2024 for pneumonia", [], "US Medical date (context only)"),
                TestCase("Dosage: 250mg twice daily", [], "US Dosage (context only)"),
                TestCase("Prescribed Lisinopril 10mg", [], "US Prescription (context only)"),
                TestCase("Follow-up: 2 weeks", [], "US Follow-up (context only)"),
                TestCase("Surgery scheduled for 04/01/2024", [], "US Surgery date (context only)"),
                TestCase("Physician: Dr. Smith, MD", [], "US Doctor name (context only)"),
            ]
            cases.extend(us_medical)
            
            # US Combined scenarios (40) - with PERSON_NAME where names appear
            us_combined = [
                TestCase("Patient John Doe (SSN: 123-45-6789) admitted to ER", ["PERSON_NAME", "SSN"], "US Patient with SSN"),
                TestCase("Dr. Jane Smith reached at (555) 234-5678 or jane@hospital.com", ["PERSON_NAME", "PHONE_US", "EMAIL"], "US Doctor contact"),
                TestCase("Invoice #INV-2024-001: john@company.com, Phone 555-123-4567, SSN 234-56-7890", ["EMAIL", "PHONE_US", "SSN"], "US Invoice details"),
                TestCase("Employee: Alice Johnson, ID: 456-78-9012, Email: alice@corp.com", ["PERSON_NAME", "SSN", "EMAIL"], "US Employee record"),
                TestCase("Customer report: Bob Smith (555) 987-6543, Card: 5105105105105100", ["PERSON_NAME", "PHONE_US", "CREDIT_CARD"], "US Customer details"),
                TestCase("Support: (555) 111-2222 or support@help.com", ["PHONE_US", "EMAIL"], "US Support info"),
                TestCase("Medical: Patient #12345, Diagnosis: Diabetes", ["MEDICAL_RECORD"], "US Medical report"),
                TestCase("Billing: Card 4532123456789999, SSN 111-22-3333", ["CREDIT_CARD", "SSN"], "US Billing info"),
                TestCase("ER Visit: 03/15/2024, Patient: Michael Johnson, MRN: 987654", ["PERSON_NAME", "MEDICAL_RECORD"], "US ER admission"),
                TestCase("Claim #CLM-2024-555: jane@company.com, Ph: (555) 234-5678, SSN: 345-67-8901", ["EMAIL", "PHONE_US", "SSN"], "US Insurance claim"),
                TestCase("Patient: Sarah Davis, DOB: 01/15/1985, SSN: 567-89-0123, Card: 5105105105105100", ["PERSON_NAME", "SSN", "CREDIT_CARD"], "US Full record"),
                TestCase("Pharmacy: Rx #RX789, Patient: John Cooper, SSN: 678-90-1234", ["PERSON_NAME", "MEDICAL_RECORD", "SSN"], "US Pharmacy record"),
                TestCase("Telehealth: Email dr.james@clinic.com, Phone (555) 555-5555, MRN: 555666", ["EMAIL", "PHONE_US", "MEDICAL_RECORD"], "US Telehealth"),
                TestCase("Invoice Payment: Card 4024007145974932, Email bill@customer.com, Phone 555-999-8888", ["CREDIT_CARD", "EMAIL", "PHONE_US"], "US Payment details"),
                TestCase("Employee onboarding: SSN 901-23-4567, Email emp@company.com, Phone (555) 666-7777", ["SSN", "EMAIL", "PHONE_US"], "US Onboarding form"),
                TestCase("Appointment: Dr. Thomas Lee, Email thomas@clinic.com, SSN required: 234 567 890", ["PERSON_NAME", "EMAIL", "SSN"], "US Appointment booking"),
                TestCase("Medical forms: MRN 111222, Age 45, Email contact@patient.com", ["MEDICAL_RECORD", "EMAIL"], "US Medical forms"),
                TestCase("Lab results: Patient ID 98765, Phone (555) 234-5678, Result date 02/19/2026", ["PHONE_US"], "US Lab results"),
                TestCase("Referral from Dr. Brown at (555) 666-7777 to Dr. Green at green@hospital.org", ["PERSON_NAME", "PHONE_US", "EMAIL"], "US Doctor referral"),
                TestCase("Insurance: Member ID 556677, SSN 345-67-8901, Card 5105105105105100", ["SSN", "CREDIT_CARD"], "US Insurance member"),
                TestCase("Patient portal: Email alice@email.com, Phone (555) 888-9999, MRN 444555", ["EMAIL", "PHONE_US", "MEDICAL_RECORD"], "US Patient portal"),
                TestCase("Prescription: Drug ABC, MRN 333444, Target date 02/25/2026", ["MEDICAL_RECORD"], "US Prescription"),
                TestCase("Hospital staff: Dr. Ray (555) 123-0000, ray@hospital.net, Badge 889900", ["PERSON_NAME", "PHONE_US", "EMAIL"], "US Hospital staff"),
                TestCase("Consultation: Patient Elizabeth, SSN 789-01-2345, Email Liz@mail.com", ["PERSON_NAME", "SSN", "EMAIL"], "US Consultation"),
                TestCase("Discharge summary: MRN 222333, Date 02/18/2026, Contact (555) 777-8888", ["MEDICAL_RECORD", "PHONE_US"], "US Discharge"),
                TestCase("Billing statement: Amount $1000, SSN 111-22-3333, Card 4532123456789", ["SSN", "CREDIT_CARD"], "US Statement"),
                TestCase("Medication reminder: MRN 666777, Email remind@health.com, Freq: daily", ["MEDICAL_RECORD", "EMAIL"], "US Reminder"),
                TestCase("Lab request: Dr. Mark at mark@lab.org, Patient: MRN 777888, Phone (555) 444-0000", ["PERSON_NAME", "EMAIL", "MEDICAL_RECORD", "PHONE_US"], "US Lab request"),
                TestCase("Follow-up appointment: MRN 101112, Email follow@hospital.com, Call (555) 999-0000", ["MEDICAL_RECORD", "EMAIL", "PHONE_US"], "US Follow-up apt"),
                TestCase("Emergency contact: John at (555) 333-4444, Email john@contact.com, SSN 246-80-1357", ["PERSON_NAME", "PHONE_US", "EMAIL", "SSN"], "US Emergency"),
                TestCase("Account setup: Email new@patient.org, Phone (555) 222-1111, SSN 523-84-1926", ["EMAIL", "PHONE_US", "SSN"], "US Account setup"),
                TestCase("Insurance verification: Card 5105-1051-0510-5100, Holder SSN 159-75-3862", ["CREDIT_CARD", "SSN"], "US Insurance verify"),
                TestCase("Billing cycle: MRN 131415, Email bill@charge.com, Amount: $500", ["MEDICAL_RECORD", "EMAIL"], "US Billing cycle"),
                TestCase("Doctor visit: Dr. Patrick (555) 666-1111, patrick@clinic.net, MRN 161718", ["PERSON_NAME", "PHONE_US", "EMAIL", "MEDICAL_RECORD"], "US Doctor visit"),
                TestCase("Referral pending: MRN 192021, from (555) 777-2222 to specialist@hospital.com", ["MEDICAL_RECORD", "PHONE_US", "EMAIL"], "US Referral pending"),
                TestCase("Lab report: SSN 321-05-4682, MRN 222324, Email results@lab.net", ["SSN", "MEDICAL_RECORD", "EMAIL"], "US Lab report"),
                TestCase("Prescription refill: MRN 252627, Phone (555) 888-3333, Email pharm@rx.com", ["MEDICAL_RECORD", "PHONE_US", "EMAIL"], "US Refill"),
                TestCase("Clinical trial: MRN 282930, Contact: (555) 999-4444, Email trial@research.org", ["MEDICAL_RECORD", "PHONE_US", "EMAIL"], "US Trial"),
                TestCase("Medical history: Patient SSN 147-25-3698, MRN 313233, Email hist@archive.com", ["SSN", "MEDICAL_RECORD", "EMAIL"], "US History"),
                TestCase("Insurance claim: Card 4024007145974932, SSN 369-14-7520, RX MRN 343536", ["CREDIT_CARD", "SSN", "MEDICAL_RECORD"], "US Claim"),
            ]
            cases.extend(us_combined)
            
            # ========== AU CASES (100) ==========
            
            # AU SSN/TFN cases (12) - medical record IDs (comparable to US patterns)
            au_ssn = [
                TestCase("My MRN is 123456", ["MEDICAL_RECORD"], "AU Medical record ID", country="AU"),
                TestCase("Patient ID 50110219", ["MEDICAL_RECORD"], "AU Patient ID", country="AU"),
                TestCase("Chart number: 223456789", ["MEDICAL_RECORD"], "AU Chart number", country="AU"),
                TestCase("Record ACN 110219460", ["MEDICAL_RECORD"], "AU Record ID", country="AU"),
                TestCase("Hospital ID: HL456789", ["MEDICAL_RECORD"], "AU Hospital ID", country="AU"),
                TestCase("Clinic ref: CL123456", ["MEDICAL_RECORD"], "AU Clinic ref", country="AU"),
                TestCase("Company registration: 999888777", ["MEDICAL_RECORD"], "AU Company ID", country="AU"),
                TestCase("Reference number 333222111", ["MEDICAL_RECORD"], "AU Reference", country="AU"),
                TestCase("Business ID 88123456", ["MEDICAL_RECORD"], "AU Business ID", country="AU"),
                TestCase("Healthcare ID 1234567890", ["MEDICAL_RECORD"], "AU Healthcare ID", country="AU"),
                TestCase("Member number 777666555", ["MEDICAL_RECORD"], "AU Member", country="AU"),
                TestCase("Registration 12345678901", ["MEDICAL_RECORD"], "AU Registration", country="AU"),
            ]
            cases.extend(au_ssn)
            
            # AU Email addresses (12)
            au_email = [
                TestCase("Email: john@example.com.au", ["EMAIL"], "AU Email basic"),
                TestCase("Contact: jane.doe@company.au", ["EMAIL"], "AU Email company"),
                TestCase("john.smith@domain.com.au", ["EMAIL"], "AU Email domain"),
                TestCase("info@australian-org.com", ["EMAIL"], "AU Email org"),
                TestCase("hello@business.net.au", ["EMAIL"], "AU Email net"),
                TestCase("support@sydney.org.au", ["EMAIL"], "AU Email sydney"),
                TestCase("admin@melbourne.edu.au", ["EMAIL"], "AU Email edu"),
                TestCase("contact@australia.gov.au", ["EMAIL"], "AU Email gov"),
                TestCase("sales@local.com.au", ["EMAIL"], "AU Email local"),
                TestCase("helpdesk@corp.com.au", ["EMAIL"], "AU Email helpdesk"),
                TestCase("service@provider.net.au", ["EMAIL"], "AU Email service"),
                TestCase("accounts@business.org.au", ["EMAIL"], "AU Email accounts"),
            ]
            cases.extend(au_email)
            
            # AU Phone numbers (12) - US patterns work cross-country
            au_phone = [
                TestCase("Call me at (555) 123-4567", ["PHONE_US"], "AU Phone US format"),
                TestCase("555-987-6543 is my number", ["PHONE_US"], "AU Phone with dashes"),
                TestCase("5551234567 without formatting", ["PHONE_US"], "AU Phone no format"),
                TestCase("Phone: 555.123.4567", ["PHONE_US"], "AU Phone with dots"),
                TestCase("Multiple: 555-111-2222 or 555-333-4444", ["PHONE_US"], "AU Multiple phones"),
                TestCase("Reach: (202) 555-0123 ext. 456", ["PHONE_US"], "AU Phone with ext"),
                TestCase("Call 555-0199 for support", ["PHONE_US"], "AU Phone support"),
                TestCase("My business: 555-1234", ["PHONE_US"], "AU Business phone"),
                TestCase("Office (555) 867-5309, Mobile 555-456-7890", ["PHONE_US"], "AU Multiple types"),
                TestCase("Main line 555-2000", ["PHONE_US"], "AU Main line"),
                TestCase("Direct: (555) 444-5555", ["PHONE_US"], "AU Direct number"),
                TestCase("Emergency: (555) 911-0000", ["PHONE_US"], "AU Emergency"),
            ]
            cases.extend(au_phone)
            
            # AU Credit cards (8) - cross-country 
            au_card = [
                TestCase("Card: 4532-1234-5678-9999", ["CREDIT_CARD"], "AU Visa card"),
                TestCase("5105105105105100 is test", ["CREDIT_CARD"], "AU Mastercard"),
                TestCase("American Express: 378282246310005", ["CREDIT_CARD"], "AU Amex"),
                TestCase("Card numbers: 6011111111111117, 4532123456789", ["CREDIT_CARD"], "AU Multiple cards"),
                TestCase("4024 0071 4597 4932 format", ["CREDIT_CARD"], "AU Card formatted"),
                TestCase("My card is 5105-1051-0510-5100", ["CREDIT_CARD"], "AU Partial card"),
                TestCase("5555555555554444 test", ["CREDIT_CARD"], "AU Test Mastercard"),
                TestCase("Discover: 6011000990139424", ["CREDIT_CARD"], "AU Discover card"),
            ]
            cases.extend(au_card)
            
            # AU Medical cases (16)
            au_medical = [
                TestCase("Patient MRN: 123456", ["MEDICAL_RECORD"], "AU Medical record number"),
                TestCase("Patient MRN: 654321", ["MEDICAL_RECORD"], "AU MRN second"),
                TestCase("Record #999888", ["MEDICAL_RECORD"], "AU Record ID"),
                TestCase("Chart: MRN 555777", ["MEDICAL_RECORD"], "AU Chart MRN"),
                TestCase("ICD-10 code: E11.9 for Diabetes", [], "AU Medical condition (context only)"),
                TestCase("Diagnosis: Type 2 Diabetes, hypertension", [], "AU Multiple conditions (context only)"),
                TestCase("Treated with Metformin 500mg daily", [], "AU Medication (context only)"),
                TestCase("HbA1c: 7.5%, glucose: 145 mg/dL", [], "AU Lab values (context only)"),
                TestCase("Blood pressure: 120/80 mmHg", [], "AU Vital signs (context only)"),
                TestCase("Allergy: Penicillin (severe)", [], "AU Allergy info (context only)"),
                TestCase("Hospitalized 15/02/2026 for pneumonia", [], "AU Medical date (context only)"),
                TestCase("Dosage: 250mg twice daily", [], "AU Dosage (context only)"),
                TestCase("Prescribed Lisinopril 10mg", [], "AU Prescription (context only)"),
                TestCase("Follow-up: 2 weeks", [], "AU Follow-up (context only)"),
                TestCase("Surgery scheduled for 01/04/2026", [], "AU Surgery date (context only)"),
                TestCase("Physician: Dr. Smith FRACS", [], "AU Doctor name (context only)"),
            ]
            cases.extend(au_medical)
            
            # AU Combined scenarios (40) - with PERSON_NAME where names appear
            au_combined = [
                TestCase("Patient John Doe invited for medical examination", ["PERSON_NAME", "EMAIL"], "AU Patient invite", country="AU"),
                TestCase("Dr. Jane Smith reached at (555) 234-5678 or jane@hospital.com.au", ["PERSON_NAME", "PHONE_US", "EMAIL"], "AU Doctor contact", country="AU"),
                TestCase("Invoice #INV-2024-001: john@company.com.au, Phone 555-123-4567", ["EMAIL", "PHONE_US"], "AU Invoice details", country="AU"),
                TestCase("Employee: Alice Johnson, Email: alice@corp.com.au", ["PERSON_NAME", "EMAIL"], "AU Employee record", country="AU"),
                TestCase("Customer report: Bob Smith (555) 987-6543, Card: 5105105105105100", ["PERSON_NAME", "PHONE_US", "CREDIT_CARD"], "AU Customer details", country="AU"),
                TestCase("Support: (555) 111-2222 or support@help.com.au", ["PHONE_US", "EMAIL"], "AU Support info", country="AU"),
                TestCase("Medical: Patient #12345, MRN: Medical Record", ["MEDICAL_RECORD"], "AU Medical report", country="AU"),
                TestCase("Billing AU: Card 4532123456789999", ["CREDIT_CARD"], "AU Billing info", country="AU"),
                TestCase("ER Visit: 15/02/2026, Patient: Michael Johnson, MRN: 987654", ["PERSON_NAME", "MEDICAL_RECORD"], "AU ER admission", country="AU"),
                TestCase("Claim #CLM-2024-555: jane@company.com.au, Ph: (555) 234-5678", ["EMAIL", "PHONE_US"], "AU Insurance claim", country="AU"),
                TestCase("Patient: Sarah Davis, MRN: 567890, Card: 5105105105105100", ["PERSON_NAME", "MEDICAL_RECORD", "CREDIT_CARD"], "AU Full record", country="AU"),
                TestCase("Pharmacy: Rx #RX789, MRN: 678901, Email pharm@rx.com.au", ["MEDICAL_RECORD", "EMAIL"], "AU Pharmacy record", country="AU"),
                TestCase("Telehealth: Email dr.james@clinic.com.au, Phone (555) 555-5555, MRN: 555666", ["EMAIL", "PHONE_US", "MEDICAL_RECORD"], "AU Telehealth", country="AU"),
                TestCase("Invoice Payment: Card 4024007145974932, Email bill@customer.com.au, Phone 555-999-8888", ["CREDIT_CARD", "EMAIL", "PHONE_US"], "AU Payment details", country="AU"),
                TestCase("Employee onboarding: Email emp@company.com.au, Phone (555) 666-7777", ["EMAIL", "PHONE_US"], "AU Onboarding form", country="AU"),
                TestCase("Appointment: Dr. Thomas Lee, Email thomas@clinic.com.au", ["PERSON_NAME", "EMAIL"], "AU Appointment booking", country="AU"),
                TestCase("Medical forms: MRN 111222, Email contact@patient.com.au", ["MEDICAL_RECORD", "EMAIL"], "AU Medical forms", country="AU"),
                TestCase("Lab results: Patient ID 98765, Phone (555) 234-5678", ["PHONE_US"], "AU Lab results", country="AU"),
                TestCase("Referral from Dr. Brown at (555) 666-7777 to green@hospital.org.au", ["PERSON_NAME", "PHONE_US", "EMAIL"], "AU Doctor referral", country="AU"),
                TestCase("Insurance: Card 5105105105105100", ["CREDIT_CARD"], "AU Insurance member", country="AU"),
                TestCase("Patient portal: Email alice@email.com.au, Phone (555) 888-9999, MRN 444555", ["EMAIL", "PHONE_US", "MEDICAL_RECORD"], "AU Patient portal", country="AU"),
                TestCase("Prescription: MRN 333444, Date 25/02/2026", ["MEDICAL_RECORD"], "AU Prescription", country="AU"),
                TestCase("Hospital staff: Dr. Ray (555) 123-0000, ray@hospital.net.au", ["PERSON_NAME", "PHONE_US", "EMAIL"], "AU Hospital staff", country="AU"),
                TestCase("Consultation: Patient Elizabeth, Email Liz@mail.com.au", ["PERSON_NAME", "EMAIL"], "AU Consultation", country="AU"),
                TestCase("Discharge summary: MRN 222333, Date 18/02/2026, Contact (555) 777-8888", ["MEDICAL_RECORD", "PHONE_US"], "AU Discharge", country="AU"),
                TestCase("Billing statement: Card 4532123456789", ["CREDIT_CARD"], "AU Statement", country="AU"),
                TestCase("Medication reminder: MRN 666777, Email remind@health.com.au", ["MEDICAL_RECORD", "EMAIL"], "AU Reminder", country="AU"),
                TestCase("Lab request: Dr. Mark at mark@lab.org.au, Patient: MRN 777888, Phone (555) 444-0000", ["PERSON_NAME", "EMAIL", "MEDICAL_RECORD", "PHONE_US"], "AU Lab request", country="AU"),
                TestCase("Follow-up appointment: MRN 101112, Email follow@hospital.com.au, Call (555) 999-0000", ["MEDICAL_RECORD", "EMAIL", "PHONE_US"], "AU Follow-up apt", country="AU"),
                TestCase("Emergency contact: John at (555) 333-4444, Email john@contact.com.au", ["PERSON_NAME", "PHONE_US", "EMAIL"], "AU Emergency", country="AU"),
                TestCase("Account setup: Email new@patient.org.au, Phone (555) 222-1111", ["EMAIL", "PHONE_US"], "AU Account setup", country="AU"),
                TestCase("Insurance verification: Card 5105-1051-0510-5100", ["CREDIT_CARD"], "AU Insurance verify", country="AU"),
                TestCase("Billing cycle: MRN 131415, Email bill@charge.com.au", ["MEDICAL_RECORD", "EMAIL"], "AU Billing cycle", country="AU"),
                TestCase("Doctor visit: Dr. Patrick (555) 666-1111, patrick@clinic.net.au, MRN 161718", ["PERSON_NAME", "PHONE_US", "EMAIL", "MEDICAL_RECORD"], "AU Doctor visit", country="AU"),
                TestCase("Referral pending: MRN 192021, from (555) 777-2222 to specialist@hospital.com.au", ["MEDICAL_RECORD", "PHONE_US", "EMAIL"], "AU Referral pending", country="AU"),
                TestCase("Lab report: MRN 222324, Email results@lab.net.au", ["MEDICAL_RECORD", "EMAIL"], "AU Lab report", country="AU"),
                TestCase("Prescription refill: MRN 252627, Phone (555) 888-3333, Email pharm@rx.com.au", ["MEDICAL_RECORD", "PHONE_US", "EMAIL"], "AU Refill", country="AU"),
                TestCase("Clinical trial: MRN 282930, Contact: (555) 999-4444, Email trial@research.org.au", ["MEDICAL_RECORD", "PHONE_US", "EMAIL"], "AU Trial", country="AU"),
                TestCase("Medical history: MRN 313233, Email hist@archive.com.au", ["MEDICAL_RECORD", "EMAIL"], "AU History", country="AU"),
                TestCase("Insurance claim: Card 4024007145974932, RX MRN 343536", ["CREDIT_CARD", "MEDICAL_RECORD"], "AU Claim", country="AU"),
            ]
            cases.extend(au_combined)
            
            return cases

        def _label_matches(self, detected_labels: set, expected_labels: list) -> bool:
            """
            Check if detected labels match expected labels.
            Uses fuzzy matching for label variations.
            """
            # For "expect nothing" cases
            if len(expected_labels) == 0:
                # If we detected PII entities, it's a false positive (FAIL)
                pii_entities = {
                    "ssn", "email", "phone", "phone_us", "credit_card", "name", 
                    "person", "person_name", "medical_record", "mrn"
                }
                detected_lower = {label.lower() for label in detected_labels}
                
                # Check if any detected label is in the PII list
                for detected in detected_lower:
                    if detected in pii_entities:
                        return False  # False positive
                    # Also check if it contains PII words
                    for pii in pii_entities:
                        if pii in detected:
                            return False
                
                return True  # No PII found (correct)
            
            detected_lower = {label.lower() for label in detected_labels}
            
            for expected in expected_labels:
                expected_lower = expected.lower()
                
                # Exact match
                if expected_lower in detected_lower:
                    continue
                
                # Fuzzy match - check if partial match exists
                matched = False
                for detected in detected_lower:
                    # Check various label aliases
                    if self._is_label_match(expected_lower, detected):
                        matched = True
                        break
                
                if not matched:
                    return False
            
            return True
        
        def _is_label_match(self, expected: str, detected: str) -> bool:
            """Check if two label names refer to the same entity type"""
            aliases = {
                "ssn": ["social_security_number", "tax_identification_number", "tax_file_number", "tfn", "id"],
                "email": ["email_address"],
                "phone_us": ["phone", "phone_number", "telephone"],
                "phone": ["phone_us", "phone_number", "telephone"],
                "credit_card": ["card_number", "card"],
                "person_name": ["name", "person", "person_name"],
                "medical_record": ["mrn", "record_number", "patient_id"],
                "medical_condition": ["disease", "diagnosis", "condition"],
                "medication": ["drug", "medicine", "drug_name"],
                "date": ["date_of_birth", "dob", "date"],
                "organization": ["org", "company", "organization"],
                "tfn": ["tax_file_number", "ssn"],
                "abn": ["australian_business_number"],
                "acn": ["australian_company_number"],
                "medicare": ["medicare_number"],
                "medical_record": ["mrn", "medical_record_number"],
            }
            
            expected = expected.strip().lower()
            detected = detected.strip().lower()
            
            if expected == detected:
                return True
            
            # Check if either is in the other's alias list
            for key, values in aliases.items():
                key = key.lower()
                values_lower = [v.lower() for v in values]
                all_variants = [key] + values_lower
                
                if expected in all_variants and detected in all_variants:
                    return True
            
            # Check substring match (for compound labels)
            if len(expected) > 3 and len(detected) > 3:
                if expected in detected or detected in expected:
                    return True
            
            return False

        def run_detector_test(self, detector_config: Dict, detector_name: str):
            """Test with a specific detector configuration"""
            print(f"\n{'='*70}")
            print(f"Testing: {detector_name}")
            print(f"{'='*70}")
            
            detector_results = {
                "name": detector_name,
                "total": 0,
                "passed": 0,
                "failed": 0,
                "total_time": 0.0,
                "avg_time": 0.0,
                "accuracy": 0.0,
                "true_positives": 0,
                "false_positives": 0,
                "false_negatives": 0,
                "precision": 0.0,
                "recall": 0.0,
                "f1_score": 0.0,
                "failures": []
            }
            
            try:
                pipeline = RedactionPipeline(RedactionConfig(**detector_config))
            except RuntimeError as e:
                print(f"[WARN] Skipped: {str(e)}")
                return None
            
            for idx, case in enumerate(self.test_cases, 1):
                if case.country != detector_config.get("country", "US"):
                    continue
                    
                start = time.time()
                try:
                    result = pipeline.redact(case.text)
                    elapsed = time.time() - start
                    
                    # Check if expected labels were detected
                    detected_labels = {span['label'] for span in result['spans']}
                    expected_set = set(case.expected_labels)
                    
                    # Calculate TP, FP, FN for this case
                    tp = len(detected_labels & expected_set)  # Intersection
                    fp = len(detected_labels - expected_set)  # In detected but not expected
                    fn = len(expected_set - detected_labels)  # In expected but not detected
                    
                    detector_results["true_positives"] += tp
                    detector_results["false_positives"] += fp
                    detector_results["false_negatives"] += fn
                    
                    # For cases with no expected labels, pass if no entities found
                    if len(case.expected_labels) == 0:
                        passed = len(detected_labels) == 0
                    else:
                        # Check if expected labels are fuzzy-matched in detected labels
                        passed = self._label_matches(detected_labels, case.expected_labels)
                    
                    detector_results["total"] += 1
                    detector_results["total_time"] += elapsed
                    
                    if passed:
                        detector_results["passed"] += 1
                        status = "[PASS]"
                    else:
                        detector_results["failed"] += 1
                        status = "[FAIL]"
                        detector_results["failures"].append({
                            "case": case.description,
                            "expected": case.expected_labels,
                            "found": list(detected_labels),
                            "text_sample": case.text[:60]
                        })
                    
                    if idx % 10 == 0:  # Progress every 10 cases
                        print(f"  [{idx}/{len(self.test_cases)}] {status} - {elapsed:.4f}s")
                        
                except Exception as e:
                    detector_results["failed"] += 1
                    detector_results["false_negatives"] += len(case.expected_labels)  # Missed all expected
                    detector_results["failures"].append({
                        "case": case.description,
                        "error": str(e)[:100]
                    })
                    detector_results["total"] += 1
            
            if detector_results["total"] > 0:
                detector_results["avg_time"] = detector_results["total_time"] / detector_results["total"]
                detector_results["accuracy"] = (detector_results["passed"] / detector_results["total"]) * 100
                
                # Calculate precision and recall
                precision, recall, f1 = self._calculate_metrics(
                    detector_results["true_positives"],
                    detector_results["false_positives"],
                    detector_results["false_negatives"]
                )
                detector_results["precision"] = precision
                detector_results["recall"] = recall
                detector_results["f1_score"] = f1
            
            self.results["by_detector"][detector_name] = detector_results
            return detector_results

        def print_results(self, results: Dict):
            """Print test results"""
            if not results:
                return
            
            print(f"\n{'─'*70}")
            print(f"Results: {results['name']}")
            print(f"{'─'*70}")
            print(f"  Total Cases:   {results['total']}")
            print(f"  Passed:        {results['passed']} ({results['accuracy']:.1f}%)")
            print(f"  Failed:        {results['failed']}")
            print(f"  Precision:     {results['precision']:.4f}")
            print(f"  Recall:        {results['recall']:.4f}")
            print(f"  F1 Score:      {results['f1_score']:.4f}")
            print(f"  Avg Time:      {results['avg_time']:.4f}s per case")
            print(f"  Total Time:    {results['total_time']:.2f}s")
            
            if results['failures'] and results['failed'] <= 5:
                print(f"\n  Failures:")
                for failure in results['failures'][:5]:
                    if 'error' in failure:
                        print(f"    - {failure['case']}: {failure['error']}")
                    else:
                        print(f"    - {failure['case']}")
                        print(f"      Expected: {failure['expected']} | Found: {failure['found']}")

        def run_all_tests(self):
            """Run comprehensive stress tests"""
            print("\n" + "="*70)
            print("ZEROPHIX STRESS TEST - 200 Test Cases (100 US + 100 AU)")
            print("Testing: Regex, ML Models, Ensemble Voting, Adaptive Weights")
            print("="*70)
            
            # Test configurations - comprehensive detector comparison
            configs = [
                # ========== US: Individual Detectors ==========
                (
                    {"country": "US", "use_spacy": False, "use_bert": False, "use_gliner": False, "use_openmed": False},
                    "US_01_Regex_Only"
                ),
                (
                    {"country": "US", "use_bert": True, "use_spacy": False, "use_gliner": False, "use_openmed": False},
                    "US_02_BERT_Only"
                ),
                (
                    {"country": "US", "use_gliner": True, "use_spacy": False, "use_bert": False, "use_openmed": False},
                    "US_03_GLiNER_Only"
                ),
                (
                    {"country": "US", "use_openmed": True, "use_spacy": False, "use_bert": False, "use_gliner": False},
                    "US_04_OpenMed_Only"
                ),
                
                # ========== US: Pairs (Ensemble) ==========
                (
                    {"country": "US", "use_bert": True, "use_gliner": True, "use_spacy": False, "use_openmed": False, "enable_ensemble_voting": True},
                    "US_05_BERT+GLiNER_Ensemble"
                ),
                (
                    {"country": "US", "use_bert": True, "use_openmed": True, "use_spacy": False, "use_gliner": False, "enable_ensemble_voting": True},
                    "US_06_BERT+OpenMed_Ensemble"
                ),
                (
                    {"country": "US", "use_gliner": True, "use_openmed": True, "use_spacy": False, "use_bert": False, "enable_ensemble_voting": True},
                    "US_07_GLiNER+OpenMed_Ensemble"
                ),
                
                # ========== US: Triple (Ensemble) ==========
                (
                    {"country": "US", "use_bert": True, "use_gliner": True, "use_openmed": True, "use_spacy": False, "enable_ensemble_voting": True},
                    "US_08_BERT+GLiNER+OpenMed_Ensemble"
                ),
                (
                    {"country": "US", "use_bert": True, "use_gliner": True, "use_openmed": True, "use_spacy": False, "enable_ensemble_voting": True, "enable_adaptive_weights": True, "adaptive_weight_method": "f1_squared"},
                    "US_09_Triple_Ensemble_Adaptive_F1"
                ),
                
                # ========== AU: Individual Detectors ==========
                (
                    {"country": "AU", "use_spacy": False, "use_bert": False, "use_gliner": False, "use_openmed": False},
                    "AU_01_Regex_Only"
                ),
                (
                    {"country": "AU", "use_bert": True, "use_spacy": False, "use_gliner": False, "use_openmed": False},
                    "AU_02_BERT_Only"
                ),
                (
                    {"country": "AU", "use_gliner": True, "use_spacy": False, "use_bert": False, "use_openmed": False},
                    "AU_03_GLiNER_Only"
                ),
                (
                    {"country": "AU", "use_openmed": True, "use_spacy": False, "use_bert": False, "use_gliner": False},
                    "AU_04_OpenMed_Only"
                ),
                
                # ========== AU: Pairs (Ensemble) ==========
                (
                    {"country": "AU", "use_bert": True, "use_gliner": True, "use_spacy": False, "use_openmed": False, "enable_ensemble_voting": True},
                    "AU_05_BERT+GLiNER_Ensemble"
                ),
                (
                    {"country": "AU", "use_bert": True, "use_openmed": True, "use_spacy": False, "use_gliner": False, "enable_ensemble_voting": True},
                    "AU_06_BERT+OpenMed_Ensemble"
                ),
                (
                    {"country": "AU", "use_gliner": True, "use_openmed": True, "use_spacy": False, "use_bert": False, "enable_ensemble_voting": True},
                    "AU_07_GLiNER+OpenMed_Ensemble"
                ),
                
                # ========== AU: Triple (Ensemble) ==========
                (
                    {"country": "AU", "use_bert": True, "use_gliner": True, "use_openmed": True, "use_spacy": False, "enable_ensemble_voting": True},
                    "AU_08_BERT+GLiNER+OpenMed_Ensemble"
                ),
                (
                    {"country": "AU", "use_bert": True, "use_gliner": True, "use_openmed": True, "use_spacy": False, "enable_ensemble_voting": True, "enable_adaptive_weights": True, "adaptive_weight_method": "f1_squared"},
                    "AU_09_Triple_Ensemble_Adaptive_F1"
                ),
            ]
            
            for config, name in configs:
                results = self.run_detector_test(config, name)
                if results:
                    self.print_results(results)
            
            # Summary
            self._print_summary()

        def _print_summary(self):
            """Print overall summary"""
            if not self.results["by_detector"]:
                return
            
            print(f"\n\n{'='*90}")
            print("OVERALL SUMMARY")
            print(f"{'='*90}\n")
            
            print(f"{'Detector':<35} {'Accuracy':<10} {'Precision':<10} {'Recall':<10} {'F1':<10} {'Status':<8}")
            print(f"{'-'*90}")
            
            for name, results in self.results["by_detector"].items():
                status = "PASS" if results["accuracy"] >= 80 else "WARN" if results["accuracy"] >= 50 else "FAIL"
                print(f"{name:<35} {results['accuracy']:>6.1f}%   {results['precision']:>8.4f}  {results['recall']:>8.4f}  {results['f1_score']:>8.4f}  {status:>6}")
            
            # Best detector
            best = max(self.results["by_detector"].items(), key=lambda x: x[1]["accuracy"])
            fastest = min(self.results["by_detector"].items(), key=lambda x: x[1]["avg_time"])
            best_precision = max(self.results["by_detector"].items(), key=lambda x: x[1]["precision"])
            best_recall = max(self.results["by_detector"].items(), key=lambda x: x[1]["recall"])
            
            print(f"\n{'Best Accuracy:':<30} {best[0]} ({best[1]['accuracy']:.1f}%)")
            print(f"{'Best Precision:':<30} {best_precision[0]} ({best_precision[1]['precision']:.4f})")
            print(f"{'Best Recall:':<30} {best_recall[0]} ({best_recall[1]['recall']:.4f})")
            print(f"{'Fastest:':<30} {fastest[0]} ({fastest[1]['avg_time']:.4f}s/case)")
            
            # Save detailed results
            self._save_results()

        def _save_results(self):
            """Save detailed results to JSON"""
            output_file = "stress_test_results.json"
            with open(output_file, "w") as f:
                json.dump(self.results["by_detector"], f, indent=2)
            print(f"\n[OK] Detailed results saved to: {output_file}")


    if __name__ == "__main__":
        tester = StressTest()
        tester.run_all_tests()
