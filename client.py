import streamlit as st
import requests
import json, os, random, string
from datetime import datetime
from streamlit_folium import st_folium
import folium

API_URL = "http://localhost:8000"

if os.path.exists("style.css"):
    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.session_state.setdefault('cart', [])
st.session_state.setdefault('login', False)
st.session_state.setdefault('role', None)

# 🔐 Login

def login_user():
    with st.sidebar:
        st.subheader("🔐 Login Pengguna")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        role = st.selectbox("Masuk sebagai", ["User", "Admin"])
        if st.button("Login"):
            if os.path.exists("users.json"):
                with open("users.json") as f:
                    users = json.load(f)
                for u in users:
                    if u['username'] == username and u['password'] == password and u['role'] == role:
                        st.session_state['login'] = True
                        st.session_state['role'] = role
                        st.session_state['username'] = username
                        st.success("Login berhasil!")
                        st.rerun()
                        return
            st.error("Login gagal. Periksa username/password.")

def simpan_user_default():
    if not os.path.exists("users.json"):
        users = [
            {"username": "admin", "password": "admin123", "role": "Admin"},
            {"username": "user", "password": "user123", "role": "User"}
        ]
        with open("users.json", "w") as f:
            json.dump(users, f)

# 🛒 Produk

def tampilkan_produk():
    st.subheader("🛒 Produk Tersedia")
    res = requests.get(f"{API_URL}/produk")
    if res.status_code != 200:
        st.error("Gagal mengambil data produk")
        return

    for p in res.json():
        with st.container():
            cols = st.columns([1, 2])
            with cols[0]:
                if p['gambar']:
                    st.image(p['gambar'], width=200)
            with cols[1]:
                st.markdown(f"### {p['nama']}")
                st.write(f"Kategori: `{p['kategori']}`")
                st.write(f"Harga: Rp {p['harga']:,}")
                st.write(f"Stok: {p['stok']}")
                qty = st.number_input("Jumlah", min_value=1, max_value=p['stok'], step=1, key=f"qty_{p['id']}")
                colb1, colb2 = st.columns(2)
                with colb1:
                    if st.button(f"🛒 Beli Sekarang", key=f"beli_{p['id']}"):
                        simpan_transaksi(p, qty)
                        st.success("✅ Berhasil dibeli!")
                with colb2:
                    if st.button(f"➕ Tambah ke Keranjang", key=f"addcart_{p['id']}"):
                        st.session_state['cart'].append({
                            "id": p['id'],
                            "nama": p['nama'],
                            "harga": p['harga'],
                            "qty": qty,
                            "stok": p['stok'],
                            "gambar": p['gambar']
                        })
                        st.success("✅ Ditambahkan ke keranjang!")

# 🧺 Keranjang

def tampilkan_keranjang():
    st.subheader("🧺 Keranjang Belanja")

    if not st.session_state['cart']:
        st.info("Keranjang masih kosong.")
        return

    total = 0
    for i, item in enumerate(st.session_state['cart']):
        with st.container():
            cols = st.columns([1, 3, 2, 2, 1])
            with cols[0]:
                if item.get('gambar'):
                    st.image(item['gambar'], width=80)
            with cols[1]:
                st.markdown(f"**{item['nama']}**")
                st.write(f"Harga: Rp {item['harga']:,}")
            with cols[2]:
                new_qty = st.number_input("Jumlah", min_value=1, max_value=item['stok'], value=item['qty'], step=1, key=f"qtycart_{i}")
                st.session_state['cart'][i]['qty'] = new_qty
            with cols[3]:
                st.write(f"Subtotal: Rp {item['harga'] * item['qty']:,}")
                total += item['harga'] * item['qty']
            with cols[4]:
                if st.button("❌", key=f"hapus_{i}"):
                    st.session_state['cart'].pop(i)
                    st.experimental_rerun()

        st.markdown("---")

    st.markdown(f"## 💰 Total Belanja: Rp {total:,}")

    with st.form("form_checkout"):
        nama = st.text_input("Nama Penerima")
        alamat = st.text_area("Alamat Pengiriman")
        tombol = st.form_submit_button("✅ Checkout Sekarang")
        if tombol:
            if not nama or not alamat:
                st.warning("Mohon isi nama dan alamat pengiriman.")
                return
            nomor_resi = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
            lokasi = random.choice([[-6.2, 106.8], [-7.2, 112.7], [-6.9, 107.6]])
            for item in st.session_state['cart']:
                transaksi = {
                    "username": st.session_state['username'],
                    "nama": item['nama'],
                    "harga": item['harga'] * item['qty'],
                    "qty": item['qty'],
                    "waktu": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "resi": nomor_resi,
                    "lokasi": lokasi,
                    "nama_penerima": nama,
                    "alamat": alamat
                }
                simpan_data_transaksi(transaksi)
            st.success(f"Checkout berhasil! Nomor Resi Anda: `{nomor_resi}`")
            st.session_state['cart'] = []
            m = folium.Map(location=lokasi, zoom_start=12)
            folium.Marker(lokasi, popup=alamat).add_to(m)
            st_folium(m, width=700)

