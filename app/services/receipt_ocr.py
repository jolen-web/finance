"""
Receipt OCR & Attachment Agent
Handles receipt image upload, OCR extraction, and data parsing
Enhanced with Gemini Vision API for intelligent data extraction
Supports password-protected PDF credit card statements
"""
import os
import re
from datetime import datetime
from pathlib import Path
from PIL import Image
import pytesseract
from werkzeug.utils import secure_filename
from app.models import Receipt, Transaction
from app import db
import json
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import PDF libraries
try:
    import pdfplumber
    import pypdf
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

# Import Gemini
try:
    import google.generativeai as genai
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        GEMINI_AVAILABLE = True
    else:
        GEMINI_AVAILABLE = False
except ImportError:
    GEMINI_AVAILABLE = False

class ReceiptOCRAgent:
    def __init__(self):
        self.upload_folder = Path(__file__).parent.parent.parent / 'data' / 'receipts'
        self.upload_folder.mkdir(parents=True, exist_ok=True)
        self.allowed_extensions = {'png', 'jpg', 'jpeg', 'pdf', 'webp'}
        self.max_file_size = 10 * 1024 * 1024  # 10MB

    def allowed_file(self, filename):
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions

    def save_receipt_file(self, file, transaction_id):
        """Save uploaded receipt file"""
        if not file or not self.allowed_file(file.filename):
            return None, "Invalid file type"

        # Create transaction-specific subdirectory
        trans_dir = self.upload_folder / str(transaction_id)
        trans_dir.mkdir(exist_ok=True)

        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        original_filename = secure_filename(file.filename)
        name, ext = os.path.splitext(original_filename)
        filename = f"{name}_{timestamp}{ext}"

        filepath = trans_dir / filename

        # Save file
        try:
            file.save(str(filepath))
            return str(filepath), filename
        except Exception as e:
            return None, str(e)

    def extract_text_from_image(self, image_path):
        """Extract text from image using OCR with preprocessing"""
        import logging
        logger = logging.getLogger(__name__)

        try:
            # Open image
            image = Image.open(image_path)
            logger.info(f"Image opened: {image.size}, mode: {image.mode}")

            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
                logger.info(f"Converted image to RGB mode")

            # Try different OCR configurations
            # Config 1: Default
            text = pytesseract.image_to_string(image)
            logger.info(f"OCR extracted {len(text)} characters (default config)")

            # If we got very little text, try with preprocessing
            if len(text.strip()) < 50:
                logger.warning(f"Low text extraction ({len(text)} chars), trying with preprocessing...")

                # Convert to grayscale
                from PIL import ImageEnhance, ImageFilter
                gray_image = image.convert('L')

                # Increase contrast
                enhancer = ImageEnhance.Contrast(gray_image)
                enhanced_image = enhancer.enhance(2.0)

                # Try OCR again
                text = pytesseract.image_to_string(enhanced_image)
                logger.info(f"OCR extracted {len(text)} characters (enhanced config)")

            logger.info("="*80)
            logger.info("EXTRACTED OCR TEXT:")
            logger.info(text)
            logger.info("="*80)

            return text, None
        except Exception as e:
            logger.error(f"OCR error: {str(e)}")
            return None, f"OCR error: {str(e)}"

    def extract_text_from_pdf(self, pdf_path, password=None):
        """Extract text from PDF with optional password support"""
        if not PDF_SUPPORT:
            return None, "PDF support not available. Install pdfplumber and pypdf."

        try:
            # First check if PDF is encrypted
            with open(pdf_path, 'rb') as file:
                reader = pypdf.PdfReader(file)

                if reader.is_encrypted:
                    if not password:
                        return None, "PDF_PASSWORD_REQUIRED"

                    # Try to decrypt with password
                    try:
                        if not reader.decrypt(password):
                            return None, "Invalid password"
                    except Exception as e:
                        return None, f"Password error: {str(e)}"

            # Extract text using pdfplumber (better for tables/statements)
            text_content = []
            with pdfplumber.open(pdf_path, password=password) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(page_text)

                    # Also try to extract tables (for credit card statements)
                    tables = page.extract_tables()
                    for table in tables:
                        # Convert table to text
                        for row in table:
                            if row:
                                text_content.append(' | '.join([str(cell) if cell else '' for cell in row]))

            full_text = '\n'.join(text_content)
            return full_text, None

        except Exception as e:
            return None, f"PDF extraction error: {str(e)}"

    def extract_with_gemini_text(self, ocr_text):
        """Use Gemini to parse OCR text into structured transaction data"""
        if not GEMINI_AVAILABLE:
            return None, "Gemini not available"

        import logging
        logger = logging.getLogger(__name__)

        try:
            # Create Gemini prompt for parsing OCR text
            prompt = f"""Parse this OCR-extracted text from a credit card statement or receipt into structured transaction data.

OCR TEXT:
{ocr_text}

ALWAYS return this exact JSON format (no other format):
{{
    "line_items": [
        {{
            "date": "YYYY-MM-DD",
            "description": "merchant or description",
            "amount": -123.45
        }}
    ]
}}

CRITICAL RULES:
1. ALWAYS return "line_items" array - even for single receipt (1-item array)
2. Extract EVERY transaction visible in the text
3. The OCR text may have dates, descriptions, and amounts on separate lines - match them by position
4. Expenses/charges = NEGATIVE amounts (e.g., -50.00)
5. Credits/payments = POSITIVE amounts (e.g., 50.00)
6. Date format: YYYY-MM-DD only (convert MM/DD/YY to YYYY-MM-DD)
7. Amounts: numbers only, no currency symbols
8. If you see multiple dates per transaction, use the first date
9. Return ONLY the JSON format shown above"""

            # Call Gemini API with text-only (no image)
            # Use the base model name for text generation
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = model.generate_content(prompt)

            # Parse response
            response_text = response.text
            logger.info(f"Gemini text parsing response: {response_text[:200]}")

            # Try to extract JSON from response
            import json as json_lib
            try:
                # Find JSON in response (it might be wrapped in markdown code blocks)
                json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    json_str = response_text

                data = json_lib.loads(json_str)

                # Convert date strings to date objects for all line items
                if data.get('line_items'):
                    for item in data['line_items']:
                        if item.get('date'):
                            try:
                                item['date'] = datetime.strptime(item['date'], '%Y-%m-%d').date()
                            except:
                                item['date'] = None

                return data, None
            except json_lib.JSONDecodeError as e:
                logger.error(f"Failed to parse Gemini response: {str(e)}")
                return None, f"Failed to parse Gemini response: {response_text[:100]}"

        except Exception as e:
            logger.error(f"Gemini text parsing error: {str(e)}")
            return None, f"Gemini text parsing error: {str(e)}"

    def extract_with_gemini(self, image_path):
        """Extract receipt data using Gemini Vision API for intelligent analysis"""
        if not GEMINI_AVAILABLE:
            return None, "Gemini API not available"

        try:
            # Read image and convert to base64
            with open(image_path, 'rb') as img_file:
                image_data = base64.standard_b64encode(img_file.read()).decode('utf-8')

            # Determine media type
            ext = os.path.splitext(image_path)[1].lower()
            media_type_map = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.webp': 'image/webp'
            }
            media_type = media_type_map.get(ext, 'image/jpeg')

            # Create Gemini prompt for multi-line transaction extraction
            prompt = """Extract ALL transactions from this image. Always return multiple line items.

ALWAYS return this exact JSON format (no other format):
{
    "line_items": [
        {
            "date": "YYYY-MM-DD",
            "description": "merchant or description",
            "amount": -123.45
        }
    ]
}

CRITICAL RULES:
1. ALWAYS return "line_items" array - even for single receipt (1-item array)
2. Extract EVERY transaction/line visible in the image
3. Expenses/charges = NEGATIVE amounts (e.g., -50.00)
4. Credits/payments = POSITIVE amounts (e.g., 50.00)
5. Date format: YYYY-MM-DD only
6. Amounts: numbers only, no currency symbols
7. If multiple dates per line, use the first date
8. Return ONLY the JSON format shown above"""

            # Call Gemini API
            # Use the base model name for vision tasks
            model = genai.GenerativeModel('gemini-2.0-flash')
            image_content = {
                'mime_type': media_type,
                'data': image_data
            }

            response = model.generate_content([prompt, image_content])

            # Parse response
            response_text = response.text

            # Try to extract JSON from response
            import json as json_lib
            try:
                # Find JSON in response (it might be wrapped in markdown code blocks)
                json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    json_str = response_text

                data = json_lib.loads(json_str)

                # Convert date strings to date objects for all line items
                if data.get('line_items'):
                    for item in data['line_items']:
                        if item.get('date'):
                            try:
                                item['date'] = datetime.strptime(item['date'], '%Y-%m-%d').date()
                            except:
                                item['date'] = None

                return data, None
            except json_lib.JSONDecodeError:
                return None, f"Failed to parse Gemini response: {response_text[:100]}"

        except Exception as e:
            return None, f"Gemini extraction error: {str(e)}"

    def _parse_column_format(self, ocr_text, logger):
        """Parse OCR text when dates, descriptions, and amounts are in separate columns/lines

        This handles cases where OCR extracts:
        Line 1-5: dates
        Line 6-10: descriptions
        Line 11-15: amounts
        """
        lines = [line.strip() for line in ocr_text.split('\n') if line.strip()]

        # Extract dates, descriptions, and amounts separately
        dates = []
        descriptions = []
        amounts = []

        date_pattern = r'^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$'
        amount_pattern = r'^[\d,]+\.\d{2}$'

        for line in lines:
            # Check if it's a date
            if re.match(date_pattern, line):
                dates.append(line)
            # Check if it's an amount
            elif re.match(amount_pattern, line):
                amounts.append(line)
            # Otherwise it's probably a description (if long enough)
            elif len(line) > 5 and not any(skip in line.upper() for skip in ['TOTAL', 'BALANCE', 'TRANSACTION', 'DATE', 'DESCRIPTION', 'AMOUNT']):
                descriptions.append(line)

        logger.info(f"Column parsing: Found {len(dates)} dates, {len(descriptions)} descriptions, {len(amounts)} amounts")

        # We need at least some data to proceed
        if not amounts or not descriptions:
            return []

        # Match them up - use the minimum count to avoid index errors
        transaction_count = min(len(descriptions), len(amounts))
        transactions = []

        # Date formats to try
        date_formats = [
            '%m/%d/%y', '%m/%d/%Y', '%d/%m/%y', '%d/%m/%Y',
            '%m-%d-%y', '%m-%d-%Y', '%d-%m-%Y'
        ]

        for i in range(transaction_count):
            # Get date (use first date if we have fewer dates than transactions)
            date_str = dates[i] if i < len(dates) else (dates[0] if dates else None)

            # Parse date
            parsed_date = None
            if date_str:
                for fmt in date_formats:
                    try:
                        parsed_date = datetime.strptime(date_str, fmt).date()
                        break
                    except:
                        continue

            # Parse amount
            amount_str = amounts[i].replace(',', '')
            amount = -float(amount_str)  # Negative for expenses

            # Get description
            description = descriptions[i].strip()

            if description and (parsed_date or date_str):
                transactions.append({
                    'date': parsed_date,
                    'description': description,
                    'amount': amount
                })
                logger.info(f"  Column match {i+1}: {parsed_date} | {description} | {amount}")

        return transactions

    def parse_statement_data(self, ocr_text):
        """Parse tabular statement data (credit card/bank statements) to extract multiple transactions

        Enhanced to handle various credit card statement formats including:
        - Standard date | description | amount format
        - Table formats with pipes or multiple spaces
        - Multiple date formats
        - Transaction totals and balances
        """
        import logging
        logger = logging.getLogger(__name__)

        logger.info("="*80)
        logger.info("RAW OCR TEXT:")
        logger.info(ocr_text)
        logger.info("="*80)

        transactions = []
        lines = ocr_text.split('\n')
        logger.info(f"Processing {len(lines)} lines from OCR text")

        # Track statement total/balance if found
        statement_total = None
        statement_info = {'total': None, 'previous_balance': None, 'new_balance': None}

        # Common patterns for credit card statements
        patterns = [
            # Pattern 1: Two dates followed by description and amount (e.g., "09/21/25  09/22/25  MERCHANT NAME  859.52")
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s+\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\s+(.+?)\s+([\d,]+\.\d{2})\s*$',
            # Pattern 2: Two dates with description and amount - more flexible spacing
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s+\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\s+(.+?)\s{2,}([\d,]+\.\d{2})',
            # Pattern 3: MM/DD/YY Description Amount (standard format)
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s+(.+?)\s+([\d,]+\.\d{2})$',
            # Pattern 4: MM/DD Description | Amount
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s+(.+?)\s*\|\s*([\d,]+\.\d{2})',
            # Pattern 5: Date in YYYY-MM-DD format
            r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})\s+(.+?)\s+([\d,]+\.\d{2})$',
            # Pattern 6: Table format with multiple separators
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s*\|\s*(.+?)\s*\|\s*([\d,]+\.\d{2})',
            # Pattern 7: Very flexible - any date, text, and amount at end
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s+(.+?)\s{2,}([\d,]+\.\d{2})\s*$',
            # Pattern 8: Month name format (e.g., "October 25, 2025 MERCHANT NAME 1415.50")
            r'([A-Za-z]+\s+\d{1,2},?\s+\d{4})\s+(.+?)\s+([\d,]+\.\d{2})\s*$',
            # Pattern 9: Month name with more flexible spacing
            r'([A-Za-z]+\s+\d{1,2},?\s+\d{4})\s+(.+?)\s{2,}([\d,]+\.\d{2})',
        ]

        line_num = 0
        for line in lines:
            line_num += 1
            line_upper = line.upper()

            # Log each line for debugging
            if line.strip():
                logger.debug(f"Line {line_num}: {line.strip()}")

            # Extract statement totals/balances
            if 'TOTAL' in line_upper or 'BALANCE' in line_upper:
                amount_match = re.search(r'([\d,]+\.\d{2})', line)
                if amount_match:
                    amount = float(amount_match.group(1).replace(',', ''))
                    if 'PREVIOUS' in line_upper:
                        statement_info['previous_balance'] = amount
                    elif 'NEW' in line_upper or 'CURRENT' in line_upper:
                        statement_info['new_balance'] = amount
                    elif 'TOTAL' in line_upper and 'PAYMENT' not in line_upper:
                        statement_info['total'] = amount
                continue

            # Skip empty lines and header lines
            if not line.strip() or len(line.strip()) < 10:
                continue

            # Skip common header patterns
            if any(header in line_upper for header in ['TRANSACTION', 'DATE', 'DESCRIPTION', 'AMOUNT', 'REFERENCE', 'POST']):
                continue

            # Try each pattern
            matched = False
            for idx, pattern in enumerate(patterns):
                match = re.search(pattern, line.strip())
                if match:
                    logger.info(f"✓ Line {line_num} matched pattern {idx+1}: {line.strip()}")
                    matched = True
                    date_str, description, amount_str = match.groups()

                    # Parse date
                    parsed_date = None
                    date_formats = [
                        '%m/%d/%y', '%m/%d/%Y', '%d/%m/%y', '%d/%m/%Y',
                        '%m-%d-%y', '%m-%d-%Y', '%d-%m-%Y', '%Y-%m-%d',
                        '%Y/%m/%d', '%d-%b-%Y', '%d-%b-%y', '%B %d, %Y', '%b %d, %Y'
                    ]

                    for fmt in date_formats:
                        try:
                            parsed_date = datetime.strptime(date_str, fmt).date()
                            break
                        except:
                            continue

                    # Parse amount (handle negative amounts and credits)
                    try:
                        amount_clean = amount_str.replace(',', '').strip()
                        amount = float(amount_clean)

                        # Check for credit/payment indicators (these should be positive)
                        is_credit = 'CR' in line_upper or 'CREDIT' in line_upper or 'PAYMENT' in description.upper()

                        # For credit card statements:
                        # - Regular charges/purchases should be NEGATIVE (money owed)
                        # - Credits/Payments should be POSITIVE (money paid back)
                        if is_credit:
                            # Payment/Credit - ensure it's positive
                            if amount < 0:
                                amount = abs(amount)
                        else:
                            # Charge/Purchase - ensure it's negative
                            if amount > 0:
                                amount = -amount

                    except:
                        continue

                    # Clean description
                    description_clean = description.strip()
                    # Remove common prefixes
                    description_clean = re.sub(r'^(PURCHASE|PAYMENT|DEBIT|CREDIT)\s+', '', description_clean, flags=re.IGNORECASE)
                    # Remove post date patterns - comprehensive cleanup for all variations:
                    # Matches: "POST 12/15", "POST12/15", "POST 12-15", "POST 12/15/23", "POST 12 15", "12/15 POST", etc.
                    # Pattern 1: POST followed by optional spaces, then date
                    description_clean = re.sub(r'\bPOST\s*\d{1,2}\s*[/-]\s*\d{1,2}(?:\s*[/-]\s*\d{2,4})?', '', description_clean, flags=re.IGNORECASE)
                    # Pattern 2: Date followed by POST
                    description_clean = re.sub(r'\d{1,2}\s*[/-]\s*\d{1,2}(?:\s*[/-]\s*\d{2,4})?\s+POST', '', description_clean, flags=re.IGNORECASE)
                    # Pattern 3: Trailing dates (MM/DD/YY or MM/DD/YYYY format)
                    description_clean = re.sub(r'\s+\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?\s*$', '', description_clean)
                    # Pattern 4: POST alone at end or beginning
                    description_clean = re.sub(r'\bPOST\b', '', description_clean, flags=re.IGNORECASE)
                    # Clean up multiple spaces
                    description_clean = re.sub(r'\s+', ' ', description_clean)
                    description_clean = description_clean.strip()

                    if parsed_date and description_clean:
                        transactions.append({
                            'date': parsed_date,
                            'description': description_clean,
                            'amount': amount
                        })
                        logger.info(f"  → Added transaction: {parsed_date} | {description_clean} | {amount}")
                        break  # Found match, don't try other patterns
                    else:
                        logger.warning(f"  ✗ Skipped - no date or description: date={parsed_date}, desc={description_clean}")

            # Log if no pattern matched this line
            if not matched and line.strip() and len(line.strip()) >= 10:
                logger.debug(f"✗ Line {line_num} no pattern match: {line.strip()}")

        # If regex-based parsing found nothing, try column-based parsing
        if len(transactions) == 0:
            logger.warning("Regex patterns found no transactions, trying column-based parsing...")
            column_transactions = self._parse_column_format(ocr_text, logger)
            if column_transactions:
                transactions = column_transactions
                logger.info(f"✓ Column-based parsing extracted {len(transactions)} transactions")

        # If still no transactions, try single receipt extraction (date, merchant, amount on separate lines)
        if len(transactions) == 0:
            logger.warning("No transactions found, trying single receipt extraction...")

            # Look for a date somewhere in the text
            receipt_date = None
            date_patterns = [
                (r'([A-Za-z]+\s+\d{1,2},\s+\d{4})', '%B %d, %Y'),  # October 25, 2025
                (r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', '%m/%d/%Y'),  # MM/DD/YYYY
                (r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})', '%Y-%m-%d'),    # YYYY-MM-DD
            ]

            for pattern, fmt in date_patterns:
                match = re.search(pattern, ocr_text)
                if match:
                    date_str = match.group(1)
                    try:
                        receipt_date = datetime.strptime(date_str, fmt).date()
                        logger.info(f"✓ Found receipt date: {receipt_date}")
                        break
                    except:
                        continue

            # Look for a total amount
            total_amount = None
            amount_match = re.search(r'(?:TOTAL|AMOUNT|Grand\s*Total|Total\s*Due)[\s:$]*(\d+(?:[.,]\d{3})*[.,]\d{2})', ocr_text, re.IGNORECASE)
            if amount_match:
                total_amount = -float(amount_match.group(1).replace(',', ''))
                logger.info(f"✓ Found total amount: {total_amount}")

            # Look for merchant name (usually near top or has specific keywords)
            merchant_name = None
            # Try to find merchant by looking for company-like names at the top
            for line in lines[:15]:  # Check first 15 lines
                line_stripped = line.strip()
                # Skip lines that are too short, dates, amounts, or headers
                if (len(line_stripped) > 10 and
                    not re.search(r'^\d+', line_stripped) and
                    not re.search(r'[A-Z]{2,3}\s*:', line_stripped) and
                    'INVOICE' not in line_stripped.upper() and
                    'RECEIPT' not in line_stripped.upper() and
                    'TRANS' not in line_stripped.upper() and
                    'TOTAL' not in line_stripped.upper()):
                    merchant_name = line_stripped
                    logger.info(f"✓ Found merchant: {merchant_name}")
                    break

            # If we found all three pieces of info, create a transaction
            if receipt_date and total_amount and merchant_name:
                transactions.append({
                    'date': receipt_date,
                    'description': merchant_name,
                    'amount': total_amount  # Keep as negative for charges (consistent with statement parsing)
                })
                logger.info(f"✓ Single receipt extraction: {receipt_date} | {merchant_name} | {total_amount}")

        # Calculate total from line items if not found in statement
        if not statement_info.get('total') and transactions:
            statement_info['total'] = sum(abs(t['amount']) for t in transactions)

        # Add statement info to first transaction if found
        if transactions and any(statement_info.values()):
            transactions[0]['_statement_info'] = statement_info

        logger.info(f"="*80)
        logger.info(f"TOTAL TRANSACTIONS EXTRACTED: {len(transactions)}")
        logger.info(f"="*80)

        return {'line_items': transactions}

    def parse_receipt_data(self, ocr_text):
        """Parse OCR text to extract merchant, date, amount, and items"""
        data = {
            'merchant': None,
            'date': None,
            'amount': None,
            'items': [],
            'line_items': []  # For multi-transaction statements
        }

        lines = ocr_text.split('\n')

        # First, check if this looks like a statement with multiple transactions
        statement_data = self.parse_statement_data(ocr_text)
        statement_transactions = statement_data.get('line_items', [])
        if len(statement_transactions) > 2:  # If we found multiple transactions, treat as statement
            data['line_items'] = statement_transactions
            return data

        # Extract merchant (usually first or second line)
        for i, line in enumerate(lines[:5]):
            if len(line.strip()) > 3 and not re.search(r'\d', line):
                data['merchant'] = line.strip()
                break

        # Extract date patterns
        date_patterns = [
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',  # MM-DD-YYYY or DD-MM-YYYY
            r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',     # YYYY-MM-DD
            r'([A-Za-z]+\s+\d{1,2},?\s+\d{4})'     # Month DD, YYYY
        ]

        for pattern in date_patterns:
            match = re.search(pattern, ocr_text)
            if match:
                try:
                    date_str = match.group(1)
                    # Try to parse date
                    for fmt in ['%m-%d-%Y', '%d-%m-%Y', '%Y-%m-%d', '%m/%d/%Y', '%B %d, %Y', '%b %d, %Y']:
                        try:
                            data['date'] = datetime.strptime(date_str, fmt).date()
                            break
                        except:
                            continue
                    if data['date']:
                        break
                except:
                    continue

        # Extract amounts (look for total)
        amount_patterns = [
            r'(?:total|amount|balance|grand\s*total)[\s:$]*(\d+[.,]\d{2})',
            r'[\$]?\s*(\d+[.,]\d{2})\s*(?:total|balance)',
            r'(\d+[.,]\d{2})[\s]*(?:\n|$)'  # Last amount on line
        ]

        amounts_found = []
        for pattern in amount_patterns:
            matches = re.finditer(pattern, ocr_text, re.IGNORECASE)
            for match in matches:
                amount_str = match.group(1).replace(',', '.')
                try:
                    amount = float(amount_str)
                    amounts_found.append(amount)
                except:
                    continue

        # Use the largest amount found (likely the total)
        if amounts_found:
            data['amount'] = max(amounts_found)

        # Extract line items (items with quantities and prices)
        item_pattern = r'([A-Za-z\s]+)\s+(\d+)\s*(?:x|@)\s*\$?(\d+[.,]\d{2})'
        items = re.finditer(item_pattern, ocr_text)

        for item in items:
            item_name = item.group(1).strip()
            quantity = item.group(2)
            price = item.group(3).replace(',', '.')

            data['items'].append({
                'name': item_name,
                'quantity': int(quantity),
                'price': float(price)
            })

        return data

    def extract_receipt_data(self, file, temp_folder='temp', password=None):
        """Extract data from receipt without creating database records

        Args:
            file: Uploaded file object
            temp_folder: Folder name for temporary storage
            password: Optional password for encrypted PDFs

        Returns:
            tuple: (filepath, filename, parsed_data, file_type) or (None, None, error_message, None)
        """
        # Save file to temporary location
        filepath, filename_or_error = self.save_receipt_file(file, temp_folder)
        if not filepath:
            return None, None, filename_or_error, None

        file_type = file.content_type or 'image/jpeg'

        # Check if file is PDF
        is_pdf = filepath.lower().endswith('.pdf')

        # NEW APPROACH: Extract text with OCR first, then use Gemini to structure it
        parsed_data = None
        ocr_text = None
        import logging
        logger = logging.getLogger(__name__)

        # Step 1: Extract text using OCR or PDF parser
        if is_pdf:
            # Extract text from PDF
            ocr_text, error = self.extract_text_from_pdf(filepath, password)
            if error:
                # Check if password is required
                if error == "PDF_PASSWORD_REQUIRED":
                    return None, None, "PDF_PASSWORD_REQUIRED", None
                return None, None, error, None
        else:
            # Perform OCR on image
            ocr_text, error = self.extract_text_from_image(filepath)
            if error:
                return None, None, error, None

        # Step 2: Try to parse with Gemini (intelligent structuring)
        if ocr_text and GEMINI_AVAILABLE:
            logger.info("Step 2: Sending OCR text to Gemini for intelligent parsing...")
            gemini_data, gemini_error = self.extract_with_gemini_text(ocr_text)

            if gemini_data and gemini_error is None:
                # Check if Gemini returned any line items
                if gemini_data.get('line_items') and len(gemini_data['line_items']) > 0:
                    parsed_data = gemini_data
                    parsed_data['_extraction_method'] = 'gemini'
                    logger.info(f"✓ Gemini parsed {len(gemini_data['line_items'])} transactions from OCR text")
                else:
                    logger.warning("✗ Gemini returned empty line_items, falling back to regex parsing")
            else:
                logger.warning(f"✗ Gemini parsing failed: {gemini_error}, falling back to regex parsing")

        # Step 3: Fall back to regex-based parsing if Gemini failed
        if not parsed_data:
            logger.info("Step 3: Using regex-based parsing as fallback...")
            parsed_data = self.parse_statement_data(ocr_text)

            # Mark extraction method if not already set
            if parsed_data and '_extraction_method' not in parsed_data:
                parsed_data['_extraction_method'] = 'ocr'

        return filepath, filename_or_error, parsed_data, file_type

    def create_receipt_record(self, user_id, filepath, filename, transaction_id, parsed_data, file_type):
        """Create Receipt database record after transaction is confirmed

        Args:
            user_id: The ID of the user
            filepath: Path to saved receipt file
            filename: Original filename
            transaction_id: Transaction ID to link to
            parsed_data: Extracted data dictionary
            file_type: MIME type of file

        Returns:
            Receipt object
        """
        receipt = Receipt(
            user_id=user_id,
            transaction_id=transaction_id,
            filename=filename,
            filepath=filepath,
            file_type=file_type,
            extracted_merchant=parsed_data.get('merchant'),
            extracted_date=parsed_data.get('date'),
            extracted_amount=parsed_data.get('amount'),
            extracted_items=json.dumps(parsed_data.get('items', [])) if parsed_data.get('items') else None
        )

        db.session.add(receipt)
        db.session.commit()

        return receipt

    def process_receipt(self, user_id, file, transaction_id, password=None):
        """Process uploaded receipt: save, OCR, and parse

        Args:
            user_id: The ID of the user uploading the receipt.
            file: Uploaded file object
            transaction_id: Transaction ID to associate receipt with
            password: Optional password for encrypted PDFs

        Returns:
            tuple: (receipt, parsed_data) or (None, error_message)
        """
        # Save file
        filepath, filename_or_error = self.save_receipt_file(file, transaction_id)
        if not filepath:
            return None, filename_or_error

        # Check if file is PDF
        is_pdf = filepath.lower().endswith('.pdf')

        # Try to extract using Gemini first (more intelligent) - for images only
        parsed_data = None
        gemini_used = False
        ocr_text = None

        if not is_pdf and GEMINI_AVAILABLE:
            parsed_data, error = self.extract_with_gemini(filepath)
            if parsed_data and error is None:
                gemini_used = True

        # Fall back to traditional OCR/PDF extraction if Gemini not available or failed
        if not parsed_data:
            if is_pdf:
                # Extract text from PDF
                ocr_text, error = self.extract_text_from_pdf(filepath, password)
                if error:
                    # Check if password is required
                    if error == "PDF_PASSWORD_REQUIRED":
                        return None, "PDF_PASSWORD_REQUIRED"
                    return None, error
            else:
                # Perform OCR on image
                ocr_text, error = self.extract_text_from_image(filepath)
                if error:
                    return None, error

            # Parse receipt data using regex patterns
            parsed_data = self.parse_receipt_data(ocr_text)

        # Determine the extracted amount
        extracted_amount = parsed_data.get('amount')
        if extracted_amount is None and parsed_data.get('line_items'):
            # If no top-level amount, sum from line items
            extracted_amount = sum(abs(item.get('amount', 0)) for item in parsed_data['line_items'])

        current_app.logger.debug(f"Calculated extracted_amount: {extracted_amount}")

        # Create receipt record
        receipt = Receipt(
            user_id=user_id,
            transaction_id=transaction_id,
            filename=filename_or_error,
            filepath=filepath,
            file_type=file.content_type or 'image/jpeg',
            extracted_merchant=parsed_data.get('merchant'),
            extracted_date=parsed_data.get('date'),
            extracted_amount=extracted_amount,
            extracted_items=json.dumps(parsed_data.get('items', [])) if parsed_data.get('items') else None
        )

        db.session.add(receipt)
        db.session.commit()

        # Add note about extraction method
        if gemini_used:
            parsed_data['_extraction_method'] = 'gemini'
            parsed_data['tax_deductible'] = parsed_data.get('tax_deductible')
            parsed_data['category'] = parsed_data.get('category')
            parsed_data['warranty_info'] = parsed_data.get('warranty_info')

        return receipt, parsed_data

    def auto_match_receipt(self, receipt_data, tolerance_days=3, tolerance_amount=5.0):
        """Try to automatically match receipt to existing transaction"""
        if not receipt_data.get('date') or not receipt_data.get('amount'):
            return None

        # Search for transactions within date and amount tolerance
        from datetime import timedelta

        date_min = receipt_data['date'] - timedelta(days=tolerance_days)
        date_max = receipt_data['date'] + timedelta(days=tolerance_days)
        amount = receipt_data['amount']

        candidates = Transaction.query.filter(
            Transaction.date >= date_min,
            Transaction.date <= date_max,
            Transaction.amount >= amount - tolerance_amount,
            Transaction.amount <= amount + tolerance_amount
        ).all()

        # If merchant name is available, filter by payee match
        if receipt_data.get('merchant') and candidates:
            merchant_lower = receipt_data['merchant'].lower()
            filtered = [t for t in candidates if merchant_lower in t.payee.lower() or t.payee.lower() in merchant_lower]
            if filtered:
                return filtered[0]

        # Return best match (closest amount)
        if candidates:
            return min(candidates, key=lambda t: abs(t.amount - amount))

        return None

    def create_transaction_from_receipt(self, receipt_data, account_id):
        """Create new transaction from receipt data"""
        transaction = Transaction(
            date=receipt_data.get('date') or datetime.now().date(),
            amount=receipt_data.get('amount') or 0.0,
            payee=receipt_data.get('merchant') or 'Unknown Merchant',
            memo=f"Auto-created from receipt. Items: {len(receipt_data.get('items', []))}",
            transaction_type='withdrawal',
            account_id=account_id
        )

        db.session.add(transaction)
        db.session.commit()

        return transaction

    def get_receipt(self, receipt_id):
        """Get receipt by ID"""
        return Receipt.query.get(receipt_id)

    def get_transaction_receipts(self, transaction_id):
        """Get all receipts for a transaction"""
        return Receipt.query.filter_by(transaction_id=transaction_id).all()

    def delete_receipt(self, receipt_id):
        """Delete receipt and associated file"""
        receipt = Receipt.query.get(receipt_id)
        if not receipt:
            return False, "Receipt not found"

        # Delete file
        try:
            if os.path.exists(receipt.filepath):
                os.remove(receipt.filepath)
        except Exception as e:
            pass  # File might already be deleted

        # Delete database record
        db.session.delete(receipt)
        db.session.commit()

        return True, "Receipt deleted successfully"

    def get_receipt_stats(self, user_id):
        """Get receipt statistics for a specific user"""
        total_receipts = Receipt.query.filter_by(user_id=user_id).count()
        receipts_with_amount = Receipt.query.filter_by(user_id=user_id).filter(Receipt.extracted_amount.isnot(None)).count()
        receipts_with_date = Receipt.query.filter_by(user_id=user_id).filter(Receipt.extracted_date.isnot(None)).count()
        receipts_with_merchant = Receipt.query.filter_by(user_id=user_id).filter(Receipt.extracted_merchant.isnot(None)).count()

        return {
            'total': total_receipts,
            'with_amount': receipts_with_amount,
            'with_date': receipts_with_date,
            'with_merchant': receipts_with_merchant,
            'extraction_rate': (receipts_with_amount / total_receipts * 100) if total_receipts > 0 else 0
        }
