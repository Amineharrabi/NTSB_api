from ntsb_api import NTSBClient

client = NTSBClient()
zip_bytes = client.download_month(2025, 4, mode="Aviation")
print(len(zip_bytes), "bytes of ZIP")