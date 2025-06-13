# PDF Invoice Extractor

A Python-based solution for extracting key information from PDF invoices, specifically designed to handle formats from **Flipkart** and **Amazon**. This tool parses essential details like **Order ID**, **Invoice Date**, **Total Amount**, and **Itemized Product Lists**, and exports the structured data into **Excel (.xlsx)** files.

---

## 🔍 Features

- **PDF Text Extraction**  
  Uses `PyPDF2` to extract raw text from PDF documents.

- **Flipkart Invoice Parsing**  
  Dedicated parser for Flipkart invoice layouts to extract relevant details.

- **Amazon Invoice Parsing**  
  Tailored parsing logic to handle Amazon invoices with accuracy.

- **Excel Export**  
  Saves extracted data into `.xlsx` files for easy access and analysis.

- **Modular Design**  
  Clean architecture with separate modules for reading, parsing, and processing.

---

## 📁 Project Structure


### Alternative View (YAML-style):
```yaml
.
├── input_pdfs/             # Place your PDF invoice files here
├── output_excel/           # Extracted Excel files will be saved here
├── scripts/                # Source code and scripts
│   ├── main_extractor.py       # Main script to run extraction
│   ├── pdf_reader.py           # Module for reading PDF content
│   ├── extract_flipkart.py     # Flipkart invoice parser
│   └── extract_amazon.py       # Amazon invoice parser
├── README.md               # This documentation file
└── requirements.txt        # List of dependencies


**⚙️ Setup & Installation**
Prerequisites
Python 3.x

pip – Python package installer

Installation Steps
Clone the Repository (or Set Up Manually)
If cloning:
git clone https://github.com/yourusername/pdf-invoice-extractor.git
cd pdf-invoice-extractor


**Create a Virtual Environment (Recommended)**
python -m venv venv


**Activate the Virtual Environment**
.\venv\Scripts\activate


**Install Dependencies**
pip install -r requirements.txt


**🚀 Usage**
Add PDF Invoices
Place your Flipkart and Amazon invoice PDFs into the input_pdfs/ directory.

Run the Extractor
From the project root:
python scripts/main_extractor.py
Check the Output
Extracted data will be saved in the output_excel/ directory as .xlsx files.


**Troubleshooting**
PDF Read Errors
If you see PyPDF2.errors.PdfReadError, the PDF might be encrypted or invalid. Ensure it's not password-protected.

No Data Extracted
The invoice format may differ. To debug, add print(raw_text) in main_extractor.py and adjust the regex patterns in extract_flipkart.py or extract_amazon.py.

Module Not Found Errors

Ensure the virtual environment is activated.

Verify all required files are in the scripts/ directory.

Check that dependencies are installed using:
pip install -r requirements.txt
