from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from dotenv import load_dotenv
import mysql.connector
import os
import subprocess
import re

load_dotenv()
address = os.getenv('ADDRESS')
port = os.getenv('PORT')
token = os.getenv("TOKEN")
admin = os.getenv("ADMIN")

db_config = {
    "user": "root",
    "password": os.getenv("DB_PASSWORD"),
    "database": "ShaHaN"
}


async def reset_configures(context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_password"):
        context.user_data.pop("awaiting_password", None)
    if context.user_data.get("awaiting_remove_ips"):
        context.user_data.pop("awaiting_remove_ips", None)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await reset_configures(context)

    keyboard = [
        ["وضعیت"],
        [" آیدی عددی", "راهنما"],
        ["تغییر رمز عبور", "مسدود کردن"],
        [" بازگشت"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("یکی از گزینه‌های زیر را انتخاب کنید:", reply_markup=reply_markup)


async def status(update: Update):
    telegramid = update.effective_chat.id
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT username, password, traffic, multiuser FROM users WHERE telegramid = %s", (telegramid,))
    result = cursor.fetchone()
    if result:
        username, password, traffic, multiuser = result
        cmd = f'ps aux | awk -v u="{username}" \'$1 == u && $0 ~ ("sshd: " u)\' | wc -l'
        session_count = subprocess.check_output(
            cmd, shell=True, text=True).strip()
        cursor.execute(
            "SELECT upload, download FROM Traffic WHERE user = %s", (username,))
        result = cursor.fetchone()
        if result:
            upload, download = result
            total = int(upload) + int(download)
            upload, download, total = (
                f"{float(val)/1024:.2f}GB" if float(val) > 1024
                else (f"{val}MB" if float(val) != 0 else "0")
                for val in (upload, download, total)
            )

        else:
            upload = 0
            download = 0
            total = 0
        traffic += "GB"
        message = (
            f"اطلاعات اتصال:\n"
            f"آدرس سرور: {address}\n"
            f"نام کاربری: {username}\n"
            f"رمز عبور: \u200E{password}\n"
            f"پورت: {port}\n\n"
            f"میزان مصرف: {total}/{traffic}\n"
            f"آپلود: {upload}\n"
            f"دانلود: {download}\n"
            f"تعداد اتصال: {session_count}/{multiuser}\n"
        )
        if username == admin:
            cursor.execute(
                "SELECT username, password, traffic, multiuser FROM users WHERE username != %s", (username,))
            result = cursor.fetchall()
            for row in result:
                user_id, user_password, user_traffic, user_multiuser = row
                cmd = f'ps aux | awk -v u="{user_id}" \'$1 == u && $0 ~ ("sshd: " u)\' | wc -l'
                user_session_count = subprocess.check_output(
                    cmd, shell=True, text=True).strip()
                cursor.execute(
                    "SELECT upload, download FROM Traffic WHERE user = %s", (user_id,))
                result = cursor.fetchone()
                if result:
                    user_upload, user_download = result
                    user_total = int(user_upload) + int(user_download)
                    user_upload, user_download, user_total = (
                        f"{float(val)/1024:.2f}GB" if float(val) > 1024
                        else (f"{val}MB" if float(val) != 0 else "0")
                        for val in (user_upload, user_download, user_total)
                    )

                else:
                    user_upload = 0
                    user_download = 0
                    user_total = 0
                user_traffic += "GB"
                message += (
                    f"---------------------------------------------\n"
                    f"کاربر: {user_id}\n"
                    f"رمز عبور: \u200E{user_password}\n"
                    f"میزان مصرف: {user_total}/{user_traffic}\n"
                    f"آپلود: {user_upload}\n"
                    f"دانلود: {user_download}\n"
                    f"تعداد اتصال: {user_session_count}/{user_multiuser}\n"
                )
    else:
        message = "اطلاعاتی یافت نشد"
    cursor.close()
    conn.close()

    await update.message.reply_text(message)


async def telegramid(update: Update):
    telegramid = update.effective_chat.id

    message = (
        f" آیدی عددی: {telegramid}\n"
    )

    await update.message.reply_text(message)


async def help(update: Update):
    telegramid = update.effective_chat.id
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT username FROM users WHERE telegramid = %s", (telegramid,))
    result = cursor.fetchone()
    if result:
        with open("help.mp4", "rb") as video_file:
            await update.message.reply_video(video=video_file, caption="راهنمای اتصال با استفاده از napsternetv")
    else:
        message = "اطلاعاتی یافت نشد"
        await update.message.reply_text(message)

    cursor.close()
    conn.close()


async def change_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegramid = update.effective_chat.id
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT username FROM users WHERE telegramid = %s", (telegramid,))
    result = cursor.fetchone()
    if result:
        username = result[0]
        if not context.user_data.get("awaiting_password"):
            await update.message.reply_text("لطفاً رمز عبور جدید خود را وارد کنید")
            context.user_data["awaiting_password"] = True
            cursor.close()
            conn.close()
            return

        new_password = update.message.text.strip()
        contains_persian = bool(re.search(r'[\u0600-\u06FF]', new_password))
        if not new_password or contains_persian:
            await update.message.reply_text("رمز عبور معتبر نیست. لطفاً فقط از حروف لاتین و اعداد استفاده کنید")
            return
        try:
            command = f'echo "{username}:{new_password}" | /usr/sbin/chpasswd'
            subprocess.run(command, shell=True, check=True)
            cursor.execute(
                "UPDATE users SET password = %s WHERE username = %s", (new_password, username,))
            conn.commit()
            await update.message.reply_text("رمز عبور با موفقیت تغییر کرد")

        except subprocess.CalledProcessError:
            await update.message.reply_text("خطا در تغییر رمز عبور")
    else:
        message = "اطلاعاتی یافت نشد"
        await update.message.reply_text(message)

    context.user_data.pop("awaiting_password", None)
    cursor.close()
    conn.close()


async def block(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegramid = update.effective_chat.id
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT username FROM users WHERE telegramid = %s", (telegramid,))
    result = cursor.fetchone()
    if result:
        username = result[0]
        cmd = cmd = f"ps aux | awk -v u='{username}' '$1 == \"{username}\" && $0 ~ (\"sshd: \" u) {{ print $2 }}'"
        pids = subprocess.check_output(
            cmd, shell=True, text=True).strip().split()

        if not pids:
            context.user_data.pop("awaiting_remove_ips", None)
            await update.message.reply_text("درحال حاضر هیچ اتصالی ندارید")
            return
        ips = []
        for pid in pids:
            cmd = f"ss -tunp | grep 'pid={pid}' |grep {port} | awk '{{print $6}}' | cut -d':' -f1"
            ip = subprocess.check_output(cmd, shell=True, text=True).strip()
            if ip not in ips:
                ips.append(ip)

        context.user_data["pids"] = pids
        context.user_data["ips"] = ips
        context.user_data["username"] = username

        keyboard = [
            [InlineKeyboardButton(ip, callback_data=f"ip:{ip}")]
            for ip in ips
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("اتصال کدام آیپی مسدود شود؟", reply_markup=reply_markup)

    else:
        context.user_data.pop("awaiting_remove_ips", None)
        message = "اطلاعاتی یافت نشد"
        await update.message.reply_text(message)

    cursor.close()
    conn.close()


async def handle_ip_click(update, context):
    pids = context.user_data.pop("pids", None)
    ips = context.user_data.pop("ips", None)
    username = context.user_data.pop("username", None)

    query = update.callback_query
    await query.answer()

    data = query.data
    selected_ip = data.split("ip:")[1]
    try:
        blocked_file = "blocked_users_ips"
        with open(blocked_file, "a") as f:
            f.write(f"{username}:{selected_ip}\n")
            f.close()
        sed_cmd = f"sed -i '/^{username}:{selected_ip}$/d' '{blocked_file}'"
        subprocess.run(
            f"echo \"{sed_cmd}\" | at now + 5 minute", shell=True, check=True)

        indices = [i for i, ip in enumerate(ips) if ip == selected_ip]
        for index in indices:
            pid = pids[index]
            subprocess.run(["kill", "-9", pid])
        await query.edit_message_text(
            f"آیپی {selected_ip} با موفقیت حذف شد",
            reply_markup=None
        )

    except:
        await query.edit_message_text(
            f"پوزش! نتونستیم حذفش کنیم",
            reply_markup=None
        )


async def handle_menu_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    commands = ["وضعیت", "آیدی عددی", "راهنما",
                "تغییر رمز عبور", "مسدود کردن", "بازگشت"]

    if text in commands:
        await reset_configures(context)
        if text == "وضعیت":
            await status(update)

        elif text == "آیدی عددی":
            await telegramid(update)

        elif text == "راهنما":
            await help(update)

        elif text == "تغییر رمز عبور":
            await change_password(update, context)

        elif text == "مسدود کردن":
            await block(update, context)

        else:
            msg = await update.message.reply_text("برگشتیم", reply_markup=ReplyKeyboardRemove())
            await msg.delete()

    elif context.user_data.get("awaiting_password"):
        await change_password(update, context)
        return

    elif context.user_data.get("awaiting_remove_ips"):
        await block(update, context)
        return

if __name__ == "__main__":

    BOT_TOKEN = token

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CallbackQueryHandler(handle_ip_click, pattern=r"^ip:"))

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("id", telegramid))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(MessageHandler(filters.TEXT & (
        ~filters.COMMAND), handle_menu_selection))

    app.run_polling()
