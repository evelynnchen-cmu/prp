import fitz  # PyMuPDF
import re

class PDFParser:
    """Extract text from PDFs and clean artifacts"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        
    def extract_text(self) -> str:
        """Extract all text from PDF"""
        full_text = ""
        for page in self.doc:
            full_text += page.get_text()
        return self._clean_text(full_text)
    
    def _clean_text(self, text: str) -> str:
        """Remove artifacts and normalize whitespace"""
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove non-ASCII characters
        text = re.sub(r'[^\x00-\x7F]+', '', text)
        # Remove page numbers and headers/footers (common patterns)
        text = re.sub(r'\n\d+\n', '\n', text)
        return text.strip()
    
    def get_metadata(self) -> dict:
        """Extract PDF metadata"""
        return {
            'num_pages': len(self.doc),
            'title': self.doc.metadata.get('title', ''),
            'author': self.doc.metadata.get('author', '')
        }
