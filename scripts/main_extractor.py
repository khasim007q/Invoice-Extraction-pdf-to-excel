import os
import sys

# Add the scripts directory to the Python path
script_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(script_dir, '..'))
input_folder = os.path.join(project_root, 'input_pdfs')
output_folder = os.path.join(project_root, 'output_excel')

if project_root not in sys.path:
    sys.path.append(project_root)
if script_dir not in sys.path:
    sys.path.append(script_dir)

try:
    from pdf_reader import extract_text_from_pdf
    from extract_flipkart import parse_flipkart_invoice
    from extract_amazon import parse_amazon_invoice # Import the Amazon parser
    from excel_writer import write_to_excel
except ImportError as e:
    print(f"Error: Could not import necessary modules. Please ensure all scripts are in the 'scripts' directory and openpyxl is installed. Error: {e}")
    sys.exit(1)

def main():
    print("--- Starting PDF processing for invoices ---")

    if not os.path.exists(input_folder):
        print(f"Error: Input folder '{input_folder}' not found. Please create it and place your PDF invoices there.")
        return

    # Create output folder if it doesn't exist
    try:
        os.makedirs(output_folder, exist_ok=True)
        print(f"Debug: Ensured output directory '{output_folder}' exists.")
    except OSError as e:
        print(f"Error: Could not create output directory '{output_folder}'. Please check permissions. Error: {e}")
        return

    # Fix: Removed extra 'f' in list comprehension
    pdf_files = [f for f in os.listdir(input_folder) if f.lower().endswith('.pdf')]

    if not pdf_files:
        print(f"No PDF files found in '{input_folder}'. Please place your PDF invoices there.")
        return

    for pdf_file in pdf_files:
        pdf_path = os.path.join(input_folder, pdf_file)
        print(f"\n--- Processing PDF: '{pdf_file}' ---")

        try:
            print("Attempting to extract text from PDF...")
            raw_text = extract_text_from_pdf(pdf_path)
            if not raw_text:
                print(f"Warning: No text extracted from '{pdf_file}'. Skipping.")
                continue
            print("Text extraction complete. Proceeding to parse invoice data.")

            parsed_data = None
            invoice_type = "Unknown"
            
            # Simple heuristic to determine invoice type
            if "flipkart.com" in raw_text.lower() or "flipkart internet" in raw_text.lower():
                invoice_type = "Flipkart"
                print(f"Detected Flipkart invoice: '{pdf_file}'. Attempting to parse...")
                parsed_data = parse_flipkart_invoice(raw_text)
            elif "amazon.in" in raw_text.lower() or "amazon seller services" in raw_text.lower():
                invoice_type = "Amazon"
                print(f"Detected Amazon invoice: '{pdf_file}'. Attempting to parse...")
                single_parsed_data = parse_amazon_invoice(raw_text)
                if single_parsed_data:
                    parsed_data = [single_parsed_data] # excel_writer expects a list
                else:
                    parsed_data = []
            else:
                print(f"Could not determine invoice type for '{pdf_file}'. Skipping.")
                continue 

            if parsed_data:
                base_filename = os.path.splitext(pdf_file)[0] 
                # Create a shorter sheet name by using the base filename and invoice type, truncate if necessary
                # Max 20 chars of filename + type, total 31 chars
                sheet_name_for_excel = f"{base_filename[:min(20, len(base_filename))]}_{invoice_type}" 
                
                output_excel_filename = f"{base_filename}_{invoice_type}_invoice.xlsx"
                output_filepath = os.path.join(output_folder, output_excel_filename)

                try:
                    print(f"Attempting to write parsed data to: {output_filepath}")
                    write_to_excel(parsed_data, output_filepath, sheet_name_for_excel) # Use the shorter sheet name
                    print(f"Successfully wrote data from '{pdf_file}' to '{output_filepath}'")
                except Exception as e:
                    print(f"Error writing parsed data to Excel for '{pdf_file}': {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"Warning: No data parsed from {invoice_type} invoice: '{pdf_file}'.")

        except Exception as e:
            print(f"Error processing '{pdf_file}': {e}")
            import traceback
            traceback.print_exc() 

    print("\n--- PDF processing complete ---")

if __name__ == "__main__":
    main()
