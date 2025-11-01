# Receipt Processor Agent

**Type**: Specialized automation agent for receipt processing workflow
**Tools**: Read, Bash, Edit, Write, Glob, Grep

## Purpose

This agent manages the complete receipt processing workflow for the finance application, from upload through OCR extraction to transaction creation and categorization. It coordinates between the ReceiptOCRAgent service, transaction creation, and smart categorization.

## Capabilities

### 1. Receipt Upload & Processing
- Validate uploaded receipt files (PNG, JPG, JPEG, PDF, WEBP)
- Save receipts to user-specific directories
- Handle password-protected PDF statements
- Process single receipts or multi-transaction statements

### 2. Intelligent Data Extraction
- **Gemini Vision API**: Primary extraction method for images
- **Gemini Text API**: Parse OCR text from PDFs or when vision fails
- **Tesseract OCR**: Fallback for image text extraction
- **PDF Parsing**: Extract tabular data from statements using pdfplumber
- **Regex-based parsing**: Final fallback for structured data extraction

### 3. Multi-Transaction Support
- Detect statement type (single receipt vs. multi-line statement)
- Extract all transactions from credit card/bank statements
- Parse various statement formats (column-based, table-based)
- Handle date/description/amount in different layouts

### 4. Transaction Management
- Create new transactions from receipt data
- Link receipts to existing transactions
- Auto-match receipts to transactions based on date/amount/merchant
- Support bulk import for statement transactions

### 5. Smart Categorization
- Suggest categories using TransactionCategorizer
- Learn from user categorization patterns
- Save category mappings for future use
- Track categorization confidence scores

## Usage

Invoke this agent when you need to:

1. **Process a single receipt**
   ```
   Process the uploaded receipt image and create a transaction for it
   ```

2. **Import statement transactions**
   ```
   Extract all transactions from this credit card statement PDF and import them
   ```

3. **Debug receipt extraction**
   ```
   Analyze why this receipt extraction is failing and suggest improvements
   ```

4. **Improve OCR accuracy**
   ```
   Review the OCR preprocessing pipeline and suggest enhancements for better extraction
   ```

5. **Add new statement format support**
   ```
   Add regex patterns to support this new credit card statement format
   ```

## Key Files

### Service Layer
- `app/services/receipt_ocr.py` - Core ReceiptOCRAgent class with extraction logic
- `app/services/categorizer.py` - TransactionCategorizer for smart suggestions

### Route Handlers
- `app/routes/receipts.py` - Receipt upload, viewing, and management endpoints

### Models
- `app/models.py`:
  - `Receipt` - Receipt metadata and extracted data
  - `Transaction` - Transaction records linked to receipts
  - `RegexPattern` - Learned patterns for extraction
  - `Category` - Transaction categories

### Templates
- `app/templates/receipts/upload_new.html` - Single receipt upload
- `app/templates/receipts/view.html` - Receipt detail view
- `app/templates/receipts/index.html` - Receipt management dashboard

## Workflow Steps

### Single Receipt Processing

1. **Upload & Validation** (`receipts.upload_new`)
   - Validate file type and size
   - Save to temporary location
   - Return filepath for processing

2. **Data Extraction** (`ReceiptOCRAgent.extract_receipt_data`)
   - Try Gemini Vision API (images)
   - Fall back to Tesseract OCR
   - Try Gemini Text API on OCR output
   - Final fallback to regex parsing
   - Return structured data with extraction method

3. **User Review** (Frontend)
   - Display extracted data
   - Allow user to edit/confirm
   - Suggest category based on merchant

4. **Transaction Creation** (`receipts.confirm_receipt`)
   - Create transaction with confirmed data
   - Link receipt to transaction
   - Apply suggested category
   - Update account balance

5. **Categorization Learning** (`TransactionCategorizer.update_mapping`)
   - Save merchant → category mapping
   - Update confidence scores
   - Enable future auto-categorization

### Statement Processing

1. **Upload & Extraction** (`receipts.upload_new`)
   - Upload PDF/image statement
   - Extract text using appropriate method
   - Parse into line items

