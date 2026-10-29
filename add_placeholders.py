"""
Fix all HTML templates:
1. Add meaningful placeholders to all inputs that don't have them
2. The CSS already handles background/color via !important overrides
"""
import os
import re

# Map of input name attributes to their placeholder text
PLACEHOLDERS = {
    # Guest / Person fields
    'full_name': 'Enter full name',
    'first_name': 'Enter first name',
    'last_name': 'Enter last name',
    'username': 'Enter username',
    'email': 'Enter email address',
    'phone': 'Enter phone number e.g. +252 61 555 0100',
    'id_number': 'Enter ID or passport number',
    'nationality': 'Enter nationality',
    'address': 'Enter full address',
    'city': 'Enter city',
    'country': 'Enter country',
    'date_of_birth': '',
    'password': 'Enter password',
    'new_password': 'Enter new password',
    'confirm_password': 'Re-enter password to confirm',

    # Booking fields
    'check_in_date': '',
    'check_out_date': '',
    'adults': '',
    'children': '',
    'promo_code': 'Enter promo code e.g. WELCOME10',
    'special_requests': 'e.g. Quiet room, extra pillows, late checkout...',
    'notes': 'Add any notes or remarks here',
    'deposit_amount': 'Enter deposit amount',
    'total_amount': 'Enter total amount',

    # Room fields
    'room_number': 'e.g. 101',
    'floor': 'e.g. 1',
    'view_type': 'e.g. Ocean View',
    'bed_type': 'e.g. King, Twin, Double',

    # Payment / Finance
    'amount': 'Enter amount',
    'payment_reference': 'Enter payment reference or transaction ID',
    'description': 'Enter description',
    'reason': 'Enter reason',
    'invoice_number': 'Enter invoice number',

    # Staff / HR
    'position': 'e.g. Front Desk Manager',
    'department': 'e.g. Front Office',
    'salary': 'Enter monthly salary',
    'emergency_contact': 'Enter emergency contact name & phone',

    # Restaurant
    'table_number': 'e.g. 5',
    'quantity': 'Enter quantity',
    'unit_price': 'Enter unit price',

    # Inventory
    'item_name': 'Enter item name',
    'sku': 'Enter SKU or item code',
    'reorder_level': 'Enter minimum stock level',
    'current_stock': 'Enter current stock quantity',

    # General
    'title': 'Enter title',
    'name': 'Enter name',
    'subject': 'Enter subject',
    'message': 'Enter your message',
    'comment': 'Enter your comment or feedback',
    'search': 'Search...',
    'code': 'Enter code',
    'price': 'Enter price',
    'capacity': 'Enter capacity',
    'size_sqm': 'Enter size in square meters',
}

TEMPLATES_DIR = r'c:\Users\pc\OneDrive\Desktop\Hotellmanagement\app\templates'

def add_placeholder(tag_html, name, existing_placeholder, field_type):
    """Add placeholder to an input tag if it doesn't already have one."""
    if existing_placeholder:
        return tag_html  # Already has placeholder

    # Skip types that don't use placeholder
    if field_type in ('checkbox', 'radio', 'submit', 'file', 'hidden', 'date', 'time', 'number', 'color', 'range'):
        return tag_html

    # Get placeholder from map
    placeholder = None
    for key, ph in PLACEHOLDERS.items():
        if key == name and ph:
            placeholder = ph
            break

    # Fallback: derive from name
    if not placeholder:
        # Convert snake_case to Title Case
        placeholder = 'Enter ' + name.replace('_', ' ').title().lower()

    # Insert placeholder before closing >
    # Handle self-closing and regular tags
    if tag_html.endswith('/>'):
        tag_html = tag_html[:-2].rstrip() + f' placeholder="{placeholder}"/>'
    else:
        tag_html = tag_html.rstrip('>')
        tag_html = tag_html.rstrip() + f' placeholder="{placeholder}">'

    return tag_html


def process_html_file(filepath):
    """Process a single HTML file and add placeholders."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Match all input and textarea tags
    # Input tags
    def replace_input(m):
        tag = m.group(0)
        # Get type attribute
        type_match = re.search(r'type=["\']([^"\']+)["\']', tag)
        field_type = type_match.group(1).lower() if type_match else 'text'

        # Get name attribute
        name_match = re.search(r'name=["\']([^"\']+)["\']', tag)
        if not name_match:
            return tag
        name = name_match.group(1).lower()

        # Check for existing placeholder
        ph_match = re.search(r'placeholder=["\']', tag)
        existing_ph = ph_match is not None

        return add_placeholder(tag, name, existing_ph, field_type)

    def replace_textarea(m):
        tag = m.group(0)
        name_match = re.search(r'name=["\']([^"\']+)["\']', tag)
        if not name_match:
            return tag
        name = name_match.group(1).lower()
        ph_match = re.search(r'placeholder=["\']', tag)
        existing_ph = ph_match is not None
        return add_placeholder(tag, name, existing_ph, 'textarea')

    # Replace inputs
    content = re.sub(r'<input[^>]+>', replace_input, content)
    # Replace textarea opening tags (before >)
    content = re.sub(r'<textarea[^>]*>', replace_textarea, content)

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False


def main():
    changed = 0
    total = 0
    for root, dirs, files in os.walk(TEMPLATES_DIR):
        # Skip errors directory
        if 'errors' in root:
            continue
        for fname in files:
            if fname.endswith('.html'):
                total += 1
                fpath = os.path.join(root, fname)
                try:
                    if process_html_file(fpath):
                        changed += 1
                        print(f'  UPDATED: {fpath.replace(TEMPLATES_DIR, "")}')
                    else:
                        print(f'  OK:      {fpath.replace(TEMPLATES_DIR, "")}')
                except Exception as e:
                    print(f'  ERROR:   {fpath.replace(TEMPLATES_DIR, "")} -> {e}')

    print(f'\n=== Done: {changed}/{total} files updated with placeholders ===')


if __name__ == '__main__':
    main()
