import PyPDF2
import os

def extract_text_from_pdf(pdf_path):
    """
    Extracts all text from a given PDF file.

    Args:
        pdf_path (str): The full path to the PDF file.

    Returns:
        str: A single string containing all extracted text,
             or None if an error occurs during extraction.
    """
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            # Create a PdfReader object to read the PDF
            reader = PyPDF2.PdfReader(file)
            
            # Iterate through each page of the PDF
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                # Extract text from the current page and append it
                # A newline character is added to separate text from different pages,
                # which can help in distinguishing content across pages during parsing.
                text += page.extract_text() + "\n" 
    except PyPDF2.errors.PdfReadError as e:
        print(f"Error reading PDF '{pdf_path}': {e}. The file might be encrypted or corrupted.")
        return None
    except FileNotFoundError:
        print(f"Error: PDF file not found at '{pdf_path}'")
        return None
    except Exception as e:
        # Catch any other unexpected errors during text extraction
        print(f"An unexpected error occurred while extracting text from '{pdf_path}': {e}")
        return None
    return text

# This block allows you to test the pdf_reader.py script independently.
# It will only run if you execute this file directly (e.g., python scripts/pdf_reader.py)
# and not when it's imported by main_extractor.py or other parsing scripts.
if __name__ == "__main__":
    # Define the path to a sample PDF for testing purposes.
    # It assumes a project structure where 'scripts' is a sibling to 'input_pdfs'.
    script_dir = os.path.dirname(__file__)
    project_root = os.path.abspath(os.path.join(script_dir, '..'))
    input_folder = os.path.join(project_root, 'input_pdfs')

    # IMPORTANT: Change 'sample_invoice.pdf' to the actual name of a PDF file
    # that you have placed in your 'input_pdfs' folder for testing.
    sample_pdf_filename = '243.pdf' # <--- UPDATED THIS LINE
    sample_pdf_path = os.path.join(input_folder, sample_pdf_filename)

    print(f"--- Testing PDF Text Extraction ---")
    print(f"Attempting to extract text from: '{sample_pdf_path}'")

    if os.path.exists(sample_pdf_path):
        extracted_text = extract_text_from_pdf(sample_pdf_path)
        
        if extracted_text:
            print("\n--- Extracted Text (First 1000 characters) ---")
            print(extracted_text) # Print only the first 1000 characters to avoid flooding the console
            print("\n... (rest of the text not shown)")
            print(f"\nSuccessfully extracted {len(extracted_text)} characters.")
        else:
            print(f"No text extracted from '{sample_pdf_path}'. Please check the error messages above.")
    else:
        print(f"\nError: Sample PDF '{sample_pdf_filename}' not found in '{input_folder}'.")
        print("Please place a sample PDF file there to test this script,")
        print("or update the 'sample_pdf_filename' variable in this script to match your file.")

