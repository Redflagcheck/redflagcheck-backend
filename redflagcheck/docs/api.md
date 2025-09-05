# API Documentatie – RedFlagCheck MVP

Alle endpoints communiceren via **JSON** en gebruiken standaard HTTP-statuscodes.  
Authenticatie: `Authorization: Bearer RFC_API_KEY` (server-to-server).  

---

## POST /api/intake
**Doel:** Intake opslaan, nieuw `analysis_id` genereren.

### Request
```json
{
  "email": "user@example.com",
  "text": "Hoi hoe gaat het?",
  "mood": "Neutraal",
  "name": "Jan",
  "context": "We chatten 2 weken",
  "screenshot_url": "https://.../upload.png",
  "source": "wpforms_prepare"
}
Response
json
Code kopiëren
{ "analysis_id": "uuid" }
Fouten
400 → ontbrekende velden

401/403 → geen/ongeldige API key

POST /api/feedback
Doel: Feedback (rating + optionele comment) opslaan bij een analyse.
Beloning: +1 bonuscredit via WordPress webhook (éénmalig per analysis_id).

Request
json
Code kopiëren
{
  "analysis_id": "uuid",
  "rating": "Slecht | Neutraal | Goed",
  "comment": "optioneel"
}
Response
json
Code kopiëren
{ "ok": true }
Fouten
400 → ontbrekende velden of ongeldige rating

404 → analysis_id niet gevonden

POST /api/request_verification
Doel: Verstuur een magic link om een e-mailadres te verifiëren.
Na klik → GET /api/verify.

Request
json
Code kopiëren
{
  "email": "user@example.com",
  "analysis_id": "uuid",
  "callback_url": "https://redflagcheck.nl/wp-json/rfc/v1/bonus"
}
Response
json
Code kopiëren
{ "ok": true }
Fouten
400 → ongeldig of ontbrekend e-mailadres

429 → te vaak aangevraagd

GET /api/verify
Doel: Valideer magic link token → markeer e-mail als verified → roep callback aan.

Query
bash
Code kopiëren
/api/verify?token=...
Gedrag
Geldige token:

markeer e-mail als verified

POST callback naar WordPress webhook (bonus)

redirect naar /verificatie-gelukt/

Ongeldige/expired token:

redirect naar /verificatie-mislukt/

WordPress Webhooks (aangeroepen door backend)
1) Bonus na verificatie
bash
Code kopiëren
POST https://redflagcheck.nl/wp-json/rfc/v1/bonus
Headers

css
Code kopiëren
Content-Type: application/json
X-RFC-Signature: <HMAC_SHA256(raw_body, RFC_BONUS_SECRET)>
Body

json
Code kopiëren
{
  "email": "user@example.com",
  "analysis_id": "uuid"
}
Response

json
Code kopiëren
{ "ok": true }
2) Bonus na feedback
bash
Code kopiëren
POST https://redflagcheck.nl/wp-json/rfc/v1/feedback-bonus
Headers

css
Code kopiëren
Content-Type: application/json
X-RFC-Signature: <HMAC_SHA256(raw_body, RFC_BONUS_SECRET)>
Body

json
Code kopiëren
{
  "email": "user@example.com",
  "analysis_id": "uuid"
}
Response

json
Code kopiëren
{ "ok": true }
Beveiliging
API-key: alle calls vanuit WordPress → Django vereisen Authorization: Bearer RFC_API_KEY.

HMAC-handtekening: Django → WordPress webhook-calls gebruiken X-RFC-Signature (HMAC_SHA256(raw_body, RFC_BONUS_SECRET)).

Magic link tokens: éénmalig geldig, TTL ~30 minuten.

Statuscodes (overzicht)
200 → Succes

201 → Succes + object aangemaakt

400 → Bad request (ontbrekende of verkeerde velden)

401 → Unauthorized (geen/ongeldige API key)

403 → Forbidden (geen toegang)

404 → Niet gevonden

429 → Rate limit overschreden

500 → Server error

yaml
Code kopiëren

---

✅ Dit bestand is volledig genoeg om jouw backend te bouwen én voor later als je anderen erbij haalt.  

Wil je dat ik nu ook het **`models.py` voorstel (met JSON-veld)** uitschrijf zodat je backend skeleton meteen aansluit op dit API-plan?