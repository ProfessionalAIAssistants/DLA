# DLA CRM Database - Complete Manager Documentation
Generated: 2025-08-29 12:17:47

## 🎯 Executive Summary
This is a comprehensive guide to the DLA CRM database structure, designed for
database managers and system administrators. The database supports a complete
CRM system with DIBBs (Defense Industrial Base Business System) integration.

## 📊 Database Overview
- **Database Type**: SQLite
- **Location**: `C:\Users\Kebron\Documents\GitHub\DLA\data\crm.db`
- **Size**: 496.0 KB (optimized - 30% reduction after backup cleanup)
- **Total Tables**: 20 (3 backup tables removed)
- **Total Records**: 1,179 (15 backup records removed)

## 🏢 Core Business Entities

### Companies and Organizations (`accounts`)
**Purpose**: Customer prospects, vendors, competitors
**Records**: 19

**Key Fields**:
- `id` (INTEGER) - NULL
- `name` (TEXT) - NOT NULL
- `type` (TEXT) - NULL
- `summary` (TEXT) - NULL
- `detail` (TEXT) - NULL
- `website` (TEXT) - NULL
- `email` (TEXT) - NULL
- `location` (TEXT) - NULL
- `linkedin` (TEXT) - NULL
- `parent_co` (TEXT) - NULL
- ... and 5 more fields

### Individual People (`contacts`)
**Purpose**: People associated with accounts
**Records**: 118

**Key Fields**:
- `id` (INTEGER) - NULL
- `first_name` (TEXT) - NOT NULL
- `last_name` (TEXT) - NOT NULL
- `title` (TEXT) - NULL
- `email` (TEXT) - NULL
- `phone` (TEXT) - NULL
- `mobile` (TEXT) - NULL
- `account_id` (INTEGER) - NULL
- `department` (TEXT) - NULL
- `reports_to` (INTEGER) - NULL
- ... and 7 more fields

### Sales Opportunities (`opportunities`)
**Purpose**: Potential deals and quotes
**Records**: 14

**Key Fields**:
- `id` (INTEGER) - NULL
- `name` (TEXT) - NOT NULL
- `account_id` (INTEGER) - NULL
- `contact_id` (INTEGER) - NULL
- `stage` (TEXT) - NULL
- `amount` (REAL) - NULL
- `probability` (INTEGER) - NULL
- `close_date` (DATE) - NULL
- `lead_source` (TEXT) - NULL
- `next_step` (TEXT) - NULL
- ... and 23 more fields

### Requests for Quote (`rfqs`)
**Purpose**: DIBBs solicitations and RFQ documents
**Records**: 1

**Key Fields**:
- `id` (INTEGER) - NULL
- `request_number` (TEXT) - NOT NULL
- `pdf_name` (TEXT) - NULL
- `pdf_path` (TEXT) - NULL
- `solicitation_url` (TEXT) - NULL
- `open_date` (DATE) - NULL
- `close_date` (DATE) - NULL
- `purchase_number` (TEXT) - NULL
- `nsn` (TEXT) - NULL
- `fsc` (TEXT) - NULL
- ... and 32 more fields

### Action Items (`tasks`)
**Purpose**: To-do items and follow-ups
**Records**: 21

**Key Fields**:
- `id` (INTEGER) - NULL
- `subject` (TEXT) - NULL
- `description` (TEXT) - NULL
- `status` (TEXT) - NULL
- `work_date` (DATE) - NULL
- `due_date` (DATE) - NULL
- `owner` (TEXT) - NULL
- `start_date` (DATE) - NULL
- `completed_date` (DATE) - NULL
- `parent_item_type` (TEXT) - NULL
- ... and 14 more fields

### Communication Log (`interactions`)
**Purpose**: Calls, emails, meetings with contacts
**Records**: 0

**Key Fields**:
- `id` (INTEGER) - NULL
- `subject` (TEXT) - NOT NULL
- `description` (TEXT) - NULL
- `type` (TEXT) - NULL
- `interaction_date` (DATETIME) - NULL
- `duration_minutes` (INTEGER) - NULL
- `location` (TEXT) - NULL
- `outcome` (TEXT) - NULL
- `related_to_type` (TEXT) - NULL
- `related_to_id` (INTEGER) - NULL
- ... and 13 more fields

### Project Management (`projects`)
**Purpose**: Organized collections of related work
**Records**: 2

**Key Fields**:
- `id` (INTEGER) - NULL
- `name` (TEXT) - NOT NULL
- `description` (TEXT) - NULL
- `start_date` (TEXT) - NULL
- `end_date` (TEXT) - NULL
- `status` (TEXT) - NULL
- `due_date` (TEXT) - NULL
- `priority` (TEXT) - NULL DEFAULT 'Medium'
- `created_date` (TEXT) - NULL
- `summary` (TEXT) - NULL
- ... and 10 more fields

## 🔗 Data Relationships
Understanding how data connects across the system:

