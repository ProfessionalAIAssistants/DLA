
# CRM Database Documentation
Generated: 2025-08-29 12:09:16

## Database Overview
- **Database File**: `data/crm.db`
- **Total Tables**: 23
- **Total Records**: 1,194

## Table Summary

### ACCOUNTS
- **Records**: 19
- **Columns**: 15

**Schema**:
- `id` (INTEGER) PRIMARY KEY
- `name` (TEXT) NOT NULL
- `type` (TEXT) 
- `summary` (TEXT) 
- `detail` (TEXT) 
- `website` (TEXT) 
- `email` (TEXT) 
- `location` (TEXT) 
- `linkedin` (TEXT) 
- `parent_co` (TEXT) 
- `cage` (TEXT) 
- `created_date` (TIMESTAMP) DEFAULT CURRENT_TIMESTAMP
- `image` (TEXT) 
- `video` (TEXT) 
- `is_active` (BOOLEAN) DEFAULT 1

### CONTACTS
- **Records**: 118
- **Columns**: 17

**Schema**:
- `id` (INTEGER) PRIMARY KEY
- `first_name` (TEXT) NOT NULL
- `last_name` (TEXT) NOT NULL
- `title` (TEXT) 
- `email` (TEXT) 
- `phone` (TEXT) 
- `mobile` (TEXT) 
- `account_id` (INTEGER) 
- `department` (TEXT) 
- `reports_to` (INTEGER) 
- `lead_source` (TEXT) 
- `address` (TEXT) 
- `description` (TEXT) 
- `created_date` (TIMESTAMP) DEFAULT CURRENT_TIMESTAMP
- `modified_date` (TIMESTAMP) DEFAULT CURRENT_TIMESTAMP
- `owner` (TEXT) 
- `is_active` (BOOLEAN) DEFAULT 1

### EMAIL_RESPONSES
- **Records**: 0
- **Columns**: 17

**Schema**:
- `id` (INTEGER) PRIMARY KEY
- `original_email_id` (INTEGER) 
- `opportunity_id` (INTEGER) 
- `vendor_account_id` (INTEGER) 
- `sender_email` (TEXT) 
- `subject` (TEXT) 
- `content` (TEXT) 
- `received_date` (TEXT) 
- `processed_date` (TEXT) 
- `quote_extracted` (BOOLEAN) DEFAULT 0
- `quote_amount` (REAL) 
- `lead_time_days` (INTEGER) 
- `availability` (TEXT) 
- `created_rfq_id` (INTEGER) 
- `created_interaction_id` (INTEGER) 
- `created_task_id` (INTEGER) 
- `processing_status` (TEXT) DEFAULT 'Pending'

### EMAIL_TEMPLATES
- **Records**: 2
- **Columns**: 9

**Schema**:
- `id` (INTEGER) PRIMARY KEY
- `name` (TEXT) 
- `type` (TEXT) 
- `subject_template` (TEXT) 
- `body_template` (TEXT) 
- `variables` (TEXT) 
- `is_active` (INTEGER) DEFAULT 1
- `created_date` (TEXT) 
- `modified_date` (TEXT) 

### INTERACTIONS
- **Records**: 0
- **Columns**: 23

**Schema**:
- `id` (INTEGER) PRIMARY KEY
- `subject` (TEXT) NOT NULL
- `description` (TEXT) 
- `type` (TEXT) 
- `interaction_date` (DATETIME) 
- `duration_minutes` (INTEGER) 
- `location` (TEXT) 
- `outcome` (TEXT) 
- `related_to_type` (TEXT) 
- `related_to_id` (INTEGER) 
- `contact_id` (INTEGER) 
- `account_id` (INTEGER) 
- `opportunity_id` (INTEGER) 
- `rfq_id` (INTEGER) 
- `created_by` (TEXT) 
- `created_date` (TIMESTAMP) DEFAULT CURRENT_TIMESTAMP
- `is_active` (INTEGER) DEFAULT 1
- `last_modified` (TIMESTAMP) 
- `email_type` (TEXT) 
- `reference_id` (TEXT) 
- `project_id` (INTEGER) 
- `direction` (TEXT) 
- `status` (TEXT) DEFAULT "Active"

