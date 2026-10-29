from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required
import os
import time
from werkzeug.utils import secure_filename
from app.models import db, HotelSetting, AuditLog
from app.utils.decorators import role_required
from app.utils.helpers import log_audit

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'svg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@settings_bp.route('/', methods=['GET', 'POST'])
@login_required
@role_required('Super Admin')
def index():
    if request.method == 'POST':
        # Handle Logo File Upload if provided
        if 'hotel_logo_file' in request.files:
            file = request.files['hotel_logo_file']
            if file and file.filename != '' and allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                save_dir = os.path.join(current_app.root_path, 'static', 'img')
                os.makedirs(save_dir, exist_ok=True)
                
                # Save as main hotel logo and versioned logo
                filename = f"hotel_logo.{ext}"
                target_path = os.path.join(save_dir, filename)
                file.save(target_path)
                
                # Also save standard copy to hotel_logo.jpg for universal fallback
                if ext != 'jpg':
                    import shutil
                    jpg_path = os.path.join(save_dir, 'hotel_logo.jpg')
                    try:
                        shutil.copyfile(target_path, jpg_path)
                    except Exception:
                        pass
                
                # Store relative static path in DB
                HotelSetting.set_value('hotel_logo_path', f"img/{filename}")
                log_audit('UPLOAD_LOGO', 'HotelSetting', None, f"New hotel logo uploaded: {filename}")

        # Handle all text settings
        for key in request.form:
            if key not in ['csrf_token', 'hotel_logo_file']:
                val = request.form.get(key, '').strip()
                if val:
                    HotelSetting.set_value(key, val)

        log_audit('UPDATE_SETTINGS', 'HotelSetting', None, "Hotel settings and branding updated")
        flash('Hotel settings and official branding saved successfully! New logo is now active across the system.', 'success')
        return redirect(url_for('settings.index'))

    settings_dict = HotelSetting.get_all_as_dict()
    recent_audits = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(15).all()

    return render_template(
        'settings/index.html',
        settings=settings_dict,
        recent_audits=recent_audits
    )


@settings_bp.route('/logo/delete', methods=['POST'])
@login_required
@role_required('Super Admin')
def delete_logo():
    HotelSetting.set_value('hotel_logo_path', 'img/hotel_logo.jpg')
    log_audit('DELETE_LOGO', 'HotelSetting', None, "Custom hotel logo removed; restored to default emblem")
    flash('Logadii hore waa la tirtiray waxaana dib loo soo celiyay astaantii hore ee asalka ahayd (Default Logo Restored).', 'info')
    return redirect(url_for('settings.index'))


# ==========================================
# DATABASE BACKUP & RESTORE MANAGER
# ==========================================

@settings_bp.route('/backup')
@login_required
@role_required('Super Admin', 'Manager')
def backup_hub():
    import os, time
    from datetime import datetime
    backup_dir = os.path.abspath('backups')
    os.makedirs(backup_dir, exist_ok=True)
    
    backup_files = []
    if os.path.exists(backup_dir):
        for f in os.listdir(backup_dir):
            if f.endswith('.db') or f.endswith('.sqlite') or f.endswith('.sql'):
                f_path = os.path.join(backup_dir, f)
                stat = os.stat(f_path)
                backup_files.append({
                    'filename': f,
                    'size_mb': round(stat.st_size / (1024 * 1024), 2),
                    'size_kb': round(stat.st_size / 1024, 1),
                    'created_at': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    'mtime': stat.st_mtime
                })
    
    # Sort newest first
    backup_files.sort(key=lambda x: x['mtime'], reverse=True)
    
    db_file = os.path.abspath('hotel_management.db')
    live_size_mb = round(os.path.getsize(db_file) / (1024 * 1024), 2) if os.path.exists(db_file) else 0.0

    return render_template(
        'settings/backup.html',
        backups=backup_files,
        live_size_mb=live_size_mb
    )


@settings_bp.route('/backup/create', methods=['POST'])
@login_required
@role_required('Super Admin', 'Manager')
def create_backup():
    import os, shutil, time, sqlite3
    from datetime import datetime
    
    backup_dir = os.path.abspath('backups')
    os.makedirs(backup_dir, exist_ok=True)
    
    src_db = os.path.abspath('hotel_management.db')
    if not os.path.exists(src_db):
        flash('Database file not found.', 'danger')
        return redirect(url_for('settings.backup_hub'))
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"hotel_backup_{timestamp}.db"
    dest_path = os.path.join(backup_dir, backup_filename)
    
    try:
        # Use SQLite online backup API for safe hot backup without locks
        src_conn = sqlite3.connect(src_db)
        dest_conn = sqlite3.connect(dest_path)
        with dest_conn:
            src_conn.backup(dest_conn)
        src_conn.close()
        dest_conn.close()
        
        log_audit('CREATE_BACKUP', 'System', None, f"Created DB backup: {backup_filename}")
        flash(f"Kaydka xogta ee degdegga ah (Instant Backup: {backup_filename}) si guul leh ayaa loo abuuray!", 'success')
    except Exception as e:
        # Fallback to copy2
        try:
            shutil.copy2(src_db, dest_path)
            flash(f"Kaydka xogta ({backup_filename}) waa la abuuray.", 'success')
        except Exception as e2:
            flash(f"Cilad ayaa dhacday xilligii kaydinta: {str(e2)}", 'danger')
            
    return redirect(url_for('settings.backup_hub'))


@settings_bp.route('/backup/download/<filename>')
@login_required
@role_required('Super Admin', 'Manager')
def download_backup(filename):
    import os
    from flask import send_file
    
    # Security check: filename must be pure basename
    clean_name = os.path.basename(filename)
    backup_path = os.path.join(os.path.abspath('backups'), clean_name)
    
    if not os.path.exists(backup_path):
        flash('Faylka la codsaday lama helin.', 'danger')
        return redirect(url_for('settings.backup_hub'))
        
    return send_file(backup_path, as_attachment=True, download_name=clean_name)


@settings_bp.route('/backup/delete/<filename>', methods=['POST'])
@login_required
@role_required('Super Admin')
def delete_backup(filename):
    import os
    clean_name = os.path.basename(filename)
    backup_path = os.path.join(os.path.abspath('backups'), clean_name)
    
    if os.path.exists(backup_path):
        os.remove(backup_path)
        log_audit('DELETE_BACKUP', 'System', None, f"Deleted backup file: {clean_name}")
        flash(f"Faylka kaydka ah '{clean_name}' waa la tirtiray.", 'info')
    else:
        flash('Faylka lama helin.', 'warning')
        
    return redirect(url_for('settings.backup_hub'))
