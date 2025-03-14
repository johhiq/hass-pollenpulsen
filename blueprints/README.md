## Pollenvarningar

För att få notifieringar när pollennivåer överstiger en viss nivå, kan du använda vår blueprint för pollenvarningar.

### Förutsättningar

- Home Assistant med Pollenpulsen-integrationen installerad och konfigurerad
- Minst en region konfigurerad i Pollenpulsen-integrationen

Om du inte redan har installerat Pollenpulsen-integrationen, följ instruktionerna i [huvuddokumentationen](https://github.com/johhiq/pollenpulsen).

### Installation

1. Gå till Inställningar > Automatisering > Blueprints
2. Klicka på "Importera Blueprint"
3. Klistra in följande URL:
   ```
   https://github.com/johhiq/pollenpulsen/blob/main/blueprints/pollen_alert.yaml
   ```
4. Klicka på "Förhandsgranska" och sedan "Importera"

### Användning

Efter import kan du skapa en automatisering som:
- Skickar en notifiering när en eller flera pollentyper överstiger en viss nivå
- Låter dig välja vilken tid på dagen du vill få notifieringen
- Kan inkludera hela pollenprognosen i notifieringen

Du kan välja flera pollentyper (t.ex. Al, Björk och Gräs) och få en samlad notifiering när någon av dem överstiger din valda tröskelnivå.

### Pollennivåer

Blueprinten använder följande nivåer:
- 0: Inga halter
- 1: Låga halter
- 2: Låga till måttliga halter
- 3: Måttliga halter
- 4: Måttliga till höga halter
- 5: Höga halter

Notifieringar skickas endast för faktiska pollennivåer (0-5), inte för specialvärden som "Data saknas" (6), "Pollensäsongen ej börjat" (7) eller "Pollensäsongen är slut" (8).

### Användningsexempel

Du kan använda samma blueprint flera gånger för att skapa olika automatiseringar med olika inställningar:

1. **Få notifiering när pollen försvinner**
   - Välj nivå "0 - Inga halter"
   - Perfekt för att veta när pollensäsongen är över för en viss pollentyp

2. **Få notifiering vid låga nivåer**
   - Välj nivå "1 - Låga halter"
   - Bra för dig som är mycket känslig

3. **Få notifiering vid måttliga nivåer**
   - Välj nivå "3 - Måttliga halter"
   - Lämpligt för de flesta allergiker

4. **Få notifiering endast vid höga nivåer**
   - Välj nivå "5 - Höga halter"
   - För dig som bara reagerar på höga nivåer

### Ta bort en automatisering

Om du vill ta bort en automatisering som du har skapat med denna blueprint:

1. Gå till Inställningar > Automatisering
2. Hitta automatiseringen i listan
3. Klicka på de tre prickarna (⋮) till höger om automatiseringen
4. Välj "Ta bort"
5. Bekräfta borttagningen

Observera att detta inte tar bort själva blueprinten, bara den specifika automatiseringen.
