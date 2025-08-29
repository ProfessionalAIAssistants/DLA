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
            'detailed_report': ''
        }
        
        # Default settings for PDF processing filters
        self.settings_file = self.base_dir / "settings.json"
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
        """Get current filter settings"""
        return self.settings.copy()
    
    def update_filter_settings(self, new_settings: Dict[str, Any]):
        """Update filter settings"""
        self.settings.update(new_settings)
        self.save_settings(self.settings)
        print(f"Settings updated and saved: {self.settings}")

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
        source = Path(source_path)
        
        if destination_folder:
            # Move to automation folder
            destination = Path(destination_folder) / source.name
        else:
            # Move to reviewed folder
            destination = self.reviewed_dir / source.name
        
        try:
            # Ensure destination directory exists
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(destination))
            print(f"Moved {source.name} to {destination.parent}")
        except Exception as e:
            print(f"Error moving file {source.name}: {e}")

    def process_pdf(self, pdf_file_path):
        """Process a single PDF file and extract data"""
        pdf_file = Path(pdf_file_path)
        
        # Initialize data structure
        data = {
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
            'skipped': False
        }
        
        try:
            text = self.extract_text_from_pdf(pdf_file_path)
            
            # Extract request numbers
            request_numbers = self.find_request_numbers(text, "REQUEST NUMBER")
            if request_numbers:
                data['request_number'] = request_numbers[0]
            
            # Extract other data using regex patterns
            patterns = {
                'nsn': r'NSN\s*(\d{4}-\d{2}-\d{3}-\d{4})',
                'quantity': r'QTY\s*(\d+)',
                'unit': r'UNIT\s*([A-Z]{2})',
                'mfr': r'MFR\s*([A-Z0-9\s]+)',
                'delivery_days': r'DELIVERY\s*(\d+)\s*DAYS',
                'fob': r'FOB\s*([A-Z\s]+)',
                'packaging_type': r'PACKAGING\s*([A-Z\s]+)',
                'inspection_point': r'INSPECTION\s*([A-Z\s]+)'
            }
            
            for field, pattern in patterns.items():
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    data[field] = match.group(1).strip()
            
            # Check for ISO and sampling requirements
            if 'ISO' in text.upper():
                data['iso'] = 'YES'
            if 'SAMPLING' in text.upper():
                data['sampling'] = 'YES'
                
        except Exception as e:
            print(f"Error processing PDF {pdf_file.name}: {e}")
            self.results['errors'].append(f"Error processing {pdf_file.name}: {str(e)}")
        
        return data

    def create_crm_opportunity(self, pdf_data):
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
                    # Create new product
                    product_id = crm_data.create_product(
                        name=f"Product for NSN {pdf_data['nsn']}",
                        nsn=pdf_data['nsn'],
                        manufacturer=pdf_data['mfr'] or 'Unknown',
                        category='PDF Import',
                        unit=pdf_data['unit'] or 'EA'
                    )
            
            # Create opportunity
            opportunity_data = {
                'name': f"{pdf_data['request_number']}",
                'description': f"Auto-created from PDF processing for request {pdf_data['request_number']}. Product: {pdf_data.get('product_description', '').strip()}. Buyer: {pdf_data.get('buyer', 'Unknown')}. Email: {pdf_data.get('email', 'N/A')}",
                'stage': 'Prospecting',
                'state': 'Active',
                'quantity': int(pdf_data['quantity']) if pdf_data['quantity'] else 1,
                'unit': pdf_data['unit'] or 'EA',
                'mfr': pdf_data['mfr'] or '',
                'buyer': pdf_data['buyer'] or '',
                'delivery_days': int(pdf_data['delivery_days']) if pdf_data['delivery_days'] else None,
                'fob': 'Origin' if pdf_data.get('fob', '').upper().strip() == 'ORIGIN' else 'Destination',
                'packaging_type': pdf_data['packaging_type'] or '',
                'iso': 'Yes' if pdf_data['iso'] == 'YES' else 'No',
                'sampling': 'Yes' if pdf_data['sampling'] == 'YES' else 'No',
                'close_date': self._parse_date(pdf_data.get('close_date')),
                'product_id': product_id
            }
            
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
                        opportunity_id = self.create_crm_opportunity(pdf_data)
                        
                        if opportunity_id:
                            # Move to automation folder
                            pdf_destination = self.automation_dir / pdf_data['nsn'] / pdf_data['request_number']
                            pdf_destination.mkdir(parents=True, exist_ok=True)
                            
                            # Save summary file
                            summary_file = pdf_destination / f"{pdf_data['request_number']}.txt"
                            with open(summary_file, 'w') as f:
                                json.dump(pdf_data, f, indent=4)
                            
                            self.move_files(str(pdf_file), str(pdf_destination))
                            report_lines.append(f"  ✓ Automated - Created opportunity {opportunity_id}")
                            
                            # Track processed file
                            self.results['processed_files'].append({
                                'filename': pdf_file.name,
                                'rfq_data': pdf_data,
                                'opportunity_id': opportunity_id,
                                'status': 'processed'
                            })
                        else:
                            pdf_data['skipped'] = True
                            self.move_files(str(pdf_file), None)
                            self.results['skipped'] += 1
                            report_lines.append(f"  ⚠ Failed to create opportunity - moved to reviewed")
                            
                            # Track as error
                            self.results['error_files'].append({
                                'filename': pdf_file.name,
                                'rfq_data': pdf_data,
                                'error': 'Failed to create opportunity'
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
                        
                        # Track skipped file
                        self.results['skipped_files'].append({
                            'filename': pdf_file.name,
                            'rfq_data': pdf_data,
                            'reason': skip_reason
                        })
                    
                    # Write to CSV
                    writer.writerow(list(pdf_data.values()))
                    self.results['processed'] += 1
                    
                except Exception as e:
                    error_msg = f"Error processing {pdf_file.name}: {str(e)}"
                    print(error_msg)
                    self.results['errors'].append(error_msg)
                    report_lines.append(f"  ✗ Error: {str(e)}")
                    
                    # Track error file
                    self.results['error_files'].append({
                        'filename': pdf_file.name,
                        'error': str(e)
                    })
        
        # Generate detailed report
        report_lines.append("")
        report_lines.append("Processing Summary:")
        report_lines.append(f"  Files Processed: {self.results['processed']}")
        report_lines.append(f"  Opportunities Created: {self.results['created']}")
        report_lines.append(f"  Files Skipped: {self.results['skipped']}")
        report_lines.append(f"  Errors: {len(self.results['errors'])}")
        
        # Add filter settings used
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
    
    def _save_processing_report(self):
        """Save detailed processing report to file for web interface"""
        try:
            from datetime import datetime
            import json
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = self.summary_dir / f"pdf_processing_report_{timestamp}.json"
            
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
                    'files_skipped': self.results['skipped'],
                    'errors': len(self.results['errors'])
                },
                'detailed_report': self.results['detailed_report']
            }
            
            with open(report_file, 'w') as f:
                json.dump(report_data, f, indent=2)
            
            print(f"Processing report saved to: {report_file}")
            
        except Exception as e:
            print(f"Error saving processing report: {e}")
    
    def _get_skip_reason(self, pdf_data, settings):
        """Generate detailed reason why a PDF was skipped"""
        reasons = []
        
        # Check delivery days
        delivery_days = pdf_data.get('delivery_days')
        min_delivery = settings.get('min_delivery_days', 50)
        if not delivery_days:
            reasons.append(f"Missing delivery days information")
        elif not delivery_days.isdigit():
            reasons.append(f"Invalid delivery days format: '{delivery_days}'")
        elif int(delivery_days) < min_delivery:
            reasons.append(f"Delivery too short: {delivery_days} days (minimum: {min_delivery})")
        
        # Check ISO requirement
        iso_required = settings.get('iso_required', 'ANY')
        if iso_required != 'ANY' and pdf_data.get('iso') != iso_required:
            reasons.append(f"ISO mismatch: requires {iso_required}, RFQ has {pdf_data.get('iso', 'N/A')}")
        
        # Check sampling requirement
        sampling_required = settings.get('sampling_required', 'ANY')
        if sampling_required != 'ANY' and pdf_data.get('sampling') != sampling_required:
            reasons.append(f"Sampling mismatch: requires {sampling_required}, RFQ has {pdf_data.get('sampling', 'N/A')}")
        
        # Check inspection point
        inspection_point = settings.get('inspection_point', 'ANY')
        if inspection_point != 'ANY':
            rfq_inspection = pdf_data.get('inspection_point', '')
            if inspection_point.upper() not in rfq_inspection.upper():
                reasons.append(f"Inspection point mismatch: requires {inspection_point}, RFQ has {rfq_inspection}")
        
        # Check manufacturer filters
        manufacturer_filters = settings.get('manufacturer_filters', [])
        if manufacturer_filters:
            rfq_mfr = pdf_data.get('mfr', '')
            if not rfq_mfr:
                reasons.append(f"Missing manufacturer information")
            elif not any(manufacturer.lower() in rfq_mfr.lower() for manufacturer in manufacturer_filters):
                reasons.append(f"Manufacturer not in filter list: '{rfq_mfr}' not in {manufacturer_filters}")
        
        # Check for missing critical data
        critical_fields = ['request_number', 'nsn']
        missing_fields = [field for field in critical_fields if not pdf_data.get(field)]
        if missing_fields:
            reasons.append(f"Missing critical information: {', '.join(missing_fields)}")
        
        return "; ".join(reasons) if reasons else "Unknown reason"

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
            with open('settings.json', 'r') as f:
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
