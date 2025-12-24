import mailbox
import json
import email.utils
from email.header import decode_header
import os

def decode_str(s):
    decoded_parts = decode_header(s)
    decoded_str = ''
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            decoded_str += part.decode(encoding or 'utf-8', errors='replace')
        else:
            decoded_str += part
    return decoded_str

def get_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                payload = part.get_payload(decode=True)
                if isinstance(payload, bytes):
                    return payload.decode('utf-8', errors='replace')
                return payload
    else:
        payload = msg.get_payload(decode=True)
        if isinstance(payload, bytes):
            return payload.decode('utf-8', errors='replace')
        return payload
    return ''

def process_mbox(mbox_path, output_path):
    mbox = mailbox.mbox(mbox_path)
    replied_ids = set()
    for msg in mbox:
        in_reply_to = msg.get('In-Reply-To', '').strip()
        if in_reply_to:
            replied_ids.add(in_reply_to)

    mbox = mailbox.mbox(mbox_path)
    emails = []
    counter = 0
    for msg in mbox:
        counter += 1
        print(f"Processing email {counter}")
        from_addr = decode_str(msg.get('From', ''))
        to_addr = decode_str(msg.get('To', ''))
        subject = decode_str(msg.get('Subject', ''))
        body = get_body(msg)
        message_id = msg.get('Message-ID', '').strip()
        replied = message_id in replied_ids
        emails.append({
            'title': subject,
            'from': from_addr,
            'to': to_addr,
            'body': body,
            'replied': replied
        })
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(emails, f, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    mbox_file = 'Takeout/Mail/All mail Including Spam and Trash.mbox'
    output_file = 'emails.json'
    if os.path.exists(mbox_file):
        process_mbox(mbox_file, output_file)
        print(f"Processed emails saved to {output_file}")
    else:
        print(f"MBOX file not found: {mbox_file}")
