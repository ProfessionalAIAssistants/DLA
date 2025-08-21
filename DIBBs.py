#!/usr/bin/env python
# coding: utf-8

# Modified DIBBs.py for Local File Processing
# Removed Google Drive dependencies and uses local folders

import fitz
import csv
import re
import os
import json
import shutil
import uuid
from datetime import datetime
from pathlib import Path

# Local directory configuration
base_dir = Path(__file__).parent
pdf_dir = base_dir / "To Process"
summary_dir = base_dir / "Output"
automation_dir = base_dir / "Automation"
reviewed_dir = base_dir / "Reviewed"

# Webhook URL (optional - set to None if not using)
webhook_url = None  # Set your webhook URL here if needed

def extract_text_from_pdf(pdf_file):
    text = ""
    with fitz.open(pdf_file) as doc:
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            text += page.get_text()
    return text

def find_table_page(pdf_file, keyword):
    doc = fitz.open(pdf_file)
    for page_number in range(len(doc)):
        page = doc.load_page(page_number)
        text = page.get_text()
        if keyword in text:
            return page_number
    return None

def starts_with_word_without_numbers(line):
    # Check if the line starts with a word that doesn't contain any numbers
    words = line.strip().split()
    if words:
        first_word = words[0]
        return not any(char.isdigit() for char in first_word)
    return False

def create_summary_files(today_str):
    # Create directories if they don't exist
    summary_dir.mkdir(exist_ok=True)
    automation_dir.mkdir(exist_ok=True)
    reviewed_dir.mkdir(exist_ok=True)
    
    csv_file_path = summary_dir / f"{today_str}_output.csv"
    skipped_csv_file_path = summary_dir / f"{today_str}_skipped.csv"

    header_row = ["PDF File", "PDF Name", "REQUEST NO.", "Open Date", "Close Date", "PURCHASE NO", "NSN", "FSC",
                  "Delivery Days", "Payment History", "Unit", "Quantity", "FOB", "ISO", "Inspection Point",
                  "Sampling", "Product Description", "MFR", "Packaging", "Package Type", "Skipped", "office",
                  "division", "address", "buyer", "buyer_code", "telephone", "email", "fax", "buyer_info"]

    # Create output CSV file if it doesn't exist
    if not csv_file_path.exists():
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(header_row)

def get_file_url(file_name):
    # For local processing, return the local file path instead of Google Drive URL
    file_path = automation_dir / file_name
    if file_path.exists():
        return str(file_path.absolute())
    else:
        return f"Local file: {file_name}"

def move_files(pdf_file, pdf_destination_folder):
    pdf_name = os.path.basename(pdf_file)

    if pdf_destination_folder:
        # Move file to automation folder
        destination_pdf = os.path.join(pdf_destination_folder, pdf_name)
        if os.path.exists(destination_pdf):
            os.remove(destination_pdf)
        shutil.move(pdf_file, pdf_destination_folder)
        print(f"Moved {pdf_name} to {pdf_destination_folder}")
    else:
        # Move file to reviewed folder
        skipped_file_path = reviewed_dir
        skipped_file_path.mkdir(exist_ok=True)
        destination_pdf = skipped_file_path / pdf_name
        if destination_pdf.exists():
            destination_pdf.unlink()
        shutil.copy(pdf_file, skipped_file_path)
        print(f"Moved {pdf_name} to {skipped_file_path}")
        os.remove(pdf_file)

def extract_table_text(pdf_file, keyword, skip_count):
    table_page = find_table_page(pdf_file, keyword)
    if table_page is not None:
        doc = fitz.open(pdf_file)
        page = doc.load_page(table_page)
        text = page.get_text("text")
        output_text = ""
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if keyword in line:
                # Start displaying lines after keyword line
                output_text += line + "\n"
                start_index = i + skip_count
                break

        # Accumulate lines till an empty line or a line with numbers at the start is encountered
        for line in lines[start_index:]:
            line = line.strip()
            if starts_with_word_without_numbers(line):
                break
            else:
                output_text += line + "\n"
        return (output_text)

def find_request_numbers(text):
    request_no_pattern = r'1\. REQUEST NO\.\s*(\S+)\s*'
    match = re.search(request_no_pattern, text)
    if match:
        return match.group(1)
    else:
        return None