```
ACCOUNTS (companies)
├── CONTACTS (people at companies)
├── OPPORTUNITIES (sales deals)
│   ├── RFQS (quote requests)
│   └── TASKS (follow-up actions)
├── INTERACTIONS (communication history)
└── PROJECTS (organized work)
    ├── PROJECT_CONTACTS (who's involved)
    ├── PROJECT_OPPORTUNITIES (related deals)
    ├── PROJECT_PRODUCTS (what's being sold)
    └── PROJECT_TASKS (project to-dos)
```

## 📦 Product & Inventory System

### PRODUCTS
**Purpose**: Product catalog with NSNs, specifications, and vendor information
**Records**: 977

### QPL
**Purpose**: Qualified Products List - approved vendors for specific products
**Records**: 3

### QUOTES
**Purpose**: Vendor quotes received for RFQ solicitations
**Records**: 0

## 📧 Email & Automation System

### EMAIL_TEMPLATES
**Purpose**: Reusable email templates for automation
**Records**: 2

### EMAIL_RESPONSES
**Purpose**: Captured email responses from vendors
**Records**: 0

### VENDOR_RFQ_EMAILS
**Purpose**: Email communications related to RFQs
**Records**: 3

## ⚙️ Workflow & Automation

### WORKFLOW_AUTOMATION_RULES
**Purpose**: Automated business rules and triggers
**Records**: 5

### WORKFLOW_EXECUTION_LOG
**Purpose**: History of automated actions performed
**Records**: 2

## 🔍 Data Quality & Maintenance

### ⚪ Empty Tables
These tables exist but contain no data:
- `interactions` - Consider if this table is needed
- `project_products` - Consider if this table is needed
- `project_tasks` - Consider if this table is needed
- `project_contacts` - Consider if this table is needed
- `project_opportunities` - Consider if this table is needed
- `quotes` - Consider if this table is needed
- `email_responses` - Consider if this table is needed

### 📊 Low Usage Tables
Tables with minimal data that may need attention:
- `rfqs`: 1 records
- `qpl`: 3 records
- `projects`: 2 records
- `vendor_rfq_emails`: 3 records
- `email_templates`: 2 records
- `workflow_execution_log`: 2 records

### 📦 Backup Tables
✅ **All backup tables have been removed** (August 29, 2025)
- Removed `rfqs_backup_20250821`: contained 5 outdated test records
- Removed `opportunities_backup_20250821`: contained 5 outdated test records  
- Removed `rfqs_backup_simple`: contained 5 duplicate outdated test records
- **Space reclaimed**: 216 KB (30% reduction in database size)

## 🔒 Security & Access Guidelines

### Database Security
- Database file should have restricted file permissions
- Regular backups should be maintained
- Consider encryption for sensitive data

### Sensitive Data Tables
- `contacts` - Contains personal information (PII)
- `email_responses` - May contain business-sensitive communications
- `opportunities` - Contains financial and competitive information
- `vendor_rfq_emails` - Contains vendor communications

## 🛠️ Maintenance Procedures

### Regular Maintenance Tasks
1. **Weekly**:
   - Review data integrity with foreign key checks
   - Monitor database size and performance

2. **Monthly**:
   - Archive old backup tables if no longer needed
   - Review empty or low-usage tables
   - Analyze database growth trends

3. **Quarterly**:
   - Full database backup
   - Schema documentation update
   - Performance optimization review

## 🔌 System Integrations

### DIBBs Integration
- `rfqs` table receives data from DIBBs PDF processing
- Automatic parsing of solicitation documents
- Links RFQs to opportunities and accounts

### Email Automation
- Email templates for automated responses
- Vendor communication tracking
- Quote collection and processing

### Web Interface
- Flask web application provides user interface
- REST API endpoints for data access
- Real-time dashboard with calendar integration

## 📈 Performance Metrics

- **Database Indexes**: 27 indexes for query optimization
- **Current Size**: 496.0 KB (optimized)
- **Records per Table**: 58.9 average
- **Recent Optimization**: Removed 3 backup tables, reclaimed 216 KB (30% reduction)

## 🚨 Troubleshooting Guide

### Common Issues
1. **Orphaned Foreign Keys**:
   - Run integrity check: `PRAGMA foreign_key_check;`
   - Fix with: Update to NULL or create missing parent records

2. **Database Locks**:
   - Check for long-running transactions
   - Restart application if needed

3. **Performance Issues**:
   - Review query execution plans
   - Consider adding indexes for frequently queried columns

## 📞 Support Information

### Database Administrator
- **System**: DLA CRM Database
- **Environment**: Production
- **Last Updated**: 2025-08-29 12:17:47

### Quick Reference Commands
```sql
-- Check database size
SELECT page_count * page_size / 1024.0 / 1024.0 AS size_mb FROM pragma_page_count(), pragma_page_size();

-- List all tables with record counts
SELECT name, (SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=m.name) as count
FROM sqlite_master m WHERE type='table';

-- Check foreign key integrity
PRAGMA foreign_key_check;
```
