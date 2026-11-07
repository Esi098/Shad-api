# Shad (web.shad.ir) — API & endpoint catalogue

> **shad-api** · reverse-engineering notes for the library in `shad_api/`.
> These notes are kept in Persian because they document the original research;
> the code, README and error strings are in English.

Extracted from the Angular bundle `main-es2015.86294d52c7b53854337c.js` (app 4.4.26) and verified live on 2026-11-06.

## 1) Architecture

Shad Web is an Angular SPA. It is **not REST-per-method**: every API operation is a
`POST` to a base URL with a JSON envelope that carries the method name
(IranLMS protocol). A separate discovery endpoint returns the URL pools, and
chat updates arrive over a WebSocket.

```
web.shad.ir (SPA)
   ├─ POST https://shgetdcmess.iranlms.ir        -> getDCs (URL pools, storages)
   ├─ POST https://shservicesbase.iranlms.ir/    -> getBaseInfo (service hosts)
   ├─ POST https://shadmessenger{125,180,152}.iranlms.ir  -> all API methods (encrypted)
   ├─ POST https://shadmessenger{7,3,5}.iranlms.ir        -> bot API (same envelope)
   ├─ WSS  wss://shsocket{5,1,13}.iranlms.ir:80           -> chat updates
   └─ POST https://shstorageNNN.iranlms.ir/GetFile.ashx   -> file download/upload
```

## 2) Discovery endpoints (live-verified)

### getDCs
```
POST https://shgetdcmess.iranlms.ir
Content-Type: application/json

{"api_version":"4","method":"getDCs","data":{},
 "client":{"app_name":"Shad","app_version":"4.4.26","platform":"Web",
           "package":"web.shad.ir","lang_code":"fa"}}
```
Response (trimmed):
```
{"status":"OK","status_det":"OK","data":{
  "default_api_urls":["https://shadmessenger125.iranlms.ir",
                      "https://shadmessenger180.iranlms.ir",
                      "https://shadmessenger152.iranlms.ir"],
  "default_bot_urls":["https://shadmessenger7.iranlms.ir",
                      "https://shadmessenger3.iranlms.ir",
                      "https://shadmessenger5.iranlms.ir"],
  "default_sockets":["wss://shsocket5.iranlms.ir:80",
                     "wss://shsocket1.iranlms.ir:80",
                     "wss://shsocket13.iranlms.ir:80"],
  "storages":{"501":"https://shstorage501.iranlms.ir/GetFile.ashx",
              "502":"https://shstorage502.iranlms.ir/GetFile.ashx",
              "...":"... (426 shards, 501..926)"}
}}
```
Note: `default_rubino_urls`/`default_wallet_urls` are not in this response today;
the SPA falls back to the constants below.

### getBaseInfo
```
POST https://shservicesbase.iranlms.ir/
{"method":"getBaseInfo","api_version":"0","data":{},
 "client":{"app_name":"Shad","app_version":"4.4.26","platform":"PWA",
           "package":"web.shad.ir","lang_code":"fa"}}
```
Live response adds: suggested_services, suggested_payment, suggested_news, etc. (see §7).

## 3) API envelope (messaging)

### Encrypted request (normal)
```
POST <default_api_urls[i]>
Content-Type: application/json

{
  "api_version": "5",              // "6" for auth flows
  "auth": "<session token>",       // omitted when not_authorized
  "tmp_session": "<tmp id>",       // only when no auth yet
  "data_enc": "<AES-encrypted {method,input,client} blob>"
}
```
Decrypted payload:
```
{"method":"getChats","input":{"start_id":"..."},
 "client":{"app_name":"Shad","app_version":"4.4.26","platform":"web",
           "package":"web.shad.ir","lang_code":"fa"}}
```

### Plain request (not_encrypt)
Used by `unregisterDevice`, and by the two discovery endpoints above:
```
{"api_version":"4","method":"<name>","data":{...},"client":{...},"auth":"..."}
```

### Response
```
{"status":"OK","status_det":"OK","data":{...}}      // or
{"status":"ERROR_*","status_det":"...","data":{...}}
```
Encrypted responses carry `data_enc` which must be AES-decrypted.

## 4) WebSocket (updates)

```
WSS wss://shsocket5.iranlms.ir:80   (also shsocket1 / shsocket13)
Origin: https://web.shad.ir
```
Handshake (worked live, no auth required to open):
```
{"api_version":"5","auth":"<token>","data":"","method":"handShake"}
```
The server answers (live test): `{"status":"OK","status_det":"OK"}`.
Then `{}` is sent periodically as ping; server pushes chat updates as JSON.

