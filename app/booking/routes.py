from flask import render_template, request, redirect, url_for, session, flash, send_file, abort
from app.booking import booking_bp
from app.booking.forms import BookingForm
from app.booking.scraper import obtener_resultados
from app.booking.exporter import export_to_csv, export_to_excel 
from datetime import datetime, timedelta
from app import db
from app.auth.models import User
from flask_login import login_required, current_user
from app.booking.models import Busqueda, Resultado
from flask_login import login_required

resultados_cache = []   

@booking_bp.route('/buscar', methods=['GET', 'POST'])
@login_required
def index():
    current_year = datetime.now().year

    form = BookingForm()
    if form.validate_on_submit():
        destino = form.destino.data
        fecha_inicio = form.fecha_inicio.data
        fecha_fin = form.fecha_fin.data
        cantidad = form.cantidad_hoteles.data or 20  # Valor por defecto
        
        #Búsuqeda por día
        if 'buscar_por_dia' in request.form:
            session['form_dia_destino'] = destino
            session['form_dia_fecha_inicio'] = str(fecha_inicio)
            session['form_dia_fecha_fin'] = str(fecha_fin)
            session['form_dia_limite'] = cantidad
            session.pop('resultados_por_dia', None)
            return redirect(url_for('booking.resultados_por_dia', page=1))
        
        #Búsqueda estandar
        global resultados_cache
        resultados_cache = obtener_resultados(destino, fecha_inicio, fecha_fin, cantidad)
        
        
        # --- INICIO DEL BLOQUE A INSERTAR ---
        # Guardar en la base de datos como entrada de historial (no guardado)
        from app.booking.models import Busqueda, Resultado

        # Crear objeto Busqueda temporal
        busqueda_temp = Busqueda(
            usuario_id=current_user.id,
            tipo='completo',
            destino=destino,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            es_guardado=False
        )
        db.session.add(busqueda_temp)
        db.session.commit()

        # Guardar cada resultado asociado
        for r in resultados_cache:
            resultado = Resultado(
                busqueda_id=busqueda_temp.id,
                datos=r
            )
            db.session.add(resultado)
        db.session.commit()
        # --- FIN DEL BLOQUE A INSERTAR ---
        
        #from flask import session
        # Guardar en sesión
        session['ultima_busqueda'] = resultados_cache
        session['resultados'] = resultados_cache  # esta es la clave usada por el exportador

        session['checkin'] = str(fecha_inicio)
        session['checkout'] = str(fecha_fin)
        session.pop('ultimo_hotel', None)  # Limpiar si hay un hotel anterior
        session['ultima_vista'] = 'resultados'
        session['tipo_resultado'] = 'completo'
        
        session['volver_a_resultado'] = 'resultados' # Detalle de redirección del guardado
        
        return render_template('resultados.html', resultados=resultados_cache, checkin=fecha_inicio, checkout=fecha_fin) 
    
    return render_template('index.html', form=form, current_year=current_year)

@booking_bp.route('/exportar/csv', methods=['POST'])
def exportar_csv():
    campos = request.form.getlist('campos')
    tipo_resultado = session.get('tipo_resultado')

    if tipo_resultado == 'por_dia':
        hoteles = session.get('precios_por_dia', [])
    elif tipo_resultado == 'resultados_por_dia':
        # Combinamos todos los días
        datos_por_dia = session.get('resultados_por_dia', [])
        hoteles = []
        for dia in datos_por_dia:
            for idx, hotel in enumerate(dia['datos']):
                hotel = hotel.copy()
                hotel['fecha'] = dia['fecha']
                hotel['posicion'] = idx + 1
                hoteles.append(hotel)
    else:
        hoteles = session.get('resultados', [])

    return export_to_csv(hoteles, campos)


@booking_bp.route('/exportar/excel', methods=['POST'])
def exportar_excel():
    campos = request.form.getlist('campos')
    tipo_resultado = session.get('tipo_resultado')

    if tipo_resultado == 'por_dia':
        hoteles = session.get('precios_por_dia', [])
    elif tipo_resultado == 'resultados_por_dia':
        # Combinamos todos los días
        datos_por_dia = session.get('resultados_por_dia', [])
        hoteles = []
        for dia in datos_por_dia:
            for idx, hotel in enumerate(dia['datos']):
                hotel = hotel.copy()
                hotel['fecha'] = dia['fecha']
                hotel['posicion'] = idx + 1
                hoteles.append(hotel)
    else:
        hoteles = session.get('resultados', [])

    return export_to_excel(hoteles, campos)



