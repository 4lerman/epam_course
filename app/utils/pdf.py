import os
from unstructured.partition.pdf import partition_pdf

def process_pdf(pdf_path, image_output_dir):
    raw_pdf_elements = partition_pdf(
        filename=pdf_path,
        extract_images_in_pdf=True,
        infer_table_structure=True,
        chunking_strategy="by_title",
        max_characters=4000,
        new_after_n_chars=3800,
        combine_text_under_n_chars=2000,
        image_output_dir_path=image_output_dir,
    )
    
    tables = []
    texts = []

    for element in raw_pdf_elements:
        if "unstructured.documents.elements.Table" in str(type(element)):
            tables.append(element)
        elif "unstructured.documents.elements.CompositeElement" in str(type(element)):
            texts.append(element)
            
    return raw_pdf_elements, texts, tables
