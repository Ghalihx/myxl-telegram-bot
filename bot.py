import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from api_request import get_otp, submit_otp, save_tokens, get_balance, purchase_package
from util import load_token
from paket_xut import get_package_xut

# Simpan nomor login per-chat (supaya /otp tahu nomor mana yang diverifikasi)
LOGIN_MSISDN = {}
# Simpan daftar paket terakhir per-chat (untuk /buy)
SESSION_PACKAGES = {}

def require_login(handler):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = load_token()
        if not user or not user.get("is_logged_in"):
            await update.message.reply_text("❌ Kamu belum login.\nGunakan /login 628xxxx lalu /otp 6digit.")
            return
        return await handler(update, context)
    return wrapper

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📱 MyXL Bot\n\n"
        "Perintah:\n"
        "/login 628xxxxxx → minta OTP\n"
        "/otp 123456 → verifikasi OTP\n"
        "/saldo → cek pulsa\n"
        "/list → daftar paket XUT\n"
        "/buy 1 → beli paket"
    )

async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Format: /login 628xxxxxx")
        return
    msisdn = context.args[0]
    try:
        get_otp(msisdn)
        # simpan nomor utk chat ini
        LOGIN_MSISDN[update.effective_chat.id] = msisdn
        await update.message.reply_text(f"✅ OTP dikirim ke {msisdn}. Lanjut dengan /otp 6digit")
    except Exception as e:
        await update.message.reply_text(f"Gagal kirim OTP: {e}")

async def otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Format: /otp 123456")
        return
    code = context.args[0]
    msisdn = LOGIN_MSISDN.get(update.effective_chat.id)
    if not msisdn:
        await update.message.reply_text("Belum ada nomor. Jalankan dulu /login 628xxxx")
        return
    try:
        # submit_otp(contact, code) → WAJIB 2 argumen!
        tokens = submit_otp(msisdn, code)
        save_tokens(tokens)
        await update.message.reply_text("✅ Login berhasil, token disimpan")
    except Exception as e:
        await update.message.reply_text(f"Gagal verifikasi OTP: {e}")

@require_login
async def saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = load_token()
        id_token = user["tokens"]["id_token"]
        balance = get_balance(id_token)
        msg = f"💰 Pulsa: Rp {balance.get('remaining')} (exp: {balance.get('expired_at')})"
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f"Gagal cek saldo: {e}")

@require_login
async def list_pkg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = load_token()
    try:
        packages = get_package_xut(user["tokens"])
        if not packages:
            await update.message.reply_text("Tidak ada paket ditemukan.")
            return
        SESSION_PACKAGES[update.effective_chat.id] = packages
        text = ["📦 Paket XUT:"]
        for p in packages:
            text.append(f"{p['number']}. {p['name']} — Rp {p['price']}")
        text.append("\nGunakan /buy <nomor>, contoh: /buy 1")
        await update.message.reply_text("\n".join(text))
    except Exception as e:
        await update.message.reply_text(f"Gagal ambil paket: {e}")

@require_login
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Format: /buy 1")
        return
    try:
        idx = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Nomor paket harus angka.")
        return
    packages = SESSION_PACKAGES.get(update.effective_chat.id)
    if not packages:
        await update.message.reply_text("❌ Jalankan /list dulu.")
        return
    selected = next((p for p in packages if p["number"] == idx), None)
    if not selected:
        await update.message.reply_text("Nomor paket tidak valid.")
        return
    try:
        user = load_token()
        purchase_package(user["tokens"], selected["code"])
        await update.message.reply_text(f"✅ Pembelian {selected['name']} Rp {selected['price']} diproses.")
    except Exception as e:
        await update.message.reply_text(f"Gagal beli paket: {e}")

def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("❌ BOT_TOKEN belum di-set. Gunakan: export BOT_TOKEN=123:ABC")
        return
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("login", login))
    app.add_handler(CommandHandler("otp", otp))
    app.add_handler(CommandHandler("saldo", saldo))
    app.add_handler(CommandHandler("list", list_pkg))
    app.add_handler(CommandHandler("buy", buy))
    app.run_polling()

if __name__ == "__main__":
    main()
        get_otp(msisdn)
        await update.message.reply_text(f"✅ OTP dikirim ke {msisdn}. Lanjut dengan /otp 6digit")
    except Exception as e:
        await update.message.reply_text(f"Gagal kirim OTP: {e}")

async def otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Format: /otp 123456")
        return
    code = context.args[0]
    try:
        tokens = submit_otp(code)
        save_tokens(tokens)
        await update.message.reply_text("✅ Login berhasil, token disimpan")
    except Exception as e:
        await update.message.reply_text(f"Gagal verifikasi OTP: {e}")

@require_login
async def saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = load_token()
        id_token = user["tokens"]["id_token"]
        balance = get_balance(id_token)
        msg = f"💰 Pulsa: Rp {balance.get('remaining')} (exp: {balance.get('expired_at')})"
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f"Gagal cek saldo: {e}")

@require_login
async def list_pkg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = load_token()
    try:
        packages = get_package_xut(user["tokens"])
        if not packages:
            await update.message.reply_text("Tidak ada paket ditemukan.")
            return
        SESSION_PACKAGES[update.effective_chat.id] = packages
        text = ["📦 Paket XUT:"]
        for p in packages:
            text.append(f"{p['number']}. {p['name']} — Rp {p['price']}")
        text.append("\nGunakan /buy <nomor>, contoh: /buy 1")
        await update.message.reply_text("\n".join(text))
    except Exception as e:
        await update.message.reply_text(f"Gagal ambil paket: {e}")

@require_login
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Format: /buy 1")
        return
    try:
        idx = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Nomor paket harus angka.")
        return
    packages = SESSION_PACKAGES.get(update.effective_chat.id)
    if not packages:
        await update.message.reply_text("❌ Jalankan /list dulu.")
        return
    selected = next((p for p in packages if p["number"] == idx), None)
    if not selected:
        await update.message.reply_text("Nomor paket tidak valid.")
        return
    try:
        user = load_token()
        purchase_package(user["tokens"], selected["code"])
        await update.message.reply_text(f"✅ Pembelian {selected['name']} Rp {selected['price']} diproses.")
    except Exception as e:
        await update.message.reply_text(f"Gagal beli paket: {e}")

def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("❌ BOT_TOKEN belum di-set. Gunakan: export BOT_TOKEN=123:ABC")
        return
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("login", login))
    app.add_handler(CommandHandler("otp", otp))
    app.add_handler(CommandHandler("saldo", saldo))
    app.add_handler(CommandHandler("list", list_pkg))
    app.add_handler(CommandHandler("buy", buy))
    app.run_polling()

if __name__ == "__main__":
    main()
