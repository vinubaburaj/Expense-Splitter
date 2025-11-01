"""
PDF Processing Service for extracting text from PDF files.

This module provides functionality to extract text from PDF files using both
direct text extraction and OCR for image-based content.
"""

import io
import logging
from typing import List, Optional, Union
from pathlib import Path

import pytesseract
from PIL import Image
import PyPDF2
from pypdf import PdfReader
import pdf2image

logger = logging.getLogger(__name__)


class PDFProcessingError(Exception):
    """Custom exception for PDF processing errors."""
    pass


class PDFProcessor:
    """
    Handles PDF text extraction using multiple methods.
    
    Supports both direct text extraction from text-based PDFs and OCR
    for image-based or scanned PDFs.
    """
    
    def __init__(self, ocr_config: Optional[str] = None):
        """
        Initialize PDFProcessor.
        
        Args:
            ocr_config: Optional Tesseract configuration string
        """
        self.ocr_config = ocr_config or '--oem 3 --psm 6'
        
    def extract_text_from_pdf(self, pdf_file: Union[str, Path, io.BytesIO]) -> str:
        """
        Extract text from PDF using direct text extraction.
        
        Args:
            pdf_file: PDF file path or BytesIO object
            
        Returns:
            Extracted text as string
            
        Raises:
            PDFProcessingError: If PDF processing fails
        """
        try:
            if isinstance(pdf_file, (str, Path)):
                with open(pdf_file, 'rb') as file:
                    return self._extract_text_from_bytes(file)
            else:
                return self._extract_text_from_bytes(pdf_file)
                
        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {str(e)}")
            raise PDFProcessingError(f"Text extraction failed: {str(e)}")
    
    def _extract_text_from_bytes(self, pdf_bytes: io.BytesIO) -> str:
        """Extract text from PDF bytes using PyPDF2."""
        text_content = []
        
        try:
            # Try with pypdf first (more modern)
            reader = PdfReader(pdf_bytes)
            for page in reader.pages:
                text_content.append(page.extract_text())
                
        except Exception:
            # Fallback to PyPDF2
            pdf_bytes.seek(0)  # Reset stream position
            reader = PyPDF2.PdfReader(pdf_bytes)
            for page in reader.pages:
                text_content.append(page.extract_text())
        
        return '\n'.join(text_content)
    
    def convert_pdf_to_images(self, pdf_file: Union[str, Path, io.BytesIO]) -> List[Image.Image]:
        """
        Convert PDF pages to images for OCR processing.
        
        Args:
            pdf_file: PDF file path or BytesIO object
            
        Returns:
            List of PIL Image objects, one per page
            
        Raises:
            PDFProcessingError: If conversion fails
        """
        try:
            if isinstance(pdf_file, (str, Path)):
                images = pdf2image.convert_from_path(pdf_file, dpi=300)
            else:
                images = pdf2image.convert_from_bytes(pdf_file.read(), dpi=300)
                
            return images
            
        except Exception as e:
            logger.error(f"Failed to convert PDF to images: {str(e)}")
            raise PDFProcessingError(f"PDF to image conversion failed: {str(e)}")
    
    def extract_text_with_ocr(self, images: List[Image.Image]) -> str:
        """
        Extract text from images using OCR.
        
        Args:
            images: List of PIL Image objects
            
        Returns:
            Extracted text as string
            
        Raises:
            PDFProcessingError: If OCR processing fails
        """
        try:
            text_content = []
            
            for i, image in enumerate(images):
                logger.info(f"Processing page {i + 1} with OCR")
                
                # Preprocess image for better OCR accuracy
                processed_image = self._preprocess_image(image)
                
                # Extract text using Tesseract
                page_text = pytesseract.image_to_string(
                    processed_image, 
                    config=self.ocr_config
                )
                
                if page_text.strip():
                    text_content.append(page_text)
                    
            return '\n'.join(text_content)
            
        except Exception as e:
            logger.error(f"OCR processing failed: {str(e)}")
            raise PDFProcessingError(f"OCR extraction failed: {str(e)}")
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image for better OCR accuracy.
        
        Args:
            image: PIL Image object
            
        Returns:
            Preprocessed PIL Image object
        """
        # Convert to grayscale
        if image.mode != 'L':
            image = image.convert('L')
        
        # Enhance contrast if needed
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.2)
        
        return image
    
    def process_pdf_comprehensive(self, pdf_file: Union[str, Path, io.BytesIO]) -> str:
        """
        Process PDF using both direct text extraction and OCR as fallback.
        
        Args:
            pdf_file: PDF file path or BytesIO object
            
        Returns:
            Extracted text as string
            
        Raises:
            PDFProcessingError: If all processing methods fail
        """
        extraction_errors = []
        
        # First try direct text extraction
        try:
            text = self.extract_text_from_pdf(pdf_file)
            if text.strip() and len(text.strip()) > 50:  # Reasonable amount of text
                logger.info("Successfully extracted text directly from PDF")
                return text
            else:
                extraction_errors.append("Direct extraction produced insufficient text")
        except PDFProcessingError as e:
            logger.warning(f"Direct text extraction failed: {str(e)}")
            extraction_errors.append(f"Direct extraction error: {str(e)}")
        except Exception as e:
            logger.warning(f"Unexpected error during direct text extraction: {str(e)}")
            extraction_errors.append(f"Direct extraction unexpected error: {str(e)}")
        
        # If direct extraction fails or produces minimal text, try OCR
        try:
            logger.info("Attempting OCR extraction as fallback")
            images = self.convert_pdf_to_images(pdf_file)
            text = self.extract_text_with_ocr(images)
            if text.strip():
                logger.info("Successfully extracted text using OCR")
                return text
            else:
                extraction_errors.append("OCR extraction produced empty text")
        except PDFProcessingError as e:
            logger.error(f"OCR extraction failed: {str(e)}")
            extraction_errors.append(f"OCR extraction error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during OCR extraction: {str(e)}")
            extraction_errors.append(f"OCR extraction unexpected error: {str(e)}")
        
        # If we get here, all methods failed
        error_details = "; ".join(extraction_errors)
        logger.error(f"All text extraction methods failed: {error_details}")
        raise PDFProcessingError(f"Failed to extract text from PDF: {error_details}")