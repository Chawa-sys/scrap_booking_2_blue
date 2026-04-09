import pandas as pd
from flask import make_response
from io import BytesIO, StringIO

def export_to_csv(hoteles, campos):
    df = pd.DataFrame(hoteles)
    if campos:  # Verificamos si se seleccionaron campos
        df = df[[c for c in campos if c in df.columns]]
    output = StringIO()
    df.to_csv(output, index=False)
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=resultados.csv"
    response.headers["Content-type"] = "text/csv"
    print("Campos seleccionados:", campos)

    return response

def export_to_excel(hoteles, campos):
    df = pd.DataFrame(hoteles)
    if campos:
        df = df[[c for c in campos if c in df.columns]]
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Resultados")
    output.seek(0)
    response = make_response(output.read())
    response.headers["Content-Disposition"] = "attachment; filename=resultados.xlsx"
    response.headers["Content-type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    print("Campos seleccionados:", campos)

    return response
    