def find_buyer(text):
    buyer = {}

    # Regex pattern to find the information block
    pattern = r'''
        ^(DLA.*?)\n                               # First line (DLA Subset)
        (.*?)\n                                   # Second line (Division)
        (.*?)\n                                   # Third line (often address)
        (.*?)\n                                   # Fourth line (city, state, zip)
        (USA)\s*\n                                # Fifth line (always USA)
        Name:\s*(.*?)\s+                          # Name
        Buyer\s*Code:(\w+)\s+                     # Buyer Code
        Tel:\s*(.*?)\s+                           # Telephone
        (?:Fax:\s*([\d-]+)\s+)?                   # Fax (optional)
        Email:\s*([^\s]+@[^\s]+)                  # Email
    '''

    # Find all matches in the document
    match = re.search(pattern, text, re.MULTILINE | re.VERBOSE | re.IGNORECASE)

    if match:
        buyer["office"] = match.group(1)
        buyer["division"] = match.group(2)
        buyer["address"] = match.group(3) + " " + match.group(4)
        buyer["name"] = match.group(6)
        buyer["buyer_code"] = match.group(7)
        buyer["tel"] = match.group(8)
        buyer["fax"] = match.group(9) if match.group(9) else "N/A"
        buyer["email"] = match.group(10)
    else:
        buyer["office"] = "Check Manually"
        buyer["division"] = "Check Manually"
        buyer["address"] = "Check Manually"
        buyer["name"] = "Check Manually"
        buyer["buyer_code"] = "Check Manually"
        buyer["tel"] = "Check Manually"
        buyer["fax"] = "Check Manually"
        buyer["email"] = "Check Manually"

    # Regular expression pattern
    pattern = r'DLA.*?(?=\s*6\. DELIVER)'

    # Extract information using regular expression
    matches = re.findall(pattern, text, re.DOTALL)
    # Print the matches
    for match in matches:
        buyer["info"] = match.strip()

    return buyer

def find_packaging_type(text):
    astm_pattern = r'(ASTM)'
    match = re.search(astm_pattern, text)
    if match:
        return "ASTM"
    else:
        mil_stand_pattern = r'(MIL-STD-)'
        match = re.search(mil_stand_pattern, text)
        if match:
            return match.group(1)
        else:
            return "ERROR"

def find_purchase_numbers(text):
    purchase_no_pattern = r'3\.\s*REQUISITION/PURCHASE REQUEST NO\.\s*(\S+)\s*'
    match = re.search(purchase_no_pattern, text)
    if match:
        return match.group(1)
    else:
        return "Manually Check"

def find_nsn_and_fsc(text):
    nsn_fsc_pattern = r'NSN/FSC:(\d+)/(\d+)'
    matches = re.search(nsn_fsc_pattern, text)
    if matches:
        fsc = matches.group(2)
        nsn = fsc + matches.group(1)
        return nsn, fsc
    else:
        nsn_material_pattern = r'NSN/MATERIAL:(\d+)'
        matches = re.search(nsn_material_pattern, text)
        if matches:
            if not matches.group(1).startswith(("5331", "5330")):
              nsn = "5331"+ matches.group(1)
            else:
              nsn = matches.group(1)
            return nsn, "Manually Check"
        else:
            return "Manually Check", "Manually Check"

def find_delivery_days(text):
    delivery_days_pattern = r'6. DELIVER BY\s*\S*\s*(\d+)'
    match = re.search(delivery_days_pattern, text)
    if match:
        return match.group(1)
    else:
        return "999"