@booking_bp.route('/ver-precios-por-dia')
def ver_precios_por_dia():
    hotel_nombre = request.args.get('hotel')
    checkin = request.args.get('checkin')
    checkout = request.args.get('checkout')
    session['fecha_inicio'] = checkin
    session['fecha_fin'] = checkout

    
    # limpieza seguda
    session.pop('precios_por_dia', None)
    session.pop('hotel_precios_dia', None)
    session.pop('resultados', None)
    session.pop('resultados_por_dia', None)
    
    # flags correctas
    session['ultimo_hotel'] = hotel_nombre
    session['checkin'] = checkin
    session['checkout'] = checkout
    session['ultima_vista'] = 'precios_dia'
    session['tipo_resultado'] = 'por_dia' # Necesario para exportar
    session['volver_a_resultado'] = 'resultados' # ← Para volver correctamente




    # Generar pares de fechas por noche
    checkin_date = datetime.strptime(checkin, "%Y-%m-%d")
    checkout_date = datetime.strptime(checkout, "%Y-%m-%d")
    fechas_por_dia = []
    while checkin_date < checkout_date:
        siguiente = checkin_date + timedelta(days=1)
        fechas_por_dia.append((checkin_date.strftime("%Y-%m-%d"), siguiente.strftime("%Y-%m-%d")))
        checkin_date = siguiente

    session.pop('precios_por_dia', None)
    session.pop('hotel_precios_dia', None)

    resultados_por_dia = []
    for dia_inicio, dia_fin in fechas_por_dia:
        resultados = obtener_resultados(hotel_nombre, dia_inicio, dia_fin, limite=5)
        for idx, r in enumerate(resultados):
            if r['hotel'].strip().lower() == hotel_nombre.strip().lower():
                r['fecha'] = f"{dia_inicio} - {dia_fin}"
                r['hotel'] = hotel_nombre
                r['posicion'] = idx + 1  # <- esto añade la posición del hotel en ese día
                resultados_por_dia.append(r)
                
                # Guardar en historial automáticamente
                if current_user.is_authenticated:
                    nueva_busqueda = Busqueda(
                        usuario_id=current_user.id,
                        tipo="precios_por_dia",
                        destino=session.get("destino", "Desconocido"),
                        fecha_inicio=datetime.strptime(checkin, "%Y-%m-%d").date(),
                        fecha_fin=datetime.strptime(checkout, "%Y-%m-%d").date(),
                        nombre_hotel=hotel_nombre,
                        es_guardado=False  # Es historial, no guardado permanente
                    )
                    db.session.add(nueva_busqueda)
                    db.session.commit()

                    for datos in resultados_por_dia:
                        fecha_rango = datos.get("fecha")
                        if fecha_rango and " - " in fecha_rango:
                            fecha_inicio_str = fecha_rango.split(" - ")[0]
                            fecha_resultado = datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date()
                        else:
                            fecha_resultado = None

                        resultado = Resultado(
                            busqueda_id=nueva_busqueda.id,
                            datos=datos,
                            fecha_resultado=fecha_resultado,
                            posicion=datos.get("posicion")
                        )
                        db.session.add(resultado)

                    db.session.commit()

                
                session['precios_por_dia'] = resultados_por_dia
                session['hotel_precios_dia'] = hotel_nombre
                session['hotel_detalle'] = r
                session['destino'] = session.get('form_dia_destino') or session.get('ultima_busqueda_destino') or 'Destino no registrado'

                break  # Suponemos solo uno por hotel/día

    return render_template("precios_dia.html", hotel=hotel_nombre, resultados=resultados_por_dia)

@booking_bp.route('/volver-a-resultados')
def volver_a_resultados():
    origen = session.get('volver_a_resultado', 'resultados')

    if origen == 'resultados_por_dia':
        resultados = session.get('resultados_por_dia')
        if resultados:
            
            session['tipo_resultado'] = 'resultados_por_dia'  # ← restaurar valor correcto
            session['resultados'] = resultados  # ← ESTA LÍNEA ES LA CLAV
            return redirect(url_for('booking.resultados_por_dia', page=1))

    elif origen == 'resultados':
        if 'ultima_busqueda' in session and 'checkin' in session and 'checkout' in session:
            resultados = session['ultima_busqueda']
            checkin = session['checkin']
            checkout = session['checkout']
            session['tipo_resultado'] = 'completo'  # ← restaurar aquí también
            session['resultados'] = resultados  # ← ESTA LÍNEA ES LA CLAV
            return render_template('resultados.html', resultados=resultados, checkin=checkin, checkout=checkout)

    flash("No hay resultados anteriores disponibles.", "warning")
    return redirect(url_for('booking.index'))
    
