import re
import string # Import string module for sanitization

def parse_amazon_invoice(text):
    """
    Parses the extracted raw text from an Amazon invoice PDF.
    It looks for specific keywords and patterns to extract details
    like Invoice Number, Order ID, Invoice Date, Total Amount, and itemized lists.

    Args:
        text (str): The full raw text extracted from an Amazon PDF invoice.

    Returns:
        dict: A dictionary containing the extracted invoice data.
              Returns an empty dictionary if no key data (like Invoice Number) is found.
              Example:
              {
                  "Invoice Number": "AMZ-INV-12345",
                  "Order ID": "ORD-AMZ-XYZ",
                  "Invoice Date": "01/01/2023",
                  "Total Amount": "1500.75",
                  "Items": [
                      {"Description": "...", "Quantity": ..., "Unit Price": ..., "Total Item Price": ...},
                      ...
                  ]
              }
    """
    data = {
        "Invoice Number": "",
        "Order ID": "",
        "Invoice Date": "",
        "Total Amount": "",
        "Items": []
    }

    # --- Section 1: Extract Header Information (Invoice Number, Order ID, Date) ---
    # Invoice Number: Look for patterns like "Invoice Number: ABC-123" or "Invoice Details: ABC-123"
    match_invoice_num = re.search(r"(?:Invoice Number|Invoice Details):\s*([A-Z0-9-]+)", text, re.IGNORECASE)
    if match_invoice_num:
        data["Invoice Number"] = match_invoice_num.group(1).strip()
    print(f"DEBUG_HEADER: Invoice Number found: {data['Invoice Number']}")

    # Order ID: Look for patterns like "Order Number: 123-ABC-456"
    match_order_id = re.search(r"(?:Order Number|Order ID):\s*([A-Z0-9-]+)", text, re.IGNORECASE)
    if match_order_id:
        data["Order ID"] = match_order_id.group(1).strip()
    print(f"DEBUG_HEADER: Order ID found: {data['Order ID']}")

    # Invoice Date: Look for patterns like "Invoice Date: DD.MM.YYYY" or "Order Date: DD.MM.YYYY"
    match_invoice_date = re.search(r"(?:Invoice Date|Order Date):\s*(\d{2}\.\d{2}\.\d{4})", text, re.IGNORECASE)
    if match_invoice_date:
        data["Invoice Date"] = match_invoice_date.group(1).strip().replace('.', '-') # Normalize to DD-MM-YYYY
    print(f"DEBUG_HEADER: Invoice Date found: {data['Invoice Date']}")
        
    # --- Section 2: Extract Items Information from the Table ---
    lines = text.splitlines()
    item_section_start_line_index = -1
    item_section_end_line_index = -1
    actual_items_data_start_index = -1 # New index to mark where actual item data starts

    # Step 1: Find the main table header line ("Description", "Unit Price", "Qty")
    for i, line in enumerate(lines):
        normalized_line = " ".join(line.split()).lower()
        if ("description" in normalized_line and "unit price" in normalized_line and "qty" in normalized_line):
            item_section_start_line_index = i
            break
    print(f"DEBUG_ITEM_SECTION: Main item table header found at index: {item_section_start_line_index}")

    if item_section_start_line_index != -1:
        # Step 2: Find the "value header" row (e.g., "AmountTax RateTax TypeTax AmountTotal Amount")
        # which usually appears right after the main header and before actual item data.
        # This loop starts from the line *after* the main header.
        sub_header_found_index = -1
        for i in range(item_section_start_line_index + 1, len(lines)):
            line_clean = lines[i].strip()
            # This pattern targets lines that look like column headers for values (e.g., "AmountTax RateTax...")
            if re.search(r'\bAmount\b.*\bTax\b.*\bTotal\b', line_clean, re.IGNORECASE):
                sub_header_found_index = i
                break
            # If we hit a blank line after the main header, keep searching for the sub-header
            if not line_clean:
                continue
            # If a line contains text but doesn't match sub-header or item-row-indicator, it might be junk
            # or a continuation of description. For now, if not sub-header, consider it as a potential item start.
            
        if sub_header_found_index != -1:
            actual_items_data_start_index = sub_header_found_index + 1
        else:
            # Fallback if no specific sub-header found, start searching for actual items
            # from the line directly after the main header.
            # We'll use a more robust check for actual item rows.
            
            # Regex to identify a line that looks like an item:
            # Starts with optional whitespace, then a number (for SI. No.), followed by descriptive text,
            # then a price-like string (e.g., '63,474.58' or '₹29,463.39').
            item_row_indicator_pattern = re.compile(
                r'^\s*\d+\s*.+?(?:₹)?[\d,]+\.?\d+', re.IGNORECASE | re.DOTALL
            )
            found_first_item_heuristic = False
            for i in range(item_section_start_line_index + 1, len(lines)):
                line_clean = lines[i].strip()
                if not line_clean: # Skip empty lines
                    continue
                if item_row_indicator_pattern.search(line_clean):
                    actual_items_data_start_index = i
                    found_first_item_heuristic = True
                    break
                # If we're past the main header and a non-empty line isn't an item,
                # we need to be careful not to skip real data. For simplicity,
                # if no explicit sub-header or item-row-indicator found after a few lines,
                # just start directly after main header.
                if i - item_section_start_line_index > 3 and not found_first_item_heuristic:
                    actual_items_data_start_index = item_section_start_line_index + 1
                    break
            
            if not found_first_item_heuristic and actual_items_data_start_index == -1:
                actual_items_data_start_index = item_section_start_line_index + 1 # Final fallback

    print(f"DEBUG_ITEM_SECTION: Actual item data start index: {actual_items_data_start_index}")

    # Step 3: Find the end of the item section (e.g., "TOTAL:", "Amount in Words")
    for i in range(actual_items_data_start_index if actual_items_data_start_index != -1 else 0, len(lines)):
        line_clean = lines[i].strip()
        if "TOTAL:" in line_clean or "Amount in Words" in line_clean or "Subtotal" in line_clean or "Shipping Address" in line_clean:
            item_section_end_line_index = i
            break
    
    if item_section_end_line_index == -1:
        item_section_end_line_index = len(lines) # Fallback if no clear end
    
    print(f"DEBUG_ITEM_SECTION: Item section end line index: {item_section_end_line_index}")

    item_table_block_text = ""
    if actual_items_data_start_index != -1 and item_section_end_line_index != -1 and \
       actual_items_data_start_index < item_section_end_line_index:
        cleaned_lines = [line.strip() for line in lines[actual_items_data_start_index : item_section_end_line_index]]
        item_table_block_text = "\n".join(cleaned_lines)
    print(f"DEBUG_ITEM_SECTION: Item table block text (first 500 chars):\n{item_table_block_text[:500]}...")
    
    if item_table_block_text:
        # Revised item_line_pattern for flexible parsing based on observed Amazon formats
        # This pattern is more robust to spaces, newlines within logical fields, and varied column content.
        # It assumes the "Description", "Unit Price", "Qty", "Net Amount", "Tax Rate", "Tax Type", "Tax Amount", "Total Amount" structure.
        # It will try to capture the main fields, allowing for flexible content in between.
        
        item_line_pattern = re.compile(
            r'^\s*(\d+)\s*'                                   # G1: SI. No. (starts with a digit, e.g., '1')
            r'(.+?)'                                          # G2: Description (non-greedy, captures anything until next specific pattern)
            r'(?:₹)?([\d,]+\.?\d+)\s*'                        # G3: Unit Price
            r'(\d+)\s*'                                       # G4: Quantity
            r'(?:₹)?([\d,]+\.?\d+)\s*'                        # G5: Net Amount
            r'([\d.]+%?)\s*'                                  # G6: Tax Rate (e.g., "9%", "12.0%", optional %)
            r'([A-Z]+)\s*'                                    # G7: Tax Type (e.g., "CGST", "IGST")
            r'(?:₹)?([\d,]+\.?\d+)\s*'                        # G8: Tax Amount
            r'(?:₹)?([\d,]+\.?\d+)$'                          # G9: Total Item Price (ends line)
        , re.DOTALL | re.MULTILINE) # DOTALL allows . to match newlines, MULTILINE for ^ and $

        all_item_matches = item_line_pattern.findall(item_table_block_text)
        print(f"DEBUG_ITEM_PARSING: Number of item matches found: {len(all_item_matches)}")

        for idx, match in enumerate(all_item_matches):
            print(f"DEBUG_ITEM_PARSING: Raw match for item {idx+1}: {match}")
            
            # Extract and clean values based on new group indices from the pattern
            # Group indices (adjusted for the new regex):
            # G1: SI. No.
            # G2: Description
            # G3: Unit Price
            # G4: Quantity
            # G5: Net Amount
            # G6: Tax Rate
            # G7: Tax Type
            # G8: Tax Amount
            # G9: Total Item Price
            
            si_no_part = match[0] # G1
            description_raw = match[1] # G2
            unit_price_raw = match[2] # G3
            quantity_raw = match[3] # G4
            net_amount_raw = match[4] # G5
            tax_rate_raw = match[5] # G6 (not used in final output, but for reference)
            tax_type_raw = match[6] # G7 (not used in final output, but for reference)
            tax_amount_raw = match[7] # G8 (not used in final output, but for reference)
            total_item_price_raw = match[8] # G9

            # Clean description: Remove Amazon-specific IDs and HSN numbers
            description = description_raw.strip().replace('\n', ' ')
            # Remove the SI. No. if it's accidentally captured at the start of description_raw
            if si_no_part and description.startswith(si_no_part.strip()):
                description = description[len(si_no_part.strip()):].strip()
            
            # Specific cleanups for Amazon descriptions
            description = re.sub(r'\s*\|\s*B\d{10,}\s*\(\S+\)', '', description).strip() # Remove product ID like | B09G99CW2N (B09G99CW2N)
            description = re.sub(r'HSN:\d+', '', description).strip() # Remove HSN codes
            description = re.sub(r'\s+', ' ', description).strip() # Consolidate multiple spaces
            
            # Sanitize and convert numerical values
            unit_price = 0.0
            if unit_price_raw:
                try: unit_price = float(unit_price_raw.replace(",", "").replace("₹", ""))
                except ValueError: pass

            quantity = 0
            if quantity_raw:
                try: quantity = int(quantity_raw)
                except ValueError: pass 

            total_item_price = 0.0
            if total_item_price_raw:
                try: total_item_price = float(total_item_price_raw.replace(",", "").replace("₹", ""))
                except ValueError: pass
            
            data["Items"].append({
                "Description": description,
                "Quantity": quantity,
                "Unit Price": unit_price,
                "Total Item Price": total_item_price
            })
            print(f"DEBUG_ITEM_PARSING: Parsed item {idx+1}: {data['Items'][-1]}")

    # Extract Total Amount (now handling the CSV-like structure for the TOTAL: line)
    # Search for the "TOTAL:" line globally in the text
    total_line_match = re.search(r"TOTAL:\s*.*?(?:₹)?([\d,]+\.?\d*)\s*$", text, re.IGNORECASE | re.DOTALL)
    if total_line_match:
        data["Total Amount"] = total_line_match.group(1).strip().replace(",", "")
    else:
        # Fallback: if "TOTAL:" line is in a CSV format with values at the end, specifically the last numeric value
        total_csv_match = re.search(r"TOTAL:.*,\s*(?:\"([\d,]+\.?\d*)\"|([\d,]+\.?\d*))\s*$", text, re.IGNORECASE | re.DOTALL)
        if total_csv_match:
            data["Total Amount"] = (total_csv_match.group(1) or total_csv_match.group(2) or "").strip().replace(",", "")
        else:
            # Final fallback for Total Amount if not found in specific TOTAL: patterns
            match_grand_total = re.search(r"(?:Grand Total|Total Amount|Total Price):\s*(?:₹)?\s*([\d,]+\.?\d*)", text, re.IGNORECASE | re.DOTALL)
            if match_grand_total:
                data["Total Amount"] = match_grand_total.group(1).strip().replace(",", "")
    print(f"DEBUG_HEADER: Final Total Amount found: {data['Total Amount']}")


    if not data["Invoice Number"] and not data["Order ID"]:
        print("DEBUG_FINAL: No Invoice Number or Order ID found. Returning empty dict.")
        return {} # Return empty dict if no main identifiers are found

    print(f"DEBUG_FINAL: Successfully parsed data for Invoice Number: {data['Invoice Number']} or Order ID: {data['Order ID']}")
    return data