def find_payment_history(pdf_file):
    table_search_term = "CAGE   Contract Number      Quantity   Unit Cost    AWD Date  Surplus Material"
    table = extract_table_text(pdf_file, table_search_term, 3)
    if table:
        # Split the table text into lines
        lines = table.strip().split('\n')

        # Find the index of UI and QUANTITY columns
        headers = ['CAGE', 'Contract', 'Number', 'Quantity', 'Unit Cost', 'AWD Date', 'Surplus Material']

        # Initialize indices to None
        cage_index = None
        quantity_index = None
        cost_index = None
        date_index = None

        # Find the indices of the headers
        for i, header in enumerate(headers):
            if "CAGE" in header:
                cage_index = i
            elif "Quantity" in header:
                quantity_index = i -1
            elif "Unit" in header and "Cost" in header:
                cost_index = i - 1
            elif "AWD" in header and "Date" in header:
                date_index = i - 1

        if cage_index is not None and quantity_index is not None and cost_index is not None and date_index is not None:

            message = ""

            # Extract data for each row starting from the second line
            for line in lines[1:]:
                row_values = line.split()
                cage = row_values[cage_index]
                quantity = str(round(float(row_values[quantity_index])))
                cost = str("{:.2f}".format(round(float(row_values[cost_index]), 2)))
                date = row_values[date_index]
                message += quantity + "@ $" + cost + " on " + date + "\n"

            return message
        else:
            print("Required headers not found in the table.")
            return "Manually Check"
    else:
        print("Table not found in the PDF.")
        return "Manually Check"

def find_FOB(text):
    FOB_pattern = r'FOB:\s*(\w+)'
    match = re.search(FOB_pattern, text)
    if match:
        return match.group(1)
    else:
        return "Manually Check"

def find_inspection_point(text):
    inspection_point_pattern = r'INSPECTION\s*POINT:\s*(\w+)'
    match = re.search(inspection_point_pattern, text)
    if match:
        return match.group(1)
    else:
        return None

def find_product_description(text):
    product_description_pattern = r'ITEM\s*DESCRIPTION \s*(.*)'
    match = re.search(product_description_pattern, text)
    if match:
        return match.group(1)
    else:
        return "Manually Check"

def find_mfr(text):
    mfr_pattern = r'^(.+?\s+\w{5}\s+P/N\s+.+)$'
    matches = re.findall(mfr_pattern, text, re.MULTILINE)

    if matches:
        return '\n'.join(match.strip() for match in matches)
    return "Manually Check"

def find_ISO(text):
    ISO_pattern = r'(ISO\s*.*\s*.*)'
    match = re.search(ISO_pattern, text)
    if match:
        return "YES"
    else:
        return "NO"

def find_bid_dates(text):
    # Regular expression to match dates in "YYYY MONTH DD" format
    date_pattern = r'(\d{4})\s+(\w{3})\s+(\d{1,2})'

    # Find all occurrences of dates in the text
    matches = re.findall(date_pattern, text)

    if matches:
        num_matches = len(matches)
        open_date = str(matches[0][1] + " " + matches[0][2] + ", " + matches[0][0])
        close_date = str(matches[1][1] + " " + matches[1][2] + ", " + matches[1][0])
        return open_date, close_date

    else:
        return None, None

def find_sampling(text):
    inspection_point_pattern = r'SAMPLING\s*.*\s*(.*)'
    match = re.search(inspection_point_pattern, text)
    if match:
        return "YES"
    else:
        return "NO"

def find_packaging(text):
    # Define the regular expression pattern
    pattern = r'PKGING DATA - (.+?)(?=\n\s*\n|\Z)'
    # Search for the pattern in the text
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1)
    else:
        return "Manually Check PDF"

def find_package_type(text):
    package_pattern = r'ASTM'
    match = re.search(package_pattern, text)
    if match:
        return "ASTM"
    else:
        package_patern = r'(MIL-STD-[^\s]*)'
        match = re.search(package_patern, text)
        if match:
            return match.group(1).replace(",", "")
        else:
          return None

def find_unit_details(pdf_file):
    table_search_term = "CLIN  PR              PRLI       UI    QUANTITY          UNIT PRICE       TOTAL PRICE      . "
    table = extract_table_text(pdf_file, table_search_term, 1)

    if table:
        # Split the table text into lines
        lines = table.split('\n')

        # Find the index of UI and QUANTITY columns
        headers = lines[0].split()
        ui_index = headers.index("UI")
        quantity_index = headers.index("QUANTITY")

        # Extract UI and Quantity values from the second line
        ui = lines[1].split()[ui_index]
        quantity = round(float(re.sub(r'[^\d.]', '', lines[1].split()[quantity_index])))

        return ui, quantity
    else:
        return None, -999

