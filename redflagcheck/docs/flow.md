# Klantreis – RedFlagCheck MVP

## Stap 1 – Homepage
- Formulier: tekst + mood
- Opslag in sessie

## Stap 2 – Saldo-check / Betalen
- Credit-check via myCred
- WooCommerce betaling + +1 credit

## Stap 3 – Voorbereiden
- Context, naam, screenshot
- Samenvatting (tekst + mood) tonen

## Stap 4 – Intake → Django
- POST /api/intake
- `analysis_id` terug
- Redirect naar /analyse/?a=...

## Stap 5 – Analyse
- Resultaat tonen
- Credit -1

## Stap 6 – E-mailrapport (optioneel)
- Verificatie met magic link
- +1 bonuscredit na verificatie

## Stap 7 – Feedback (optioneel)
- Rating: Slecht / Neutraal / Goed
- Optioneel comment
- +1 bonuscredit na invullen
