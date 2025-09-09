#!/usr/bin/env python
# coding: utf-8

# DIBBs CRM Integration Processor
# Integrates DIBBS.py PDF processing with CRM database

import fitz
import csv
import re
import os
import json
import shutil
import uuid
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Add the src directory to the path for imports
src_dir = Path(__file__).parent.parent
sys.path.insert(0, str(src_dir))

from core import crm_data
from core.config_manager import config_manager

# Create module reference for backward compatibility
crm_data = crm_data.crm_data

class DIBBsCRMProcessor:
    def __init__(self):
        # Use config manager for directory configuration
        self.config = config_manager
        self.base_dir = Path(__file__).parent.parent.parent  # Root directory of the project
        self.pdf_dir = self.config.get_upload_dir()
        self.summary_dir = self.config.get_output_dir()
        self.automation_dir = self.config.get_data_dir() / "processed" / "Automation"
        self.reviewed_dir = self.config.get_processed_dir()
        
        # Ensure directories exist
        self.config.ensure_directories()
        self.automation_dir.mkdir(parents=True, exist_ok=True)
        
        # Processing results tracking
        self.results = {
            'processed': 0,
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'errors': [],
            'created_opportunities': [],
            'created_contacts': [],
            'updated_contacts': [],
            'created_accounts': [],
            'updated_accounts': [],
            'created_products': [],
            'created_tasks': [],
            'detailed_report': '',
            'processed_files': [],
            'skipped_files': [],
            'error_files': []
        }
        
        # Default settings for PDF processing filters
        self.settings_file = self.base_dir / "config/settings.json"
        self.settings = self.load_settings()

    def load_settings(self) -> Dict[str, Any]:
        """Load settings from file or create default settings"""
        default_settings = {
            'min_delivery_days': 120,
            'iso_required': 'NO',
            'sampling_required': 'NO',
            'inspection_point': 'DESTINATION',
            'manufacturer_filters': ['Parker'],
            'auto_process': True
        }
        
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                # Merge with defaults to ensure all keys exist
                default_settings.update(settings)
                return default_settings
            else:
                # Create default settings file
                self.save_settings(default_settings)
                return default_settings
        except Exception as e:
            print(f"Error loading settings: {e}")
            return default_settings
    
    def save_settings(self, settings: Dict[str, Any]):
        """Save settings to file"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            self.settings = settings
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def get_filter_settings(self) -> Dict[str, Any]:
        """Get current filter settings - reload from file to ensure latest values"""
        self.settings = self.load_settings()  # Reload from file
        return self.settings.copy()
    
    def update_filter_settings(self, new_settings: Dict[str, Any]):
        """Update filter settings"""
        self.settings.update(new_settings)
        self.save_settings(self.settings)
        print(f"Settings updated and saved: {self.settings}")
        # Reload settings to ensure they're properly persisted
        self.settings = self.load_settings()

    def extract_text_from_pdf(self, pdf_file):
        """Extract text from PDF file"""
        text = ""
        with fitz.open(pdf_file) as doc:
            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                text += page.get_text()
        return text

    def find_table_page(self, pdf_file, keyword):
        """Find page containing specific keyword"""
        doc = fitz.open(pdf_file)
        for page_number in range(len(doc)):
            page = doc.load_page(page_number)
            text = page.get_text()
            if keyword in text:
                return page_number
        return None

    def starts_with_word_without_numbers(self, line):
        """Check if line starts with word without numbers"""
        words = line.strip().split()
        if words:
            first_word = words[0]
            return not any(char.isdigit() for char in first_word)
        return False

    def find_request_numbers(self, text, keyword):
        """Extract request numbers from text"""
        lines = text.split("\n")
        matching_lines = []
        
        for line in lines:
            if keyword in line and self.starts_with_word_without_numbers(line):
                matching_lines.append(line)
        
        request_numbers = []
        for line in matching_lines:
            # Extract potential request numbers
            parts = line.split()
            for part in parts:
                if re.match(r'^[A-Z]{4}[0-9][A-Z][0-9]{2}[A-Z][0-9]{4}$', part):
                    request_numbers.append(part)
        
        return request_numbers

    def create_summary_files(self, today_str):
        """Create necessary output directories and files"""
        csv_file_path = self.summary_dir / f"{today_str}_output.csv"
        
        if not csv_file_path.exists():
            headers = ['request_number', 'nsn', 'quantity', 'unit', 'mfr', 'delivery_days', 
                      'fob', 'packaging_type', 'iso', 'sampling', 'inspection_point', 'skipped']
            
            with open(csv_file_path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(headers)

    def move_files(self, source_path, destination_folder):
        """Move processed files to appropriate folder"""
        # DEVELOPMENT: File moving commented out for testing purposes
        # source = Path(source_path)
        
        # if destination_folder:
        #     # Move to automation folder
        #     destination = Path(destination_folder) / source.name
        # else:
        #     # Move to reviewed folder
        #     destination = self.reviewed_dir / source.name
        
        # try:
        #     # Ensure destination directory exists
        #     destination.parent.mkdir(parents=True, exist_ok=True)
        #     shutil.move(str(source), str(destination))
        #     print(f"Moved {source.name} to {destination.parent}")
        # except Exception as e:
        #     print(f"Error moving file {source.name}: {e}")
        
        print(f"DEVELOPMENT MODE: File moving disabled - {Path(source_path).name} remains in To Process")

    def find_request_numbers(self, text):
        """Find request numbers using DIBBs.py pattern"""
        request_no_pattern = r'1\. REQUEST NO\.\s*(\S+)\s*'
        match = re.search(request_no_pattern, text)
        if match:
            return match.group(1)
        else:
            return None

    def find_buyer(self, text):
        """Find buyer information using DIBBs.py pattern"""
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

    def find_nsn_and_fsc(self, text):
        """Find NSN and FSC using DIBBs.py pattern"""
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
                    nsn = "5331" + matches.group(1)
                else:
                    nsn = matches.group(1)
                return nsn, "Manually Check"
            else:
                return "Manually Check", "Manually Check"

    def find_delivery_days(self, text):
        """Find delivery days using DIBBs.py pattern"""
        delivery_days_pattern = r'6. DELIVER BY\s*\S*\s*(\d+)'
        match = re.search(delivery_days_pattern, text)
        if match:
            return match.group(1)
        else:
            return "999"

    def extract_table_text(self, pdf_file, keyword, skip_count):
        """Extract table text from PDF starting after a keyword"""
        table_page = self.find_table_page(pdf_file, keyword)
        if table_page is not None:
            try:
                import fitz
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
                    if self.starts_with_word_without_numbers(line):
                        break
                    else:
                        output_text += line + "\n"
                return output_text
            except Exception:
                return None
        return None

    def find_unit_details(self, pdf_file):
        """Find unit and quantity details using DIBBs.py pattern"""
        table_search_term = "CLIN  PR              PRLI       UI    QUANTITY          UNIT PRICE       TOTAL PRICE      . "
        table = self.extract_table_text(pdf_file, table_search_term, 1)

        if table:
            # Split the table text into lines
            lines = table.split('\n')

            # Find the index of UI and QUANTITY columns
            headers = lines[0].split()
            try:
                ui_index = headers.index("UI")
                quantity_index = headers.index("QUANTITY")

                # Extract UI and Quantity values from the second line
                ui = lines[1].split()[ui_index]
                quantity = round(float(re.sub(r'[^\d.]', '', lines[1].split()[quantity_index])))

                return ui, quantity
            except (ValueError, IndexError):
                return None, -999
        else:
            return None, -999

    def find_bid_dates(self, text):
        """Find bid dates using DIBBs.py pattern"""
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

    def find_FOB(self, text):
        """Find FOB using DIBBs.py pattern"""
        FOB_pattern = r'FOB:\s*(\w+)'
        match = re.search(FOB_pattern, text)
        if match:
            return match.group(1)
        else:
            return "Manually Check"

    def find_inspection_point(self, text):
        """Find inspection point using DIBBs.py pattern"""
        inspection_point_pattern = r'INSPECTION\s*POINT:\s*(\w+)'
        match = re.search(inspection_point_pattern, text)
        if match:
            return match.group(1)
        else:
            return None

    def find_product_description(self, text):
        """Find product description using DIBBs.py pattern"""
        product_description_pattern = r'ITEM\s*DESCRIPTION \s*(.*)'
        match = re.search(product_description_pattern, text)
        if match:
            return match.group(1)
        else:
            return "Manually Check"

    def find_mfr(self, text):
        """Find manufacturer using enhanced pattern matching for various formats"""
        # Look for IAW BASIC SPEC format (priority pattern) - line-based approach
        lines = text.split('\n')
        mfr_lines = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('IAW BASIC SPEC NR'):
                mfr_lines.append(line)
            elif line.startswith('IAW REFERENCE SPEC NR'):
                mfr_lines.append(line)
            elif line.startswith('REVISION NR') and 'DTD' in line:
                mfr_lines.append(line)
            elif line.startswith('PART PIECE NUMBER:'):
                mfr_lines.append(line)
        
        if mfr_lines:
            return ' '.join(mfr_lines)
        
        # Fallback to original P/N pattern for other document types
        mfr_pattern = r'^(.+?\s+\w{5}\s+P/N\s+.+)$'
        matches = re.findall(mfr_pattern, text, re.MULTILINE)

        if matches:
            return '\n'.join(match.strip() for match in matches)
        
        return "Manually Check"

    def find_ISO(self, text):
        """Find ISO requirement using DIBBs.py pattern"""
        ISO_pattern = r'(ISO\s*.*\s*.*)'
        match = re.search(ISO_pattern, text)
        if match:
            return "YES"
        else:
            return "NO"

    def find_sampling(self, text):
        """Find sampling requirement using DIBBs.py pattern"""
        inspection_point_pattern = r'SAMPLING\s*.*\s*(.*)'
        match = re.search(inspection_point_pattern, text)
        if match:
            return "YES"
        else:
            return "NO"

    def find_packaging(self, text):
        """Find packaging information using DIBBs.py pattern"""
        # Define the regular expression pattern
        pattern = r'PKGING DATA - (.+?)(?=\n\s*\n|\Z)'
        # Search for the pattern in the text
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1)
        else:
            return "Manually Check PDF"

    def find_package_type(self, text):
        """Find package type using DIBBs.py pattern"""
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

    def find_purchase_numbers(self, text):
        """Find purchase numbers using DIBBs.py pattern"""
        purchase_no_pattern = r'3\.\s*REQUISITION/PURCHASE REQUEST NO\.\s*(\S+)\s*'
        match = re.search(purchase_no_pattern, text)
        if match:
            return match.group(1)
        else:
            return "Manually Check"

    def find_payment_history(self, pdf_file):
        """Extract payment history from PDF table"""
        table_search_term = "CAGE   Contract Number      Quantity   Unit Cost    AWD Date  Surplus Material"
        table = self.extract_table_text(pdf_file, table_search_term, 3)
        if table:
            # Split the table text into lines
            lines = table.strip().split('\n')

            # Find the index of UI and QUANTITY columns
            #headers = lines[0].split()
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
                    quantity_index = i - 1
                elif "Unit" in header and "Cost" in header:
                    cost_index = i - 1
                elif "AWD" in header and "Date" in header:
                    date_index = i - 1

            if cage_index is not None and quantity_index is not None and cost_index is not None and date_index is not None:
                message = ""

                # Extract data for each row starting from the second line
                for line in lines[1:]:
                    if line.strip():  # Skip empty lines
                        row_values = line.split()
                        if len(row_values) >= max(cage_index, quantity_index, cost_index, date_index) + 1:
                            try:
                                cage = row_values[cage_index]
                                quantity = str(round(float(row_values[quantity_index])))
                                cost = str("{:.2f}".format(round(float(row_values[cost_index]), 2)))
                                date = row_values[date_index]
                                message += quantity + "@ $" + cost + " on " + date + "\n"
                            except (ValueError, IndexError) as e:
                                print(f"Error parsing payment history row: {e}")
                                continue

                return message.strip() if message else "No payment history found"
            else:
                print("Required headers not found in the table.")
                return "Manually Check"
        else:
            print("Table not found in the PDF.")
            return "Manually Check"

    def process_pdf(self, pdf_file_path):
        """Process a single PDF file and extract data using DIBBs.py methods"""
        pdf_file = Path(pdf_file_path)
        
        try:
            text = self.extract_text_from_pdf(str(pdf_file_path))
            
            # Use DIBBs.py extraction methods
            request_number = self.find_request_numbers(text)
            open_date, close_date = self.find_bid_dates(text)
            purchase_number = self.find_purchase_numbers(text)
            nsn, fsc = self.find_nsn_and_fsc(text)
            delivery_days = self.find_delivery_days(text)
            unit, quantity = self.find_unit_details(str(pdf_file_path))
            fob = self.find_FOB(text)
            iso = self.find_ISO(text)
            inspection_point = self.find_inspection_point(text)
            sampling = self.find_sampling(text)
            product_description = self.find_product_description(text)
            mfr = self.find_mfr(text)
            packaging = self.find_packaging(text)
            package_type = self.find_package_type(text)
            buyer_info = self.find_buyer(text)
            payment_history = self.find_payment_history(str(pdf_file_path))
            
            # Create data structure compatible with CRM
            data = {
                'request_number': request_number or '',
                'nsn': nsn if nsn != "Manually Check" else '',
                'quantity': str(quantity) if quantity and quantity != -999 else '',
                'unit': unit or '',
                'mfr': mfr if mfr != "Manually Check" else '',
                'delivery_days': delivery_days if delivery_days != "999" else '',
                'fob': fob if fob != "Manually Check" else '',
                'packaging_type': package_type or '',
                'iso': iso,
                'sampling': sampling,
                'inspection_point': inspection_point or '',
                'buyer': buyer_info.get('name', '') if isinstance(buyer_info, dict) else '',
                'email': buyer_info.get('email', '') if isinstance(buyer_info, dict) else '',
                'product_description': product_description if product_description != "Manually Check" else '',
                'close_date': close_date or '',
                'open_date': open_date or '',
                'purchase_number': purchase_number if purchase_number != "Manually Check" else '',
                'fsc': fsc if fsc != "Manually Check" else '',
                'packaging': packaging if packaging != "Manually Check PDF" else '',
                'office': buyer_info.get('office', '') if isinstance(buyer_info, dict) else '',
                'division': buyer_info.get('division', '') if isinstance(buyer_info, dict) else '',
                'address': buyer_info.get('address', '') if isinstance(buyer_info, dict) else '',
                'buyer_code': buyer_info.get('buyer_code', '') if isinstance(buyer_info, dict) else '',
                'telephone': buyer_info.get('tel', '') if isinstance(buyer_info, dict) else '',
                'fax': buyer_info.get('fax', '') if isinstance(buyer_info, dict) else '',
                'buyer_info': buyer_info.get('info', '') if isinstance(buyer_info, dict) else '',
                'payment_history': payment_history if payment_history != "Manually Check" else '',
                'skipped': False
            }
            
            print(f"DEBUG: Extracted NSN: {nsn}")
            print(f"DEBUG: Extracted Request Number: {request_number}")
            print(f"DEBUG: Extracted Delivery Days: {delivery_days}")
            
            return data
            
        except Exception as e:
            print(f"Error processing PDF {pdf_file.name}: {e}")
            self.results['errors'].append(f"Error processing {pdf_file.name}: {str(e)}")
            return {
                'request_number': '',
                'nsn': '',
                'quantity': '',
                'unit': '',
                'mfr': '',
                'delivery_days': '',
                'fob': '',
                'packaging_type': '',
                'iso': 'NO',
                'sampling': 'NO',
                'inspection_point': '',
                'buyer': '',
                'email': '',
                'product_description': '',
                'close_date': '',
                'payment_history': '',
                'skipped': True
            }
            
    def create_crm_opportunity(self, pdf_data, pdf_file_path=None):
        """Create opportunity in CRM database from PDF data"""
        try:
            # First, try to find or create the product
            product_id = None
            if pdf_data['nsn']:
                # Check if product exists
                existing_products = crm_data.get_products({'nsn': pdf_data['nsn']})
                if existing_products:
                    product_id = existing_products[0]['id']
                else:
                    # Create new product with all available PDF data
                    product_name = pdf_data.get('product_description', '').strip()
                    if not product_name or product_name == "Manually Check":
                        product_name = f"Product for NSN {pdf_data['nsn']}"
                    
                    product_id = crm_data.create_product(
                        name=product_name,
                        nsn=pdf_data['nsn'],
                        fsc=pdf_data.get('fsc', '') if pdf_data.get('fsc') != "Manually Check" else '',
                        description=pdf_data.get('product_description', '').strip() if pdf_data.get('product_description') != "Manually Check" else '',
                        manufacturer=pdf_data['mfr'] or 'Unknown',
                        category='PDF Import',
                        unit=pdf_data['unit'] or 'EA'
                    )
                    
                    # Track product creation
                    if not hasattr(self.results, 'created_products'):
                        self.results['created_products'] = []
                    self.results['created_products'].append({
                        'id': product_id,
                        'nsn': pdf_data['nsn'],
                        'name': product_name,
                        'fsc': pdf_data.get('fsc', '') if pdf_data.get('fsc') != "Manually Check" else '',
                        'description': pdf_data.get('product_description', '').strip() if pdf_data.get('product_description') != "Manually Check" else ''
                    })
            
            # Try to find or create account from office/division information using intelligent matching
            account_id = None
            if pdf_data.get('office') or pdf_data.get('division'):
                # Use intelligent account matcher to respect parent-child relationships
                from intelligent_account_matcher import intelligent_account_matcher
                
                office = pdf_data.get('office', '')
                division = pdf_data.get('division', '')
                address = pdf_data.get('address', '')
                
                print(f"DEBUG: Using intelligent account matcher for Office='{office}', Division='{division}'")
                account_id = intelligent_account_matcher.smart_account_match(office, division, address)
                
                if account_id:
                    print(f"DEBUG: Intelligent matcher returned account ID: {account_id}")
                    # Get the account details for logging
                    account = crm_data.get_account_by_id(account_id)
                    if account:
                        print(f"DEBUG: Using account: {account['name']} (Parent: {account.get('parent_co', 'None')})")
                else:
                    print(f"DEBUG: Intelligent matcher failed to find/create account")
                
                # Fallback to old logic only if intelligent matcher fails completely
                if not account_id:
                    print("DEBUG: Falling back to legacy account creation logic")
                    account_name = f"{office} {division}".strip() if office and division else office or division or 'DLA'
                    existing_accounts = crm_data.get_accounts({'name': account_name})
                    
                    if existing_accounts:
                        account_id = existing_accounts[0]['id']
                        print(f"DEBUG: Found existing account {account_id} for {account_name}")
                        
                        # Check if we can update the account with new information
                        existing_account = existing_accounts[0]
                        update_data = {}
                        
                        # Update billing address if it's missing or different
                        new_address = pdf_data.get('address', '').strip()
                        current_address = (existing_account.get('billing_address') or '').strip()
                        if new_address and (not current_address or current_address != new_address):
                            update_data['billing_address'] = new_address
                            print(f"DEBUG: Will update account billing address")
                        
                        # Update summary if it's missing
                        if not existing_account.get('summary'):
                            update_data['summary'] = f"Defense Logistics Agency - {account_name}"
                            print(f"DEBUG: Will update account summary")
                        
                        # Apply updates if any
                        if update_data:
                            try:
                                crm_data.update_account(account_id, **update_data)
                                print(f"DEBUG: Updated account {account_id} with: {list(update_data.keys())}")
                                
                                # Track account updates
                                if not hasattr(self.results, 'updated_accounts'):
                                    self.results['updated_accounts'] = []
                                self.results['updated_accounts'].append({
                                    'id': account_id,
                                    'name': account_name,
                                    'updates': list(update_data.keys())
                                })
                            except Exception as update_error:
                                print(f"DEBUG: Failed to update account: {update_error}")
                    else:
                        # Create new account as last resort
                        try:
                            account_data = {
                                'name': account_name,
                                'type': 'Customer',  # Use valid type from CHECK constraint
                                'summary': f"Defense Logistics Agency - {account_name}",
                                'billing_address': pdf_data.get('address', ''),
                                'is_active': True
                            }
                            
                            account_id = crm_data.create_account(**account_data)
                            print(f"DEBUG: Created new account {account_id} for {account_name}")
                            
                            # Track account creation
                            if not hasattr(self.results, 'created_accounts'):
                                self.results['created_accounts'] = []
                            self.results['created_accounts'].append({
                                'id': account_id,
                                'name': account_name
                            })
                            
                        except Exception as account_error:
                            print(f"DEBUG: Failed to create account: {account_error}")
            
            # Try to find or create contact from buyer information
            contact_id = None
            if pdf_data.get('email') and pdf_data.get('buyer'):
                # Check if contact with this email already exists
                existing_contacts = crm_data.get_contacts({'email': pdf_data['email']})
                if existing_contacts:
                    contact_id = existing_contacts[0]['id']
                    print(f"DEBUG: Found existing contact {contact_id} for email {pdf_data['email']}")
                    
                    # Check if we can update the contact with new/better information
                    existing_contact = existing_contacts[0]
                    update_data = {}
                    
                    # Update account if missing
                    if account_id and not existing_contact.get('account_id'):
                        update_data['account_id'] = account_id
                        print(f"DEBUG: Will link contact to account {account_id}")
                    
                    # Update phone if missing or different
                    new_phone = pdf_data.get('telephone', '').strip()
                    current_phone = (existing_contact.get('phone') or '').strip()
                    if new_phone and (not current_phone or current_phone != new_phone):
                        update_data['phone'] = new_phone
                        print(f"DEBUG: Will update contact phone: {new_phone}")
                    
                    # Update fax if missing or different
                    new_fax = pdf_data.get('fax', '').strip()
                    current_fax = (existing_contact.get('fax') or '').strip()
                    if new_fax and (not current_fax or current_fax != new_fax):
                        update_data['fax'] = new_fax
                        print(f"DEBUG: Will update contact fax: {new_fax}")
                    
                    # Update buyer_code if missing or different
                    new_buyer_code = pdf_data.get('buyer_code', '').strip()
                    current_buyer_code = (existing_contact.get('buyer_code') or '').strip()
                    if new_buyer_code and (not current_buyer_code or current_buyer_code != new_buyer_code):
                        update_data['buyer_code'] = new_buyer_code
                        print(f"DEBUG: Will update contact buyer_code: {new_buyer_code}")
                    
                    # Update department if missing
                    new_department = pdf_data.get('division', '').strip()
                    current_department = (existing_contact.get('department') or '').strip()
                    if new_department and not current_department:
                        update_data['department'] = new_department
                        print(f"DEBUG: Will update contact department: {new_department}")
                    
                    # Update address if missing or different
                    new_address = pdf_data.get('address', '').strip()
                    current_address = (existing_contact.get('address') or '').strip()
                    if new_address and (not current_address or current_address != new_address):
                        update_data['address'] = new_address
                        print(f"DEBUG: Will update contact address")
                    
                    # Apply updates if any
                    if update_data:
                        try:
                            crm_data.update_contact(contact_id, **update_data)
                            print(f"DEBUG: Updated contact {contact_id} with: {list(update_data.keys())}")
                            
                            # Track contact updates
                            if not hasattr(self.results, 'updated_contacts'):
                                self.results['updated_contacts'] = []
                            self.results['updated_contacts'].append({
                                'id': contact_id,
                                'name': pdf_data['buyer'],
                                'email': pdf_data['email'],
                                'updates': list(update_data.keys())
                            })
                        except Exception as update_error:
                            print(f"DEBUG: Failed to update contact: {update_error}")
                else:
                    # Create new contact from buyer information
                    try:
                        # Split buyer name into first and last names
                        buyer_name = pdf_data['buyer'].strip()
                        name_parts = buyer_name.split(' ', 1)
                        first_name = name_parts[0] if name_parts else buyer_name
                        last_name = name_parts[1] if len(name_parts) > 1 else ''
                        
                        contact_data = {
                            'first_name': first_name,
                            'last_name': last_name,
                            'email': pdf_data['email'],
                            'phone': pdf_data.get('telephone', ''),
                            'fax': pdf_data.get('fax', ''),
                            'buyer_code': pdf_data.get('buyer_code', ''),
                            'account_id': account_id,
                            'department': pdf_data.get('division', ''),
                            'address': pdf_data.get('address', ''),
                            'lead_source': 'PDF Import',
                            'description': f"Auto-created from PDF processing for request {pdf_data['request_number']}",
                            'is_active': True
                        }
                        
                        contact_id = crm_data.create_contact(**contact_data)
                        print(f"DEBUG: Created new contact {contact_id} for {pdf_data['buyer']} ({pdf_data['email']})")
                        
                        # Update results to track contact creation
                        if not hasattr(self.results, 'created_contacts'):
                            self.results['created_contacts'] = []
                        self.results['created_contacts'].append({
                            'id': contact_id,
                            'name': pdf_data['buyer'],
                            'email': pdf_data['email'],
                            'buyer_code': pdf_data.get('buyer_code', '')
                        })
                        
                    except Exception as contact_error:
                        print(f"DEBUG: Failed to create contact: {contact_error}")
                        # Continue with opportunity creation even if contact creation fails
            
            # Create opportunity
            opportunity_data = {
                'name': f"{pdf_data['request_number']}",
                'description': f"Auto-created from PDF processing for request {pdf_data['request_number']}. Product: {pdf_data.get('product_description', '').strip()}. Buyer: {pdf_data.get('buyer', 'Unknown')}. Email: {pdf_data.get('email', 'N/A')}",
                'stage': 'Prospecting',
                'state': 'Active',
                'nsn': pdf_data['nsn'] if pdf_data['nsn'] else '',
                'quantity': int(pdf_data['quantity']) if pdf_data['quantity'] else 1,
                'unit': pdf_data['unit'] or 'EA',
                'mfr': pdf_data['mfr'] or '',
                'buyer': pdf_data.get('buyer', '') or '',
                'delivery_days': int(pdf_data['delivery_days']) if pdf_data['delivery_days'] else None,
                'fob': 'Origin' if pdf_data.get('fob', '').upper().strip() == 'ORIGIN' else 'Destination',
                'packaging_type': pdf_data['packaging_type'] or '',
                'iso': 'Yes' if pdf_data['iso'] == 'YES' else 'No',
                'sampling': 'Yes' if pdf_data['sampling'] == 'YES' else 'No',
                'close_date': self._parse_date(pdf_data.get('close_date')),
                'payment_history': pdf_data.get('payment_history', '') or '',
                'product_id': product_id,
                'pdf_file_path': pdf_file_path or ''
            }
            
            # Link the contact and account to the opportunity
            if contact_id:
                opportunity_data['contact_id'] = contact_id
            if account_id:
                opportunity_data['account_id'] = account_id
            
            # Debug FOB value specifically
            print(f"DEBUG FOB: Raw='{pdf_data['fob']}', Processed='{opportunity_data['fob']}'")
            print(f"DEBUG: About to create opportunity with data: {opportunity_data}")
            opportunity_id = crm_data.create_opportunity(**opportunity_data)
            
            if opportunity_id:
                self.results['created'] += 1
                self.results['created_opportunities'].append({
                    'id': opportunity_id,
                    'request_number': pdf_data['request_number'],
                    'nsn': pdf_data['nsn']
                })
                
                # Process QPL data if MFR information is available
                if pdf_data.get('mfr') and pdf_data.get('nsn'):
                    try:
                        # Import MFR parser with proper path handling
                        import sys
                        import os
                        
                        # Add the root directory to path for the import
                        root_dir = str(self.base_dir)
                        if root_dir not in sys.path:
                            sys.path.insert(0, root_dir)
                        
                        from mfr_parser import MFRParser
                        
                        print(f"🔄 Processing QPL for opportunity {opportunity_id}")
                        print(f"   NSN: {pdf_data['nsn']}")
                        print(f"   MFR: {pdf_data['mfr']}")
                        
                        parser = MFRParser()
                        qpl_result = parser.process_opportunity_mfr(
                            opportunity_id=opportunity_id,
                            nsn=pdf_data['nsn'],
                            mfr_string=pdf_data['mfr'],
                            product_name=pdf_data.get('product_description', f"Product {pdf_data['nsn']}"),
                            description=pdf_data.get('product_description', '')
                        )
                        
                        if qpl_result['success']:
                            print(f"✓ Successfully created {qpl_result['manufacturers_count']} QPL entries for opportunity {opportunity_id}")
                            self.results['created_qpl_entries'] = self.results.get('created_qpl_entries', 0) + qpl_result['manufacturers_count']
                            
                            # Track QPL creation in results
                            if 'qpl_entries' not in self.results:
                                self.results['qpl_entries'] = []
                            self.results['qpl_entries'].extend(qpl_result['qpl_entries'])
                        else:
                            print(f"⚠️ QPL processing failed: {qpl_result.get('message', 'Unknown error')}")
                            
                    except ImportError as import_error:
                        print(f"⚠️ Failed to import MFR parser: {import_error}")
                        print(f"   Root dir: {root_dir}")
                        print(f"   Current working directory: {os.getcwd()}")
                    except Exception as qpl_error:
                        print(f"⚠️ QPL processing error for opportunity {opportunity_id}: {qpl_error}")
                        import traceback
                        traceback.print_exc()
                        # Don't fail the whole process if QPL processing fails
                
                return opportunity_id
            
        except Exception as e:
            error_msg = f"Error creating CRM opportunity for {pdf_data['request_number']}: {str(e)}"
            print(error_msg)
            self.results['errors'].append(error_msg)
        
        return None

    def process_all_pdfs(self):
        """Process all PDFs in the To Process folder"""
        print(f"Starting DIBBs CRM PDF Processing...")
        print(f"Input folder: {self.pdf_dir}")
        print(f"Output folder: {self.summary_dir}")
        
        # Reset results for this processing run
        self.results = {
            'processed': 0,
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'errors': [],
            'created_opportunities': [],
            'detailed_report': '',
            'processed_files': [],
            'skipped_files': [],
            'error_files': []
        }
        
        today_str = datetime.today().strftime("%Y-%m-%d")
        self.create_summary_files(today_str)
        
        csv_file_path = self.summary_dir / f"{today_str}_output.csv"
        
        # Get list of PDF files (deduplicated)
        pdf_files = list(set(list(self.pdf_dir.glob("*.pdf")) + list(self.pdf_dir.glob("*.PDF"))))
        
        if not pdf_files:
            print("No PDF files found to process")
            return self.results
        
        report_lines = []
        report_lines.append(f"DIBBs CRM Processing Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("=" * 60)
        
        with open(csv_file_path, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            
            for pdf_file in pdf_files:
                try:
                    print(f"Processing: {pdf_file.name}")
                    report_lines.append(f"Processing: {pdf_file.name}")
                    
                    # Process PDF and extract data
                    pdf_data = self.process_pdf(str(pdf_file))
                    
                    # Determine if PDF meets criteria for automation using current settings
                    settings = self.settings  # Use current settings instead of reloading
                    
                    # Check each criteria individually
                    delivery_ok = (
                        pdf_data.get('delivery_days') and
                        pdf_data['delivery_days'].isdigit() and
                        int(pdf_data['delivery_days']) >= int(settings.get('min_delivery_days', 50))
                    )
                    
                    iso_ok = (
                        settings.get('iso_required', 'ANY') == 'ANY' or
                        pdf_data.get('iso') == settings.get('iso_required')
                    )
                    
                    sampling_ok = (
                        settings.get('sampling_required', 'ANY') == 'ANY' or
                        pdf_data.get('sampling') == settings.get('sampling_required')
                    )
                    
                    inspection_ok = (
                        settings.get('inspection_point', 'ANY') == 'ANY' or
                        (pdf_data.get('inspection_point') and
                         settings.get('inspection_point', '').upper() in pdf_data['inspection_point'].upper())
                    )
                    
                    manufacturer_ok = (
                        not settings.get('manufacturer_filters') or
                        (pdf_data.get('mfr') and
                         any(manufacturer.lower() in pdf_data['mfr'].lower() 
                            for manufacturer in settings.get('manufacturer_filters', [])))
                    )
                    
                    should_automate = delivery_ok and iso_ok and sampling_ok and inspection_ok and manufacturer_ok
                    
                    if should_automate:
                        # Create CRM opportunity
                        opportunity_id = self.create_crm_opportunity(pdf_data, str(pdf_file))
                        
                        if opportunity_id:
                            # Move to automation folder
                            pdf_destination = self.automation_dir / pdf_data['nsn'] / pdf_data['request_number']
                            pdf_destination.mkdir(parents=True, exist_ok=True)
                            
                            # Save summary file
                            summary_file = pdf_destination / f"{pdf_data['request_number']}.txt"
                            with open(summary_file, 'w') as f:
                                json.dump(pdf_data, f, indent=4)
                            
                            self.move_files(str(pdf_file), str(pdf_destination))
                            
                            # Create detailed success message
                            success_msg = f"  ✓ Automated - Created opportunity {opportunity_id}"
                            if hasattr(self.results, 'created_contacts') and self.results['created_contacts']:
                                # Check if any contact was created for this PDF
                                for contact in self.results['created_contacts']:
                                    if contact.get('email') == pdf_data.get('email'):
                                        success_msg += f" and contact {contact['id']}"
                                        break
                            report_lines.append(success_msg)
                            
                            # Track processed file with detailed record information
                            file_records = self._count_file_records(pdf_data, opportunity_id)
                            self.results['processed_files'].append({
                                'filename': pdf_file.name,
                                'rfq_data': pdf_data,
                                'opportunity_id': opportunity_id,
                                'status': 'processed',
                                'created_records': file_records['created'],
                                'updated_records': file_records['updated'],
                                'records_detail': file_records['detail']
                            })
                        else:
                            pdf_data['skipped'] = True
                            self.move_files(str(pdf_file), None)
                            self.results['skipped'] += 1
                            report_lines.append(f"  ⚠ Failed to create opportunity - moved to reviewed")
                            
                            # Track as error with record information
                            self.results['error_files'].append({
                                'filename': pdf_file.name,
                                'rfq_data': pdf_data,
                                'error': 'Failed to create opportunity',
                                'created_records': 0,
                                'updated_records': 0,
                                'records_detail': []
                            })
                    else:
                        # Skip - don't create opportunity, just move file to reviewed
                        pdf_data['skipped'] = True
                        self.move_files(str(pdf_file), None)
                        self.results['skipped'] += 1
                        
                        # Generate detailed skip reason
                        skip_reason = self._get_skip_reason(pdf_data, settings)
                        report_lines.append(f"  ⊘ Skipped - Does not meet automation criteria")
                        report_lines.append(f"    Reason: {skip_reason}")
                        
                        # Track skipped file with record information
                        self.results['skipped_files'].append({
                            'filename': pdf_file.name,
                            'rfq_data': pdf_data,
                            'reason': skip_reason,
                            'created_records': 0,
                            'updated_records': 0,
                            'records_detail': []
                        })
                    
                    # Write to CSV
                    writer.writerow(list(pdf_data.values()))
                    self.results['processed'] += 1
                    
                except Exception as e:
                    error_msg = f"Error processing {pdf_file.name}: {str(e)}"
                    print(error_msg)
                    self.results['errors'].append(error_msg)
                    report_lines.append(f"  ✗ Error: {str(e)}")
                    
                    # Track error file with record information
                    self.results['error_files'].append({
                        'filename': pdf_file.name,
                        'error': str(e),
                        'created_records': 0,
                        'updated_records': 0,
                        'records_detail': []
                    })
        
        # Generate detailed report
        report_lines.append("")
        report_lines.append("Processing Summary:")
        report_lines.append(f"  Files Processed: {self.results['processed']}")
        report_lines.append(f"  Opportunities Created: {self.results['created']}")
        
        # Add detailed record creation summary
        contacts_created = len(self.results.get('created_contacts', []))
        if contacts_created > 0:
            report_lines.append(f"  Contacts Created: {contacts_created}")
            for contact in self.results['created_contacts']:
                report_lines.append(f"    • {contact.get('name', 'Unknown')} ({contact.get('email', 'N/A')})")
        
        # Add detailed contact update summary
        contacts_updated = len(self.results.get('updated_contacts', []))
        if contacts_updated > 0:
            report_lines.append(f"  Contacts Updated: {contacts_updated}")
            for contact in self.results['updated_contacts']:
                updates = ', '.join(contact.get('updates', []))
                report_lines.append(f"    • {contact.get('name', 'Unknown')} ({contact.get('email', 'N/A')}) - {updates}")
        
        # Add detailed account creation summary
        accounts_created = len(self.results.get('created_accounts', []))
        if accounts_created > 0:
            report_lines.append(f"  Accounts Created: {accounts_created}")
            for account in self.results['created_accounts']:
                report_lines.append(f"    • {account.get('name', 'Unknown')}")
        
        # Add detailed account update summary
        accounts_updated = len(self.results.get('updated_accounts', []))
        if accounts_updated > 0:
            report_lines.append(f"  Accounts Updated: {accounts_updated}")
            for account in self.results['updated_accounts']:
                updates = ', '.join(account.get('updates', []))
                report_lines.append(f"    • {account.get('name', 'Unknown')} - {updates}")
        
        # Add product creation summary
        products_created = len(self.results.get('created_products', []))
        if products_created > 0:
            report_lines.append(f"  Products Created: {products_created}")
            for product in self.results['created_products']:
                report_lines.append(f"    • {product.get('name', 'Unknown')} (NSN: {product.get('nsn', 'N/A')})")
        
        # Add task creation summary
        tasks_created = len(self.results.get('created_tasks', []))
        if tasks_created > 0:
            report_lines.append(f"  Tasks Created: {tasks_created}")
            for task in self.results['created_tasks']:
                report_lines.append(f"    • {task.get('subject', 'Unknown')}")
        
        report_lines.append(f"  Files Skipped: {self.results['skipped']}")
        report_lines.append(f"  Errors: {len(self.results['errors'])}")
        
        # Add created opportunities detail
        if self.results.get('created_opportunities'):
            report_lines.append("")
            report_lines.append("Created Opportunities:")
            for opp in self.results['created_opportunities']:
                report_lines.append(f"  • {opp.get('request_number', 'Unknown')} (ID: {opp.get('id', 'N/A')}) - NSN: {opp.get('nsn', 'N/A')}")
        
        # Add skipped files detail
        if self.results.get('skipped_files'):
            report_lines.append("")
            report_lines.append("Skipped Files:")
            for skipped in self.results['skipped_files']:
                report_lines.append(f"  • {skipped['filename']}")
                report_lines.append(f"    Reason: {skipped['reason']}")
                if skipped.get('rfq_data', {}).get('request_number'):
                    report_lines.append(f"    RFQ: {skipped['rfq_data']['request_number']}")
        
        # Add detailed update information (keeping existing logic)
        if self.results.get('updated_contacts') or self.results.get('updated_accounts'):
            report_lines.append("")
            report_lines.append("Update Details:")
            
            # Contact updates
            for contact_update in self.results.get('updated_contacts', []):
                report_lines.append(f"  📞 Contact: {contact_update['name']} ({contact_update['email']})")
                report_lines.append(f"     Updated: {', '.join(contact_update['updates'])}")
            
            # Account updates
            for account_update in self.results.get('updated_accounts', []):
                report_lines.append(f"  🏢 Account: {account_update['name']}")
                report_lines.append(f"     Updated: {', '.join(account_update['updates'])}")        # Add filter settings used
        report_lines.append("")
        report_lines.append("Filter Settings Applied:")
        report_lines.append(f"  Min Delivery Days: {settings.get('min_delivery_days', 'Not set')}")
        report_lines.append(f"  ISO Required: {settings.get('iso_required', 'ANY')}")
        report_lines.append(f"  Sampling Required: {settings.get('sampling_required', 'ANY')}")
        report_lines.append(f"  Inspection Point: {settings.get('inspection_point', 'ANY')}")
        report_lines.append(f"  Manufacturer Filters: {settings.get('manufacturer_filters', [])}")

        if self.results['errors']:
            report_lines.append("")
            report_lines.append("Errors:")
            for error in self.results['errors']:
                report_lines.append(f"  - {error}")
        
        self.results['detailed_report'] = '\n'.join(report_lines)
        
        # Save detailed processing report to file for web interface
        self._save_processing_report()
        
        print("DIBBs CRM Processing completed")
        print(f"Processed: {self.results['processed']}, Created: {self.results['created']}, Errors: {len(self.results['errors'])}")
        
        return self.results
    
    def _count_file_records(self, pdf_data, opportunity_id):
        """Count records created/updated for a specific file"""
        created_count = 0
        updated_count = 0
        detail = []
        
        # Count opportunity (always created when this method is called)
        if opportunity_id:
            created_count += 1
            detail.append(f"Opportunity: {pdf_data.get('request_number', 'Unknown')}")
        
        # Count contacts created/updated for this file
        email = pdf_data.get('email', '')
        if email:
            # Check if we created a contact for this email
            for contact in self.results.get('created_contacts', []):
                if contact.get('email') == email:
                    created_count += 1
                    detail.append(f"Contact: {contact.get('name', 'Unknown')}")
                    break
            else:
                # Check if we updated a contact for this email
                for contact in self.results.get('updated_contacts', []):
                    if contact.get('email') == email:
                        updated_count += 1
                        detail.append(f"Contact: {contact.get('name', 'Unknown')} (updated)")
                        break
        
        # Count accounts created/updated for this file
        account_name = ''
        if pdf_data.get('office') or pdf_data.get('division'):
            account_name_parts = []
            if pdf_data.get('office'):
                account_name_parts.append(pdf_data['office'])
            if pdf_data.get('division') and pdf_data['division'] != pdf_data.get('office'):
                account_name_parts.append(pdf_data['division'])
            account_name = ' '.join(account_name_parts) if account_name_parts else 'DLA'
            
            # Check if we created an account
            for account in self.results.get('created_accounts', []):
                if account.get('name') == account_name:
                    created_count += 1
                    detail.append(f"Account: {account_name}")
                    break
            else:
                # Check if we updated an account
                for account in self.results.get('updated_accounts', []):
                    if account.get('name') == account_name:
                        updated_count += 1
                        detail.append(f"Account: {account_name} (updated)")
                        break
        
        # Count products created
        nsn = pdf_data.get('nsn', '')
        if nsn:
            for product in self.results.get('created_products', []):
                if product.get('nsn') == nsn:
                    created_count += 1
                    detail.append(f"Product: NSN {nsn}")
                    break
        
        return {
            'created': created_count,
            'updated': updated_count,
            'detail': detail
        }

    def _save_processing_report(self):
        """Save detailed processing report to file for web interface"""
        try:
            from datetime import datetime
            import json
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = self.summary_dir / f"pdf_processing_report_{timestamp}.json"
            
            # Prepare comprehensive record summary
            created_records = {
                'opportunities': self.results.get('created_opportunities', []),
                'contacts': self.results.get('created_contacts', []),
                'accounts': self.results.get('created_accounts', []),
                'products': self.results.get('created_products', []),
                'tasks': self.results.get('created_tasks', [])
            }
            
            updated_records = {
                'contacts': self.results.get('updated_contacts', []),
                'accounts': self.results.get('updated_accounts', [])
            }
            
            report_data = {
                'processing_start': datetime.now().isoformat(),
                'processing_end': datetime.now().isoformat(),
                'filter_settings': self.settings,
                'total_files': self.results['processed'],
                'processed_files': self.results.get('processed_files', []),
                'skipped_files': self.results.get('skipped_files', []),
                'error_files': self.results.get('error_files', []),
                'summary': {
                    'files_processed': self.results['processed'],
                    'opportunities_created': self.results['created'],
                    'contacts_created': len(self.results.get('created_contacts', [])),
                    'contacts_updated': len(self.results.get('updated_contacts', [])),
                    'accounts_created': len(self.results.get('created_accounts', [])),
                    'accounts_updated': len(self.results.get('updated_accounts', [])),
                    'products_created': len(self.results.get('created_products', [])),
                    'tasks_created': len(self.results.get('created_tasks', [])),
                    'files_skipped': self.results['skipped'],
                    'errors': len(self.results['errors'])
                },
                'created_records': created_records,
                'updated_records': updated_records,
                'detailed_report': self.results['detailed_report'],
                # Legacy fields for backward compatibility
                'processed': self.results['processed'],
                'created': self.results['created'],
                'updated': len(self.results.get('updated_contacts', [])) + len(self.results.get('updated_accounts', [])),
                'skipped': self.results['skipped'],
                'errors': self.results['errors']
            }
            
            with open(report_file, 'w') as f:
                json.dump(report_data, f, indent=2)
            
            print(f"Processing report saved to: {report_file}")
            
        except Exception as e:
            print(f"Error saving processing report: {e}")
    
    def _get_skip_reason(self, pdf_data, settings):
        """Generate detailed reason why a PDF was skipped using DIBBs.py automation criteria"""
        reasons = []
        
        # DIBBs.py automation criteria:
        # delivery_days >= 120 AND iso == "NO" AND sampling == "NO" AND 
        # inspection_point == "DESTINATION" AND manufacturer contains "Parker"
        
        # Check delivery days (must be >= 120)
        delivery_days = pdf_data.get('delivery_days')
        if not delivery_days or delivery_days == "999":
            reasons.append("Missing delivery days information")
        elif not str(delivery_days).isdigit():
            reasons.append(f"Invalid delivery days format: '{delivery_days}'")
        elif int(delivery_days) < 120:
            reasons.append(f"Delivery too short: {delivery_days} days (minimum: 120 for automation)")
        
        # Check ISO requirement (must be "NO" for automation)
        iso_value = pdf_data.get('iso', 'NO')
        if iso_value != "NO":
            reasons.append(f"ISO requirement mismatch: automation requires NO, RFQ has {iso_value}")
        
        # Check sampling requirement (must be "NO" for automation)
        sampling_value = pdf_data.get('sampling', 'NO')
        if sampling_value != "NO":
            reasons.append(f"Sampling requirement mismatch: automation requires NO, RFQ has {sampling_value}")
        
        # Check inspection point (must be "DESTINATION" for automation)
        inspection_point = pdf_data.get('inspection_point', '')
        if inspection_point != "DESTINATION":
            reasons.append(f"Inspection point mismatch: automation requires DESTINATION, RFQ has '{inspection_point}'")
        
        # Check manufacturer filters (must contain "Parker" for automation)
        mfr = pdf_data.get('mfr', '')
        if not mfr or mfr == "Manually Check":
            reasons.append("Missing manufacturer information")
        elif "parker" not in mfr.lower():
            reasons.append(f"Manufacturer not in automation list: '{mfr}' does not contain 'Parker'")
        
        # Check for missing critical data
        critical_fields = ['request_number', 'nsn']
        missing_fields = []
        for field in critical_fields:
            value = pdf_data.get(field, '')
            if not value or value == "Manually Check":
                missing_fields.append(field)
        
        if missing_fields:
            reasons.append(f"Missing critical information: {', '.join(missing_fields)}")
        
        return "; ".join(reasons) if reasons else "Meets automation criteria"

    def _parse_date(self, date_string):
        """Parse date from various formats to YYYY-MM-DD"""
        if not date_string:
            return None
        
        try:
            # Handle formats like "SEP 27, 2023" or "JUN 17, 2024"
            from datetime import datetime
            parsed_date = datetime.strptime(date_string, "%b %d, %Y")
            return parsed_date.strftime("%Y-%m-%d")
        except:
            try:
                # Try other common formats
                parsed_date = datetime.strptime(date_string, "%Y-%m-%d")
                return date_string
            except:
                return None
    
    def load_settings(self):
        """Load settings from settings.json"""
        try:
            with open('config/settings.json', 'r') as f:
                return json.load(f)
        except:
            return {
                'min_delivery_days': 50,
                'iso_required': 'ANY',
                'sampling_required': 'ANY', 
                'inspection_point': 'ANY',
                'manufacturer_filters': []
            }

# Function to create a new processor instance
def get_dibbs_processor():
    return DIBBsCRMProcessor()

# Create global instance for import
dibbs_processor = DIBBsCRMProcessor()