# This block allows you to test the extract_amazon.py script independently.
if __name__ == "__main__":
    import os
    import sys
    
    script_dir = os.path.dirname(__file__)
    project_root = os.path.abspath(os.path.join(script_dir, '..'))
    input_folder = os.path.join(project_root, 'input_pdfs')
    
    # Add project_root to sys.path for direct testing of this script
    if project_root not in sys.path:
        sys.path.append(project_root)
    # Ensure pdf_reader can be imported if running directly
    try:
        from pdf_reader import extract_text_from_pdf
    except ImportError as e:
        print(f"Error: Could not import 'extract_text_from_pdf'. Please ensure 'pdf_reader.py' is in the 'scripts' directory. {e}")
        sys.exit(1)


    sample_pdf_filenames = [
        # 'Bag invoice main (1).pdf', # This file was deleted by the user.
        'Iphoneinvoicev2.pdf',
        'pdfcoffee.com_invoice-amazonpdf-pdf-free.pdf',
    ]

    for sample_pdf_filename in sample_pdf_filenames:
        sample_pdf_path = os.path.join(input_folder, sample_pdf_filename)
        print(f"\n--- Testing Amazon PDF: '{sample_pdf_filename}' ---")

        if os.path.exists(sample_pdf_path):
            print("Attempting to extract text from PDF...")
            extracted_text = extract_text_from_pdf(sample_pdf_path)
            
            if extracted_text:
                print("\n--- Raw Extracted Text Snippet (First 1000 chars) ---")
                print(extracted_text[:1000])
                print("...")
                
                parsed_data = parse_amazon_invoice(extracted_text)
                
                print("\n--- Parsed Amazon Invoice Data ---")
                if parsed_data:
                    for key, value in parsed_data.items():
                        if key == "Items":
                            print(f"{key}:")
                            for item in value:
                                print(f"  - {item}")
                        else:
                            print(f"{key}: {value}")
                else:
                    print("No Amazon invoice data was successfully parsed. Check the PDF content and parsing logic.")
            else:
                print(f"Could not extract any text from '{sample_pdf_filename}'.")
        else:
            print(f"\nError: Sample Amazon PDF '{sample_pdf_filename}' not found in '{input_folder}'.")
            print("Please place the PDF there to test this script.")