### OPPORTUNITIES
- **Records**: 14
- **Columns**: 33

**Schema**:
- `id` (INTEGER) PRIMARY KEY
- `name` (TEXT) NOT NULL
- `account_id` (INTEGER) 
- `contact_id` (INTEGER) 
- `stage` (TEXT) 
- `amount` (REAL) 
- `probability` (INTEGER) 
- `close_date` (DATE) 
- `lead_source` (TEXT) 
- `next_step` (TEXT) 
- `type` (TEXT) 
- `description` (TEXT) 
- `created_date` (TIMESTAMP) DEFAULT CURRENT_TIMESTAMP
- `modified_date` (TIMESTAMP) DEFAULT CURRENT_TIMESTAMP
- `owner` (TEXT) 
- `forecast_category` (TEXT) 
- `state` (TEXT) 
- `bid_price` (REAL) 
- `product_id` (INTEGER) 
- `bid_date` (DATE) 
- `mfr` (TEXT) 
- `iso` (TEXT) 
- `fob` (TEXT) 
- `buyer` (TEXT) 
- `packaging_type` (TEXT) 
- `purchase_costs` (REAL) 
- `packaging_shipping` (REAL) 
- `quantity` (INTEGER) 
- `profit` (REAL) 
- `sampling` (TEXT) DEFAULT "No"
- `unit` (TEXT) 
- `project_id` (INTEGER) 
- `delivery_days` (INTEGER) 

### OPPORTUNITIES_BACKUP_20250821
- **Records**: 5
- **Columns**: 31

**Schema**:
- `id` (INT) 
- `name` (TEXT) 
- `account_id` (INT) 
- `contact_id` (INT) 
- `stage` (TEXT) 
- `amount` (REAL) 
- `probability` (INT) 
- `close_date` (NUM) 
- `lead_source` (TEXT) 
- `next_step` (TEXT) 
- `type` (TEXT) 
- `description` (TEXT) 
- `created_date` (NUM) 
- `modified_date` (NUM) 
- `owner` (TEXT) 
- `forecast_category` (TEXT) 
- `state` (TEXT) 
- `bid_price` (REAL) 
- `product_id` (INT) 
- `bid_date` (NUM) 
- `mfr` (TEXT) 
- `iso` (TEXT) 
- `fob` (TEXT) 
- `buyer` (TEXT) 
- `packaging_type` (TEXT) 
- `purchase_costs` (REAL) 
- `packaging_shipping` (REAL) 
- `quantity` (INT) 
- `profit` (REAL) 
- `sampling` (TEXT) 
- `unit` (TEXT) 

### PRODUCTS
- **Records**: 977
- **Columns**: 16

**Schema**:
- `id` (INTEGER) PRIMARY KEY
- `name` (TEXT) NOT NULL
- `product_code` (TEXT) 
- `nsn` (TEXT) NOT NULL
- `fsc` (TEXT) 
- `description` (TEXT) 
- `category` (TEXT) 
- `family` (TEXT) 
- `unit_price` (REAL) 
- `cost_price` (REAL) 
- `list_price` (REAL) 
- `manufacturer` (TEXT) 
- `part_number` (TEXT) 
- `is_active` (BOOLEAN) DEFAULT 1
- `created_date` (TIMESTAMP) DEFAULT CURRENT_TIMESTAMP
- `modified_date` (TIMESTAMP) DEFAULT CURRENT_TIMESTAMP

### PROJECT_CONTACTS
- **Records**: 0
- **Columns**: 5

**Schema**:
- `id` (INTEGER) PRIMARY KEY
- `project_id` (INTEGER) NOT NULL
- `contact_id` (INTEGER) NOT NULL
- `role` (TEXT) DEFAULT 'participant'
- `created_date` (TEXT) DEFAULT CURRENT_TIMESTAMP

