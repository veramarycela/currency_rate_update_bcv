from odoo import fields, models
import requests
import pandas as pd
from io import BytesIO

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

        return ["VEF", "USD"]

    def _obtain_rates(self, base_currency, currencies, date_from, date_to):
        self.ensure_one()
        if self.service != "BCV":
            return super()._obtain_rates(base_currency, currencies, date_from, date_to)
        print(base_currency)
        print(currencies)
        print(date_from)
        print(date_to)
        # URL del archivo Excel
        url = "https://www.bcv.org.ve/sites/default/files/EstadisticasGeneral/2_1_2d23_smc.xls"

        # Realizar la solicitud GET para descargar el archivo
        response = requests.get(url, verify=False)

        # Verificar si la solicitud fue exitosa
        if response.status_code == 200:
            # Leer el contenido del archivo Excel desde la respuesta
            excel_content = response.content
            print(excel_content)
            # Leer el archivo Excel usando pandas
            df = pd.read_excel(BytesIO(excel_content))

            # Filtrar los datos por fecha y monedas específicas
            df_filtered = df[df["Fecha"] >= date_from]
            df_filtered = df_filtered[df_filtered["Fecha"] <= date_to]
            df_filtered = df_filtered[df_filtered["Moneda"].isin(currencies)]

            # Crear un diccionario con las tasas de cambio
            content = {}
            for index, row in df_filtered.iterrows():
                fecha_valor = row["Fecha"].strftime("%Y-%m-%d")
                moneda = row["Moneda"]
                tasa_cambio = row["Tasa de cambio"]

                if fecha_valor not in content:
                    content[fecha_valor] = {}

                content[fecha_valor][moneda] = tasa_cambio

            print(content)
            return content
        else:
            print("Error al descargar el archivo:", response.status_code)
            return {}