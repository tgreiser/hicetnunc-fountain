# Teia XTZ Fountain
Pytezos bot for managing the Teia Tezos Fountain. Teia is a NFT community build on Tezos. See: https://teia.art/about

This project may be of educational use if you want to know how to use pytezos to send transactions and verify the completion.

Join us on the discord - https://discord.gg/MgDT9xK3GJ

 :taco:+:snake:+:robot: = :fountain:

Requirements:

- Python 3
- Pip
- Pytezos - https://pytezos.org/quick_start.html
- pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib

## Google Docs integration:

- https://developers.google.com/docs/api/quickstart/python
- A GDC project is used to manage the API access. https://developers.google.com/workspace/guides/create-project

## Credentials

You can generate a key and password with tezos-client: ```tezos-client gen keys fountain --encrypted``` Then your key will be in ~/.tezos-client/secret_keys. You can also export a secret key from Temple wallet - Settings > Reveal Private Key.

Export these crenentials as environment variables as shown below.

## Run The Fountain

```
export TEIA_FOUNTAIN_KEY="edesk..."
export TEIA_FOUNTAIN_PASS="matlock"
python fountain.py
```

- If you like this project, consider supporting my art - https://teia.art/tz/tz1cTS1WwovU7SC783xgJxZrzr151mcshmNi
- If you want to donate to help fund the Fountain, send XTZ to **TBA**