### PROJECT_OPPORTUNITIES
- **Records**: 0
- **Columns**: 5

**Schema**:
- `id` (INTEGER) PRIMARY KEY
- `project_id` (INTEGER) NOT NULL
- `opportunity_id` (INTEGER) NOT NULL
- `relationship_type` (TEXT) DEFAULT 'related'
- `created_date` (TEXT) DEFAULT CURRENT_TIMESTAMP

### PROJECT_PRODUCTS
- **Records**: 0
- **Columns**: 6

**Schema**:
- `id` (INTEGER) PRIMARY KEY
- `project_id` (INTEGER) NOT NULL
- `product_id` (TEXT) NOT NULL
- `quantity` (INTEGER) 
- `role` (TEXT) 
- `created_date` (TEXT) DEFAULT CURRENT_TIMESTAMP

### PROJECT_TASKS
- **Records**: 0
- **Columns**: 5

**Schema**:
- `id` (INTEGER) PRIMARY KEY
- `project_id` (INTEGER) NOT NULL
- `task_id` (INTEGER) NOT NULL
- `relationship_type` (TEXT) DEFAULT 'associated'
- `created_date` (TEXT) DEFAULT CURRENT_TIMESTAMP

### PROJECTS
- **Records**: 2
- **Columns**: 20

**Schema**:
- `id` (INTEGER) PRIMARY KEY
- `name` (TEXT) NOT NULL
- `description` (TEXT) 
- `start_date` (TEXT) 
- `end_date` (TEXT) 
- `status` (TEXT) 
- `due_date` (TEXT) 
- `priority` (TEXT) DEFAULT 'Medium'
- `created_date` (TEXT) 
- `summary` (TEXT) 
- `vendor_id` (INTEGER) 
- `parent_project_id` (INTEGER) 
- `budget` (REAL) 
- `actual_cost` (REAL) 
- `progress_percentage` (INTEGER) 
- `project_manager` (TEXT) 
- `team_members` (TEXT) 
- `notes` (TEXT) 
- `completion_date` (DATE) 
- `last_modified` (TIMESTAMP) 

### QPL
- **Records**: 3
- **Columns**: 15

**Schema**:
- `id` (INTEGER) PRIMARY KEY
- `nsn` (TEXT) NOT NULL
- `fsc` (TEXT) 
- `product_name` (TEXT) 
- `manufacturer` (TEXT) 
- `part_number` (TEXT) 
- `cage_code` (TEXT) 
- `description` (TEXT) 
- `specifications` (TEXT) 
- `qualification_date` (DATE) 
- `expiration_date` (DATE) 
- `status` (TEXT) DEFAULT 'Active'
- `product_id` (INTEGER) 
- `created_date` (TIMESTAMP) DEFAULT CURRENT_TIMESTAMP
- `modified_date` (TIMESTAMP) DEFAULT CURRENT_TIMESTAMP

### QUOTES
- **Records**: 0
- **Columns**: 12

**Schema**:
- `id` (INTEGER) PRIMARY KEY
- `rfq_email_id` (TEXT) 
- `vendor_account_id` (INTEGER) 
- `quote_number` (TEXT) 
- `quote_amount` (DECIMAL(10,2)) 
- `lead_time` (TEXT) 
- `delivery_terms` (TEXT) 
- `validity_period` (TEXT) 
- `notes` (TEXT) 
- `status` (TEXT) DEFAULT 'Pending'
- `quote_date` (TEXT) 
- `response_date` (TEXT) 

### RFQS
- **Records**: 1
- **Columns**: 42

