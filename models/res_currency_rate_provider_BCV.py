# Copyright 2009 Camptocamp
# Copyright 2009 Grzegorz Grzelak
# Copyright 2019 Brainbean Apps (https://brainbeanapps.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models
from collections import defaultdict
from datetime import date, timedelta
from urllib.request import urlopen
from io import BytesIO
from pathlib import Path
from bs4 import BeautifulSoup

import xml.sax
import os
import requests
import pandas as pd
import urllib.request
import time




class ResCurrencyRateProviderBCV(models.Model):
    _inherit = "res.currency.rate.provider"

    service = fields.Selection(
        selection_add=[("BCV", "Banco Central de Venezuela")],
        ondelete={"BCV": "set default"},
    )

    def _get_supported_currencies(self):
        self.ensure_one()
        if self.service != "BCV":
            return super()._get_supported_currencies()

        # Lista de monedas desde el archivo Excel
        return ["VEF", "USD"] 
               

    def _obtain_rates(self, base_currency, currencies, date_from, date_to):
        self.ensure_one()
        if self.service != "BCV":
            return super()._obtain_rates(base_currency, currencies, date_from, date_to)
        
        

        url = "https://www.bcv.org.ve/seccionportal/tipo-de-cambio-oficial-del-bcv"

        # Realizar la solicitud GET a la página web
        response = requests.get(url, verify=False)
        time.sleep(2)
        
        # Verificar si la solicitud fue exitosa (código de estado 200)
        if response.status_code == 200:
            # Analizar el contenido HTML de la página web
            soup = BeautifulSoup(response.content, "html.parser")
    
            # Encontrar el elemento div con la clase "recuadrotsmc"
            tipo_cambio_element = soup.find("div", id="dolar")
    
            # Extraer el valor del tipo de cambio USD
            tipo_cambio_usd = tipo_cambio_element.find("strong").text.strip()

            print("Tipo de cambio USD:", tipo_cambio_usd)
        else:
            print("Error al obtener la página:", response.status_code)

        # Encontrar el elemento div con la clase "pull-right dinpro center"
        fecha_valor_element = soup.find("div", class_="pull-right dinpro center")

        # Extraer la fecha valor del span dentro del elemento encontrado
        fecha_valor_span = fecha_valor_element.find("span", class_="date-display-single")
        fecha_valor = fecha_valor_span["content"]

        # Crear un diccionario con las tasas de cambio

        content = {
        fecha_valor: {"VEF": 1.0},  # Tipo de cambio del bolívar venezolano (VES) a dólar estadounidense (USD)
        fecha_valor: {"USD": float(tipo_cambio_usd.replace(',', '.'))}  # Tipo de cambio del dólar estadounidense (USD) a bolívar venezolano (VEF)
         }
        
        print(content)
        return content


class EcbRatesHandler(xml.sax.ContentHandler):
    def __init__(self, currencies, date_from, date_to):
        self.currencies = currencies
        self.date_from = date_from
        self.date_to = date_to
        self.date = None
        self.content = defaultdict(dict)

    def startElement(self, name, attrs):
        if name == "Cube" and "time" in attrs:
            self.date = fields.Date.from_string(attrs["time"])
        elif name == "Cube" and all([x in attrs for x in ["currency", "rate"]]):
            currency = attrs["currency"]
            rate = attrs["rate"]
            if (
                (self.date_from is None or self.date >= self.date_from)
                and (self.date_to is None or self.date <= self.date_to)
                and currency in self.currencies
            ):
                self.content[self.date.isoformat()][currency] = rate