## 5) Authentication / login methods

| step | method | notes |
|---|---|---|
| request code | `sendCode` | `not_authorized:true`, `api_version:"6"`; model has phone + `public_key` |
| verify code | `signIn` (obfuscated constant) | `not_authorized:true`, `api_version:"6"`; returns auth token |
| two-step | `checkTwoStepPasscode`, `setupTwoStepVerification`, `turnOffTwoStep`, `abortTwoStepSetup`, `requestRecoveryEmail`, `verifyRecoveryEmail`, `resendCodeRecoveryEmail`, `loginDisableTwoStep`, `loginTwoStepForgetPassword` | |
| device | `registerDevice`, `unregisterDevice` | device hash/token, app version |
| session | `getMySessions`, `terminateSession`, `terminateOtherSessions` | |
| bootstrap | `getDCs`, `getBaseInfo`, `getTime`, `getServiceInfo` | |

The login envelope uses a temporary RSA session: the client generates an RSA
keypair, sends its public key inside `sendCode`, receives a session key, and
then encrypts `signIn` with AES. Implementing it faithfully is the next step
(needs a real phone + code).

## 6) Files (upload / download)

Upload:
1. `requestSendFile` with `{"file_name","size","mime"}` -> returns `file_id`,
   `dc_url`, `access_hash_send` (and chunk info).
2. POST each chunk (binary) to `dc_url` with headers:
   `access-hash-send`, `auth`, `file-id`, `part-number`, `total-part`, `chunk-size`.
3. Response `status_det == "OK"`; final `access_hash_rec` is returned.

Download:
```
POST <file.dc_url>       (e.g. https://shstorage501.iranlms.ir/GetFile.ashx)
headers:
  access-hash-rec: <hash>
  auth: <token>
  file-id: <id>
  start-index: <byte offset>
  last-index: <byte end>
  Content-Type: text/plain
body: empty
```
Response: raw bytes (`arraybuffer`) + `total_length` response header.

## 7) Hosts / service endpoints (live or from getBaseInfo)

| purpose | endpoint |
|---|---|
| web app | https://web.shad.ir |
| app landing | https://app.shad.ir , https://shad.ir |
| APK | https://cdnu19.iranlms.ir/Shad_2_8_2.apk |
| link shortener | https://url.shad.ir (key `shad00000000000000000000`) |
| barcode | https://shbarcode.iranlms.ir , https://shbarcode4.iranlms.ir |
| rubino (stories) | https://shad1.iranlms.ir , https://shrubino4.iranlms.ir |
| wallet | https://shwallet1.iranlms.ir |
| webapp | https://shwebapp1.iranlms.ir , https://shwebapp.iranlms.ir |
| services | https://shservices.iranlms.ir , https://shservices10.iranlms.ir/ |
| link object panel | https://panel.iranlms.ir/api/v3.0/getlinkObject (needs credentials) |
| ASN | https://shasn.iranlms.ir/ |
| basket | https://xbasket3.iranlms.ir |
| comments | https://shcomments.iranlms.ir |
| home | https://homesh6.iranlms.ir |
| news | https://shkhabar.iranlms.ir |
| payment | https://shmegapal.iranlms.ir , https://shpaymentc.iranlms.ir |
| quiz | https://shquiz3.iranlms.ir |
| usage | https://shusage3.iranlms.ir |
| old panel | https://shpanel3.iranlms.ir |

## 8) Full method list (195 methods found in the bundle)