@booking_bp.route('/ver-precios-por-dia-guardado')
def ver_precios_por_dia_guardado():
    if 'precios_por_dia' in session and 'hotel_precios_dia' in session:
        resultados = session['precios_por_dia']
        hotel = session['hotel_precios_dia']
        session['tipo_resultado'] = 'por_dia'  # ← ESTA LÍNEA ACTUALIZA LA EXPORTACIÓN
        session['volver_a_resultado'] = 'resultados'  # ← CONSISTENCIA PARA volver_a_resultados
        return render_template("precios_dia.html", hotel=hotel, resultados=resultados)
    else:
        flash("No hay resultados guardados de precios por día.", "warning")
        return redirect(url_for('booking.index'))

@booking_bp.route('/resultados-por-dia')
def resultados_por_dia():
    from datetime import datetime, timedelta

    # Validar que haya datos del formulario
    destino = session.get('form_dia_destino')
    fecha_inicio = session.get('form_dia_fecha_inicio')
    fecha_fin = session.get('form_dia_fecha_fin')
    limite = session.get('form_dia_limite', 5)
    page = int(request.args.get('page', 1))

    if not destino or not fecha_inicio or not fecha_fin:
        flash("No hay datos válidos para búsqueda por día.", "warning")
        return redirect(url_for('booking.index'))

    # Si aún no se ha hecho el scraping por día, lo hacemos y guardamos en sesión
    if 'resultados_por_dia' not in session:
        fechas = []
        inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        fin = datetime.strptime(fecha_fin, "%Y-%m-%d")
        while inicio < fin:
            siguiente = inicio + timedelta(days=1)
            fechas.append((inicio.strftime("%Y-%m-%d"), siguiente.strftime("%Y-%m-%d")))
            inicio = siguiente

        resultados_por_dia = []
        for dia_inicio, dia_fin in fechas:
            resultados = obtener_resultados(destino, dia_inicio, dia_fin, limite=limite)
            resultados_por_dia.append({
                "fecha": f"{dia_inicio} - {dia_fin}",
                "datos": resultados
            })

        session['resultados_por_dia'] = resultados_por_dia
        session['tipo_resultado'] = 'resultados_por_dia' # Reemplazadndo session['tipo_resultado'] = 'por_dia'
        session['volver_a_resultado'] = 'resultados_por_dia'  # ← NUEVA línea
        
        # Guardado para resultados_por_dia.html:
        session['destino'] = destino
        session['fecha_inicio'] = fecha_inicio
        session['fecha_fin'] = fecha_fin
        
        # Guardar en historial automáticamente
        if current_user.is_authenticated:
            nueva_busqueda = Busqueda(
                usuario_id=current_user.id,
                tipo="resultados_por_dia",
                destino=destino,
                fecha_inicio=datetime.strptime(fecha_inicio, "%Y-%m-%d").date(),
                fecha_fin=datetime.strptime(fecha_fin, "%Y-%m-%d").date(),
                nombre_hotel="Múltiples hoteles (por día)",
                es_guardado=False  # Es historial, no guardado
            )
            db.session.add(nueva_busqueda)
            db.session.commit()

            for bloque in resultados_por_dia:
                fecha_rango = bloque.get("fecha")
                if fecha_rango and " - " in fecha_rango:
                    fecha_inicio_bloque = fecha_rango.split(" - ")[0].strip()
                    fecha_resultado = datetime.strptime(fecha_inicio_bloque, "%Y-%m-%d").date()
                else:
                    fecha_resultado = None

                for idx, hotel in enumerate(bloque.get("datos", [])):
                    resultado = Resultado(
                        busqueda_id=nueva_busqueda.id,
                        datos=hotel,
                        fecha_resultado=fecha_resultado,
                        posicion=hotel.get("posicion", idx + 1)
                    )
                    db.session.add(resultado)

            db.session.commit()


    # Obtener los resultados de la sesión
    todos_los_resultados = session['resultados_por_dia']

    if page < 1 or page > len(todos_los_resultados):
        flash("Día fuera de rango.", "danger")
        return redirect(url_for('booking.resultados_por_dia', page=1))

    # Extraemos solo los del día actual
    dia_actual = todos_los_resultados[page - 1]

    return render_template("resultados_por_dia.html",
                           fecha=dia_actual['fecha'],
                           resultados=dia_actual['datos'],
                           pagina=page,
                           total_paginas=len(todos_los_resultados))
    

