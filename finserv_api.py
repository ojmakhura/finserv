#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 21 06:53:27 2025

@author: junior
"""
import os
import time
import requests
import fitz  # PyMuPDF
import google.generativeai as genai
import hashlib
from fastapi import FastAPI, UploadFile, File, HTTPException
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Read configuration from environment variables
SOLR_BASE_URL = os.getenv("SOLR_BASE_URL")
SOLR_CORE = os.getenv("SOLR_CORE")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Validate required environment variables
if not SOLR_BASE_URL:
    raise ValueError("SOLR_BASE_URL environment variable is required but not set")
if not SOLR_CORE:
    raise ValueError("SOLR_CORE environment variable is required but not set")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is required but not set")

# Construct full Solr URL
SOLR_URL = f"{SOLR_BASE_URL.rstrip('/')}/{SOLR_CORE}"

def calculate_file_hash(file_content):
    """Calculate SHA256 hash of file content."""
    return hashlib.sha256(file_content).hexdigest()

def check_document_exists(doc_id, verify_ssl=False):
    """Check if a document with the given ID already exists in Solr."""
    url = f"{SOLR_URL}/select"
    params = {
        "q": f"id:{doc_id}",
        "fl": "id,summary,attr_stream_source_info,file_uri",
        "wt": "json"
    }
    response = requests.get(url, params=params, verify=verify_ssl)
    response.raise_for_status()
    
    docs = response.json()["response"]["docs"]
    return len(docs) > 0, docs[0] if docs else None

def upload_pdf_to_solr(doc_id, pdf_path, verify_ssl=False):
    url = f"{SOLR_URL}/update/extract?commit=true&literal.id={doc_id}&uprefix=attr_&fmap.content=content"
    with open(pdf_path, "rb") as f:
        files = {'myfile': f}
        response = requests.post(url, files=files, verify=verify_ssl)
    response.raise_for_status()
    print(f"Uploaded PDF '{pdf_path}' to Solr as ID '{doc_id}'")

def get_extracted_text(doc_id, verify_ssl=False):
    url = f"{SOLR_URL}/select"
    params = {
        "q": f"id:{doc_id}",
        "fl": "attr_content",
        "wt": "json"
    }
    # Wait a moment for Solr to commit the document
    time.sleep(2)
    response = requests.get(url, params=params, verify=verify_ssl)
    response.raise_for_status()
    
    docs = response.json()["response"]["docs"]
    if not docs:
        raise Exception(f"No document found with ID '{doc_id}'")
    text = docs[0].get("attr_content", "")
    if isinstance(text, list):
        text = " ".join(text)
    text = text.strip()
    if not text:
        return ""
    return text

def extract_text_with_ocr(pdf_path):
    """
    Extract text from PDF using Tesseract OCR.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        str: Extracted text or empty string if extraction fails
    """
    try:
        import pytesseract
        from PIL import Image
        import io
        
        doc = fitz.open(pdf_path)
        text = ""
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            
            # Convert page to image
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better OCR quality
            img_data = pix.tobytes("png")
            
            # Convert to PIL Image
            pil_image = Image.open(io.BytesIO(img_data))
            
            # Use Tesseract to extract text
            page_text = pytesseract.image_to_string(pil_image, config='--psm 6')
            
            text += page_text + "\n"
        
        doc.close()
        return text.strip()
    
    except ImportError as e:
        print(f"Tesseract OCR dependencies not available: {e}")
        print("Please install: pip install pytesseract pillow")
        return ""
    except Exception as e:
        print(f"Error extracting text with Tesseract OCR: {e}")
        return ""

def get_extracted_text_with_ocr_fallback(doc_id, pdf_path=None, verify_ssl=False):
    """
    Get extracted text from Solr, with OCR fallback if no text found.
    
    Args:
        doc_id (str): Document ID in Solr
        pdf_path (str, optional): Path to PDF file for OCR fallback
        verify_ssl (bool): Whether to verify SSL certificates
        
    Returns:
        str: Extracted text
    """
    url = f"{SOLR_URL}/select"
    params = {
        "q": f"id:{doc_id}",
        "fl": "attr_content",
        "wt": "json"
    }
    # Wait a moment for Solr to commit the document
    time.sleep(2)
    response = requests.get(url, params=params, verify=verify_ssl)
    response.raise_for_status()
    
    docs = response.json()["response"]["docs"]
    if not docs:
        raise Exception(f"No document found with ID '{doc_id}'")
    
    text = docs[0].get("attr_content", "")
    if isinstance(text, list):
        text = " ".join(text)
    text = text.strip()
    
    # If no text found and PDF path provided, try OCR
    if not text and pdf_path and os.path.exists(pdf_path):
        print(f"No text found in Solr for {doc_id}, attempting OCR extraction...")
        text = extract_text_with_ocr(pdf_path)
        
        # If OCR found text, update Solr with the OCR-extracted content
        if text:
            try:
                update_solr_with_ocr_text(doc_id, text, verify_ssl)
                print(f"Updated Solr with OCR-extracted text for {doc_id}")
            except Exception as e:
                print(f"Failed to update Solr with OCR text: {e}")
    
    return text

def update_solr_with_ocr_text(doc_id, ocr_text, verify_ssl=False):
    """
    Update Solr document with OCR-extracted text.
    
    Args:
        doc_id (str): Document ID in Solr
        ocr_text (str): OCR-extracted text
        verify_ssl (bool): Whether to verify SSL certificates
    """
    url = f"{SOLR_URL}/update?commit=true"
    data = [
        {
            "id": doc_id,
            "attr_content": {"set": ocr_text}
        }
    ]
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=data, headers=headers, verify=verify_ssl)
    response.raise_for_status()

def update_solr_with_summary(doc_id, summary, verify_ssl=False):
    url = f"{SOLR_URL}/update?commit=true"
    data = [
        {
            "id": doc_id,
            "summary": {"set": summary}
        }
    ]
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=data, headers=headers, verify=verify_ssl)
    response.raise_for_status()
    print(f"Updated document ID '{doc_id}' with summary")
    
def summarize_document(document_text, summarizing_question=None):
    """
    Summarizes the given document text using the Gemini API.

    Args:
        document_text (str): The text content of the document to summarize.
        summarizing_question (str, optional): Custom question/prompt for summarization. 
                                            If None, uses default financial services question.

    Returns:
        str: The summarized text, or None if an error occurs during summarization.
    """
    if not document_text:
        print("No document text provided for summarization.")
        return None

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash') # Or 'gemini-1.5-flash', 'gemini-1.5-pro' for larger contexts

    # Use custom question if provided, otherwise use default financial services question
    if summarizing_question:
        prompt = f"{summarizing_question}\n\nDocument text:\n\n{document_text}\n\nSummary:"
    else:
        prompt = f"What financial or banking services are governed by the act in the following document:\n\n{document_text}. Provide a detailed list of all the services you can find.\n\nSummary:"

    try:
        response = model.generate_content(prompt)
        # Access the text from the candidate, handling cases where it might not exist
        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            summary = "".join([part.text for part in response.candidates[0].content.parts])
            return summary
        else:
            print("Gemini response did not contain a valid summary.")
            return None
    except Exception as e:
        print(f"Error summarizing document with Gemini: {e}")
        # If the error is due to safety settings, you might want to log more details:
        if hasattr(e, 'response') and hasattr(e.response, 'prompt_feedback'):
            print(f"Gemini Prompt Feedback: {e.response.prompt_feedback}")
        return None

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)

app = FastAPI()

@app.post("/upload-pdf/")
async def upload_and_process_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF file, extract text using Solr, summarize with Gemini, and store the summary.
    Avoids duplicates by using file hash as document ID.
    
    Args:
        file: The PDF file to upload
        
    Returns:
        dict: Response containing document ID, summary, and status
    """
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Read file content
    content = await file.read()
    
    # Calculate file hash to use as document ID (prevents duplicates)
    file_hash = calculate_file_hash(content)
    doc_id = f"doc_{file_hash}"
    
    # Check if document already exists
    exists, existing_doc = check_document_exists(doc_id)
    
    if exists:
        # Get the original filename from Solr
        original_filename = existing_doc.get("attr_stream_source_info", [file.filename])[0] if existing_doc.get("attr_stream_source_info") else file.filename
        existing_summary = existing_doc.get("summary", [""])[0] if existing_doc.get("summary") else ""
        
        # Check if summary exists and is not empty
        if existing_summary and existing_summary.strip():
            return {
                "status": "already_exists",
                "document_id": doc_id,
                "current_filename": file.filename,
                "original_filename": original_filename,
                "summary": existing_summary,
                "message": f"Document already exists in the system (duplicate of '{original_filename}')"
            }
        else:
            # Document exists but no summary - generate summary
            try:
                # Get extracted text from Solr
                extracted_text = get_extracted_text(doc_id)
                
                # If no text found, try OCR using the fileUri from Solr or current upload
                if not extracted_text:
                    print(f"No text found in Solr for duplicate {doc_id}, attempting OCR extraction...")
                    
                    # First try to get the file path from Solr's file_uri field
                    pdf_path = None
                    if existing_doc.get("file_uri"):
                        file_uri = existing_doc["file_uri"][0] if isinstance(existing_doc["file_uri"], list) else existing_doc["file_uri"]
                        # Remove file:// prefix if present
                        if file_uri.startswith("file://"):
                            pdf_path = file_uri[7:]  # Remove "file://" prefix
                        else:
                            pdf_path = file_uri
                        
                        if not os.path.exists(pdf_path):
                            print(f"File URI path does not exist: {pdf_path}")
                            pdf_path = None
                    
                    # If fileUri didn't work, use the current upload (save it temporarily)
                    if not pdf_path:
                        temp_ocr_path = f"/tmp/ocr_{file_hash}_{file.filename}"
                        with open(temp_ocr_path, "wb") as temp_file:
                            temp_file.write(content)
                        pdf_path = temp_ocr_path
                    
                    # Attempt OCR extraction
                    if pdf_path and os.path.exists(pdf_path):
                        extracted_text = extract_text_with_ocr(pdf_path)
                        
                        # Update Solr with OCR text if found
                        if extracted_text:
                            try:
                                update_solr_with_ocr_text(doc_id, extracted_text)
                                print(f"Updated Solr with OCR-extracted text for duplicate {doc_id}")
                            except Exception as e:
                                print(f"Failed to update Solr with OCR text: {e}")
                        
                        # Clean up temporary OCR file if we created one
                        if pdf_path.startswith("/tmp/ocr_"):
                            try:
                                os.remove(pdf_path)
                            except:
                                pass
                
                if extracted_text:
                    # Summarize the document using Gemini
                    summary = summarize_document(extracted_text)
                    
                    if summary:
                        # Update Solr with the summary
                        update_solr_with_summary(doc_id, summary)
                        
                        return {
                            "status": "summary_generated",
                            "document_id": doc_id,
                            "current_filename": file.filename,
                            "original_filename": original_filename,
                            "summary": summary,
                            "message": f"Document already exists (duplicate of '{original_filename}') - summary generated successfully"
                        }
                    else:
                        return {
                            "status": "summary_failed",
                            "document_id": doc_id,
                            "current_filename": file.filename,
                            "original_filename": original_filename,
                            "summary": "",
                            "message": f"Document already exists (duplicate of '{original_filename}') but summary generation failed"
                        }
                else:
                    return {
                        "status": "no_content",
                        "document_id": doc_id,
                        "current_filename": file.filename,
                        "original_filename": original_filename,
                        "summary": "",
                        "message": f"Document already exists (duplicate of '{original_filename}') but no text content found"
                    }
            except Exception as e:
                return {
                    "status": "error",
                    "document_id": doc_id,
                    "current_filename": file.filename,
                    "original_filename": original_filename,
                    "summary": "",
                    "message": f"Document already exists (duplicate of '{original_filename}') but error occurred while generating summary: {str(e)}"
                }
    
    # Save uploaded file temporarily
    temp_file_path = f"/tmp/{file_hash}_{file.filename}"
    
    try:
        # Save the uploaded file
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(content)
        
        # Upload PDF to Solr for text extraction
        upload_pdf_to_solr(doc_id, temp_file_path)
        
        # Get extracted text from Solr with OCR fallback
        extracted_text = get_extracted_text_with_ocr_fallback(doc_id, temp_file_path)
        
        if not extracted_text:
            raise HTTPException(status_code=400, detail="No text could be extracted from the PDF using either Solr or OCR")
        
        # Summarize the document using Gemini
        summary = summarize_document(extracted_text)
        
        if not summary:
            raise HTTPException(status_code=500, detail="Failed to generate summary")
        
        # Update Solr with the summary
        update_solr_with_summary(doc_id, summary)
        
        return {
            "status": "success",
            "document_id": doc_id,
            "filename": file.filename,
            "summary": summary,
            "message": "PDF uploaded and processed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
    
    finally:
        # Clean up temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.get("/update-summary/{doc_id}")
async def update_document_summary(doc_id: str, summarizing_question: str = None):
    """
    Extract text and update summary for an already uploaded document.
    If no text found in Solr, attempts OCR extraction (requires original file).
    
    Args:
        doc_id: The document ID in Solr
        summarizing_question: Optional custom question/prompt for summarization
        
    Returns:
        dict: Response containing document ID, updated summary, and status
    """
    try:
        # Check if document exists
        exists, existing_doc = check_document_exists(doc_id)
        
        if not exists:
            raise HTTPException(status_code=404, detail=f"Document with ID '{doc_id}' not found")
        
        # Get the original filename from Solr
        original_filename = existing_doc.get("attr_stream_source_info", ["unknown"])[0] if existing_doc.get("attr_stream_source_info") else "unknown"
        
        # Get extracted text from Solr
        extracted_text = get_extracted_text(doc_id)
        
        # If no text found, try to find the original PDF file and run OCR
        if not extracted_text or not extracted_text.strip():
            print(f"No text found in Solr for {doc_id}, attempting to locate and OCR original file...")
            
            # First try to get the file path from Solr's file_uri field
            pdf_path = None
            if existing_doc.get("file_uri"):
                file_uri = existing_doc["file_uri"][0] if isinstance(existing_doc["file_uri"], list) else existing_doc["file_uri"]
                # Remove file:// prefix if present
                if file_uri.startswith("file://"):
                    pdf_path = file_uri[7:]  # Remove "file://" prefix
                else:
                    pdf_path = file_uri
                
                if not os.path.exists(pdf_path):
                    print(f"File URI path does not exist: {pdf_path}")
                    pdf_path = None
            
            # If fileUri didn't work, try common temporary locations as fallback
            if not pdf_path:
                potential_paths = [
                    f"/tmp/{doc_id.replace('doc_', '')}_{original_filename}",
                    f"/tmp/{original_filename}",
                    f"/tmp/{doc_id}_{original_filename}",
                    f"/uploads/{original_filename}",
                    f"/uploads/{doc_id}_{original_filename}"
                ]
                
                for path in potential_paths:
                    if os.path.exists(path):
                        pdf_path = path
                        break
            
            if pdf_path:
                print(f"Found PDF file at {pdf_path}, attempting OCR extraction...")
                extracted_text = extract_text_with_ocr(pdf_path)
                
                if extracted_text:
                    # Update Solr with the OCR-extracted content
                    try:
                        update_solr_with_ocr_text(doc_id, extracted_text)
                        print(f"Updated Solr with OCR-extracted text for {doc_id}")
                    except Exception as e:
                        print(f"Failed to update Solr with OCR text: {e}")
                        # Continue with summarization even if Solr update fails
                else:
                    raise HTTPException(status_code=400, detail=f"No text content could be extracted from document ID '{doc_id}' using OCR")
            else:
                raise HTTPException(status_code=400, detail=f"No text content found for document ID '{doc_id}' and original PDF file not available for OCR (file_uri: {existing_doc.get('file_uri', 'not found')})")
        
        # At this point we should have extracted_text
        if not extracted_text or not extracted_text.strip():
            raise HTTPException(status_code=400, detail=f"No text content found for document ID '{doc_id}'")
        
        # Summarize the document using Gemini
        summary = summarize_document(extracted_text, summarizing_question)
        
        if not summary:
            raise HTTPException(status_code=500, detail="Failed to generate summary")
        
        # Update Solr with the new summary
        update_solr_with_summary(doc_id, summary)
        
        return {
            "status": "summary_updated",
            "document_id": doc_id,
            "filename": original_filename,
            "summary": summary,
            "message": f"Summary updated successfully for document '{original_filename}'"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating summary for document '{doc_id}': {str(e)}")

@app.post("/update-summary-with-file/{doc_id}")
async def update_document_summary_with_file(doc_id: str, file: UploadFile = File(...)):
    """
    Update summary for an existing document by providing the PDF file for OCR processing.
    Useful when the original file is not available and OCR is needed.
    
    Args:
        doc_id: The document ID in Solr
        file: The PDF file to process with OCR
        
    Returns:
        dict: Response containing document ID, updated summary, and status
    """
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Check if document exists
        exists, existing_doc = check_document_exists(doc_id)
        
        if not exists:
            raise HTTPException(status_code=404, detail=f"Document with ID '{doc_id}' not found")
        
        # Get the original filename from Solr
        original_filename = existing_doc.get("attr_stream_source_info", ["unknown"])[0] if existing_doc.get("attr_stream_source_info") else "unknown"
        
        # Save uploaded file temporarily
        content = await file.read()
        temp_file_path = f"/tmp/ocr_{doc_id}_{file.filename}"
        
        try:
            with open(temp_file_path, "wb") as temp_file:
                temp_file.write(content)
            
            # Extract text using OCR
            extracted_text = extract_text_with_ocr(temp_file_path)
            
            if not extracted_text or not extracted_text.strip():
                raise HTTPException(status_code=400, detail="No text could be extracted from the PDF using OCR")
            
            # Update Solr with the OCR-extracted content
            update_solr_with_ocr_text(doc_id, extracted_text)
            print(f"Updated Solr with OCR-extracted text for {doc_id}")
            
            # Summarize the document using Gemini
            summary = summarize_document(extracted_text)
            
            if not summary:
                raise HTTPException(status_code=500, detail="Failed to generate summary")
            
            # Update Solr with the new summary
            update_solr_with_summary(doc_id, summary)
            
            return {
                "status": "summary_updated_with_ocr",
                "document_id": doc_id,
                "original_filename": original_filename,
                "uploaded_filename": file.filename,
                "summary": summary,
                "message": f"Summary updated successfully for document '{original_filename}' using OCR from '{file.filename}'"
            }
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating summary with OCR for document '{doc_id}': {str(e)}")

@app.get("/document/{doc_id}")
async def get_document_info(doc_id: str):
    """
    Get information about a document including its summary.
    
    Args:
        doc_id: The document ID in Solr
        
    Returns:
        dict: Response containing document information
    """
    try:
        # Check if document exists
        exists, existing_doc = check_document_exists(doc_id)
        
        if not exists:
            raise HTTPException(status_code=404, detail=f"Document with ID '{doc_id}' not found")
        
        # Get the original filename from Solr
        original_filename = existing_doc.get("attr_stream_source_info", ["unknown"])[0] if existing_doc.get("attr_stream_source_info") else "unknown"
        existing_summary = existing_doc.get("summary", [""])[0] if existing_doc.get("summary") else ""
        
        return {
            "status": "found",
            "document_id": doc_id,
            "filename": original_filename,
            "summary": existing_summary,
            "has_summary": bool(existing_summary and existing_summary.strip()),
            "message": f"Document '{original_filename}' found"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving document '{doc_id}': {str(e)}")