### auth/account (9)
changePassword, getTime, loginDisableTwoStep, loginTwoStepForgetPassword, logout, registerDevice, requestDeleteAccount, sendCode, unregisterDevice
### messages (33)
actionOnMessageReaction, clickMessageUrl, createPoll, deleteMessages, editMessage, forwardMessages, getAvailableReactions, getChatAds, getChatReaction, getMessageReactions, getMessageShareUrl, getMessages, getMessagesByID, getMessagesInterval, getMessagesUpdates, getPollOptionVoters, getPollStatus, getTranscription, getWalletTransferMessage, replyRequestObjectOwner, reportObject, searchChatMessages, searchGlobalMessages, seenChats, sendChatActivity, sendMessage, sendMessageAPICall, sendWalletTransferMessage, setActionChat, setChatUseTime, setPinMessage, transcribeVoice, votePoll
### chats/links (23)
actionOnJoinRequest, createJoinLink, deleteBotChat, deleteChatHistory, deleteRevokedJoinLink, deleteUserChat, editJoinLink, getAbsObjects, getBarcodeAction, getChats, getChatsByID, getChatsUpdates, getJoinLinkUserJoined, getJoinLinks, getJoinRequests, getLandingPage, getLinkFromAppUrl, getObjectByUsername, getProfileLinkItems, getRelatedObjects, getServiceInfo, getWebAppFunction, revokeJoinLink
### channels (18)
addChannel, addChannelMembers, banChannelMember, channelPreviewByJoinLink, checkChannelUsername, editChannelInfo, getBannedChannelMembers, getChannelAdminAccessList, getChannelAdminMembers, getChannelAllMembers, getChannelInfo, getChannelLink, joinChannelAction, joinChannelByLink, removeChannel, setChannelAdmin, setChannelLink, updateChannelUsername
### groups (23)
addGroup, addGroupMembers, banGroupMember, deleteNoAccessGroupChat, editGroupInfo, getBannedGroupMembers, getCommonGroups, getGroupAdminAccessList, getGroupAdminMembers, getGroupAllMembers, getGroupDefaultAccess, getGroupInfo, getGroupLink, getGroupMentionList, getGroupMessageReadParticipants, getGroupOnlineCount, groupPreviewByJoinLink, joinGroup, leaveGroup, removeGroup, setGroupAdmin, setGroupDefaultAccess, setGroupLink
### profile/settings (50)
abortSetRecoveryEmail, abortTwoStepSetup, actionOnStickerSet, actionOnUnconfirmedSession, addAddressBook, addFolder, addSetWallpaper, addToMyGifSet, checkUserUsername, deleteAvatar, deleteContact, deleteFolder, editFolder, getAppearanceSetting, getAvatars, getBaseInfo, getBlockedUsers, getContacts, getContactsLastOnline, getContactsUpdates, getFolders, getMyGifSet, getMySessions, getMyStickerSets, getPrivacySetting, getStickerSetByID, getStickersByEmoji, getStickersBySetIDs, getSuggestedFolders, getTrendStickerSets, getTwoPasscodeStatus, getUnconfirmedSessions, getUserInfo, getUserSetting, getWallpapers, requestRecoveryEmail, resendCodeRecoveryEmail, resetContacts, resetWallpapers, searchStickers, setBlockUser, setSetting, setupTwoStepVerification, terminateOtherSessions, terminateSession, turnOffTwoStep, updateProfile, updateUsername, uploadAvatar, verifyRecoveryEmail
### voice/live (20)
addLiveComment, createGroupVoiceChat, discardGroupVoiceChat, getDisplayAsInGroupVoiceChat, getGroupVoiceChat, getGroupVoiceChatParticipants, getGroupVoiceChatParticipantsByObjectGuids, getGroupVoiceChatUpdates, getLiveComments, getLivePlayUrl, getLiveStatus, getLiveViewers, joinGroupVoiceChat, leaveGroupVoiceChat, sendGroupVoiceChatActivity, sendLive, setGroupVoiceChatSetting, setGroupVoiceChatState, setLiveSetting, stopLive
### other (19)
cancelChangeObjectOwner, checkTwoStepPasscode, getBotInfo, getDCs, getMapView, getPaymentInfo, getPendingObjectOwner, getProfilePosts, getProfilesStoryList, getSelection, getlinkObject, handShake, requestChangeObjectOwner, requestSendFile, searchGlobalObjects, searchSelection, sendRubinoPost, setAskSpamAction, stopBot

## 9) Live verification (sample calls)

```
# works today, returns URL pools
curl -s -X POST https://shgetdcmess.iranlms.ir -H 'Content-Type: application/json' \
  -d '{"api_version":"4","method":"getDCs","data":{}}' | head -c 300
# -> {"status":"OK",...,"default_api_urls":[...]}

# messaging host answers (empty/plain request is rejected, but JSON comes back)
curl -s -X POST https://shadmessenger125.iranlms.ir -H 'Content-Type: application/json' \
  -d '{"api_version":"4","method":"getTime","data":{}}'
# -> {"status":"ERROR_GENERIC","status_det":"INVALID_INPUT"}

# socket handshake works
# wss://shsocket5.iranlms.ir:80 -> {"status":"OK","status_det":"OK"}
```

## 10) Modular plan (for the library)

```
shad_api/
  config.py     # this catalogue: URL pools, versions, client info
  http.py       # POST envelope, DC rotation, retries, timeouts
  crypto.py     # RSA temp session + AES data_enc (auth & normal calls)
  auth.py       # sendCode / signIn / two-step / registerDevice
  socket.py     # wss handshake, ping, update stream
  files.py      # requestSendFile + chunk upload + GetFile.ashx download
  services.py   # getBaseInfo + suggested_* hosts
  api.py        # thin method wrappers (getChats, sendMessage, ...)
  client.py     # high-level facade (login, send, upload, contacts)
```