**Schema**:
- `id` (INTEGER) PRIMARY KEY
- `request_number` (TEXT) NOT NULL
- `pdf_name` (TEXT) 
- `pdf_path` (TEXT) 
- `solicitation_url` (TEXT) 
- `open_date` (DATE) 
- `close_date` (DATE) 
- `purchase_number` (TEXT) 
- `nsn` (TEXT) 
- `fsc` (TEXT) 
- `delivery_days` (INTEGER) 
- `payment_history` (TEXT) 
- `unit` (TEXT) 
- `quantity` (INTEGER) 
- `fob` (TEXT) 
- `iso` (TEXT) 
- `inspection_point` (TEXT) 
- `sampling` (TEXT) 
- `product_description` (TEXT) 
- `manufacturer` (TEXT) 
- `packaging` (TEXT) 
- `package_type` (TEXT) 
- `office` (TEXT) 
- `division` (TEXT) 
- `buyer_address` (TEXT) 
- `buyer_name` (TEXT) 
- `buyer_code` (TEXT) 
- `buyer_telephone` (TEXT) 
- `buyer_email` (TEXT) 
- `buyer_fax` (TEXT) 
- `buyer_info` (TEXT) 
- `status` (TEXT) DEFAULT 'New'
- `opportunity_id` (INTEGER) 
- `account_id` (INTEGER) 
- `contact_id` (INTEGER) 
- `product_id` (INTEGER) 
- `notes` (TEXT) 
- `created_date` (TIMESTAMP) DEFAULT CURRENT_TIMESTAMP
- `modified_date` (TIMESTAMP) DEFAULT CURRENT_TIMESTAMP
- `quote_amount` (DECIMAL(10,2)) 
- `lead_time` (TEXT) 
- `effective_date` (DATE) 

### RFQS_BACKUP_20250821
- **Records**: 5
- **Columns**: 39

**Schema**:
- `id` (INT) 
- `request_number` (TEXT) 
- `pdf_name` (TEXT) 
- `pdf_path` (TEXT) 
- `solicitation_url` (TEXT) 
- `open_date` (NUM) 
- `close_date` (NUM) 
- `purchase_number` (TEXT) 
- `nsn` (TEXT) 
- `fsc` (TEXT) 
- `delivery_days` (INT) 
- `payment_history` (TEXT) 
- `unit` (TEXT) 
- `quantity` (INT) 
- `fob` (TEXT) 
- `iso` (TEXT) 
- `inspection_point` (TEXT) 
- `sampling` (TEXT) 
- `product_description` (TEXT) 
- `manufacturer` (TEXT) 
- `packaging` (TEXT) 
- `package_type` (TEXT) 
- `office` (TEXT) 
- `division` (TEXT) 
- `buyer_address` (TEXT) 
- `buyer_name` (TEXT) 
- `buyer_code` (TEXT) 
- `buyer_telephone` (TEXT) 
- `buyer_email` (TEXT) 
- `buyer_fax` (TEXT) 
- `buyer_info` (TEXT) 
- `status` (TEXT) 
- `opportunity_id` (INT) 
- `account_id` (INT) 
- `contact_id` (INT) 
- `product_id` (INT) 
- `notes` (TEXT) 
- `created_date` (NUM) 
- `modified_date` (NUM) 

### RFQS_BACKUP_SIMPLE
- **Records**: 5
- **Columns**: 39

**Schema**:
- `id` (INT) 
- `request_number` (TEXT) 
- `pdf_name` (TEXT) 
- `pdf_path` (TEXT) 
- `solicitation_url` (TEXT) 
- `open_date` (NUM) 
- `close_date` (NUM) 
- `purchase_number` (TEXT) 
- `nsn` (TEXT) 
- `fsc` (TEXT) 
- `delivery_days` (INT) 
- `payment_history` (TEXT) 
- `unit` (TEXT) 
- `quantity` (INT) 
- `fob` (TEXT) 
- `iso` (TEXT) 
- `inspection_point` (TEXT) 
- `sampling` (TEXT) 
- `product_description` (TEXT) 
- `manufacturer` (TEXT) 
- `packaging` (TEXT) 
- `package_type` (TEXT) 
- `office` (TEXT) 
- `division` (TEXT) 
- `buyer_address` (TEXT) 
- `buyer_name` (TEXT) 
- `buyer_code` (TEXT) 
- `buyer_telephone` (TEXT) 
- `buyer_email` (TEXT) 
- `buyer_fax` (TEXT) 
- `buyer_info` (TEXT) 
- `status` (TEXT) 
- `opportunity_id` (INT) 
- `account_id` (INT) 
- `contact_id` (INT) 
- `product_id` (INT) 
- `notes` (TEXT) 
- `created_date` (NUM) 
- `modified_date` (NUM) 

