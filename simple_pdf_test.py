#!/usr/bin/env python3
"""
Simple test to verify PyMuPDF is working for PDF extraction
"""

import sys
import os
import logging

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.processing.document_processor import DocumentExtractor
from src.core.config import config

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

def test_pdf_extraction():
    """Test PDF extraction directly"""
    
    print("=== Simple PDF Extraction Test ===")
    print(f"🔧 Config PDF Library: {config.pdf_library}")
    
    # Test PDF file
    test_pdf_path = "test_documents/CapsuleHandbookVersion2024.Jan1.pdf"
    
    if not os.path.exists(test_pdf_path):
        print(f"❌ Test PDF not found at {test_pdf_path}")
        return False
    
    try:
        with open(test_pdf_path, 'rb') as f:
            pdf_content = f.read()
        
        print(f"📁 PDF file size: {len(pdf_content):,} bytes")
        
        # Extract text
        extractor = DocumentExtractor()
        text = extractor.extract_text(pdf_content, "test.pdf")
        
        print(f"📄 Extracted text length: {len(text):,} characters")
        print(f"📝 First 300 characters:")
        print("-" * 50)
        print(repr(text[:300]))
        print("-" * 50)
        
        # Check for specific content that should be extracted properly
        checks = [
            ("TEAM MEMBER HANDBOOK", "Should contain 'TEAM MEMBER HANDBOOK'"),
            ("TABLE OF CONTENTS", "Should contain 'TABLE OF CONTENTS'"),
            ("COMPENSATION", "Should contain 'COMPENSATION'"),
            ("Employment Categories", "Should contain 'Employment Categories'"),
        ]
        
        all_passed = True
        print("\n🔍 Content verification:")
        
        for content, description in checks:
            if content in text:
                print(f"✅ {description}")
            else:
                print(f"❌ {description}")
                all_passed = False
        
        # Check for spacing issues
        print("\n⚠️  Spacing issue checks:")
        spacing_issues = [
            ("m em ber", "member spacing"),
            ("tim e", "time spacing"),
            ("com pan y", "company spacing"),
            ("pol ic y", "policy spacing"),
            ("hand book", "handbook spacing"),
        ]
        
        spacing_problems = []
        for issue, description in spacing_issues:
            if issue in text:
                print(f"❌ Found {description} issue: '{issue}'")
                spacing_problems.append(description)
            else:
                print(f"✅ No {description} issues detected")
        
        if spacing_problems:
            print(f"\n⚠️  {len(spacing_problems)} spacing issues found:")
            for problem in spacing_problems:
                print(f"   - {problem}")
            return False
        else:
            print("\n✅ No spacing issues detected!")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print(f"🐍 Python executable: {sys.executable}")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"🔧 Virtual environment: {os.environ.get('VIRTUAL_ENV', 'Not set')}")
    print()
    
    success = test_pdf_extraction()
    
    if success:
        print("\n🎉 PDF extraction test passed! PyMuPDF is working correctly.")
    else:
        print("\n💥 PDF extraction test failed!")
    
    sys.exit(0 if success else 1)