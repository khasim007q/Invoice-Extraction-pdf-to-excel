PDF Invoice Extractor
This project provides a Python-based solution for extracting key information from PDF invoices, specifically designed to handle formats from Flipkart and Amazon. It parses details such as Order ID, Invoice Date, Total Amount, and itemized product lists, then saves this structured data into Excel files.

Features
PDF Text Extraction: Utilizes PyPDF2 to extract raw text from PDF documents.

Flipkart Invoice Parsing: Includes a dedicated parser for Flipkart invoice layouts, extracting order details and item specifics.

Amazon Invoice Parsing: Features a parser designed to handle Amazon invoice formats, extracting similar details.

Excel Export: Saves the extracted and structured invoice data into .xlsx files for easy analysis and record-keeping.

Modular Design: The project is structured into separate modules (pdf_reader.py, extract_flipkart.py, extract_amazon.py) for clarity and maintainability.

Project Structure
.
├── input_pdfs/
│   └── (Your PDF invoice files go here)
├── output_excel/
│   └── (Extracted Excel files will be saved here)
├── scripts/
│   ├── main_extractor.py
│   ├── pdf_reader.py
│   ├── extract_flipkart.py
│   └── extract_amazon.py
├── README.md
└── requirements.txt

Setup and Installation
Prerequisites
Python 3.x

pip (Python package installer)

Installation Steps
Clone the Repository (or create the project structure manually):

If you're setting up a new project on your local machine, create the directory structure as shown above.

Navigate to the Project Directory:

cd path/to/your/project/Aaans Private limited project

Create a Virtual Environment (Recommended):

This helps manage dependencies and avoids conflicts with other Python projects.

python -m venv venv

Activate the Virtual Environment:

On Windows:

.\venv\Scripts\activate

On macOS/Linux:

source venv/bin/activate

Install Dependencies:

Install the required Python packages using the requirements.txt file provided.

pip install -r requirements.txt

Usage
Place PDF Invoices: Put your Amazon and Flipkart PDF invoice files into the input_pdfs/ directory.

Run the Extractor: Execute the main script from the project root directory.

python scripts/main_extractor.py

View Output: The extracted data, organized into Excel files, will be saved in the output_excel/ directory. Each processed PDF will have its own corresponding Excel file.

Troubleshooting
PDF Read Errors: If you encounter errors like PyPDF2.errors.PdfReadError, the PDF might be encrypted or corrupted. Ensure the PDFs are not password-protected and are valid.

No Data Parsed: If the script runs but no data is extracted, or the extracted data is incorrect, the PDF's layout might differ from the patterns defined in extract_flipkart.py or extract_amazon.py. You may need to inspect the raw extracted text (by adding print(raw_text) in main_extractor.py) and adjust the regular expressions in the respective parsing scripts.

Module Not Found Errors: Ensure your virtual environment is activated and all dependencies are installed (pip install -r requirements.txt). Also, verify that pdf_reader.py, extract_flipkart.py, and extract_amazon.py are located within the scripts/ directory.

Contributing
Feel free to fork this repository, open issues, and submit pull requests if you have improvements or encounter bugs.