@booking_bp.route('/guardar_resultado', methods=['POST'])
@login_required
def guardar_resultado():
    
    from flask import current_app
    import json

    user = current_user

    tipo = session.get('tipo_resultado')  # 'completo', 'por_dia', 'resultados_por_dia'
    destino = session.get('form_dia_destino') or session.get('ultima_busqueda_destino') or 'Destino no registrado'
    fecha_inicio = session.get('form_dia_fecha_inicio') or session.get('checkin')
    fecha_fin = session.get('form_dia_fecha_fin') or session.get('checkout')
    nombre_hotel = session.get('ultimo_hotel') if tipo == 'por_dia' else None

    # Resultado según tipo
    if tipo == 'por_dia':
        resultados = session.get('precios_por_dia', [])
    elif tipo == 'resultados_por_dia':
        resultados = []
        for dia in session.get('resultados_por_dia', []):
            for idx, hotel in enumerate(dia['datos']):
                hotel = hotel.copy()
                hotel['fecha'] = dia['fecha']
                hotel['posicion'] = idx + 1
                resultados.append(hotel)
    else:
        resultados = session.get('resultados', [])

    if not resultados:
        flash("No hay resultados para guardar.", "warning")
        return redirect(url_for('booking.volver_a_resultados'))

    # Antes de crear la búsqueda
    if isinstance(fecha_inicio, str):
        fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()

    if isinstance(fecha_fin, str):
        fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d").date()

    
    # Crear búsqueda
    nueva = Busqueda(
        usuario_id=user.id,
        tipo='completo' if tipo == 'completo' else tipo,
        destino=destino,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        nombre_hotel=nombre_hotel,
        es_guardado=True
    )
    db.session.add(nueva)
    db.session.commit()

    # Guardar resultados
    for r in resultados:
        resultado = Resultado(
            busqueda_id=nueva.id,
            datos=r,
            fecha_resultado=r.get('fecha'),
            posicion=r.get('posicion')
        )
        db.session.add(resultado)
    db.session.commit()

    flash("✅ Resultado guardado correctamente.", "success")
    #return redirect(request.referrer or url_for('booking.volver_a_resultados'))
    return redirect(url_for('booking.volver_a_resultados'))


