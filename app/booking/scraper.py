import asyncio
import urllib.parse
from datetime import timedelta
from playwright.async_api import async_playwright


async def scraper_async(destino, fecha_inicio, fecha_fin, limite=20, scroll_count=2):
    resultados = []
    destino_codificado = urllib.parse.quote(destino)

    url = (
        f"https://www.booking.com/searchresults.es.html?ss={destino_codificado}"
        f"&checkin={fecha_inicio}&checkout={fecha_fin}&group_adults=2&no_rooms=1&group_children=0"
    )

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/121.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        print(f"Navegando a: {url}")
        await page.goto(url, timeout=90000, wait_until="domcontentloaded")

        # Aceptar cookies
        try:
            aceptar_btn = await page.query_selector('button:has-text("Aceptar")')
            if aceptar_btn:
                await aceptar_btn.click()
        except:
            pass

        # Esperar hoteles
        try:
            await page.wait_for_selector('div[data-testid="property-card"]', timeout=50000)
        except:
            print("⚠️ No se encontraron hoteles o la página tardó demasiado.")
            await browser.close()
            return []

        # Scroll para cargar más resultados
        for _ in range(scroll_count):
            await page.mouse.wheel(0, 5000)
            await page.wait_for_timeout(3000)

        hoteles = await page.query_selector_all('div[data-testid="property-card"]')
        for hotel in hoteles[:limite]:
            hotel_dict = {}

            # Nombre
            try:
                titulo = await hotel.query_selector('div[data-testid="title"]')
                hotel_dict["hotel"] = await titulo.inner_text() if titulo else "N/A"
            except:
                hotel_dict["hotel"] = "N/A"

            # Imagen
            try:
                img = await hotel.query_selector('img[data-testid="image"]')
                hotel_dict["imagen_url"] = await img.get_attribute("src") if img else "N/A"
            except:
                hotel_dict["imagen_url"] = "N/A"

            # Precio final
            try:
                precio = await hotel.query_selector('span[data-testid="price-and-discounted-price"]')
                hotel_dict["price"] = await precio.inner_text() if precio else "N/A"
            except:
                hotel_dict["price"] = "N/A"

            # Precio original
            try:
                original = await hotel.query_selector('//div[@data-testid="availability-rate-wrapper"]//span[@aria-hidden="true" and contains(text(), "S/")]')
                hotel_dict["precio_original"] = await original.inner_text() if original else "N/A"
            except:
                hotel_dict["precio_original"] = "N/A"

            # Puntaje
            try:
                score = await hotel.query_selector('div[data-testid="review-score"] div[aria-hidden="true"]')
                hotel_dict["score"] = await score.inner_text() if score else "N/A"
            except:
                hotel_dict["score"] = "N/A"

            # Descripción textual del puntaje
            try:
                desc = await hotel.query_selector('div[data-testid="review-score"] div[aria-hidden="false"] > div:nth-child(1)')
                hotel_dict["avg_review"] = await desc.inner_text() if desc else "N/A"
            except:
                hotel_dict["avg_review"] = "N/A"

            # Número de reseñas
            try:
                count = await hotel.query_selector('div[data-testid="review-score"] div[aria-hidden="false"] > div:nth-child(2)')
                raw = await count.inner_text()
                hotel_dict["reviews_count"] = raw.split()[0] if raw else "N/A"
            except:
                hotel_dict["reviews_count"] = "N/A"

            # Dirección
            try:
                dir = await hotel.query_selector('span[data-testid="address"]')
                hotel_dict["direccion"] = await dir.inner_text() if dir else "N/A"
            except:
                hotel_dict["direccion"] = "N/A"

            # Distancia
            try:
                dist = await hotel.query_selector('span[data-testid="distance"]')
                hotel_dict["distancia"] = await dist.inner_text() if dist else "N/A"
            except:
                hotel_dict["distancia"] = "N/A"

            # Estrellas
            try:
                estrellas = await hotel.query_selector('div[role="button"][aria-label*="de 5"]')
                hotel_dict["estrellas"] = await estrellas.get_attribute("aria-label") if estrellas else "N/A"
            except:
                hotel_dict["estrellas"] = "N/A"

            # Calificación de ubicación
            try:
                ubicacion = await hotel.query_selector('a[data-testid="secondary-review-score-link"] span')
                ubicacion_texto = await ubicacion.inner_text() if ubicacion else "N/A"
                partes = ubicacion_texto.strip().rsplit(" ", 1) if ubicacion_texto != "N/A" else []
                hotel_dict["ubicacion_texto"] = partes[0] if len(partes) > 0 else "N/A"
                hotel_dict["ubicacion_score"] = partes[1] if len(partes) > 1 else "N/A"
            except:
                hotel_dict["ubicacion_texto"] = "N/A"
                hotel_dict["ubicacion_score"] = "N/A"

            # Impuestos
            try:
                impuestos = await hotel.query_selector('div[data-testid="taxes-and-charges"]')
                hotel_dict["impuestos"] = await impuestos.inner_text() if impuestos else "N/A"
            except:
                hotel_dict["impuestos"] = "N/A"

            # Habitación
            try:
                habitacion = await hotel.query_selector('div[data-testid="recommended-units"] h4')
                hotel_dict["habitacion"] = await habitacion.inner_text() if habitacion else "N/A"
            except:
                hotel_dict["habitacion"] = "N/A"

            # Tipo de unidad
            try:
                unidad = await hotel.query_selector('div[data-testid="property-card-unit-configuration"] span')
                hotel_dict["tipo_unidad"] = await unidad.inner_text() if unidad else "N/A"
            except:
                hotel_dict["tipo_unidad"] = "N/A"

            # Tipo de cama
            try:
                cama = await hotel.query_selector('//div[@data-testid="recommended-units"]//li[1]/div[1]/div[1]')
                hotel_dict["tipo_cama"] = await cama.inner_text() if cama else "N/A"
            except:
                hotel_dict["tipo_cama"] = "N/A"

            # Desayuno
            try:
                desayuno = await hotel.query_selector('//div[@data-testid="recommended-units"]//li//span[contains(translate(text(), "DESAYUNO", "desayuno"), "desayuno")]')
                hotel_dict["desayuno"] = await desayuno.inner_text() if desayuno else "N/A"
            except:
                hotel_dict["desayuno"] = "N/A"

            # Cancelación
            try:
                cancelacion = await hotel.query_selector('//span[@data-testid="cancellation-policy-icon"]/parent::div/following-sibling::div//strong')
                hotel_dict["cancelacion"] = await cancelacion.inner_text() if cancelacion else "N/A"
            except:
                hotel_dict["cancelacion"] = "N/A"

            # Pago
            try:
                pago = await hotel.query_selector('//span[@data-testid="prepayment-policy-icon"]/parent::div/following-sibling::div//div')
                hotel_dict["pago"] = await pago.inner_text() if pago else "N/A"
            except:
                hotel_dict["pago"] = "N/A"

            # Urgencia
            try:
                urgencia = await hotel.query_selector('div.b7d3eb6716')
                hotel_dict["urgencia"] = await urgencia.inner_text() if urgencia else "N/A"
            except:
                hotel_dict["urgencia"] = "N/A"

            # Oferta
            try:
                oferta = await hotel.query_selector('span[data-testid="property-card-deal"] span')
                hotel_dict["oferta"] = await oferta.inner_text() if oferta else "N/A"
            except:
                hotel_dict["oferta"] = "N/A"

            resultados.append(hotel_dict)

        await browser.close()
        print(f"🔍 Total de hoteles encontrados: {len(hoteles)}")

    return resultados

# Adaptador sincrónico para usar en Flask
def obtener_resultados(destino, fecha_inicio, fecha_fin, limite=20):
    if limite <= 5:
        scroll_count = 1
    elif limite <= 20:
        scroll_count = 2
    elif limite <= 40:
        scroll_count = 4
    elif limite <= 60:
        scroll_count = 6
    else:
        scroll_count = 8  # máximo
    return asyncio.run(scraper_async(destino, fecha_inicio, fecha_fin, limite, scroll_count))



