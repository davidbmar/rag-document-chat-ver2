#!/usr/bin/env python3
"""
Debug script to test PDF extraction methods
"""

import sys
import os
import logging

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.config import config
from src.processing.document_processor import DocumentExtractor

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_pdf_extraction():
    """Test PDF extraction with current configuration"""
    
    print("=== PDF Extraction Debug ===")
    print(f"Config PDF Library: {config.pdf_library}")
    
    # Test PyMuPDF availability
    try:
        import fitz
        print(f"✅ PyMuPDF available: version {fitz.version}")
        has_pymupdf = True
    except ImportError:
        print("❌ PyMuPDF not available")
        has_pymupdf = False
    
    # Test PyPDF2 availability
    try:
        import PyPDF2
        print(f"✅ PyPDF2 available")
        has_pypdf2 = True
    except ImportError:
        try:
            import pypdf as PyPDF2
            print(f"✅ pypdf available (as PyPDF2)")
            has_pypdf2 = True
        except ImportError:
            print("❌ Neither PyPDF2 nor pypdf available")
            has_pypdf2 = False
    
    # Test with a sample PDF if available
    test_pdf_path = "test_documents/CapsuleHandbookVersion2024.Jan1.pdf"
    if os.path.exists(test_pdf_path):
        print(f"\n=== Testing with {test_pdf_path} ===")
        
        try:
            with open(test_pdf_path, 'rb') as f:
                pdf_content = f.read()
            
            extractor = DocumentExtractor()
            text = extractor.extract_text(pdf_content, test_pdf_path)
            
            print(f"✅ Extraction successful!")
            print(f"📄 Text length: {len(text)} characters")
            print(f"📝 First 200 characters:")
            print(repr(text[:200]))
            
            # Check for common spacing issues
            spacing_issues = []
            if " m em ber" in text or "m em ber" in text:
                spacing_issues.append("'member' spacing issue found")
            if " tim e" in text or "tim e" in text:
                spacing_issues.append("'time' spacing issue found")
            
            if spacing_issues:
                print("⚠️  Spacing issues detected:")
                for issue in spacing_issues:
                    print(f"   - {issue}")
            else:
                print("✅ No obvious spacing issues detected in first 200 chars")
                
        except Exception as e:
            print(f"❌ Extraction failed: {e}")
    else:
        print(f"\n❌ Test PDF not found at {test_pdf_path}")
    
    print(f"\n=== Environment Info ===")
    print(f"Python executable: {sys.executable}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"VIRTUAL_ENV: {os.environ.get('VIRTUAL_ENV', 'Not set')}")

if __name__ == "__main__":
    test_pdf_extraction()