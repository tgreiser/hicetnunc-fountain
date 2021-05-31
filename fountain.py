from pytezos import Key
from pytezos import pytezos
from pytezos.rpc.node import RpcError
from pytezos.operation.result import OperationResult
from decimal import Decimal
import datetime
import os
import time
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# The ID and range of a sample spreadsheet.
FOUNTAIN_SPREADSHEET_ID = '1LZLUqemQ5Q2gYllW6BTxfRYzC_IRihbsOta7xHQEe7I'
FOUNTAIN_RANGE_NAME = 'Form Responses 1!A2:I'

# Address: tz1UqhPnVXdPccrVsa5khscwCLHTF2Q2CAer
key = Key.from_encoded_key(os.environ['FOUNTAIN_KEY'], os.environ['FOUNTAIN_PASS'])
pytezos = pytezos.using(shell='mainnet', key=key)
acct_id = pytezos.key.public_key_hash()
acct = pytezos.account()

send_amt = .33333
send_to = []
applied = {}

#print("%s current balance: %s XTZ" % (acct_id, int(acct['balance']) / 1000000) )

def balance(acct_id):
    try:
        acct = pytezos.account(acct_id)
    except RpcError as e:
        print(e)
        return -1
    return int(acct['balance'])

def transfer(send_to, send_amt):
    opg = pytezos.transaction(destination=send_to, amount=Decimal(send_amt))
    res = run_opg(opg)
    op_hash = res['hash']
    while True:
        time.sleep(60)
        ver = verify_op(op_hash)
        if ver == 1:
            applied[send_to] = op_hash
            break
        elif ver == -1:
            print("Retry failed %s XTZ to %s" % (send_amt, send_to))
            return transfer(send_to, send_amt)
        else:
            print("Waiting for confirmation for %s" % op_hash)
            # ver 0 pass through and try again

    return op_hash

# 1 - verified
# 0 - not found
# -1 - failure
def verify_op(op_hash):
    try:
        opg = pytezos.shell.head.operations[op_hash]()
    except StopIteration as e:
        return 0
    ret = -1
    for op in OperationResult.iter_contents(opg):
        #print(op['metadata']['operation_result']['status'])
        if op['metadata']['operation_result']['status'] == 'applied':
            ret = 1
            break
    return ret

def run_opg(opg):
    try:
        res = opg.autofill().sign().inject()
    except RpcError as e:
        retry = True
        for arg in e.args:
            if arg['kind'] != 'temporary':
                retry = False
                print("ERROR! %s" % arg)
                break
        if retry:
            time.sleep(.1)
            return run_opg(opg)
    return res

def store_balance(service, row_num, balance):
    processed = '' if balance == 0 else 'Skipped'
    if balance == -1:
        processed = "Invalid Tezos account number"
    values = [
            [ float(balance) / 1000000, processed ]
            ]
    body = { 'values': values }
    range_name = 'Form Responses 1!F%s:G%s' % (row_num, row_num)
    #print(range_name)
    result = service.spreadsheets().values().update(
        spreadsheetId=FOUNTAIN_SPREADSHEET_ID, range=range_name,
        valueInputOption='USER_ENTERED', body=body).execute()
    print('{0} cells updated.'.format(result.get('updatedCells')))

def store_results(service, row_num, op_hash):
    values = [
            [ str(datetime.datetime.now()), "https://tzkt.io/%s" % op_hash ]
            ]
    body = { 'values': values }
    range_name = 'Form Responses 1!G%s:H%s' % (row_num, row_num)
    #print(range_name)
    result = service.spreadsheets().values().update(
        spreadsheetId=FOUNTAIN_SPREADSHEET_ID, range=range_name,
        valueInputOption='USER_ENTERED', body=body).execute()
    print('{0} cells updated.'.format(result.get('updatedCells')))

def main():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=FOUNTAIN_SPREADSHEET_ID,
                                range=FOUNTAIN_RANGE_NAME).execute()
    values = result.get('values', [])

    if not values:
        print('No data found.')
    else:
        row_num = 1
        for row in values:
            row_num += 1
            if row[1] == '':
                break
            address = row[1].strip()
            approved = row[4] == 'TRUE'
            processed_on = row[6] if len(row) > 6 else ''
            #print('%s, %s' % (address, approved))
            if approved and processed_on == '':
                acct_balance = balance(address)
                print("%s balance=%0.4f XTZ %s" % (address, acct_balance / 1000000, row_num))
                # TODO - write balance to sheet
                store_balance(service, row_num, acct_balance)
                if acct_balance == 0:
                    op_hash = transfer(address, send_amt)
                    print('Sent %s to %s with %s' % (send_amt, address, op_hash))
                    store_results(service, row_num, op_hash)

if __name__ == '__main__':
    main()
