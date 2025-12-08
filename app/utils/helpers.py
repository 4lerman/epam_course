import base64


def format_image_data_uri(b64_string):
    """
    Detects MIME type from base64 string and returns proper Data URI.
    """
    if not b64_string:
        return ""

    try:
        header = base64.b64decode(b64_string[:20])
        if header.startswith(b'\x89PNG\r\n\x1a\n'):
            mime = "image/png"
        elif header.startswith(b'\xff\xd8\xff'):
            mime = "image/jpeg"
        elif header.startswith(b'GIF87a') or header.startswith(b'GIF89a'):
            mime = "image/gif"
        elif b'WEBP' in header:
            mime = "image/webp"
        else:
            mime = "image/jpeg"  # Default fallback

        return f"data:{mime};base64,{b64_string}"
    except Exception:
        return f"data:image/jpeg;base64,{b64_string}"


def get_images_base64(chunks):
    images_b64 = []
    for chunk in chunks:
        if "CompositeElement" in str(type(chunk)):
            chunks_els = chunk.metadata.orig_elements
            for el in chunks_els:
                if 'Image' in str(type(el)) and el.metadata.image_base64:
                    images_b64.append(el.metadata.image_base64)
    return images_b64