### نمونهٔ ورودی متدهای کلیدی

| method | model fields |
|---|---|
| `sendCode` | — |
| `registerDevice` | — |
| `getChats` | start_id |
| `getMessages` | — |
| `sendMessage` | — |
| `requestSendFile` | file_name, mime, size |
| `getUserInfo` | user_guid |
| `getContacts` | start_id |
| `getChatsByID` | object_guids |
| `getGroupInfo` | group_guid |
| `getChannelInfo` | channel_guid |
| `joinGroup` | hash_link |
| `joinChannelByLink` | hash_link |
| `getJoinLinks` | creator_guid, object_guid |
| `getMySessions` | — |
| `getTwoPasscodeStatus` | password |
| `getAbsObjects` | objects_guids |
| `getObjectByUsername` | username |
| `getMessagesInterval` | filter_type, middle_message_id, object_guid |
| `getChatsUpdates` | state |
| `getTime` | — |
| `getDCs` | — |

فهرست کامل با تمام ۱۹۵ متد و فیلدهای ورودی: `docs/shad_methods.json`

---

## ۱۱) جریان لاگین (تست زنده ✅)

ورود با شمارهٔ `09928999225` و کد پیامکی روی `shadmessenger125` تست و تأیید شد.

1. **`sendCode`** (api_version 6، `not_authorized`، `data_enc` با `tmp_session`):
```json
{"phone_number":"989928999225",      // بدون + و بدون صفر اول
 "send_type":"SMS",
 "public_key":"<Xg(base64(PEM))>"}
```
⚠️ شماره باید **بدون `+`** باشد (`989928999225`)؛ با `+98...` پاسخ `INVALID_INPUT` می‌دهد.
پاسخ: `phone_code_hash`، `code_digits_count`، `has_confirmed_recovery_email`.

2. **`signIn`** (همان پاکت، همان `tmp_session`):
```json
{"phone_number":"989928999225",
 "phone_code_hash":"...",
 "phone_code":"121571",
 "public_key":"<همان public_key>"}
```
پاسخ: `status:"OK"` + `auth` + `user`.
`auth` با **RSA-OAEP(SHA-1)** و کلید خصوصیِ همان keypair باز می‌شود → توکن ۳۲ کاراکتری.

3. **`registerDevice`** بلافاصله بعد از لاگین الزامی است؛ بدون آن همهٔ متدها
`ERROR_ACTION: NOT_REGISTERED` می‌دهند:
```json
{"token_type":"Web","token":"","app_version":"WB_4.4.26","lang_code":"fa",
 "system_version":"...","device_model":"...","device_hash":"..."}
```

4. **تماس‌های بعدی (api_version 6):**
```json
{"api_version":"6",
 "auth":"<Xg(auth_token)>",
 "data_enc":"<AES(passphrase(auth_token), {method,input,client})>",
 "sign":"<base64(RSA-SHA256(data_enc))>"}
```
پاسخ `data_enc` با همان `auth_token` رمزگشایی می‌شود.

## ۱۲) پیاده‌سازی ماژولار در پروژه

```
shad_api/
├── config.py    # URL poolها، نگارش‌ها، client info
├── crypto.py    # Xg، passphrase، AES، RSA keypair، OAEP decrypt، sign
├── http.py      # discovery (getDCs/getBaseInfo) + پاکت API + failover روی URL pool
├── session.py   # ذخیرهٔ نشست (auth، کلید خصوصی، device_hash) با مجوز 0600
├── client.py    # ShadClient: login، پروفایل، چت، مخاطب، پیام، فایل
└── __init__.py

examples/          →  login.py · list_chats.py · send_message.py · send_file.py
```

نشست ذخیره‌شده: فایل JSON انتخابی شما (پیش‌فرض `session.json`، مجوز 0600؛ شامل توکن و کلید خصوصی).

### تست‌های زنده انجام‌شده

| عملیات | نتیجه |
|---|---|
| `sendCode` + `signIn` | ✅ لاگین با کد پیامکی، توکن ذخیره شد |
| `getUserInfo` | ✅ پروفایل (نام/یوزرنیم/شناسه) |
| `getChats` | ✅ ۱۰۰ چت + `has_continue` |
| `getContacts` | ✅ ۱۰۰ مخاطب |
| `getMessages` | ✅ با `sort:"FromMax", limit` |
| `sendMessage` | ✅ ارسال متن به خود (message_id برگشت) |
| `requestSendFile` + chunk upload | ✅ آپلود ۱۵KB، گرفتن `access_hash_rec` |
| `sendMessage` با `file_inline` | ✅ ارسال فایل با کپشن |
| `download` از `storages[dc_id]` | ✅ بایت‌به‌بایت برابر فایل اصلی |

