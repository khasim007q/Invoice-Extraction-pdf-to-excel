import re

def _parse_single_flipkart_section(section_text, global_order_id="", global_invoice_date=""):
    """
    Parses a single section of text identified as a Flipkart invoice or note.
    This helper function contains the core logic for extracting header and item data.
    It takes global Order ID and Invoice Date as input, which are used as fallbacks.
    """
    data = {
        "Invoice Type": "Unknown",
        "Invoice Number": "",
        "Order ID": global_order_id,  # Initialize with global value
        "Invoice Date": global_invoice_date, # Initialize with global value
        "Total Amount": "",
        "Items": []
    }

    lines = section_text.splitlines()
    
    # --- Extract Header Information for a Single Section ---
    for i, line in enumerate(lines):
        line_stripped = line.strip()

        # Identify Invoice Type (Tax Invoice, Debit Note, Credit Note)
        if "Tax Invoice" in line_stripped and data["Invoice Type"] == "Unknown":
            data["Invoice Type"] = "Tax Invoice"
            # print(f"DEBUG_HEADER: Identified as Tax Invoice from line: {line_stripped}")
        elif "Debit Note" in line_stripped and data["Invoice Type"] == "Unknown":
            data["Invoice Type"] = "Debit Note"
            # print(f"DEBUG_HEADER: Identified as Debit Note from line: {line_stripped}")
        elif "Credit Note" in line_stripped and data["Invoice Type"] == "Unknown":
            data["Invoice Type"] = "Credit Note"
            # print(f"DEBUG_HEADER: Identified as Credit Note from line: {line_stripped}")

        # Order ID: Appears early and consistently, potentially with leading non-breaking space
        if "Order ID:" in line_stripped:
            match = re.search(r"Order ID:\s*(\xa0)?([A-Z0-9]+)", line_stripped)
            if match and data["Order ID"] == global_order_id: # Only update if not already found in section
                data["Order ID"] = match.group(2).strip()
                # print(f"DEBUG_HEADER: Found Order ID in section: {data['Order ID']}")

        # Invoice Number/Note Number: More robust patterns and cleaning
        # Prioritize "Invoice Number" first, then Debit/Credit Note Numbers
        inv_num_patterns = [
            (r"Invoice Number\s*#?\s*([A-Z0-9-]+?)(?:Tax Invoice|Debit Note|Credit Note)?$", "Invoice Number"), # Non-greedy capture, then optional suffix
            (r"Debit Note Number\s*#?\s*([A-Z0-9-]+?)(?:Debit Note)?$", "Debit Note Number"),
            (r"Credit Note Number\s*#?\s*([A-Z0-9-]+?)(?:Credit Note)?$", "Credit Note Number"),
            (r"Original Invoice Number:\s*([A-Z0-9-]+)", "Original Invoice Number")
        ]
        
        if not data["Invoice Number"]: # Only try to find if not already set
            for pattern_str, name_of_field in inv_num_patterns:
                match = re.search(pattern_str, line_stripped, re.IGNORECASE)
                if match:
                    # Clean the suffix if it was captured as part of the ID
                    inv_id = match.group(1).strip()
                    # A more explicit cleanup for common suffixes
                    inv_id = re.sub(r"(tax invoice|debit note|credit note)$", "", inv_id, flags=re.IGNORECASE).strip()
                    data["Invoice Number"] = inv_id
                    # print(f"DEBUG_HEADER: Found {name_of_field}: {data['Invoice Number']}")
                    break # Stop after finding the first relevant invoice number

        # Invoice Date: Capture DD-MM-YYYY, accounting for leading non-breaking space
        if "Invoice Date:" in line_stripped:
            match = re.search(r"Invoice Date:\s*(\xa0)?(\d{2}-\d{2}-\d{4})", line_stripped)
            if match and data["Invoice Date"] == global_invoice_date: # Only update if not already found in section
                data["Invoice Date"] = match.group(2).strip()
                # print(f"DEBUG_HEADER: Found Invoice Date in section: {data['Invoice Date']}")
        elif "Order Date:" in line_stripped and data["Invoice Date"] == global_invoice_date:
            match = re.search(r"Order Date:\s*(\xa0)?(\d{2}-\d{2}-\d{4})", line_stripped)
            if match:
                data["Invoice Date"] = match.group(2).strip()
                # print(f"DEBUG_HEADER: Found Invoice Date (from Order Date) in section: {data['Invoice Date']}")

        # Grand Total
        if "Grand Total ₹" in line_stripped:
            match = re.search(r"Grand Total\s*₹\s*([-]?[\d,]+\.\d{2})", line_stripped)
            if match and not data["Total Amount"]:
                data["Total Amount"] = match.group(1).strip().replace(",", "")
                # print(f"DEBUG_HEADER: Found Total Amount: {data['Total Amount']}")
    
    # --- Extract Items Information for a Single Section ---
    item_section_start_line_index = -1
    item_section_end_line_index = -1

    # Find the start of the item list (common headers)
    for i, line in enumerate(lines):
        normalized_line = " ".join(line.split()).lower()
        if ("product title" in normalized_line and "qty" in normalized_line and "gross" in normalized_line) or \
           ("description" in normalized_line and "qty" in normalized_line and "gross" in normalized_line):
            item_section_start_line_index = i
            # print(f"DEBUG_ITEM: Item section START detected at line {i}: {line}")
            break

    # Find the end of the item list
    if item_section_start_line_index != -1:
        for i in range(item_section_start_line_index + 1, len(lines)):
            line = lines[i].strip()
            # More specific end markers to avoid including totals as items
            if re.search(r"Total\s+items:", line, re.IGNORECASE) or \
               re.search(r"Grand Total\s*₹", line) or \
               "Signature" in line or \
               "Authorized Signatory" in line or \
               "Regd. office:" in line or \
               "Contact Flipkart:" in line or \
               "Payment Details" in line or \
               re.search(r"E\.\s*&\s*O\.E\.\s*page", line): # Stop if next section starts
                item_section_end_line_index = i
                # print(f"DEBUG_ITEM: Item section END detected at line {i}: {line}")
                break
        
        if item_section_end_line_index == -1:
            item_section_end_line_index = len(lines) # Fallback if no clear end marker
            # print(f"DEBUG_ITEM: Item section END defaulted to end of section: {item_section_end_line_index}")

    if item_section_start_line_index != -1 and item_section_end_line_index != -1:
        
        # Helper function to check if a line is a pure non-item line (header, footer, etc.)
        def is_pure_non_item_line(line_to_check):
            # These patterns identify lines that are *definitely* not item data,
            # focusing on general document structure and column headers that are *not*
            # part of a numerical item row.
            patterns_to_check = [
                r"E\. & O\.E\. page",
                r"Billing Address",
                r"Phone: xxxxxxxxxx",
                r"Order ID:",
                r"Order Date:",
                r"Invoice Date:",
                r"PAN:",
                r"CIN:",
                r"Invoice Number",
                r"Sold By:",
                r"Ship-from Address:",
                r"GSTIN",
                r"Description\s+Qty\s+Gross\s+Amount", # This is the main item table header
                r"Signature",
                r"Authorized Signatory",
                r"Regd\. office:",
                r"Contact Flipkart:",
                r"www\.flipkart\.com",
                r"Total\s+items:", # Summary total line
                r"Grand Total\s*₹", # Summary total line
                r"Payment Details",
                r"Handsets\s*$", # Specific category header line, ends with Handsets
                # General column headers without values that should be skipped if they appear alone
                r"^\s*Amount\s*₹Discounts\s*$",
                r"^\s*/Coupons\s*₹Taxable\s*$",
                r"^\s*value\s*₹CGST\s*$",
                r"^\s*₹SGST\s*$",
                r"^\s*/UTGST\s*$",
                r"^\s*₹Total\s*₹\s*$",
                r"^\s*Value\s*₹Total\s*₹\s*$",
                r"^\s*Value\s*₹IGST\s*$",
                r"^\s*₹IGST\s*$",
            ]
            for pattern in patterns_to_check:
                if re.search(pattern, line_to_check, re.IGNORECASE):
                    print(f"DEBUG_ITEM: (is_pure_non_item_line) Matched pattern '{pattern}' for line: '{line_to_check}'")
                    return True
            return False

        # Helper function to check if a line is a "Total" summary line
        def is_total_summary_line(line_to_check):
            # This regex needs to be precise to only match the overall "Total" sums.
            # It should not match lines that are part of an item description but contain a total.
            return bool(re.search(r"^\s*Total\s+\d+\s+([-]?[\d,.-]+)\s+([\d,.-]+)\s+([\d,.-]+)\s+([\d,.-]+)\s+([\d,.-]+)\s+([-]?[\d,]+\.\d{2})$", line_to_check))


        # Helper functions for specific item matching patterns
        def _match_freight_charge(block):
            match = re.search(
                r"^(?:SAC:\s*(\d+)\s*)?" # Optional SAC number (Group 1)
                r"(Freight charges for pick up of(?:\s*\nused product)?)\s*" # Description (Group 2)
                r"(?:\s*\d+\.\d+(?:0+)?\s*%\s*CGST:\s*)?"
                r"(?:\s*\n?\s*\d+\.\d+(?:0+)?\s*%\s*SGST/UTGST:\s*)?"
                r"(\d+)\s*" # Quantity (Group 3)
                r"([-]?[\d,]+\.\d{2})\s*" # Gross Amount (Group 4)
                r"([-]?[\d,]+\.\d{2})\s*" # Discounts (Group 5)
                r"([-]?[\d,]+\.\d{2})\s*" # Taxable (Group 6)
                r"([-]?[\d,]+\.\d{2})\s*" # CGST (Group 7)
                r"([-]?[\d,]+\.\d{2})\s*" # SGST (Group 8)
                r"([-]?[\d,]+\.\d{2})$", # Total (Group 9)
                block, re.IGNORECASE | re.DOTALL
            )
            if match:
                desc_parts = []
                if match.group(1): # Add SAC if present
                    desc_parts.append(f"SAC: {match.group(1).strip()}")
                desc_parts.append(match.group(2).strip().replace('\n', ' '))
                desc = " ".join(part for part in desc_parts if part)
                desc = re.sub(r'\s+', ' ', desc).strip()
                return {
                    "Description": desc,
                    "Quantity": int(match.group(3)),
                    "Unit Price": float(match.group(4).replace(",", "")),
                    "Total Item Price": float(match.group(9).replace(",", ""))
                }, len(match.group(0).splitlines())
            return None, 0

        def _match_secure_packaging_fee(block):
            match = re.search(
                r"^(?:SAC:\s*(\d+)\s*)?" # Optional SAC number (Group 1)
                r"(Secure Packaging Fee(?:\s*\n?1\.\s*\[IMEI/Serial No:\s*\]\s*([\d\s]+))?)\s*" # Description (Group 2), IMEI (Group 3)
                r"(?:\s*\d+\.\d+(?:0+)?\s*%\s*CGST:\s*)?"
                r"(?:\s*\n?\s*\d+\.\d+(?:0+)?\s*%\s*SGST/UTGST:\s*)?"
                r"(\d+)\s*" # Quantity (Group 4)
                r"([-]?[\d,]+\.\d{2})\s*" # Gross Amount (Group 5)
                r"([-]?[\d,]+\.\d{2})\s*" # Discounts (Group 6)
                r"([-]?[\d,]+\.\d{2})\s*" # Taxable (Group 7)
                r"([-]?[\d,]+\.\d{2})\s*" # CGST (Group 8)
                r"([-]?[\d,]+\.\d{2})\s*" # SGST (Group 9)
                r"([-]?[\d,]+\.\d{2})$", # Total (Group 10)
                block, re.IGNORECASE | re.DOTALL
            )
            if match:
                desc_parts = []
                if match.group(1): # SAC number
                    desc_parts.append(f"SAC: {match.group(1).strip()}")
                
                # Combine the base description and IMEI if present
                base_desc = "Secure Packaging Fee"
                if match.group(3): # IMEI was captured
                    base_desc += f" 1. [IMEI/Serial No: ] {match.group(3).strip()}"
                
                desc_parts.append(base_desc)
                
                desc = " ".join(part for part in desc_parts if part)
                desc = re.sub(r'\s+', ' ', desc).strip()

                return {
                    "Description": desc,
                    "Quantity": int(match.group(4)),
                    "Unit Price": float(match.group(5).replace(",", "")),
                    "Total Item Price": float(match.group(10).replace(",", ""))
                }, len(match.group(0).splitlines())
            return None, 0

        def _match_product_exchange(block):
            match = re.search(
                r"^(Product Exchange)\s*\n" # G1: "Product Exchange" header
                r"FSN:\s*([A-Z0-9]+)\s*\n" # G2: FSN
                r"HSN/SAC:\s*(\d+)(?:Exchange of\s*)?" # G3: HSN/SAC, optional "Exchange of"
                r"([\s\S]+?)(?:\s*\n?Total\s+\d+\s+[-]?[\d,]+\.\d{2}\s+[-]?[\d,]+\.\d{2}\s+[-]?[\d,]+\.\d{2}\s+[-]?[\d,]+\.\d{2}\s+[-]?[\d,]+\.\d{2})?\s*\n" # G4: Product Name (non-greedy), followed by optional internal Total line, and newline
                r"(\d+)\s+" # G5: Quantity
                r"([-]?[\d,]+\.\d{2})\s+" # G6: Gross Amount
                r"([-]?[\d,]+\.\d{2})\s+" # G7: Discounts
                r"([-]?[\d,]+\.\d{2})\s+" # G8: Taxable Value
                r"(?:([-]?[\d,]+\.\d{2})\s+)?" # G9: CGST (Optional)
                r"(?:([-]?[\d,]+\.\d{2})\s+)?" # G10: SGST/UTGST (Optional)
                r"([-]?[\d,]+\.\d{2})$", # G11: Total Item Price for THIS item
                block, re.IGNORECASE | re.DOTALL
            )
            if match:
                product_name_raw = match.group(4).strip().replace('\n', ' ')
                # Remove any numbers or "Total" from the product name if they were accidentally captured
                product_name_cleaned = re.sub(r'([\d,]+\.\d{2}(?:\s*[-]?[\d,]+\.\d{2})*|Total(?:\s+\d+)?(?:\s*[-]?[\d,]+\.\d{2})*)', '', product_name_raw, flags=re.IGNORECASE).strip()
                product_name_cleaned = re.sub(r'Sport(?:1)?$', '', product_name_cleaned, flags=re.IGNORECASE).strip() # Remove "Sport" if it's there
                product_name_cleaned = re.sub(r'\s+', ' ', product_name_cleaned).strip() # Compact spaces

                final_desc_parts = ["Product Exchange"]
                final_desc_parts.append(f"FSN: {match.group(2).strip()}")
                final_desc_parts.append(f"HSN/SAC: {match.group(3).strip()}")
                final_desc_parts.append(product_name_cleaned) # Use the cleaned product name
                
                final_desc = " ".join(part for part in final_desc_parts if part).strip()
                final_desc = re.sub(r'\s+', ' ', final_desc).strip()

                return {
                    "Description": final_desc,
                    "Quantity": int(match.group(5)), # Quantity
                    "Unit Price": float(match.group(6).replace(",", "")), # Gross Amount
                    "Total Item Price": float(match.group(11).replace(",", "")) # Total Item Price
                }, len(match.group(0).splitlines())
            return None, 0

        def _match_spotify_premium(block):
            match = re.search(
                r"^(Digital Voucher Code)\s*\n" # G1: "Digital Voucher Code" header
                r"FSN:\s*([A-Z0-9]+)\s*\n" # G2: FSN
                r"HSN/SAC:\s*(\d+)(Spotify Premium - \d+M at Rs \d+)\s*\n" # G3: HSN/SAC, G4: Spotify description
                r"(?:18\.0\s*%\s*IGST:)?\s*" # Optional IGST label
                r"(\d+)\s+" # G5: Quantity (should be 1)
                r"([-]?[\d,]+\.\d{2})\s+" # G6: Gross Amount
                r"([-]?[\d,]+\.\d{2})\s+" # G7: Discounts
                r"([-]?[\d,]+\.\d{2})\s+" # G8: Taxable Value
                r"(?:([-]?[\d,]+\.\d{2})\s*)?" # G9: IGST (Optional)
                r"([-]?[\d,]+\.\d{2})\s*\n" # G10: Total Item Price for THIS item
                r"(?:Total\s*\d+\s*[-]?[\d,]+\.\d{2}\s*[-]?[\d,]+\.\d{2}\s*[-]?[\d,]+\.\d{2}\s*[-]?[\d,]+\.\d{2})?$", # Optional summary "Total" line for this sub-section
                block, re.IGNORECASE | re.DOTALL
            )
            if match:
                desc_parts = ["Digital Voucher Code"]
                if match.group(2): # FSN
                    desc_parts.append(f"FSN: {match.group(2).strip()}")
                # Note: HSN/SAC and Spotify description are captured together in G3 and G4,
                # as '998599Spotify Premium - 12M at Rs 699' is one string.
                # So we combine them.
                if match.group(3) and match.group(4):
                    desc_parts.append(f"HSN/SAC: {match.group(3).strip()} {match.group(4).strip()}")
                elif match.group(3): # Fallback if G4 is empty
                     desc_parts.append(f"HSN/SAC: {match.group(3).strip()}")
                
                final_desc = " ".join(part for part in desc_parts if part).replace('\n', ' ')
                final_desc = re.sub(r'\s+', ' ', final_desc).strip()

                return {
                    "Description": final_desc,
                    "Quantity": int(match.group(5)),
                    "Unit Price": float(match.group(6).replace(",", "")),
                    "Total Item Price": float(match.group(10).replace(",", ""))
                }, len(match.group(0).splitlines())
            return None, 0
        
        def _match_shipping_and_handling_charges(block):
            match = re.search(
                r"^(Shipping And Handling Charges)\s*" # Description (Group 1)
                r"(\d+)\s*" # Quantity (Group 2)
                r"([-]?[\d,]+\.\d{2})\s*" # Gross Amount (Group 3)
                r"([-]?[\d,]+\.\d{2})\s*" # Discounts (Group 4)
                r"([-]?[\d,]+\.\d{2})\s*" # Taxable (Group 5)
                r"([-]?[\d,]+\.\d{2})\s*" # CGST (Group 6)
                r"([-]?[\d,]+\.\d{2})\s*" # SGST (Group 7)
                r"([-]?[\d,]+\.\d{2})$", # Total (Group 8)
                block, re.IGNORECASE | re.DOTALL
            )
            if match:
                return {
                    "Description": match.group(1).strip(),
                    "Quantity": int(match.group(2)),
                    "Unit Price": float(match.group(3).replace(",", "")),
                    "Total Item Price": float(match.group(8).replace(",", ""))
                }, len(match.group(0).splitlines())
            return None, 0


        def _match_standard_product(block):
            # This will be the most general pattern, applied last.
            match = re.search(
                r"^(?!Total\s+\d+|Grand Total\s*₹|SAC:\s*\d+\s*(?:Freight|Secure)|Product Exchange|Digital Voucher Code|Shipping And Handling Charges)\s*" # Negative lookahead for total/known specific item start lines
                r"(?:FSN:\s*([A-Z0-9]+)\s*\n)?" # G1: FSN (Optional)
                r"(?:HSN/SAC:\s*(\d+))?\s*" # G2: HSN/SAC (Optional)
                # G3: Main product description, multi-line, non-greedy.
                # Modified negative lookahead to stop before quantity/price or other structured data.
                r"((?:(?!\s*\n?\s*\d+\s+[-]?[\d,]+\.\d{2}[\s\S]*?$|\s*1\.\s*\[IMEI/Serial No:|\s*Warranty:|\s*Phone and 6 Months Warranty)\s*[\s\S])*?)" 
                r"(?:\s*\n1\.\s*\[IMEI/Serial No:\s*([\d\s]+)\])?\s*" # G4: IMEI (Optional)
                r"(?:\s*\nWarranty:.*?)?" # Non-capturing optional warranty
                r"(?:\s*\nPhone and 6 Months Warranty for In the Box(?:\s*\nAccessories)?)?" # Non-capturing specific warranty lines
                r"(?:\s*\d+\.\d+(?:0+)?\s*%\s*(?:CGST|SGST/UTGST|IGST):\s*)?" # Non-capturing tax rate lines (label only)
                r"(\d+)\s*" # G5: Quantity
                r"([-]?[\d,]+\.\d{2})\s*" # G6: Gross Amount
                r"(?:([-]?[\d,]+\.\d{2})\s*)?" # G7: Discounts (Optional)
                r"(?:([-]?[\d,]+\.\d{2})\s*)?" # G8: Taxable Value (Optional)
                r"(?:([-]?[\d,]+\.\d{2})\s*)?" # G9: CGST (Optional)
                r"(?:([-]?[\d,]+\.\d{2})\s*)?" # G10: SGST/UTGST (Optional)
                r"([-]?[\d,]+\.\d{2})$", # G11: Total
                block, re.IGNORECASE | re.DOTALL
            )
            if match:
                full_description_parts = []
                if match.group(1): # FSN
                    full_description_parts.append(f"FSN: {match.group(1).strip()}")
                if match.group(2): # HSN/SAC
                    full_description_parts.append(f"HSN/SAC: {match.group(2).strip()}")
                
                item_desc_core = match.group(3).strip()
                # Aggressive cleanup for the description
                item_desc_core = re.sub(r'1\.\s*\[IMEI/Serial No:\s*[\d\s]+\]', '', item_desc_core, flags=re.IGNORECASE | re.DOTALL).strip()
                item_desc_core = re.sub(r'Warranty:.*$', '', item_desc_core, flags=re.IGNORECASE | re.DOTALL).strip()
                item_desc_core = re.sub(r'Phone and 6 Months Warranty for In the Box(?:Accessories)?', '', item_desc_core, flags=re.IGNORECASE | re.DOTALL).strip()
                item_desc_core = re.sub(r'\s*\d+\.\d+(?:0+)?\s*%\s*(?:CGST:|SGST/UTGST:|IGST:)?', '', item_desc_core, flags=re.IGNORECASE).strip()
                item_desc_core = re.sub(r'Amount ₹Discounts|/Coupons ₹Taxable|value ₹CGST|₹SGST|/UTGST|₹Total ₹|Value ₹IGST|Value ₹Total ₹|Handsets|Accessories', '', item_desc_core, flags=re.IGNORECASE).strip()
                item_desc_core = re.sub(r'(?:FSN:\s*[A-Z0-9]+|HSN/SAC:\s*\d+)\s*', '', item_desc_core, flags=re.IGNORECASE).strip() # Remove FSN/HSN from description if they leaked
                item_desc_core = re.sub(r'([\d,]+\.\d{2}(?:\s*[-]?[\d,]+\.\d{2})*|\s*Total(?:\s*\d+)?(?:\s*[-]?[\d,]+\.\d{2})*)', '', item_desc_core, flags=re.IGNORECASE).strip() # Remove numerical values/totals that might have snuck in
                item_desc_core = re.sub(r'\b\d{10,}\b', '', item_desc_core, flags=re.IGNORECASE).strip() # Remove long numbers that might be IMEI if not captured by G4
                item_desc_core = re.sub(r'\s+', ' ', item_desc_core).strip() # Compact multiple spaces


                full_description_parts.append(item_desc_core)

                if match.group(4): # IMEI
                    full_description_parts.append(f"[IMEI/Serial No: {match.group(4).strip()}]")
                
                final_desc = " ".join(part for part in full_description_parts if part).replace('\n', ' ')
                final_desc = re.sub(r'\s+', ' ', final_desc).strip() # Compact multiple spaces

                return {
                    "Description": final_desc,
                    "Quantity": int(match.group(5)),
                    "Unit Price": float(match.group(6).replace(",", "")),
                    "Total Item Price": float(match.group(11).replace(",", ""))
                }, len(match.group(0).splitlines())
            return None, 0

        # Iterate through lines within the identified item section
        line_idx = item_section_start_line_index + 1
        while line_idx < item_section_end_line_index:
            line = lines[line_idx].strip()
            print(f"DEBUG_ITEM: Processing line {line_idx}: '{line}'")

            processed_lines_for_item = 1 # Initialize for each iteration

            if not line:
                line_idx += 1
                continue
            
            # --- Aggressive skipping of lines that are absolutely NOT items ---
            if is_pure_non_item_line(line):
                print(f"DEBUG_ITEM: Skipping known non-item/summary/address line: '{line}'")
                line_idx += 1
                continue

            # --- Explicitly skip "Total" summary lines to prevent them from becoming items ---
            if is_total_summary_line(line):
                print(f"DEBUG_ITEM: Found a 'Total' summary line, explicitly skipping: '{line}'")
                line_idx += 1
                continue
            
            # --- Aggregating multi-line item descriptions into a potential_full_item_block ---
            lookahead_lines = []
            current_temp_line_idx = line_idx
            # Try to grab up to next 10 lines for matching, or until end of section
            for k in range(10): 
                if (current_temp_line_idx + k) < item_section_end_line_index:
                    current_line_to_add = lines[current_temp_line_idx + k].strip()
                    if is_pure_non_item_line(current_line_to_add) or is_total_summary_line(current_line_to_add):
                        print(f"DEBUG_ITEM: Breaking lookahead as line {current_temp_line_idx + k} ('{current_line_to_add}') is a pure non-item/summary line.")
                        break
                    # Also break if the line seems to start a new item's data section
                    if re.match(r"^(?:FSN:|HSN/SAC:|SAC:\s*\d+|Shipping And Handling Charges|Product Exchange|Digital Voucher Code)\b", current_line_to_add, re.IGNORECASE) and k > 0:
                         print(f"DEBUG_ITEM: Breaking lookahead as line {current_temp_line_idx + k} ('{current_line_to_add}') appears to be start of new item (specific type).")
                         break
                    if re.match(r"^\d+\s+[-]?[\d,]+\.\d{2}\s+[-]?[\d,]+\.\d{2}", current_line_to_add) and k > 0: # Checks for Qty Amount Discount pattern
                        print(f"DEBUG_ITEM: Breaking lookahead as line {current_temp_line_idx + k} ('{current_line_to_add}') appears to be numerical start of new item.")
                        break # Changed from pass to break
                    lookahead_lines.append(current_line_to_add)
                else:
                    break
            
            potential_full_item_block = "\n".join(lookahead_lines)
            print(f"DEBUG_ITEM: Attempting to match with full block (from line {line_idx}): '{potential_full_item_block}'")

            found_item = None
            consumed_lines = 0

            # Order of matching is crucial: most specific to most general
            # Attempt more specific matches first
            found_item, consumed_lines = _match_freight_charge(potential_full_item_block)
            if found_item:
                data["Items"].append(found_item)
                print(f"DEBUG_ITEM: Added Freight Charge item: {found_item}")
                line_idx += consumed_lines
                continue

            found_item, consumed_lines = _match_secure_packaging_fee(potential_full_item_block)
            if found_item:
                data["Items"].append(found_item)
                print(f"DEBUG_ITEM: Added Secure Packaging Fee item: {found_item}")
                line_idx += consumed_lines
                continue

            found_item, consumed_lines = _match_spotify_premium(potential_full_item_block)
            if found_item:
                data["Items"].append(found_item)
                print(f"DEBUG_ITEM: Added Spotify Premium item: {found_item}")
                line_idx += consumed_lines
                continue
            
            found_item, consumed_lines = _match_shipping_and_handling_charges(potential_full_item_block)
            if found_item:
                data["Items"].append(found_item)
                print(f"DEBUG_ITEM: Added Shipping And Handling Charges item: {found_item}")
                line_idx += consumed_lines
                continue

            found_item, consumed_lines = _match_product_exchange(potential_full_item_block)
            if found_item:
                data["Items"].append(found_item)
                print(f"DEBUG_ITEM: Added Product Exchange item: {found_item}")
                line_idx += consumed_lines
                continue

            # Fallback to standard product last
            found_item, consumed_lines = _match_standard_product(potential_full_item_block)
            if found_item:
                data["Items"].append(found_item)
                print(f"DEBUG_ITEM: Added Standard Product item: {found_item}")
                line_idx += consumed_lines
                continue

            # If no specific item pattern matched by any of the helper functions
            print(f"DEBUG_ITEM: Line '{line}' (from line_idx {line_idx}) was not matched by any item pattern. Advancing by 1.")
            line_idx += 1 # Default: advance by 1 (consume current line and try next)

    # Return only if primary identifiers (Order ID or Invoice Number) are found
    if data["Order ID"] or data["Invoice Number"]:
        return data
    return {}


