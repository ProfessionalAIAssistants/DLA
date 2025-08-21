"""
PDF Processing Module for DIBBs Integration
Processes PDFs from "To Process" folder and integrates data into CRM
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import PyPDF2
from datetime import datetime, date
import shutil

# Import our CRM modules
from crm_data import CRMData

class PDFProcessor:
    def __init__(self):
        self.crm_data = CRMData()
        self.to_process_dir = Path("To Process")
        self.reviewed_dir = Path("Reviewed")
        self.settings_file = Path("settings.json")
        
        # Ensure directories exist
        self.reviewed_dir.mkdir(exist_ok=True)
        
        # Load or create default settings
        self.settings = self.load_settings()
        
    def load_settings(self) -> Dict[str, Any]:
        """Load settings from file or create defaults"""
        default_settings = {
            'min_delivery_days': 100,
            'iso_required': 'YES',
            'sampling_required': 'NO', 
            'inspection_point': 'DESTINATION',
            'manufacturer_filter': 'Parker',
            'auto_create_opportunities': True,
            'link_related_records': True,
            'move_processed_files': True,
            'skip_duplicates': True
        }
        
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    default_settings.update(loaded_settings)
                    return default_settings
            except Exception as e:
                print(f"Error loading settings, using defaults: {e}")
        
        # Save default settings
        self.save_settings(default_settings)
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
    
    def should_process_rfq(self, rfq_data: Dict[str, Any]) -> bool:
        """Check if RFQ meets filter criteria for processing"""
        # Check delivery days
        delivery_days = rfq_data.get('delivery_days')
        if delivery_days:
            try:
                if int(delivery_days) < self.settings['min_delivery_days']:
                    return False
            except (ValueError, TypeError):
                pass
        
        # Check ISO requirement
        iso_required = self.settings['iso_required']
        if iso_required != 'ANY':
            rfq_iso = rfq_data.get('iso', 'NO').upper()
            if rfq_iso != iso_required:
                return False
        
        # Check sampling requirement
        sampling_required = self.settings['sampling_required']
        if sampling_required != 'ANY':
            rfq_sampling = rfq_data.get('sampling', 'NO').upper()
            if rfq_sampling != sampling_required:
                return False
        
        # Check inspection point
        inspection_point = self.settings['inspection_point']
        if inspection_point != 'ANY':
            rfq_inspection = rfq_data.get('inspection_point', '').upper()
            if rfq_inspection != inspection_point:
                return False
        
        # Check manufacturer filter
        manufacturer_filter = self.settings.get('manufacturer_filter', '').strip()
        if manufacturer_filter:
            manufacturers = [m.strip().lower() for m in manufacturer_filter.split('\n') if m.strip()]
            rfq_mfr = rfq_data.get('mfr', '').lower()
            if not any(mfr in rfq_mfr for mfr in manufacturers):
                return False
        
        return True
    
    def _get_database_stats(self) -> Dict[str, int]:
        """Get current database statistics"""
        from crm_data import crm_data
        try:
            return {
                'accounts': len(crm_data.get_accounts()),
                'contacts': len(crm_data.get_contacts()),
                'products': len(crm_data.get_products()),
                'rfqs': len(crm_data.get_rfqs()),
                'interactions': len(crm_data.get_interactions()),
                'opportunities': len(crm_data.get_opportunities())
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _get_skip_reason(self, rfq_data: Dict[str, Any]) -> str:
        """Determine why an RFQ was skipped"""
        reasons = []
        
        # Check delivery days
        delivery_days = rfq_data.get('delivery_days')
        if delivery_days:
            try:
                if int(delivery_days) < self.settings['min_delivery_days']:
                    reasons.append(f"• Delivery too short: {delivery_days} days (minimum: {self.settings['min_delivery_days']})")
            except (ValueError, TypeError):
                pass
        
        # Check ISO requirement
        iso_required = self.settings['iso_required']
        if iso_required != 'ANY':
            rfq_iso = rfq_data.get('iso', 'NO').upper()
            if rfq_iso != iso_required:
                reasons.append(f"• ISO mismatch: requires {iso_required}, RFQ has {rfq_iso}")
        
        # Check sampling requirement
        sampling_required = self.settings['sampling_required']
        if sampling_required != 'ANY':
            rfq_sampling = rfq_data.get('sampling', 'NO').upper()
            if rfq_sampling != sampling_required:
                reasons.append(f"• Sampling mismatch: requires {sampling_required}, RFQ has {rfq_sampling}")
        
        # Check inspection point
        inspection_point = self.settings['inspection_point']
        if inspection_point != 'ANY':
            rfq_inspection = rfq_data.get('inspection_point', '').upper()
            if rfq_inspection != inspection_point:
                reasons.append(f"• Inspection point mismatch: requires {inspection_point}, RFQ has {rfq_inspection}")
        
        # Check manufacturer filter
        manufacturer_filter = self.settings.get('manufacturer_filter', '').strip()
        if manufacturer_filter:
            manufacturers = [m.strip().lower() for m in manufacturer_filter.split('\n') if m.strip()]
            rfq_mfr = rfq_data.get('mfr', '').lower()
            if not any(mfr in rfq_mfr for mfr in manufacturers):
                mfr_display = rfq_data.get('mfr', 'Unknown')[:50]  # Truncate long manufacturer names
                if len(rfq_data.get('mfr', '')) > 50:
                    mfr_display += "..."
                reasons.append(f"• Manufacturer not in filter: '{mfr_display}'")
        
        return "\n".join(reasons) if reasons else "Unknown reason"
    
    def _save_processing_report(self, results: Dict[str, Any]):
        """Save detailed processing report to file"""
        import json
        from datetime import datetime
        
        try:
            # Create Output directory if it doesn't exist
            output_dir = Path("Output")
            output_dir.mkdir(exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            report_file = output_dir / f"pdf_processing_report_{timestamp}.json"
            
            # Save detailed report
            with open(report_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
                
            print(f"Detailed processing report saved to: {report_file}")
            
        except Exception as e:
            print(f"Error saving processing report: {e}")

    def process_all_pdfs(self) -> Dict[str, Any]:
        """Process all PDFs in the To Process folder"""
        from datetime import datetime
        
        # Enhanced results structure for detailed reporting
        results = {
            'processed': 0,
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'errors': [],
            'processed_files': [],
            'skipped_files': [],
            'error_files': [],
            'created_records': {
                'rfqs': [],
                'accounts': [],
                'contacts': [],
                'products': []
            },
            'updated_records': {
                'rfqs': [],
                'accounts': [],
                'contacts': [],
                'products': []
            },
            'processing_start': datetime.now().isoformat(),
            'processing_end': None,
            'filter_settings': self.get_filter_settings(),
            'database_stats_before': self._get_database_stats(),
            'database_stats_after': None
        }
        
        if not self.to_process_dir.exists():
            results['processing_end'] = datetime.now().isoformat()
            results['database_stats_after'] = self._get_database_stats()
            return results
        
        # Get all PDF files
        pdf_files = list(self.to_process_dir.glob("*.pdf")) + list(self.to_process_dir.glob("*.PDF"))
        
        for pdf_path in pdf_files:
            try:
                # First extract and parse data without creating records
                text_content = self.extract_pdf_text(pdf_path)
                parsed_data = self.parse_pdf_content(text_content, pdf_path.name)
                
                results['processed'] += 1
                
                # Check if RFQ should be processed based on filters BEFORE creating records
                if parsed_data.get('rfq') and not self.should_process_rfq(parsed_data['rfq']):
                    results['skipped'] += 1
                    results['skipped_files'].append({
                        'filename': pdf_path.name,
                        'reason': self._get_skip_reason(parsed_data['rfq']),
                        'rfq_data': parsed_data['rfq']
                    })
                    # Move to reviewed folder but mark as skipped
                    self.move_to_reviewed(pdf_path, skipped=True)
                    continue
                
                # Only now process the data and create records
                result = self.process_parsed_data(parsed_data)
                result['rfq_data'] = parsed_data['rfq']
                
                # Track processed file details
                file_result = {
                    'filename': pdf_path.name,
                    'rfq_data': result.get('rfq_data', {}),
                    'created_records': result.get('created_records', 0),
                    'updated_records': result.get('updated_records', 0),
                    'record_details': result.get('record_details', {})
                }
                results['processed_files'].append(file_result)
                
                if result['created_records'] > 0:
                    results['created'] += result['created_records']
                    # Add detailed record information
                    if 'record_details' in result:
                        for record_type, records in result['record_details'].get('created', {}).items():
                            if record_type in results['created_records']:
                                results['created_records'][record_type].extend(records)
                            
                if result['updated_records'] > 0:
                    results['updated'] += result['updated_records']
                    # Add detailed record information
                    if 'record_details' in result:
                        for record_type, records in result['record_details'].get('updated', {}).items():
                            if record_type in results['updated_records']:
                                results['updated_records'][record_type].extend(records)
                    
                # Move processed PDF to Reviewed folder
                if self.settings['move_processed_files']:
                    self.move_to_reviewed(pdf_path)
                
            except Exception as e:
                error_detail = {
                    'filename': pdf_path.name,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
                results['errors'].append(f"Error processing {pdf_path.name}: {str(e)}")
                results['error_files'].append(error_detail)
        
        # Finalize report
        results['processing_end'] = datetime.now().isoformat()
        results['database_stats_after'] = self._get_database_stats()
        
        # Save detailed report
        self._save_processing_report(results)
        
        return results
    
    def process_single_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """Process a single PDF file"""
        # Extract text from PDF
        text_content = self.extract_pdf_text(pdf_path)
        
        # Parse the content for structured data
        parsed_data = self.parse_pdf_content(text_content, pdf_path.name)
        
        # Process the parsed data and create/update records
        result = self.process_parsed_data(parsed_data)
        
        # Add RFQ data for filtering
        result['rfq_data'] = parsed_data['rfq']
        
        return result
    
    def extract_pdf_text(self, pdf_path: Path) -> str:
        """Extract text content from PDF"""
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            print(f"Error extracting text from {pdf_path}: {e}")
        
        return text
    
    def parse_pdf_content(self, text: str, filename: str) -> Dict[str, Any]:
        """Parse PDF content to extract structured data"""
        parsed_data = {
            'filename': filename,
            'opportunity': {},
            'account': {},
            'contact': {},
            'product': {},
            'rfq': {},
            'raw_text': text
        }
        
        # Parse RFQ/Opportunity information
        self.parse_rfq_info(text, parsed_data, filename)
        
        # Parse account/company information
        self.parse_account_info(text, parsed_data)
        
        # Parse contact information
        self.parse_contact_info(text, parsed_data)
        
        # Parse product information
        self.parse_product_info(text, parsed_data)
        
        return parsed_data
    
    def parse_rfq_info(self, text: str, parsed_data: Dict[str, Any], filename: str = ""):
        """Parse RFQ and opportunity information"""
        # Extract RFQ number patterns
        rfq_patterns = [
            r'SPE[A-Z0-9]+',  # Put SPE pattern first as it's most specific
            r'RFQ[:\s#]+([A-Z0-9\-]{3,})',  # Require at least 3 characters after RFQ
            r'Request\s+(?:for\s+)?(?:Quote|Quotation)[:\s#]+([A-Z0-9\-]{3,})',
            r'Solicitation[:\s#]+([A-Z0-9\-]{3,})',
        ]
        
        for pattern in rfq_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                parsed_data['rfq']['request_number'] = match.group(1) if len(match.groups()) > 0 else match.group(0)
                parsed_data['opportunity']['name'] = f"RFQ {parsed_data['rfq']['request_number']}"
                break
        
        # If no request number found or if we found a short SPE number, 
        # check if filename has a better SPE pattern
        if filename:
            filename_spe_match = re.search(r'SPE[A-Z0-9]{6,}', filename)
            if filename_spe_match:
                filename_spe = filename_spe_match.group(0)
                current_rfq = parsed_data['rfq'].get('request_number', '')
                # Use filename SPE if no request number found OR if current is short SPE pattern
                if not current_rfq or (current_rfq.startswith('SPE') and len(current_rfq) < len(filename_spe)):
                    parsed_data['rfq']['request_number'] = filename_spe
                    parsed_data['opportunity']['name'] = f"RFQ {filename_spe}"
            elif not parsed_data['rfq'].get('request_number'):
                # Fallback to full filename if no SPE pattern in filename
                base_filename = Path(filename).stem
                parsed_data['rfq']['request_number'] = base_filename
                parsed_data['opportunity']['name'] = f"RFQ {base_filename}"
        
        # Extract NSN (National Stock Number)
        nsn_pattern = r'NSN[:\s]*([0-9\-]{13,15})'
        nsn_match = re.search(nsn_pattern, text, re.IGNORECASE)
        if nsn_match:
            parsed_data['rfq']['nsn'] = nsn_match.group(1)
        
        # Extract close/due dates
        date_patterns = [
            r'(?:close|due|closing)(?:\s+date)?[:\s]*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
            r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})(?:\s+(?:close|due|closing))',
            r'(?:submit|submission)(?:\s+by)?[:\s]*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    date_str = match.group(1)
                    # Parse and format date
                    parsed_date = datetime.strptime(date_str.replace('-', '/'), '%m/%d/%Y').date()
                    parsed_data['rfq']['close_date'] = parsed_date.isoformat()
                    parsed_data['opportunity']['close_date'] = parsed_date.isoformat()
                except:
                    continue
                break
        
        # Extract quantities
        qty_patterns = [
            r'(?:quantity|qty|quan)[:\s]*(\d+)',
            r'(\d+)\s*(?:each|ea|units?|pcs?)'
        ]
        
        for pattern in qty_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                parsed_data['rfq']['quantity'] = int(match.group(1))
                break
        
        # Extract delivery days (from original DIBBs.py logic)
        delivery_pattern = r'6\.\s*DELIVER\s+BY\s*\S*\s*(\d+)'
        delivery_match = re.search(delivery_pattern, text, re.IGNORECASE)
        if delivery_match:
            parsed_data['rfq']['delivery_days'] = int(delivery_match.group(1))
        else:
            parsed_data['rfq']['delivery_days'] = 999
        
        # Extract ISO requirement
        iso_patterns = [
            r'ISO[:\s]*([YN]\w*)',
            r'(?:ISO|INTERNATIONAL STANDARD)[:\s]*(YES|NO)',
            r'(?:QUALITY|CERTIFICATION)[:\s]*ISO[:\s]*(YES|NO)'
        ]
        
        for pattern in iso_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                iso_value = match.group(1).upper()
                parsed_data['rfq']['iso'] = 'YES' if iso_value.startswith('Y') else 'NO'
                break
        else:
            parsed_data['rfq']['iso'] = 'NO'  # Default
        
        # Extract sampling requirement
        sampling_patterns = [
            r'SAMPLING[:\s]*(YES|NO)',
            r'SAMPLE[:\s]*REQUIRED[:\s]*(YES|NO)',
            r'(?:FIRST ARTICLE|SAMPLE)[:\s]*(REQUIRED|NOT REQUIRED)'
        ]
        
        for pattern in sampling_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                sampling_value = match.group(1).upper()
                parsed_data['rfq']['sampling'] = 'YES' if 'REQUIRED' in sampling_value or sampling_value == 'YES' else 'NO'
                break
        else:
            parsed_data['rfq']['sampling'] = 'NO'  # Default
        
        # Extract inspection point
        inspection_patterns = [
            r'INSPECTION\s*POINT[:\s]*(\w+)',
            r'INSPECT[:\s]*AT[:\s]*(\w+)',
            r'(?:DESTINATION|ORIGIN|SOURCE)\s*INSPECTION'
        ]
        
        for pattern in inspection_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if len(match.groups()) > 0:
                    parsed_data['rfq']['inspection_point'] = match.group(1).upper()
                else:
                    # For the third pattern, extract the inspection type
                    if 'DESTINATION' in match.group(0).upper():
                        parsed_data['rfq']['inspection_point'] = 'DESTINATION'
                    elif 'ORIGIN' in match.group(0).upper():
                        parsed_data['rfq']['inspection_point'] = 'ORIGIN'
                    elif 'SOURCE' in match.group(0).upper():
                        parsed_data['rfq']['inspection_point'] = 'SOURCE'
                break
        else:
            parsed_data['rfq']['inspection_point'] = 'DESTINATION'  # Default
        
        # Set default values
        parsed_data['rfq']['status'] = 'New'
        parsed_data['opportunity']['stage'] = 'Qualification'
    
    def parse_account_info(self, text: str, parsed_data: Dict[str, Any]):
        """Parse company/account information"""
        # Look for government agencies or company names
        agency_patterns = [
            r'(?:Department of|Dept of|DOD|DOT|DHS|GSA|VA|USAF|Army|Navy|Marines?)\s+([A-Z][A-Za-z\s&]+)',
            r'([A-Z][A-Za-z\s&]+(?:Agency|Administration|Department|Command|Center|Office))',
            r'U\.?S\.?\s+([A-Z][A-Za-z\s&]+)',
            r'([A-Z]{2,}(?:\s+[A-Z][A-Za-z]+)*)\s+(?:Base|Station|Depot|Arsenal)'
        ]
        
        for pattern in agency_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                account_name = match.group(1).strip()
                if len(account_name) > 3:  # Filter out short matches
                    parsed_data['account']['name'] = account_name
                    parsed_data['account']['type'] = 'Customer'
                    break
        
        # Extract address information
        address_pattern = r'([A-Z][A-Za-z\s,]+),?\s+([A-Z]{2})\s+(\d{5}(?:-\d{4})?)'
        address_match = re.search(address_pattern, text)
        if address_match:
            parsed_data['account']['city'] = address_match.group(1).strip()
            parsed_data['account']['state'] = address_match.group(2)
            parsed_data['account']['postal_code'] = address_match.group(3)
    
    def parse_contact_info(self, text: str, parsed_data: Dict[str, Any]):
        """Parse contact information"""
        # Extract email addresses
        email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        email_matches = re.findall(email_pattern, text)
        if email_matches:
            parsed_data['contact']['email'] = email_matches[0]
        
        # Extract phone numbers
        phone_patterns = [
            r'(?:phone|tel|telephone)[:\s]*(\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4})',
            r'(\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4})'
        ]
        
        for pattern in phone_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                parsed_data['contact']['phone'] = match.group(1)
                break
        
        # Extract contact names (basic pattern)
        name_patterns = [
            r'(?:contact|POC|point of contact)[:\s]*([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+),?\s+(?:Contracting|Contract|Procurement)'
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                full_name = match.group(1).strip()
                name_parts = full_name.split()
                if len(name_parts) >= 2:
                    parsed_data['contact']['first_name'] = name_parts[0]
                    parsed_data['contact']['last_name'] = ' '.join(name_parts[1:])
                break
    
    def parse_product_info(self, text: str, parsed_data: Dict[str, Any]):
        """Parse product information"""
        # Extract product description
        desc_patterns = [
            r'(?:description|item|product|supply)[:\s]*([A-Z][A-Za-z0-9\s,\-\.]{10,100})',
            r'Line\s+Item[:\s]*([A-Z][A-Za-z0-9\s,\-\.]{10,100})',
            r'ITEM\s+DESCRIPTION[:\s]*([A-Z][A-Za-z0-9\s,\-\.]{10,100})'
        ]
        
        for pattern in desc_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                description = match.group(1).strip()
                # Clean up description
                description = re.sub(r'\s+', ' ', description)
                if len(description) > 10:
                    parsed_data['product']['description'] = description
                    parsed_data['product']['name'] = description  # Use description as name
                    parsed_data['rfq']['product_description'] = description
                break
        
        # Extract part numbers
        part_patterns = [
            r'(?:part|p\/n|part number|item number)[:\s]*([A-Z0-9\-]+)',
            r'([A-Z]{2,}[0-9\-]+[A-Z0-9]*)'
        ]
        
        for pattern in part_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                parsed_data['product']['part_number'] = match.group(1)
                break
        
        # Extract manufacturer information (MFR)
        mfr_patterns = [
            r'MFR[:\s]*([A-Z][A-Za-z\s&\-\.]+?)(?:\n|$|[0-9])',
            r'MANUFACTURER[:\s]*([A-Z][A-Za-z\s&\-\.]+?)(?:\n|$|[0-9])',
            r'(?:MADE BY|BRAND)[:\s]*([A-Z][A-Za-z\s&\-\.]+?)(?:\n|$|[0-9])',
            r'([A-Z][A-Za-z\s&\-\.]*(?:PARKER|MONKEY MONKEY|BOEING|LOCKHEED|GENERAL|HONEYWELL)[A-Za-z\s&\-\.]*)',
        ]
        
        for pattern in mfr_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                manufacturer = match.group(1).strip()
                # Clean up manufacturer name
                manufacturer = re.sub(r'\s+', ' ', manufacturer)
                manufacturer = manufacturer.strip('.,;:')
                if len(manufacturer) > 2:
                    parsed_data['product']['manufacturer'] = manufacturer
                    parsed_data['rfq']['mfr'] = manufacturer
                break
        
        # If no MFR found, set default for compatibility
        if 'mfr' not in parsed_data['rfq']:
            parsed_data['rfq']['mfr'] = 'Unknown'
    
    def process_parsed_data(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process parsed data and create/update database records"""
        result = {
            'created_records': 0,
            'updated_records': 0,
            'record_ids': {}
        }
        
        # Process Account
        if parsed_data['account'].get('name'):
            account_id = self.process_account(parsed_data['account'])
            result['record_ids']['account_id'] = account_id
            if account_id:
                if self.is_new_record('accounts', account_id):
                    result['created_records'] += 1
                else:
                    result['updated_records'] += 1
        
        # Process Contact
        if parsed_data['contact'].get('email') or parsed_data['contact'].get('last_name'):
            contact_id = self.process_contact(parsed_data['contact'], result['record_ids'].get('account_id'))
            result['record_ids']['contact_id'] = contact_id
            if contact_id:
                if self.is_new_record('contacts', contact_id):
                    result['created_records'] += 1
                else:
                    result['updated_records'] += 1
        
        # Process Product
        if parsed_data['product'].get('description') or parsed_data['product'].get('part_number'):
            product_id = self.process_product(parsed_data['product'])
            result['record_ids']['product_id'] = product_id
            if product_id:
                if self.is_new_record('products', product_id):
                    result['created_records'] += 1
                else:
                    result['updated_records'] += 1
        
        # Process RFQ
        if parsed_data['rfq'].get('request_number'):
            rfq_id = self.process_rfq(parsed_data['rfq'], result['record_ids'])
            result['record_ids']['rfq_id'] = rfq_id
            if rfq_id:
                if self.is_new_record('rfqs', rfq_id):
                    result['created_records'] += 1
                else:
                    result['updated_records'] += 1
        
        # Process Opportunity
        if parsed_data['opportunity'].get('name'):
            opportunity_id = self.process_opportunity(parsed_data['opportunity'], result['record_ids'])
            result['record_ids']['opportunity_id'] = opportunity_id
            if opportunity_id:
                if self.is_new_record('opportunities', opportunity_id):
                    result['created_records'] += 1
                else:
                    result['updated_records'] += 1
        
        return result
    
    def process_account(self, account_data: Dict[str, Any]) -> Optional[int]:
        """Process account data - create or update"""
        if not account_data.get('name'):
            return None
        
        # Check if account exists
        existing = self.crm_data.execute_query(
            "SELECT * FROM accounts WHERE LOWER(name) = LOWER(?)",
            [account_data['name']]
        )
        
        if existing:
            # Update existing account
            account_id = existing[0]['id']
            update_data = {k: v for k, v in account_data.items() if v}
            if update_data:
                self.crm_data.update_account(account_id, **update_data)
            return account_id
        else:
            # Create new account
            account_data.setdefault('status', 'Active')
            account_data.setdefault('created_date', datetime.now().isoformat())
            return self.crm_data.create_account(**account_data)
    
    def process_contact(self, contact_data: Dict[str, Any], account_id: Optional[int] = None) -> Optional[int]:
        """Process contact data - create or update"""
        if not (contact_data.get('email') or contact_data.get('last_name')):
            return None
        
        # Check if contact exists by email or name
        where_clause = ""
        params = []
        
        if contact_data.get('email'):
            where_clause = "LOWER(email) = LOWER(?)"
            params.append(contact_data['email'])
        elif contact_data.get('last_name'):
            where_clause = "LOWER(last_name) = LOWER(?) AND LOWER(first_name) = LOWER(?)"
            params.extend([contact_data.get('last_name', ''), contact_data.get('first_name', '')])
        
        existing = self.crm_data.execute_query(f"SELECT * FROM contacts WHERE {where_clause}", params)
        
        if existing:
            # Update existing contact
            contact_id = existing[0]['id']
            update_data = {k: v for k, v in contact_data.items() if v}
            if account_id:
                update_data['account_id'] = account_id
            if update_data:
                self.crm_data.update_contact(contact_id, **update_data)
            return contact_id
        else:
            # Create new contact
            if account_id:
                contact_data['account_id'] = account_id
            contact_data.setdefault('status', 'Active')
            contact_data.setdefault('created_date', datetime.now().isoformat())
            return self.crm_data.create_contact(**contact_data)
    
    def process_product(self, product_data: Dict[str, Any]) -> Optional[int]:
        """Process product data - create or update"""
        if not (product_data.get('description') or product_data.get('part_number')):
            return None
        
        # Check if product exists
        where_clause = ""
        params = []
        
        if product_data.get('part_number'):
            where_clause = "LOWER(part_number) = LOWER(?)"
            params.append(product_data['part_number'])
        else:
            where_clause = "LOWER(description) = LOWER(?)"
            params.append(product_data['description'])
        
        existing = self.crm_data.execute_query(f"SELECT * FROM products WHERE {where_clause}", params)
        
        if existing:
            # Update existing product
            product_id = existing[0]['id']
            update_data = {k: v for k, v in product_data.items() if v}
            if update_data:
                self.crm_data.update_product(product_id, **update_data)
            return product_id
        else:
            # Create new product
            product_data.setdefault('status', 'Active')
            product_data.setdefault('created_date', datetime.now().isoformat())
            return self.crm_data.create_product(**product_data)
    
    def process_rfq(self, rfq_data: Dict[str, Any], record_ids: Dict[str, int]) -> Optional[int]:
        """Process RFQ data - create or update"""
        if not rfq_data.get('request_number'):
            return None
        
        # Check if RFQ exists
        existing = self.crm_data.execute_query(
            "SELECT * FROM rfqs WHERE LOWER(request_number) = LOWER(?)",
            [rfq_data['request_number']]
        )
        
        if existing:
            # Update existing RFQ
            rfq_id = existing[0]['id']
            update_data = {k: v for k, v in rfq_data.items() if v}
            # Link to other records
            if record_ids.get('account_id'):
                update_data['account_id'] = record_ids['account_id']
            if record_ids.get('contact_id'):
                update_data['contact_id'] = record_ids['contact_id']
            if record_ids.get('product_id'):
                update_data['product_id'] = record_ids['product_id']
            
            if update_data:
                self.crm_data.update_rfq(rfq_id, **update_data)
            return rfq_id
        else:
            # Create new RFQ
            # Link to other records
            if record_ids.get('account_id'):
                rfq_data['account_id'] = record_ids['account_id']
            if record_ids.get('contact_id'):
                rfq_data['contact_id'] = record_ids['contact_id']
            if record_ids.get('product_id'):
                rfq_data['product_id'] = record_ids['product_id']
            
            rfq_data.setdefault('created_date', datetime.now().isoformat())
            return self.crm_data.create_rfq(**rfq_data)
    
    def process_opportunity(self, opportunity_data: Dict[str, Any], record_ids: Dict[str, int]) -> Optional[int]:
        """Process opportunity data - create or update"""
        if not opportunity_data.get('name'):
            return None
        
        # Check if opportunity exists
        existing = self.crm_data.execute_query(
            "SELECT * FROM opportunities WHERE LOWER(name) = LOWER(?)",
            [opportunity_data['name']]
        )
        
        if existing:
            # Update existing opportunity
            opportunity_id = existing[0]['id']
            update_data = {k: v for k, v in opportunity_data.items() if v}
            # Link to other records
            if record_ids.get('account_id'):
                update_data['account_id'] = record_ids['account_id']
            if record_ids.get('contact_id'):
                update_data['contact_id'] = record_ids['contact_id']
            if record_ids.get('rfq_id'):
                update_data['rfq_id'] = record_ids['rfq_id']
            
            if update_data:
                self.crm_data.update_opportunity(opportunity_id, **update_data)
            return opportunity_id
        else:
            # Create new opportunity
            # Link to other records
            if record_ids.get('account_id'):
                opportunity_data['account_id'] = record_ids['account_id']
            if record_ids.get('contact_id'):
                opportunity_data['contact_id'] = record_ids['contact_id']
            if record_ids.get('rfq_id'):
                opportunity_data['rfq_id'] = record_ids['rfq_id']
            
            opportunity_data.setdefault('created_date', datetime.now().isoformat())
            opportunity_data.setdefault('probability', 25)
            return self.crm_data.create_opportunity(**opportunity_data)
    
    def is_new_record(self, table: str, record_id: int) -> bool:
        """Check if a record was just created (within last minute)"""
        try:
            result = self.crm_data.execute_query(
                f"SELECT created_date FROM {table} WHERE id = ?",
                [record_id]
            )
            if result:
                created_date = datetime.fromisoformat(result[0]['created_date'])
                now = datetime.now()
                return (now - created_date).total_seconds() < 60
        except:
            pass
        return False
    
    def move_to_reviewed(self, pdf_path: Path, skipped: bool = False):
        """Move processed PDF to Reviewed folder"""
        try:
            # Create subfolder for skipped files if needed
            if skipped:
                destination_dir = self.reviewed_dir / "Skipped"
                destination_dir.mkdir(exist_ok=True)
            else:
                destination_dir = self.reviewed_dir
            
            destination = destination_dir / pdf_path.name
            
            # If file already exists in destination, add timestamp
            if destination.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                name_parts = pdf_path.stem, timestamp, pdf_path.suffix
                destination = destination_dir / f"{name_parts[0]}_{name_parts[1]}{name_parts[2]}"
            
            shutil.move(str(pdf_path), str(destination))
            status = "skipped and moved" if skipped else "processed and moved"
            print(f"{pdf_path.name} {status} to {destination_dir.name} folder")
            
        except Exception as e:
            print(f"Error moving {pdf_path.name}: {e}")

# Initialize PDF processor
pdf_processor = PDFProcessor()
