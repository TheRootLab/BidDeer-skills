"""Safe synthetic text-layer PDFs with embedded raster image objects."""

import zlib
from pathlib import Path


ImageSpec = tuple[int, int, tuple[int, int, int]]


def make_test_pdf(
    output_path: str,
    image_specs: list[ImageSpec] | None = None,
    *,
    text: str = "Hello World",
) -> Path:
    return make_multi_page_test_pdf(
        output_path,
        [image_specs if image_specs is not None else [(4, 4, (255, 0, 0))]],
        page_texts=[text],
    )


def make_multi_page_test_pdf(
    output_path: str,
    page_image_specs: list[list[ImageSpec]],
    *,
    page_texts: list[str] | None = None,
) -> Path:
    page_texts = page_texts or ["Hello World"] * len(page_image_specs)
    images = [
        [
            (width, height, zlib.compress(bytes(color) * (width * height)))
            for width, height, color in specs
        ]
        for specs in page_image_specs
    ]
    page_count = len(images)
    first_image_object = 3 + 2 * page_count
    image_count = sum(len(page) for page in images)
    font_object = first_image_object + image_count
    objects: list[bytes] = []

    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    page_refs = " ".join(f"{3 + 2 * index} 0 R" for index in range(page_count))
    objects.append(
        f"<< /Type /Pages /Kids [{page_refs}] /Count {page_count} >>".encode()
    )

    image_offset = 0
    for page_index, page_images in enumerate(images):
        page_object = 3 + 2 * page_index
        content_object = page_object + 1
        xobjects = " ".join(
            f"/Im{image_index} {first_image_object + image_offset + image_index} 0 R"
            for image_index in range(len(page_images))
        )
        resources = (
            f"<< /XObject << {xobjects} >> /Font << /F1 {font_object} 0 R >> >>"
        )
        objects.append(
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                f"/Contents {content_object} 0 R /Resources {resources} >>"
            ).encode()
        )

        content = []
        text = page_texts[page_index] if page_index < len(page_texts) else ""
        if text:
            content.append(
                b"BT /F1 12 Tf 50 750 Td (%s) Tj ET"
                % text.encode("ascii", errors="replace")
            )
        for image_index, (width, height, _data) in enumerate(page_images):
            content.append(
                b"q %d 0 0 %d %d 700 cm /Im%d Do Q"
                % (width, height, 50 + image_index * 60, image_index)
            )
        stream = b"\n".join(content)
        objects.append(
            b"<< /Length %d >>\nstream\n%s\nendstream"
            % (len(stream), stream)
        )
        image_offset += len(page_images)

    for page_images in images:
        for width, height, data in page_images:
            objects.append(
                (
                    b"<< /Type /XObject /Subtype /Image /Width %d /Height %d "
                    b"/ColorSpace /DeviceRGB /BitsPerComponent 8 /Length %d "
                    b"/Filter /FlateDecode >>\nstream\n%s\nendstream"
                )
                % (width, height, len(data), data)
            )

    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for object_number, body in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{object_number} 0 obj\n".encode())
        output.extend(body)
        output.extend(b"\nendobj\n")
    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode())
    output.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode()
    )

    path = Path(output_path)
    path.write_bytes(output)
    return path
