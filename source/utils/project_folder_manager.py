import os
import re
import pathlib
from librepy.jobmanager.data.settings_dao import SettingsDAO
import shutil
import uno


def sanitize_customer_name(customer_name):
    """
    Sanitize customer name for use as filesystem folder name.
    
    Args:
        customer_name (str): The raw customer name
        
    Returns:
        str: Sanitized folder name safe for filesystem use
    """
    if not customer_name:
        return "Unknown_Customer"
    
    name = customer_name.strip()
    if not name:
        return "Unknown_Customer"
    
    illegal_chars = r'[<>:"/\\|?*]'
    name = re.sub(illegal_chars, '_', name)
    
    name = re.sub(r'[^\w\s\-_.]', '_', name)
    
    name = re.sub(r'\s+', '_', name)
    
    name = name.strip('._')
    
    if not name:
        return "Unknown_Customer"
    
    if len(name) > 100:
        name = name[:97] + "..."
    
    return name


def get_project_paths(customer_name, logger):
    """
    Get or create project folder paths for a customer.
    
    Args:
        customer_name (str): The customer name
        logger: Logger instance for error reporting
        
    Returns:
        Tuple[pathlib.Path, pathlib.Path, pathlib.Path]: 
            (project_folder, photos_folder, documents_folder)
            
    Raises:
        Exception: For unrecoverable I/O errors or missing master folder configuration
    """
    settings_dao = SettingsDAO(logger)
    master_folder_path = settings_dao.get_master_folder()
    
    if not master_folder_path:
        raise Exception("Master folder not configured. Please set it in Settings → Master Folder.")
    
    master_folder = pathlib.Path(master_folder_path)
    
    if not master_folder.exists():
        try:
            master_folder.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created master folder: {master_folder}")
        except Exception as e:
            raise Exception(f"Cannot create master folder '{master_folder}': {e}")
    
    sanitized_name = sanitize_customer_name(customer_name)
    
    project_folder = master_folder / sanitized_name
    counter = 1
    base_project_folder = project_folder
    
    while project_folder.exists():
        project_folder = base_project_folder.parent / f"{base_project_folder.name}_{counter}"
        counter += 1
    
    try:
        project_folder.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created project folder: {project_folder}")
    except Exception as e:
        raise Exception(f"Cannot create project folder '{project_folder}': {e}")
    
    photos_folder = project_folder / "Photos"
    documents_folder = project_folder / "Documents"
    
    try:
        photos_folder.mkdir(parents=True, exist_ok=True)
        documents_folder.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created attachment folders: {photos_folder}, {documents_folder}")
    except Exception as e:
        raise Exception(f"Cannot create attachment folders: {e}")
    
    return project_folder, photos_folder, documents_folder 


def setup_project_folders(customer_name, logger):
    return get_project_paths(customer_name.strip(), logger)


def copy_files_to_folder(file_urls, dest_folder, folder_type, logger):
    copied_files = []
    for file_url in file_urls:
        source_path = pathlib.Path(uno.fileUrlToSystemPath(file_url))
        if not source_path.exists():
            logger.warning(f"Source file does not exist: {source_path}")
            continue
        dest_path = dest_folder / source_path.name
        counter = 1
        base_dest_path = dest_path
        while dest_path.exists():
            dest_path = base_dest_path.parent / f"{base_dest_path.stem}_{counter}{base_dest_path.suffix}"
            counter += 1
        shutil.copy2(source_path, dest_path)
        copied_files.append(dest_path.name)
        logger.info(f"Copied {source_path.name} to {dest_path}")
    return copied_files 


def rename_project_folder(old_name, new_name, logger):
    settings_dao = SettingsDAO(logger)
    master_folder_path = settings_dao.get_master_folder()
    if not master_folder_path:
        raise Exception("Master folder not configured")
    master_folder = pathlib.Path(master_folder_path)
    old_sanitized = sanitize_customer_name(old_name)
    new_sanitized = sanitize_customer_name(new_name)
    if old_sanitized == new_sanitized:
        folder = master_folder / old_sanitized
        photos = folder / "Photos"
        docs = folder / "Documents"
        return folder, photos, docs
    old_path = master_folder / old_sanitized
    new_path_base = master_folder / new_sanitized
    if not old_path.exists():
        return setup_project_folders(new_name, logger)
    new_path = new_path_base
    if new_path.exists():
        if not any(new_path.iterdir()):
            shutil.rmtree(new_path)
        else:
            counter = 1
            while new_path.exists():
                new_path = pathlib.Path(f"{new_path_base}_{counter}")
                counter += 1
    os.rename(old_path, new_path)
    photos_folder = new_path / "Photos"
    documents_folder = new_path / "Documents"
    photos_folder.mkdir(parents=True, exist_ok=True)
    documents_folder.mkdir(parents=True, exist_ok=True)
    return new_path, photos_folder, documents_folder 