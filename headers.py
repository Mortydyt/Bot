from bot_secrets import ACCESS_TOKEN

HEADERS = {
    'Content-Type': 'application/json',
    'Idempotence-Key': 'YOUR_UNIQUE_PAYMENT_ID',
    'Authorization': f'Bearer {ACCESS_TOKEN}'
}