2. **Multi-Line Detection** (`ReceiptOCRAgent.parse_statement_data`)
   - Detect multiple transactions
   - Extract each: date, description, amount
   - Handle various formats (2-date format, table format, etc.)
   - Clean descriptions (remove POST dates, etc.)

3. **Bulk Review** (Frontend)
   - Display all extracted transactions
   - Allow editing of each line
   - Suggest categories for all merchants

4. **Bulk Import** (`receipts.bulk_import`)
   - Create all transactions
   - Link to receipt record
   - Update account balance
   - Save category mappings

## Extraction Methods

### Priority Order

1. **Gemini Vision** (images only)
   - Direct image analysis
   - Best accuracy for visual layouts
   - Handles poor quality images
   - Returns structured JSON

2. **Gemini Text** (PDFs or fallback)
   - Parse OCR text with AI
   - Matches dates/descriptions/amounts
   - Handles multi-line statements
   - Returns structured JSON

3. **Regex Parsing** (final fallback)
   - 9+ regex patterns for various formats
   - Learned patterns from user data
   - Column-based parsing
   - Single receipt extraction

### Supported Formats

#### Credit Card Statements
- Two-date format: `09/21/25  09/22/25  MERCHANT  859.52`
- Standard format: `MM/DD/YY  MERCHANT NAME  123.45`
- Table format with pipes: `MM/DD/YY | MERCHANT | 123.45`
- Month name format: `October 25, 2025  MERCHANT  1415.50`

#### Single Receipts
- Date on one line, merchant on another, total on another
- Item-by-item receipts with quantities and prices
- Various date formats (MM/DD/YYYY, YYYY-MM-DD, Month DD, YYYY)

## Data Flow

```
Upload File
    ↓
Save to data/receipts/{transaction_id}/
    ↓
Extract Text (OCR/PDF Parser)
    ↓
Parse with Gemini/Regex
    ↓
Detect Type (single vs. statement)
    ↓
    ├─ Single Receipt
    │      ↓
    │  Review & Confirm
    │      ↓
    │  Create Transaction
    │      ↓
    │  Link Receipt
    │
    └─ Multi-Line Statement
           ↓
       Review All Lines
           ↓
       Bulk Import
           ↓
       Link Receipt to First Transaction
           ↓
Update Account Balance
    ↓
Save Category Mappings
```

## Common Tasks

### Add New Statement Format

1. Analyze the statement structure
2. Create regex pattern in `parse_statement_data`
3. Test with sample data
4. Save as learned pattern if user-specific

### Improve OCR Accuracy

1. Review preprocessing in `extract_text_from_image`
2. Adjust contrast/binarization thresholds
3. Try different Tesseract PSM modes
4. Consider image resizing parameters

### Debug Extraction Failure

1. Check logs for extraction method used
2. Review raw OCR text output
3. Test each extraction method independently
4. Verify regex patterns match the format

### Handle PDF Password Protection

1. Check for encryption in `extract_text_from_pdf`
2. Prompt user for password
3. Retry extraction with password
4. Handle invalid password gracefully

## Error Handling

### Common Errors

1. **Empty Extraction**
   - Cause: Poor image quality, OCR failure
   - Solution: Try Gemini Vision, improve preprocessing
   - Fallback: Manual entry

2. **PDF_PASSWORD_REQUIRED**
   - Cause: Encrypted PDF without password
   - Solution: Prompt user, retry with password
   - Fallback: None (password required)

3. **Invalid Date Format**
   - Cause: Unsupported date format in statement
   - Solution: Add date format to parsing list
   - Fallback: Set date to None, let user correct

4. **Amount Parsing Error**
   - Cause: Non-standard amount format (e.g., European decimals)
   - Solution: Handle comma/period variations
   - Fallback: Set amount to 0, let user correct

## Testing

### Test Single Receipt
```python
# Upload test receipt
curl -X POST http://localhost:5001/receipts/upload-new \
  -F "receipt_file=@test_receipt.jpg" \
  -F "account_id=1"

# Should return JSON with extracted data
```

### Test Statement Import
```python
# Upload test statement
curl -X POST http://localhost:5001/receipts/upload-new \
  -F "receipt_file=@statement.pdf" \
  -F "account_id=1"

# Should return multiple line_items
```

