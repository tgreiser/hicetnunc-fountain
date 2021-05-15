from pytezos import Key
from pytezos import pytezos
from pytezos.rpc.node import RpcError
from pytezos.operation.result import OperationResult
from decimal import Decimal
import os
import time

# Address: tz1UqhPnVXdPccrVsa5khscwCLHTF2Q2CAer
key = Key.from_encoded_key(os.environ['FOUNTAIN_KEY'], os.environ['FOUNTAIN_PASS'])
pytezos = pytezos.using(shell='mainnet', key=key)
acct_id = pytezos.key.public_key_hash()
acct = pytezos.account()

send_amt = .33333
send_to = [ acct_id, 'tz1cTS1WwovU7SC783xgJxZrzr151mcshmNi' ]
applied = {}

print("%s current balance: %s XTZ" % (acct_id, int(acct['balance']) / 1000000) )

def has_no_money(acct_id, amt):
    acct = pytezos.account(acct_id)
    no_money = int(acct['balance']) <= int(amt * 1000000)
    print("%s current balance: %s XTZ - under limit? %s" % (acct_id, int(acct['balance']) / 1000000, no_money) )
    return no_money

def transfer(send_to, send_amt):
    opg = pytezos.transaction(destination=send_to, amount=Decimal(send_amt))
    res = run_opg(opg)
    op_hash = res['hash']
    while True:
        time.sleep(60)
        ver = verify_op(op_hash)
        if ver == 1:
            applied[send_acct] = op_hash
            break
        elif ver == -1:
            print("Retry failed %s XTZ to %s" % (send_amt, send_to))
            return transfer(send_to, send_amt)
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


for send_acct in send_to:
    # TODO - change the has_no_money test max to 0 instead of send_amt
    if has_no_money(send_acct, send_amt):
        op_hash = transfer(send_acct, send_amt * .1)

print('Sent %s to %s' % (send_amt, applied))