نکتهٔ فایل: `requestSendFile` فیلدهای `upload_url`, `id`, `access_hash_send`, `dc_id` می‌دهد؛
آپلود به `upload_url` با هدرهای `access-hash-send/auth/file-id/part-number/total-part/chunk-size`
(چانک ۱۳۱۰۷۲ بایت) و دانلود از `storages[dc_id]` (مثل `https://shst185.iranlms.ir/GetFile.ashx`).

## ۱۳) رمز دومرحله‌ای (2FA) و مدیریت نشست‌ها

مدل‌ها از باندل استخراج و متدهای خواندنی زنده تست شدند.

| متد | model | توضیح |
|---|---|---|
| `getTwoPasscodeStatus` | — | `{sign_in_type: "Simple"\\|"TwoStep", has_pending_recovery_email, has_confirmed_recovery_email}` |
| `checkTwoPasscode` | `{password}` | اعتبارسنجی رمز |
| `setupTwoStepVerification` | `{password, hint, recovery_email?}` | فعال‌سازی 2FA |
| `changePassword` | `{password, new_password, new_hint}` | تغییر رمز |
| `turnOffTwoStep` | `{password}` | خاموش‌کردن 2FA |
| `abortTwoStepSetup` | — | لغو فرایند فعال‌سازی |
| `requestRecoveryEmail` | `{password, recovery_email}` | درخواست ایمیل بازیابی |
| `verifyRecoveryEmail` | `{code, password?}` | تأیید کد ایمیل |
| `resendCodeRecoveryEmail` | `{password}` | ارسال دوباره کد ایمیل |
| `abortSetRecoveryEmail` | `{password}` | لغو ایمیل بازیابی |
| `getMySessions` | — | `{active_session, other_sessions[], can_remove_all}` |
| `terminateSession` | `{session_key}` | خاتمهٔ یک نشست |
| `terminateOtherSessions` | — | خاتمهٔ همهٔ نشست‌های دیگر |
| `getUnconfirmedSessions` | — | نشست‌های تأییدنشده |
| `actionOnUnconfirmedSession` | `{unconfirmed_session_key, action}` | Approve/Reject |

ورود با 2FA (قبل از لاگین):
- `loginDisableTwoStep` → `{email_code, forget_password_code_hash, phone_number}`
- `loginTwoStepForgetPassword` → `{phone_number}`

### تست زنده (فقط خواندنی)

```python
status = await client.get_two_passcode_status()
# {"sign_in_type":"Simple","has_pending_recovery_email":false,"has_confirmed_recovery_email":false}

sessions = await client.get_sessions()
# نشست فعال: Chrome | Web 4.4.26 | IP ...
# سایر نشست‌ها: ...
```

دستورهای تغییردهنده (نیاز به `--yes`): `2fa-setup`, `2fa-off`, `2fa-change`, `terminate` /
`terminate --all --yes`. هیچ‌کدام روی حساب واقعی اجرا نشدند.

## ۱۴) محدودیت‌های فایل (تست زنده)

| مورد | مقدار / نتیجه |
|---|---|
| سقف حجم `requestSendFile` | **۱۰۰ MiB** (`104857600` بایت) — ۱۰۴۸۵۷۶۰۰ OK، ۱۰۵۰۰۰۰۰۰ → `INVALID_INPUT` |
| پسوندهای مجاز (تست‌شده) | `.txt` `.pdf` `.zip` `.rar` `.jpg` `.mp4` |
| پسوندهای مسدود (تست‌شده) | `.apk` `.bin` `.gz` `.7z` → `INVALID_AUTH`/`INVALID_INPUT` |
| چانک آپلود | ۱۳۱۰۷۲ بایت (`131072`) |
| دانلود | `storages[dc_id]` → `https://shstNNN.iranlms.ir/GetFile.ashx` |

### راه‌حل‌ها در کلاینت

```python
# فایل بزرگ‌تر از ۱۰۰MB: به بخش‌های جدا بشکن
user = await client.get_user_info()
await client.send_file_split(user["user_guid"], "big.txt")

# یا zip کن (پسوند zip مجاز است)
await client.send_file_zipped(user["user_guid"], "big.txt")
```

خطای اندازه/پسوند قبل از ارسال با پیام انگلیسی و قابل‌فهم گزارش می‌شود؛
`--split` فایل را به بخش‌های `<100MiB` با نام‌گذاری `.partNN` می‌شکند.