# 💾 Simpan Transaksi

def simpan_transaksi(p, qty):
    transaksi = {
        "username": st.session_state['username'],
        "nama": p['nama'],
        "harga": p['harga'] * qty,
        "qty": qty,
        "waktu": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "resi": f"R-{random.randint(100000,999999)}",
        "lokasi": random.choice([[-6.2, 106.8], [-7.2, 112.7], [-6.9, 107.6]])
    }
    simpan_data_transaksi(transaksi)


def simpan_data_transaksi(transaksi):
    data = json.load(open("transaksi.json")) if os.path.exists("transaksi.json") else []
    data.append(transaksi)
    with open("transaksi.json", "w") as f:
        json.dump(data, f, indent=4)

# 📋 Riwayat (Admin)

def riwayat_transaksi():
    st.subheader("📋 Riwayat Transaksi")
    if os.path.exists("transaksi.json"):
        for t in json.load(open("transaksi.json")):
            st.write(f"👤 {t.get('username')} - 🛒 {t.get('nama')} x {t.get('qty')} | Rp {t.get('harga'):,} | Resi: `{t.get('resi')}` | {t.get('waktu')}")
    else:
        st.info("Belum ada transaksi.")

# 📍 Lacak Pesanan (User)

def lacak_pesanan():
    st.subheader("📍 Lacak Pesanan")
    resi = st.text_input("Masukkan Nomor Resi")
    if resi and os.path.exists("transaksi.json"):
        data = json.load(open("transaksi.json"))
        for t in data:
            if t['resi'] == resi and t['username'] == st.session_state['username']:
                st.success(f"📦 Barang: {t['nama']}")
                st.write(f"Jumlah: {t['qty']} | Tanggal: {t['waktu']}")
                st.write(f"Penerima: {t.get('nama_penerima')}\nAlamat: {t.get('alamat')}")
                st.write("📍 Lokasi Pengiriman:")
                m = folium.Map(location=t['lokasi'], zoom_start=12)
                folium.Marker(t['lokasi'], popup=t['nama']).add_to(m)
                st_folium(m, width=700)
                return
        st.warning("Resi tidak ditemukan atau bukan milik Anda.")

# 🧠 Main
simpan_user_default()
st.set_page_config(page_title="Toko Elektronik Nusantara", layout="wide")
jumlah_item = sum(item['qty'] for item in st.session_state['cart'])

st.markdown("<h1 style='text-align:center;'>🛍️ Toko Elektronik Nusantara</h1>", unsafe_allow_html=True)

if not st.session_state['login']:
    login_user()
else:
    st.sidebar.success(f"Masuk sebagai {st.session_state['role']}")
    role = st.session_state['role']

    if role == "Admin":
        menu = st.sidebar.radio("📂 Menu", ["Lihat Produk", "Riwayat Transaksi", "Lacak Pesanan", "Logout"])
        if menu == "Lihat Produk":
            tampilkan_produk()
        elif menu == "Riwayat Transaksi":
            riwayat_transaksi()
        elif menu == "Lacak Pesanan":
            lacak_pesanan()
        elif menu == "Logout":
            st.session_state.clear()
            st.rerun()

    elif role == "User":
        menu = st.sidebar.radio("📂 Menu", [f"🛍️ Belanja", f"🧺 Keranjang ({jumlah_item})", "📍 Lacak Pesanan", "🚪 Logout"])
        if "Belanja" in menu:
            tampilkan_produk()
        elif "Keranjang" in menu:
            tampilkan_keranjang()
        elif "Lacak" in menu:
            lacak_pesanan()
        elif "Logout" in menu:
            st.session_state.clear()
            st.rerun()