"""
Author: Qigqi
FilePath: /tools/process_papers.py
Description: Extract images and their corresponding context and captions from LaTeX source files.
Copyright (c) 2024 by Qigqi, All Rights Reserved.
"""

import json
import os
import shutil
import tarfile
from glob import glob
from pathlib import Path

import fitz
import regex as re
from tqdm import tqdm

def move_file(source_path, target_folder):
    """
    Move a file from source_path to target_folder, handling filename conflicts.

    Args:
        source_path (str): Path to the source file.
        target_folder (str): Path to the target folder.

    Returns:
        str: Path to the moved file.
    """
    if os.path.exists(source_path):
        count = 1
        file_name = Path(source_path).name
        base_name = Path(source_path).stem
        file_ext = Path(source_path).suffix
        target_path = os.path.join(target_folder, file_name)
        while os.path.exists(target_path):
            target_path = os.path.join(target_folder, f'{base_name}_{count}{file_ext}')
            count += 1
        shutil.move(source_path, target_path)
        return target_path
    else:
        print(f'{source_path} does not exist!')

def write_list_to_json(data_list, file_path):
    """
    Write a list of dictionaries to a JSON file.

    Args:
        data_list (list): List of dictionaries to be written to JSON.
        file_path (str): Path to the output JSON file.
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as json_file:
            json.dump(data_list, json_file, ensure_ascii=False, indent=4)
        print(f"Data successfully written to {file_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

def process_pdf(file_path, pdfs_folder='pdf', image_folder='image'):
    """
    Convert a PDF file to PNG and move both the PDF and PNG to specified folders.

    Args:
        file_path (str): Path to the PDF file.
        pdfs_folder (str): Folder to move the PDF file.
        image_folder (str): Folder to save the PNG image.

    Returns:
        list: A list containing paths to the PDF and PNG files.
    """
    if os.path.exists(file_path):
        base_name = Path(file_path).stem
        count = 1
        png_path = os.path.join(image_folder, f'{base_name}.png')
        while os.path.exists(png_path):
            png_path = os.path.join(image_folder, f'{base_name}_{count}.png')
            count += 1
        try:
            with fitz.open(file_path) as pdf_document:
                page = pdf_document.load_page(0)
                pix = page.get_pixmap(dpi=400)
                pix.save(png_path)
        except Exception as e:
            print(f"Error opening or processing the PDF file: {e}")
            return None
        
        pdf_path = move_file(file_path, pdfs_folder)
        return [pdf_path, png_path]
    else:
        print(f"File does not exist: {file_path}")
        return None

def move_files_to_root(root_folder, title):
    """
    Move all files from subdirectories to the root folder, appending the title to filenames.

    Args:
        root_folder (str): Path to the root folder.
        title (str): Title to prepend to the filenames.
    """
    try:
        for dirpath, _, filenames in os.walk(root_folder):
            if dirpath == root_folder:
                continue  # Skip the root directory itself

            for filename in filenames:
                source_path = os.path.join(dirpath, filename)
                target_path = os.path.join(root_folder, title + '$' + filename)

                # Modify filename if target path already exists
                if os.path.exists(target_path):
                    base, extension = os.path.splitext(filename)
                    counter = 1
                    while os.path.exists(target_path):
                        new_filename = f"{base}_{counter}{extension}"
                        target_path = os.path.join(root_folder, new_filename)
                        counter += 1
                # Move the file to the root folder
                shutil.move(source_path, target_path)
    except Exception as e:
        print(e)

    # Remove empty subdirectories
    for dirpath, dirnames, _ in os.walk(root_folder, topdown=False):
        for dirname in dirnames:
            full_dirpath = os.path.join(dirpath, dirname)
            if not os.listdir(full_dirpath):
                os.rmdir(full_dirpath)

def extract_figure_info(tex_path, title):
    """
    Extract figure paths, captions, and surrounding context from a LaTeX file.

    Args:
        tex_path (str): Path to the LaTeX source file.
        title (str): Title to prepend to figure filenames.

    Returns:
        list: List of dictionaries containing figure information.
    """
    folder_path = Path(tex_path).parent
    with open(tex_path, 'r', errors='ignore') as file:
        content = file.read()

    # Regular expression to match \begin{figure} ... \end{figure} environments
    figure_pattern = re.compile(r'\\begin{figure}.*?\\end{figure}', re.DOTALL)
    figures = figure_pattern.findall(content)

    results = []
    try:
        for figure in figures:
            figures_path_list = re.findall(r'\\includegraphics.*?\{(.*?)\}', figure)
            for idx, figure_path in enumerate(figures_path_list):
                file_name = Path(figure_path).name
                figures_path_list[idx] = os.path.join(folder_path, title + '$' + file_name)
            figure_caption = re.search(r'\\caption\{(.*?)\}', figure)
            figure_caption = figure_caption.group(1) if figure_caption else ''
            label_match = re.search(r'\\label\{(.*?)\}', figure)
            label = label_match.group(1) if label_match else None

            if label:
                # Find all paragraphs that reference this label
                ref_pattern = re.compile(rf'\\ref\{{{label}\}}')
                paragraphs = re.split(r'\n\s*\n', content)
                related_paragraphs = [para for para in paragraphs if ref_pattern.search(para)]
                content_paragraphs = "\n\n".join(related_paragraphs)
            else:
                # Get the previous and next non-empty paragraphs
                figure_start = content.find(figure)
                pre_content = content[:figure_start]
                post_content = content[figure_start + len(figure):]

                # Split into paragraphs and remove empty ones
                pre_paragraphs = [para for para in re.split(r'\n\s*\n', pre_content) if para.strip()]
                post_paragraphs = [para for para in re.split(r'\n\s*\n', post_content) if para.strip()]

                prev_paragraph = pre_paragraphs[-1] if pre_paragraphs else ''
                next_paragraph = post_paragraphs[0] if post_paragraphs else ''
                prev_paragraph = prev_paragraph.strip()
                next_paragraph = next_paragraph.strip()

                content_paragraphs = "\n\n".join(filter(None, [prev_paragraph, next_paragraph]))

            results.append({
                'figure_path': list(set(figures_path_list)),
                'figure_caption': figure_caption,
                'content': content_paragraphs
            })
    except Exception as e:
        print(e)
    return results

def extract_figure_path_content_caption_paragraphs(tex_path, title):
    """
    Extract image paths, captions, and paragraphs from a LaTeX file, including surrounding content.

    Args:
        tex_path (str): Path to the LaTeX source file.
        title (str): Title to prepend to figure filenames.

    Returns:
        list: List of dictionaries containing figure paths, captions, and surrounding context.
    """
    temp_folder = os.path.dirname(tex_path)
    with open(tex_path, 'r', errors='ignore') as file:
        latex_text = file.read()
    # Define regex patterns
    figure_pattern = re.compile(r'(.*?)(\\begin{figure}.*?\\end{figure})(.*)', re.DOTALL)
    image_pattern = re.compile(r'\\includegraphics(\[.*\])?\{(.+)\}')
    caption_pattern = re.compile(r'\\caption\{(.+)\}', re.DOTALL)
    label_pattern = re.compile(r'\\label\{(.+)\}')

    # Find all matching figure environments
    matches = list(figure_pattern.finditer(latex_text))

    results = []

    for match in matches:
        try:
            content = ''
            figures_path_list = []

            preceding_text = match.group(1).strip()
            figures_path = image_pattern.findall(match.group(2).strip())

            for figure_path in figures_path:
                file_name = Path(figure_path[-1]).name
                figures_path_list.append(os.path.join(temp_folder, title + '$' + file_name))
            figure_caption = caption_pattern.findall(match.group(2).strip())
            following_text = match.group(3).strip()
            figure_label = label_pattern.findall(match.group(2).strip())
            if len(figure_label) != 0:
                paragraph_pattern = re.compile(r'([^\n]*?Figure~\\ref{' + figure_label[0] + r'}[^\n]*(?:\n\n|\Z))', re.DOTALL)
                a = paragraph_pattern.findall(match.string)
                content = a
            if len(content) == 0:
                # Find preceding and following paragraphs
                preceding_paragraph = preceding_text.split('\n\n')[-1].strip() if preceding_text else ''
                following_paragraph = following_text.split('\n\n')[0].strip() if following_text else ''
                content = preceding_paragraph + following_paragraph

            results.append({
                'figure_path': list(set(figures_path_list)),
                'figure_caption': figure_caption,
                'content': content
            })
        except re.error as e:
            print(f'Error {e}.')
    return results

def move_get_path(figure_path, source_folder):
    """
    Handle files with different extensions and move them to appropriate folders.

    Args:
        figure_path (str): Path to the figure file.
        source_folder (str): Source folder where the figure file is located.

    Returns:
        list: A list containing paths to the PDF and image files.
    """
    pdf_folder = os.path.join(source_folder, 'chartpdf')
    image_folder = os.path.join(source_folder, 'chartimg')

    os.makedirs(pdf_folder, exist_ok=True)
    os.makedirs(image_folder, exist_ok=True)

    image_ext = ['.jpg', '.jpeg', '.png']
    file_exts = ['.png', '.pdf', '.jpg', '.jpeg']

    file_ext = Path(figure_path).suffix
    if file_ext == '.pdf' and os.path.exists(figure_path):
        pdf_image_pairs_path = process_pdf(figure_path, pdf_folder, image_folder)
        return [pdf_image_pairs_path[0], pdf_image_pairs_path[1]]
    elif file_ext in image_ext and os.path.exists(figure_path):
        image_path = move_file(figure_path, image_folder)
        return ['None', image_path]
    elif len(file_ext) == 0:
        file, _ = os.path.splitext(figure_path)
        for ext in file_exts:
            figure_path = file + ext
            is_exists = os.path.exists(figure_path)
            if os.path.exists(figure_path):
                image_path = move_get_path(figure_path, source_folder)
                return image_path

def main():
    version = 4
    """
    1:cvpr, eccv, iccv
    2:9
    3:
    4:nips iclr chi
    """
    tar_gz_folder = f'tex_source_v{version}'  # Path to the .tar.gz files
    output_json_file = f'chart_caption_raw_v{version}.json'  # Path to the output JSON file
    temp_extract_folder = 'temp_extract_folder'  # Temporary extraction folder
    source_path = f'chartdata_v{version}'
    error_file = 0
    os.makedirs(temp_extract_folder, exist_ok=True)
    all_extracted_info = []
    shutil.rmtree(temp_extract_folder)

    # Iterate through all .tar.gz files
    for index, tar_file in enumerate(tqdm(os.listdir(tar_gz_folder), desc='Processing papers.....')):
        if tar_file.endswith('.tar.gz'):
            tar_path = os.path.join(tar_gz_folder, tar_file)
            paper_title = tar_file.split('.')[0]
            # Extract .tar.gz file to temporary folder
            try:
                with tarfile.open(tar_path, 'r:gz') as tar:
                    tar.extractall(temp_extract_folder)
            except (tarfile.ReadError, EOFError, tarfile.TarError) as e:
                print(f"Error extracting {tar_path}: {e}")
                error_file += 1
                continue

            move_files_to_root(temp_extract_folder, paper_title)
            tex_files = glob(os.path.join(temp_extract_folder, '*.tex'), recursive=True)

            for file in tex_files:
                try:
                    extracted_infos = extract_figure_info(file, paper_title)
                    for extracted_info in extracted_infos:
                        for figure_path in extracted_info['figure_path']:
                            if len(figure_path) != 0:
                                paths = move_get_path(figure_path, source_path)
                                all_extracted_info.append({
                                    'title': paper_title,
                                    'pdf_path': paths[0],
                                    'image_path': paths[-1],
                                    'caption': extracted_info['figure_caption'],
                                    'content': extracted_info['content']
                                })
                            else:
                                pass
                except (EOFError, TypeError, IndexError) as e:
                    continue
            # Clear temporary folder
            shutil.rmtree(temp_extract_folder)
            os.makedirs(temp_extract_folder, exist_ok=True)
    write_list_to_json(all_extracted_info, output_json_file)
    # Clean up temporary folder
    shutil.rmtree(temp_extract_folder)
    print("PDF file extraction and caption extraction has been completed!")
    print(f'Number of files not ending with .gz: {error_file}.')

if __name__ == '__main__':
    main()