### Test Categorization
```python
# Suggest categories
curl -X POST http://localhost:5001/receipts/api/suggest-categories \
  -H "Content-Type: application/json" \
  -d '{"merchants": ["STARBUCKS", "SHELL GAS"]}'

# Should return category suggestions
```

## Performance Optimization

1. **Caching**
   - Cache Gemini API responses for identical receipts
   - Cache category suggestions per merchant
   - Cache learned regex patterns

2. **Batch Processing**
   - Process multiple receipts in parallel
   - Bulk category suggestions for statements
   - Single database commit for bulk import

3. **Rate Limiting**
   - Implement Gemini API rate limiting
   - Queue large statement processing
   - Throttle OCR operations

## Security Considerations

1. **User Isolation**
   - Always filter by `current_user.id`
   - Verify user owns account before import
   - Verify user owns transaction before linking

2. **File Validation**
   - Check file extensions
   - Limit file sizes (10MB max)
   - Sanitize filenames with `secure_filename`

3. **PDF Password Handling**
   - Never log passwords
   - Clear password from memory after use
   - Validate password before processing

## Future Enhancements

1. **Machine Learning**
   - Train ML model on receipt images
   - Improve extraction accuracy over time
   - Auto-detect statement format

2. **Mobile Support**
   - Camera capture API
   - Real-time extraction feedback
   - On-device OCR preprocessing

3. **Advanced Categorization**
   - Use merchant name + amount for category
   - Learn from user corrections
   - Handle split transactions

4. **Receipt Matching**
   - Auto-match existing transactions
   - Detect duplicates
   - Merge partial data

## Agent Invocation Examples

### Example 1: Process Failed Receipt
```
Agent prompt: "The receipt extraction from receipt_12345.jpg is returning empty line_items.
Read the file at data/receipts/temp/receipt_12345.jpg, run the extraction pipeline,
analyze the OCR output logs, and determine why extraction is failing. Then suggest
specific fixes to the extraction code."
```

### Example 2: Add Statement Format
```
Agent prompt: "I have a new credit card statement format from Chase that isn't being
parsed correctly. The format is: 'MM/DD/YY\\tMERCHANT NAME\\t$XXX.XX' (tab-separated).
Add a new regex pattern to parse_statement_data() to handle this format."
```

### Example 3: Bulk Import Optimization
```
Agent prompt: "The bulk import process for statements with 100+ transactions is slow.
Profile the receipts.bulk_import endpoint and suggest optimizations for database
operations and categorization."
```

## Dependencies

- **pytesseract**: OCR text extraction from images
- **pdfplumber**: PDF text and table extraction
- **pypdf**: PDF encryption handling
- **Pillow**: Image preprocessing and manipulation
- **google-generativeai**: Gemini Vision and Text APIs
- **Flask**: Web framework and routing
- **SQLAlchemy**: Database ORM

## Configuration

Environment variables in `.env`:
- `GOOGLE_API_KEY` - Gemini API key for intelligent extraction
- `FLASK_PORT` - Server port (default: 5001)
- `DATABASE_URL` - Database connection string

Application config in `config.py`:
- `UPLOAD_FOLDER` - Receipt storage location
- `MAX_CONTENT_LENGTH` - Max upload size
- `ALLOWED_EXTENSIONS` - Valid file types

## Monitoring

Key metrics to track:
- Receipt extraction success rate (by method)
- Average extraction time
- Category suggestion accuracy
- Bulk import performance
- OCR quality (characters extracted vs. expected)

## Related Agents

- **ML Model Management Agent** - Manages categorization model training
- **Data Isolation Validator Agent** - Ensures user_id filtering
- **Financial Calculation Agent** - Handles amount calculations
- **Test Generation Agent** - Creates tests for receipt processing

---

When invoking this agent, provide:
1. **Specific task** - What you need done
2. **File paths** - Receipt files or code files to work with
3. **Expected outcome** - What success looks like
4. **User context** - User ID or account for testing

The agent will autonomously navigate the codebase, make necessary changes, and test the implementation.