def parse_flipkart_invoice(full_text):
    """
    Parses the full text from a Flipkart PDF, identifying and processing
    multiple invoice/note sections within the document.
    Also attempts to capture global Order ID and Invoice Date that might appear
    at the very beginning of the full document.

    Args:
        full_text (str): The entire raw text extracted from the PDF.

    Returns:
        list: A list of dictionaries, where each dictionary represents a
              parsed invoice or note section.
    """
    all_parsed_sections = []
    
    # Attempt to capture global Order ID and Invoice Date from the very beginning of the text
    global_order_id = ""
    global_invoice_date = ""

    # Search for Order ID in the first few lines of the full text
    order_id_match = re.search(r"Order ID:\s*(\xa0)?([A-Z0-9]+)", full_text[:500]) # Search in first 500 chars
    if order_id_match:
        global_order_id = order_id_match.group(2).strip()
        print(f"DEBUG_GLOBAL: Found Global Order ID: {global_order_id}")

    # Search for Invoice Date in the first few lines of the full text (Order Date often doubles as Invoice Date)
    invoice_date_match = re.search(r"(?:Invoice Date:|Order Date:)\s*(\xa0)?(\d{2}-\d{2}-\d{4})", full_text[:500])
    if invoice_date_match:
        global_invoice_date = invoice_date_match.group(2).strip()
        print(f"DEBUG_GLOBAL: Found Global Invoice Date: {global_invoice_date}")


    # Split the document into potential sections based on the "E. & O.E. page" marker
    section_delimiter_pattern = r"(?s)(E\.\s*&\s*O\.E\.\s*page\s*\d+\s*of\s*\d+)"
    raw_parts = re.split(section_delimiter_pattern, full_text, flags=re.IGNORECASE)

    sections_to_process = []
    current_section_content = []
    current_section_marker = ""

    # Process the raw parts: ['preamble', 'delimiter1', 'content1', 'delimiter2', 'content2', ...]
    for i, part in enumerate(raw_parts):
        if not part.strip():
            continue
        
        # If the part is a delimiter (e.g., "E. & O.E. page 1 of 1"), and we have accumulated content,
        # then finalize the previous section and start a new one.
        if re.match(section_delimiter_pattern, part, re.IGNORECASE):
            if current_section_content:
                sections_to_process.append(current_section_marker + "\n" + "\n".join(current_section_content))
            current_section_marker = part.strip()
            current_section_content = []
        else:
            current_section_content.append(part.strip())

    # After the loop, add the last collected section if any content remains
    if current_section_content:
        sections_to_process.append(current_section_marker + "\n" + "\n".join(current_section_content))

    # Now, parse each identified section, passing global order ID and date
    for section_text in sections_to_process:
        parsed_data = _parse_single_flipkart_section(section_text, global_order_id, global_invoice_date)
        if parsed_data:
            all_parsed_sections.append(parsed_data)

    return all_parsed_sections


