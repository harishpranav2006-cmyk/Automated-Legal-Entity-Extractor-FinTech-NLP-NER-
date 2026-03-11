"""
generate_test_pdf.py
Generates a synthetic held-out contract PDF for end-to-end testing.
Run: python generate_test_pdf.py
"""
from pathlib import Path

CONTRACT_TEXT = """SERVICES AGREEMENT

This Services Agreement (the "Agreement") is entered into as of January 15, 2024
(the "Effective Date") by and between:

    Acme Corporation ("Client"), a corporation organized under the laws of the
    State of Delaware, and

    Nexus Solutions Ltd ("Service Provider"), a company incorporated under the
    laws of the State of New York.

TERM

This Agreement shall commence on January 15, 2024, and shall continue in full
force and effect until January 15, 2026 (the "Termination Date"), unless earlier
terminated in accordance with the provisions hereof.

CONSIDERATION

In consideration of the services to be rendered, Client agrees to pay Service
Provider a total fee of $5,000,000.00 (Five Million Dollars) payable in quarterly
installments.

GOVERNING LAW

This Agreement shall be governed by and construed in accordance with the laws of
the State of New York, without regard to its conflict of law provisions.

IN WITNESS WHEREOF, the parties have executed this Agreement as of the date first
written above.

ACME CORPORATION                    NEXUS SOLUTIONS LTD

By: _______________________         By: _______________________
Name: John Smith                    Name: Sarah Johnson
Title: Chief Executive Officer      Title: Managing Director
Date: January 15, 2024              Date: January 15, 2024
"""

def create_text_pdf(text: str, output_path: str):
    """Create a minimal valid text-layer PDF without external libraries."""
    lines = text.split('\n')
    
    # Build PDF content stream
    stream_lines = []
    stream_lines.append("BT")
    stream_lines.append("/F1 11 Tf")
    stream_lines.append("50 750 Td")
    stream_lines.append("14 TL")  # leading

    for line in lines:
        # Escape special PDF chars
        safe = line.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
        stream_lines.append(f"({safe}) Tj T*")

    stream_lines.append("ET")
    stream_content = "\n".join(stream_lines)
    stream_bytes = stream_content.encode("latin-1", errors="replace")

    # Build PDF objects
    objects = []

    # Object 1: Catalog
    objects.append(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj")

    # Object 2: Pages
    objects.append(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj")

    # Object 3: Page
    objects.append(
        b"3 0 obj\n"
        b"<< /Type /Page /Parent 2 0 R\n"
        b"   /MediaBox [0 0 612 792]\n"
        b"   /Contents 4 0 R\n"
        b"   /Resources << /Font << /F1 5 0 R >> >> >>\n"
        b"endobj"
    )

    # Object 4: Content stream
    stream_len = len(stream_bytes)
    obj4 = (
        f"4 0 obj\n<< /Length {stream_len} >>\nstream\n".encode()
        + stream_bytes
        + b"\nendstream\nendobj"
    )
    objects.append(obj4)

    # Object 5: Font
    objects.append(
        b"5 0 obj\n"
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>\n"
        b"endobj"
    )

    # Build PDF bytes
    pdf = b"%PDF-1.4\n"
    offsets = []
    for obj in objects:
        offsets.append(len(pdf))
        pdf += obj + b"\n"

    # Cross-reference table
    xref_offset = len(pdf)
    pdf += b"xref\n"
    pdf += f"0 {len(objects) + 1}\n".encode()
    pdf += b"0000000000 65535 f \n"
    for off in offsets:
        pdf += f"{off:010d} 00000 n \n".encode()

    pdf += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    ).encode()

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(pdf)
    print(f"Created: {output_path}")


if __name__ == "__main__":
    create_text_pdf(CONTRACT_TEXT, "data/test/held_out_contract.pdf")