### SQLITE_SEQUENCE
- **Records**: 12
- **Columns**: 2

**Schema**:
- `name` () 
- `seq` () 

### TASKS
- **Records**: 21
- **Columns**: 24

**Schema**:
- `id` (INTEGER) PRIMARY KEY
- `subject` (TEXT) 
- `description` (TEXT) 
- `status` (TEXT) 
- `work_date` (DATE) 
- `due_date` (DATE) 
- `owner` (TEXT) 
- `start_date` (DATE) 
- `completed_date` (DATE) 
- `parent_item_type` (TEXT) 
- `parent_item_id` (INTEGER) 
- `sub_item_type` (TEXT) 
- `sub_item_id` (INTEGER) 
- `priority` (TEXT) 
- `time_taken` (INTEGER) 
- `created_date` (TIMESTAMP) DEFAULT CURRENT_TIMESTAMP
- `modified_date` (TIMESTAMP) DEFAULT CURRENT_TIMESTAMP
- `contact_id` (INTEGER) 
- `project_id` (INTEGER) 
- `account_id` (INTEGER) 
- `type` (TEXT) 
- `related_to_type` (TEXT) 
- `related_to_id` (TEXT) 
- `assigned_to` (TEXT) 

### VENDOR_RFQ_EMAILS
- **Records**: 3
- **Columns**: 12

**Schema**:
- `id` (INTEGER) PRIMARY KEY
- `opportunity_id` (INTEGER) 
- `vendor_account_id` (INTEGER) 
- `vendor_contact_id` (INTEGER) 
- `rfq_email_id` (TEXT) 
- `subject` (TEXT) 
- `email_body` (TEXT) 
- `status` (TEXT) DEFAULT 'Draft'
- `created_date` (TEXT) 
- `sent_date` (TEXT) 
- `response_received_date` (TEXT) 
- `response_data` (TEXT) 

### WORKFLOW_AUTOMATION_RULES
- **Records**: 5
- **Columns**: 9

**Schema**:
- `id` (INTEGER) PRIMARY KEY
- `rule_name` (TEXT) 
- `trigger_event` (TEXT) 
- `trigger_conditions` (TEXT) 
- `actions` (TEXT) 
- `enabled` (BOOLEAN) DEFAULT 1
- `created_date` (TEXT) DEFAULT CURRENT_TIMESTAMP
- `last_executed` (TEXT) 
- `execution_count` (INTEGER) DEFAULT 0

### WORKFLOW_EXECUTION_LOG
- **Records**: 2
- **Columns**: 7

**Schema**:
- `id` (INTEGER) PRIMARY KEY
- `rule_id` (INTEGER) 
- `trigger_data` (TEXT) 
- `execution_time` (TEXT) 
- `success` (BOOLEAN) 
- `actions_performed` (TEXT) 
- `error_message` (TEXT) 

## Data Integrity Issues
- ❌ Opportunities without valid Account: 1 orphaned records
- ❌ Tasks without valid assigned_to: 18 orphaned records

## Empty Tables
- email_responses
- interactions
- project_contacts
- project_opportunities
- project_products
- project_tasks
- quotes

## Low Usage Tables
- email_templates (2 records)
- projects (2 records)
- qpl (3 records)
- rfqs (1 records)
- vendor_rfq_emails (3 records)
- workflow_execution_log (2 records)