@booking_bp.route('/guardar_resultado_precios_dia', methods=['POST'])
@login_required
def guardar_resultado_precios_dia():
    from flask import current_app
    
    precios_por_dia = session.get("precios_por_dia")
    hotel = session.get("hotel_detalle")
    destino = session.get("destino")  # desde session
    
    current_app.logger.info(f"[GUARDAR] precios_por_dia: {precios_por_dia}")
    

    if not precios_por_dia:
        flash("❌ No hay precios por día en sesión.", "danger")
        return redirect(url_for("booking.ver_precios_por_dia_guardado"))

    if not hotel:
        flash("❌ No hay información del hotel disponible para guardar.", "danger")
        return redirect(url_for("booking.ver_precios_por_dia_guardado"))

    if not destino:
        flash("❌ No se encontró el destino para esta búsqueda.", "danger")
        return redirect(url_for("booking.ver_precios_por_dia_guardado"))

    #if not precios_por_dia or not hotel:
    #    flash("No hay datos para guardar.")
    #    return redirect(url_for("booking.ver_precios_por_dia_guardado"))

    try:
        fecha_inicio_str = session.get("fecha_inicio")
        fecha_fin_str = session.get("fecha_fin")

        if not fecha_inicio_str or not fecha_fin_str:
            raise ValueError("Faltan las fechas en la sesión.")
        
        fecha_inicio = datetime.strptime(session.get("fecha_inicio"), "%Y-%m-%d").date()
        fecha_fin = datetime.strptime(session.get("fecha_fin"), "%Y-%m-%d").date()

        nueva_busqueda = Busqueda(
            usuario_id=current_user.id,
            tipo="precios_por_dia",
            destino=destino,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            nombre_hotel=hotel.get("nombre"),
            es_guardado=True
        )
        db.session.add(nueva_busqueda)
        db.session.commit()


        
        # Guardar cada fila con la fecha
        for datos in precios_por_dia:
            # Separar el rango en dos fechas y tomar la primera
            fecha_rango = datos.get("fecha")
            if fecha_rango and " - " in fecha_rango:
                fecha_inicio_str = fecha_rango.split(" - ")[0]
                fecha_resultado = datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date()
            else:
                fecha_resultado = None  # O puedes decidir una acción por defecto
                
            resultado = Resultado(
                busqueda_id=nueva_busqueda.id,
                datos=datos,
                fecha_resultado=fecha_resultado,
                posicion=datos.get("posicion")
            )
            db.session.add(resultado)

        db.session.commit()
        flash("✅ Resultados guardados correctamente.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"❌ Error al guardar los resultados: {str(e)}")

    return redirect(url_for("booking.ver_precios_por_dia_guardado"))

@booking_bp.route('/guardar_resultado_por_dia', methods=['POST'])
@login_required
def guardar_resultado_por_dia():
    from flask import current_app

    resultados_por_dia = session.get("resultados_por_dia")
    destino = session.get("destino")
    fecha_inicio_str = session.get("fecha_inicio")
    fecha_fin_str = session.get("fecha_fin")

    current_app.logger.info(f"[GUARDAR] resultados_por_dia: {resultados_por_dia}")
    current_app.logger.info(f"fecha_inicio: {fecha_inicio_str}")
    current_app.logger.info(f"fecha_fin: {fecha_fin_str}")
    current_app.logger.info(f"hotel: No aplica en búsqueda por día (múltiples hoteles)")
    current_app.logger.info(f"destino: {destino}")

    if not resultados_por_dia or not destino or not fecha_inicio_str or not fecha_fin_str:
        flash("❌ Faltan datos necesarios para guardar.", "danger")
        return redirect(url_for("booking.resultados_por_dia", page=1))

    try:
        fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date()
        fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d").date()

        nueva_busqueda = Busqueda(
            usuario_id=current_user.id,
            tipo="resultados_por_dia",
            destino=destino,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            nombre_hotel="Múltiples hoteles (por día)",
            es_guardado=True
        )
        db.session.add(nueva_busqueda)
        db.session.commit()

        for bloque in resultados_por_dia:
            fecha_rango = bloque.get("fecha")
            if fecha_rango and " - " in fecha_rango:
                fecha_inicio_bloque = fecha_rango.split(" - ")[0].strip()
                fecha_resultado = datetime.strptime(fecha_inicio_bloque, "%Y-%m-%d").date()
            else:
                fecha_resultado = None

            for hotel in bloque.get("datos", []):
                resultado = Resultado(
                    busqueda_id=nueva_busqueda.id,
                    datos=hotel,
                    fecha_resultado=fecha_resultado,
                    posicion=hotel.get("posicion")
                )
                db.session.add(resultado)

        db.session.commit()
        flash("✅ Resultados por día guardados correctamente.", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"❌ Error al guardar los resultados por día: {str(e)}", "danger")

    return redirect(url_for("booking.resultados_por_dia", page=1))


@booking_bp.route('/historial')
@login_required
def historial():
    from datetime import datetime, timedelta
    hoy = datetime.utcnow()
    hace_7_dias = hoy - timedelta(days=7)

    # Obtener historial del usuario
    historial = Busqueda.query.filter(
        Busqueda.usuario_id == current_user.id,
        Busqueda.es_guardado == False,
        Busqueda.created_at >= hace_7_dias
    ).order_by(Busqueda.created_at.desc()).all()

    return render_template("historial.html", historial=historial)



@booking_bp.route('/ver-resultado-historial/<int:id>')
@login_required
def ver_resultado_historial(id):
    from flask import abort
    page = int(request.args.get("page", 1))
    busqueda = Busqueda.query.get_or_404(id)

    # Verifica que sea del usuario actual o un superusuario (opcional)
    if busqueda.usuario_id != current_user.id:
        abort(403)

    resultados = busqueda.resultados

    if busqueda.tipo == 'completo':
        return render_template('resultados.html',
                               resultados=[r.datos for r in resultados],
                               checkin=busqueda.fecha_inicio,
                               checkout=busqueda.fecha_fin,
                               modo_visualizacion=True)

    elif busqueda.tipo == 'precios_por_dia':
        return render_template('precios_dia.html',
                               hotel=busqueda.nombre_hotel,
                               resultados=[r.datos for r in resultados],
                               fecha_inicio=busqueda.fecha_inicio,
                               fecha_fin=busqueda.fecha_fin,
                               modo_visualizacion=True)

    elif busqueda.tipo == 'resultados_por_dia':
        # Agrupar por fecha_resultado y orden por posición
        bloques = {}
        for r in resultados:
            fecha = r.fecha_resultado.strftime('%Y-%m-%d') if r.fecha_resultado else 'Sin fecha'
            if fecha not in bloques:
                bloques[fecha] = []
            bloques[fecha].append(r)

        # Convertir a formato esperado por resultados_por_dia.html
        resultados_por_dia = []
        for fecha, bloque in sorted(bloques.items()):
            bloque_ordenado = sorted(bloque, key=lambda r: r.posicion or 0)
            resultados_por_dia.append({
                "fecha": fecha,
                "datos": [r.datos for r in bloque_ordenado]
            })

        total_paginas = len(resultados_por_dia)
        if page < 1 or page > total_paginas:
            flash("❌ Página fuera de rango", "danger")
            return redirect(url_for('booking.historial'))
        return render_template('resultados_por_dia.html',
                               resultados=resultados_por_dia[page - 1]["datos"],
                               fecha=resultados_por_dia[page - 1]["fecha"],
                               pagina=page,
                               total_paginas=total_paginas,
                               modo_visualizacion=True,
                               busqueda_id=busqueda.id)

    flash("❌ Tipo de búsqueda desconocido.", "danger")
    return redirect(url_for('booking.historial'))

@booking_bp.route('/historial/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_historial(id):
    busqueda = Busqueda.query.get_or_404(id)
    
    # Verificar que la búsqueda sea del usuario actual
    if busqueda.usuario_id != current_user.id:
        flash("No tienes permiso para eliminar esta búsqueda.", "danger")
        return redirect(url_for('booking.historial'))

    db.session.delete(busqueda)
    db.session.commit()
    flash("Búsqueda eliminada correctamente.", "success")
    
    referer = request.referrer or ''
    if 'guardados' in referer:
        return redirect(url_for('booking.guardados'))
    else:
        return redirect(url_for('booking.historial'))



@booking_bp.route('/exportar/historial', methods=['POST'])
@login_required
def exportar_historial():
    from flask import make_response
    import io
    

    busqueda_id = request.form.get("busqueda_id")
    campos = request.form.getlist("campos")
    formato = request.form.get("formato")

    if not busqueda_id or not campos or not formato:
        flash("❌ Datos incompletos para exportar.", "danger")
        return redirect(url_for("booking.historial"))

    busqueda = Busqueda.query.get_or_404(busqueda_id)

    # Seguridad: solo el dueño o un superusuario puede exportar
    if busqueda.usuario_id != current_user.id:
        abort(403)

    # Convertimos los resultados a una lista de dicts con solo los campos deseados
    datos_filtrados = []
    for r in busqueda.resultados:
        fila = {}
        for campo in campos:
            if campo == "fecha":
                fila["fecha"] = r.fecha_resultado.strftime('%Y-%m-%d') if r.fecha_resultado else ""
            elif campo == "posición":
                fila["posición"] = r.posicion
            else:
                fila[campo] = r.datos.get(campo, "")
        datos_filtrados.append(fila)

    # Exportar
    if formato == "csv":
        
        output = export_to_csv(datos_filtrados, campos)
        
        return export_to_csv(datos_filtrados, campos)


    elif formato == "excel":
        
        output = export_to_excel(datos_filtrados, campos)
        
        return export_to_excel(datos_filtrados, campos)


    flash("❌ Formato desconocido.", "danger")
    return redirect(url_for("booking.historial"))

@booking_bp.route('/guardados')
@login_required
def guardados():
    desde = datetime.utcnow()  # Puedes agregar filtros de fecha si lo deseas

    busquedas = Busqueda.query.filter_by(usuario_id=current_user.id, es_guardado=True).order_by(Busqueda.created_at.desc()).all()

    return render_template('guardados.html', busquedas=busquedas)

@booking_bp.app_errorhandler(404)
def booking_page_not_found(error):
    flash("Página no encontrada. Te llevamos al inicio.", "warning")
    return redirect(url_for('booking.index'))