def process_pdf(pdf_file):
    text = extract_text_from_pdf(pdf_file)
    request_number = find_request_numbers(text)
    open_date, close_date = find_bid_dates(text)
    purchase_number = find_purchase_numbers(text)
    nsn, fsc = find_nsn_and_fsc(text)
    delivery_days = find_delivery_days(text)
    payment_history = find_payment_history(pdf_file)
    unit, quantity = find_unit_details(pdf_file)
    fob = find_FOB(text)
    iso = find_ISO(text)
    inspection_point = find_inspection_point(text)
    sampling = find_sampling(text)
    product_description = find_product_description(text)
    mfr = find_mfr(text)
    packaging = find_packaging(text)
    package_type = find_package_type(text)
    buyer = find_buyer(text)
    url = get_file_url(os.path.basename(pdf_file))
    pdf_name = os.path.basename(pdf_file)

    print(nsn)

    return {
        "solicitation_url": url,
        "pdf_name": pdf_name,
        "request_number": request_number,
        "open_date": open_date,
        "close_date": close_date,
        "purchase_number": purchase_number,
        "nsn": nsn,
        "fsc": fsc,
        "delivery_days": delivery_days,
        "payment_history": payment_history,
        "unit": unit,
        "quantity": quantity,
        "fob": fob,
        "iso": iso,
        "inspection_point": inspection_point,
        "sampling": sampling,
        "product_description": product_description,
        "mfr": mfr,
        "packaging": packaging,
        "package_type": package_type,
        "skipped": False,
        "office": buyer["office"],
        "division": buyer["division"],
        "address": buyer["address"],
        "buyer": buyer["name"],
        "buyer_code": buyer["buyer_code"],
        "telephone": buyer["tel"],
        "email": buyer["email"],
        "fax": buyer["fax"],
        "buyer_info": buyer["info"],
    }

def send_to_webhook(data):
    """Send data to webhook if configured"""
    if webhook_url is None:
        print("No webhook configured, skipping webhook transmission")
        return
    
    try:
        import requests
        json_data = json.dumps(data, indent=4)
        
        # Save to local automation folder
        pdf_destination_folder = automation_dir / data['nsn'] / data['request_number']
        pdf_destination_folder.mkdir(parents=True, exist_ok=True)

        summary_file = pdf_destination_folder / f"{data['request_number']}.txt"
        with open(summary_file, 'w') as f:
            f.write(json_data)

        response = requests.post(webhook_url, json=data)
        print(f"Webhook Response: {response.status_code}")
    except ImportError:
        print("Requests library not available for webhook, saving locally only")
    except Exception as e:
        print(f"Webhook error: {e}")

def main(pdf_input_dir=None):
    # Use provided directory or default
    input_dir = Path(pdf_input_dir) if pdf_input_dir else pdf_dir
    
    today_str = datetime.today().strftime("%Y-%m-%d")
    create_summary_files(today_str)

    csv_file_path = summary_dir / f"{today_str}_output.csv"

    with open(csv_file_path, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        for file_name in os.listdir(input_dir):
            if file_name.lower().endswith(".pdf"):
                pdf_file = input_dir / file_name
                pdf_data = process_pdf(str(pdf_file))

                # move pdf file to final destination
                if (pdf_data['delivery_days'] and
                  int(pdf_data['delivery_days']) >= 120 and
                  pdf_data['iso'] == "NO" and
                  pdf_data['sampling'] == "NO" and
                  pdf_data['inspection_point'] == "DESTINATION" and
                  any(manufacturer.lower() in pdf_data['mfr'].lower() for manufacturer in ["Parker"])):
                    pdf_destination = automation_dir / pdf_data['nsn'] / pdf_data['request_number']
                    pdf_destination.mkdir(parents=True, exist_ok=True)
                    print("Made PDF Folder: " + str(pdf_destination))
                    move_files(str(pdf_file), str(pdf_destination))
                else:
                    pdf_data['skipped'] = True
                    move_files(str(pdf_file), None)

                #Record the summary file
                writer.writerow(pdf_data.values())
                print(pdf_data.values())

                #send to webhook for n8n (optional)
                send_to_webhook(pdf_data)

if __name__ == "__main__":
    print("Starting Local DIBBs PDF Processing...")
    print(f"Input folder: {pdf_dir}")
    print(f"Output folder: {summary_dir}")
    print(f"Automation folder: {automation_dir}")
    print(f"Reviewed folder: {reviewed_dir}")
    
    main()
    print("Completed")
