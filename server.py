from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import os

app = FastAPI()
DB_FILE = "database.json"
TRANSAKSI_FILE = "transaksi.json"

class Produk(BaseModel):
    id: int
    nama: str
    kategori: str
    harga: float
    stok: int

class Transaksi(BaseModel):
    user: str
    nama: str
    alamat: str
    produk_id: int
    nama_produk: str
    qty: int
    harga: float
    resi: str
    waktu: str

def load_data(file):
    if os.path.exists(file):
        with open(file, 'r') as f:
            return json.load(f)
    return []

def save_data(data, file):
    with open(file, 'w') as f:
        json.dump(data, f, indent=4)

@app.get("/")
def home():
    return {"message": "API Toko Elektronik aktif."}

@app.get("/produk")
def get_produk():
    return load_data(DB_FILE)

@app.post("/produk")
def tambah_produk(produk: Produk):
    data = load_data(DB_FILE)
    if any(p['id'] == produk.id for p in data):
        raise HTTPException(status_code=400, detail="ID produk sudah ada")
    data.append(produk.dict())
    save_data(data, DB_FILE)
    return {"message": "Produk berhasil ditambahkan"}

@app.put("/produk/{id}")
def update_produk(id: int, produk: Produk):
    data = load_data(DB_FILE)
    for i, p in enumerate(data):
        if p["id"] == id:
            data[i] = produk.dict()
            save_data(data, DB_FILE)
            return {"message": "Produk berhasil diperbarui"}
    raise HTTPException(status_code=404, detail="Produk tidak ditemukan")

@app.delete("/produk/{id}")
def hapus_produk(id: int):
    data = load_data(DB_FILE)
    for i, p in enumerate(data):
        if p["id"] == id:
            del data[i]
            save_data(data, DB_FILE)
            return {"message": "Produk berhasil dihapus"}
    raise HTTPException(status_code=404, detail="Produk tidak ditemukan")

@app.post("/transaksi")
def tambah_transaksi(transaksi: Transaksi):
    data = load_data(TRANSAKSI_FILE)
    transaksi_dict = transaksi.dict()
    transaksi_dict['id'] = len(data) + 1
    data.append(transaksi_dict)
    save_data(data, TRANSAKSI_FILE)
    return {"status": "sukses", "data": transaksi_dict}

@app.get("/transaksi")
def get_transaksi():
    return load_data(TRANSAKSI_FILE)
