import io
import pandas as pd
import re
from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import logging

app = FastAPI()
templates = Jinja2Templates(directory="templates")

logging.basicConfig(level=logging.INFO)

@app.post("/convert")
async def convert_file(file: UploadFile = File(...)):
    logging.info("File upload received.")
    
    # Datei einlesen
    data = await file.read()
    
    # Datei als ISO-8859-1 (ANSI) dekodieren
    data = data.decode('ISO-8859-1', errors="ignore")  # Alternativer Zeichensatz
    logging.info("File decoded using ISO-8859-1.")

    # Datei in Zeilen aufteilen
    lines = data.split('\n')
    logging.info(f"File split into {len(lines)} lines.")

    # Artikelinformationen extrahieren
    articles = []
    for line in lines:
        if line.startswith('PG321;'):
            article_data = line.split(';')
            article = {
                'EAN': article_data[1],
                'Objektnummer': article_data[3],
                'Objektbezeichnung': article_data[4],
                'Ausgnr': article_data[5],
                'VKP Verkaufspreis': article_data[6],
                'AGP Einkaufspreis': article_data[7],
                'Menge': article_data[8],
                'Gesamt': article_data[9],
                'MWST': article_data[11]
            }
            articles.append(article)

    logging.info(f"Extracted {len(articles)} articles.")

    # DataFrame erstellen
    df = pd.DataFrame(articles)

    # Filialinformationen extrahieren
    filiale_info = ''
    for line in lines:
        if line.startswith('PG312;'):
            filiale_data = line.split(';')
            filiale_info = f"Filiale_{filiale_data[2]}_Standort_{filiale_data[7]}"
            break

    logging.info(f"Filialinformationen: {filiale_info}")

    # Datum und Lieferscheinnummer extrahieren
    datum = ''
    lieferscheinnummer = ''
    for line in lines:
        if line.startswith('PG320;'):
            pg320_data = line.split(';')
            datum = pg320_data[1]
            lieferscheinnummer = pg320_data[3]
            break

    logging.info(f"Datum: {datum}, Lieferscheinnummer: {lieferscheinnummer}")

    # # Neue Zeile mit Informationen erstellen
    # new_row = {
    #     'EAN': 'Informationen',
    #     'Objektnummer': '',
    #     'Objektbezeichnung': '',
    #     'Ausgnr': '',
    #     'VKP Verkaufspreis': '',
    #     'AGP Einkaufspreis': '',
    #     'Menge': '',
    #     'Gesamt': '',
    #     'MWST': f"{filiale_info} {datum} {lieferscheinnummer}"
    # }

    # # Neue Zeile an den Anfang des DataFrames einfügen
    # df = pd.concat([pd.DataFrame([new_row]), df], ignore_index=True)

    # Excel-Datei in Arbeitsspeicher schreiben
    excel_file = io.BytesIO()
    with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Sheet1', index=False)

    # Excel-Datei als Antwort zurückgeben
    excel_file.seek(0)

    # Überprüfen der Variablen
    if not filiale_info:
        filiale_info = "Unbekannte_Filiale"
    if not datum:
        datum = "Unbekanntes_Datum"
    if not lieferscheinnummer:
        lieferscheinnummer = "Unbekannte_Lieferscheinnummer"

    filename = f"{filiale_info}_{datum}_{lieferscheinnummer}.xlsx"
    filename = re.sub(r'[^a-zA-Z0-9_\.]', '_', filename)  # Nicht-alphanumerische Zeichen ersetzen

    headers = {
        'Content-Disposition': f'attachment; filename="{filename}"'
    }

    logging.info(f"Returning file {filename}.")

    return StreamingResponse(excel_file, headers=headers, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.get("/", response_class=HTMLResponse)
async def main(request: Request):
    logging.info("Serving main page.")
    return templates.TemplateResponse("index.html", {"request": request})
