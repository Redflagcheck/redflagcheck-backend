# RedFlagCheck – MVP

AI-tool die berichten analyseert op red flags (ghosting, manipulatie, bindingsangst).

## MVP Scope
- WordPress intake (WPForms + WooCommerce + myCred)
- Django backend (intake, analyse, feedback)
- Direct resultaat online
- E-mailrapport na verificatie (+1 credit bonus)
- Enquête na resultaat (+1 credit bonus)

## User flow
1. Homepage → tekst + mood (sessie)
2. Betaling via WooCommerce → credits
3. Voorbereiden → context / naam / screenshot
4. Intake → Django (`analysis_id` terug)
5. Analyse → resultaat direct tonen
6. Optioneel e-mailrapport (verificatie)
7. Optioneel feedback (rating + comment)

## Checklist
- [ ] WordPress intake + saldo-check
- [ ] Voorbereiden → doorsturen naar Django
- [ ] Django model + `/api/intake`
- [ ] Analyse starten + resultaat tonen
- [ ] E-mailverificatie flow
- [ ] Feedback + bonus