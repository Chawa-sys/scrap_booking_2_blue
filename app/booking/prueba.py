import asyncio
import urllib.parse
from playwright.async_api import async_playwright

async def obtener_datos_hoteles(destino, fecha_inicio, fecha_fin):
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
            btn_aceptar = await page.query_selector('button:has-text("Aceptar")')
            if btn_aceptar:
                await btn_aceptar.click()
        except:
            pass

        # Esperar a que cargue la lista de hoteles
        try:
            await page.wait_for_selector('div[data-testid="property-card"]', timeout=50000)
        except:
            print("❌ No se cargaron los hoteles.")
            await browser.close()
            return

        hoteles = await page.query_selector_all('div[data-testid="property-card"]')
        if not hoteles:
            print("⚠️ No se encontraron hoteles.")
            await browser.close()
            return

        print(f"🔎 Se encontraron {len(hoteles)} hoteles. Mostrando los primeros 5:\n")

        for i, hotel in enumerate(hoteles[:5], 1):
            print(f"🏨 Hotel #{i}")

            # Nombre
            titulo = await hotel.query_selector('div[data-testid="title"]')
            nombre = await titulo.inner_text() if titulo else "N/A"
            print(f"   🏷️ Nombre: {nombre}")
            
            # Imagen
            imagen = await hotel.query_selector('img[data-testid="image"]')
            imagen_url = await imagen.get_attribute("src") if imagen else "N/A"
            print(f"   🖼️ Imagen: {imagen_url}")

            # Precio
            precio = await hotel.query_selector('span[data-testid="price-and-discounted-price"]')
            precio_texto = await precio.inner_text() if precio else "N/A"
            print(f"   💰 Precio: {precio_texto}")

            # Puntaje numérico
            puntaje = await hotel.query_selector('div[data-testid="review-score"] div[aria-hidden="true"]')
            puntaje_texto = await puntaje.inner_text() if puntaje else "Sin puntuación"
            print(f"   ⭐ Puntaje: {puntaje_texto}")

            # Descripción del puntaje
            descripcion = await hotel.query_selector('div[data-testid="review-score"] div[aria-hidden="false"] > div')
            descripcion_texto = await descripcion.inner_text() if descripcion else "N/A"
            print(f"   💬 Descripción: {descripcion_texto}")

            # Comentarios
            comentarios = await hotel.query_selector('div[aria-hidden="false"] > div:nth-child(2)')
            comentarios_texto = await comentarios.inner_text() if comentarios else "N/A"
            print(f"   🗣️ Comentarios: {comentarios_texto}")
            
            # Dirección
            direccion = await hotel.query_selector('span[data-testid="address"]')
            direccion_texto = await direccion.inner_text() if direccion else "N/A"
            print(f"   📍 Dirección: {direccion_texto}")
            
            # Distancia
            distancia = await hotel.query_selector('span[data-testid="distance"]')
            distancia_texto = await distancia.inner_text() if distancia else "N/A"
            print(f"   📏 Distancia: {distancia_texto}")

            # Estrellas
            estrellas = await hotel.query_selector('div[role="button"][aria-label*="de 5"]')
            estrellas_texto = await estrellas.get_attribute("aria-label") if estrellas else "N/A"
            print(f"   ⭐ Estrellas: {estrellas_texto}")

            # Calificación Ubicación
            ubicacion_span = await hotel.query_selector('a[data-testid="secondary-review-score-link"] span')
            ubicacion_texto = await ubicacion_span.inner_text() if ubicacion_span else "N/A"
            # Separar por espacio desde el final
            if ubicacion_texto != "N/A":
                partes = ubicacion_texto.strip().rsplit(" ", 1)
                ubicacion_label = partes[0] if len(partes) > 0 else "N/A"
                ubicacion_puntaje = partes[1] if len(partes) > 1 else "N/A"
            else:
                ubicacion_label = "N/A"
                ubicacion_puntaje = "N/A"
            print(f"   📌 {ubicacion_label}: {ubicacion_puntaje}")

            # Oferta
            oferta = await hotel.query_selector('span[data-testid="property-card-deal"] span')
            oferta_texto = await oferta.inner_text() if oferta else "N/A"
            print(f"   🏷️ Oferta: {oferta_texto}")

            # Nombre - habitación
            habitacion = await hotel.query_selector('div[data-testid="recommended-units"] h4')
            habitacion_texto = await habitacion.inner_text() if habitacion else "N/A"
            print(f"   🛏️ Habitación: {habitacion_texto}")
            
            # Tipo de unidad
            tipo_unidad = await hotel.query_selector('div[data-testid="property-card-unit-configuration"] span')
            tipo_unidad_texto = await tipo_unidad.inner_text() if tipo_unidad else "N/A"
            print(f"   🏠 Tipo de unidad: {tipo_unidad_texto}")
            
            # Tipo de cama
            tipo_cama = await hotel.query_selector('//div[@data-testid="recommended-units"]//li[1]/div[1]/div[1]')
            tipo_cama_texto = await tipo_cama.inner_text() if tipo_cama else "N/A"
            print(f"   🛌 Tipo de cama: {tipo_cama_texto}")
            
            # Desayuno
            desayuno = await hotel.query_selector('//div[@data-testid="recommended-units"]//li//span[contains(translate(text(), "DESAYUNO", "desayuno"), "desayuno")]')
            desayuno_texto = await desayuno.inner_text() if desayuno else "N/A"
            print(f"   🥐 Desayuno: {desayuno_texto}")

            
            # Cancelación 
            cancelacion = await hotel.query_selector('//span[@data-testid="cancellation-policy-icon"]/parent::div/following-sibling::div//strong')
            cancelacion_texto = await cancelacion.inner_text() if cancelacion else "N/A"
            print(f"   ✅ Cancelación: {cancelacion_texto}")
            
            # Pago
            pago = await hotel.query_selector('//span[@data-testid="prepayment-policy-icon"]/parent::div/following-sibling::div//div')
            pago_texto = await pago.inner_text() if pago else "N/A"
            print(f"   💵 Pago: {pago_texto}")
            
            # Urgencia
            urgencia = await hotel.query_selector('div.b7d3eb6716') #Clase ofuscada usada temporalmente. Si Booking cambia su sistema de clases, este campo dejará de funcionar.
            urgencia_texto = await urgencia.inner_text() if urgencia else "N/A"
            print(f"   ⚠️ Urgencia: {urgencia_texto}")

            # Precio original
            precio_original = await hotel.query_selector('//div[@data-testid="availability-rate-wrapper"]//span[@aria-hidden="true" and contains(text(), "S/")]')
            precio_original_texto = await precio_original.inner_text() if precio_original else "N/A"
            print(f"   💸 Precio original: {precio_original_texto}")
            
            # Impuestos
            impuestos = await hotel.query_selector('div[data-testid="taxes-and-charges"]')
            impuestos_texto = await impuestos.inner_text() if impuestos else "N/A"
            print(f"   ➕ Impuestos: {impuestos_texto}")



            
            print("-" * 60)

        await browser.close()

def ejecutar_scraper_multiple():
    destino = "Cusco"
    checkin = "2025-06-15"
    checkout = "2025-06-16"
    asyncio.run(obtener_datos_hoteles(destino, checkin, checkout))

ejecutar_scraper_multiple()