# This block allows you to test the extract_flipkart.py script independently.
if __name__ == "__main__":
    import os
    import sys
    
    script_dir = os.path.dirname(__file__)
    project_root = os.path.abspath(os.path.join(script_dir, '..'))
    input_folder = os.path.join(project_root, 'input_pdfs')

    if project_root not in sys.path:
        sys.path.append(project_root)
    if script_dir not in sys.path:
        sys.path.append(script_dir)

    try:
        from pdf_reader import extract_text_from_pdf
    except ImportError:
        print("Error: Could not import 'extract_text_from_pdf'.")
        print("Please ensure 'pdf_reader.py' is in the 'scripts' directory.")
        sys.exit(1)

    sample_pdf_filename = '243.pdf' # This should match the file you provided raw text for
    sample_pdf_path = os.path.join(input_folder, sample_pdf_filename)

    if os.path.exists(sample_pdf_path):
        print(f"Attempting to extract and parse: '{sample_pdf_filename}'")
        extracted_text = extract_text_from_pdf(sample_pdf_path)
        
        if extracted_text:
            print("\n--- Raw Extracted Text Snippet (First 3000 characters) ---")
            print(extracted_text[:3000])
            print("...")
            
            all_parsed_flipkart_data = parse_flipkart_invoice(extracted_text)
            
            print("\n--- Parsed Flipkart Invoice Data (All Sections) ---")
            if all_parsed_flipkart_data:
                for idx, invoice_data in enumerate(all_parsed_flipkart_data):
                    print(f"\n----- Section {idx + 1} -----")
                    for key, value in invoice_data.items():
                        if key == "Items":
                            print(f"{key}:")
                            for item in value:
                                print(f"  - {item}")
                        else:
                            print(f"{key}: {value}")
            else:
                print("No Flipkart invoice data was successfully parsed from any section. Check the PDF content and parsing logic.")
        else:
            print(f"Could not extract any text from '{sample_pdf_filename}'.")
    else:
        print(f"\nError: Sample Flipkart PDF '{sample_pdf_filename}' not found in '{input_folder}'.")
        print("Please place a sample Flipkart invoice PDF there to test this script.")
        print("You might need to adjust 'sample_pdf_filename' in this script to match your file.")
