import os
import uuid
from werkzeug.utils import secure_filename
from config import Config

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def save_uploaded_file(file_obj, subfolder='claims'):
    if not file_obj or file_obj.filename == '':
        return None, "No selected file"
    
    if not allowed_file(file_obj.filename):
        return None, f"Invalid file type. Allowed: {', '.join(Config.ALLOWED_EXTENSIONS)}"
    
    original_filename = secure_filename(file_obj.filename)
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
    
    # Generate unique stored filename to prevent collisions and execution
    unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
    
    upload_dir = os.path.join(Config.UPLOAD_FOLDER, subfolder)
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, unique_filename)
    file_obj.save(file_path)
    
    rel_path = f"uploads/{subfolder}/{unique_filename}"
    return {
        "original_name": original_filename,
        "unique_name": unique_filename,
        "file_path": rel_path,
        "full_path": file_path,
        "file_type": ext,
        "file_size": os.path.getsize(file_path)
    }, None
