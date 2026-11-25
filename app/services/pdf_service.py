import fitz  # PyMuPDF is imported using the name fitz.


def extract_pdf_text(pdf_bytes: bytes):
    """
    Extract text from every page of an uploaded PDF.
    """

    pages = []

    try:
        with fitz.open(stream=pdf_bytes, filetype="pdf") as pdf_document:

            # Check password protection
            if pdf_document.is_encrypted:
                raise ValueError("Password-protected PDFs are not supported.")

            total_pages = len(pdf_document)

            # Read each page
            for page_number, page in enumerate(pdf_document, start=1):

                extracted_text = page.get_text("text").strip()

                pages.append(
                    {
                        "page_number": page_number,
                        "text": extracted_text,
                        "character_count": len(extracted_text),
                    }
                )

            full_text = "\n\n".join(page["text"] for page in pages if page["text"])

            if not full_text.strip():
                raise ValueError(
                    "No extractable text found. "
                    "This may be a scanned PDF requiring OCR."
                )

            return {
                "total_pages": total_pages,
                "total_characters": len(full_text),
                "full_text": full_text,
                "pages": pages,
            }

    except ValueError:
        raise

    except Exception as error:
        raise ValueError(f"Unable to process PDF: {str(error)}")
