import os
import json
import hashlib
from django.http import HttpResponse

from django.shortcuts import render, redirect
#Importacion de los scripts de models (Manipulacion de los JSON)
from P2PEduApp.models import *

def welcome(request):

	user=load_profile()
	img_path, img_name = get_random_image()
	response = render(request, 'welcome.html', {'user':user,'image_path': img_path, 'image_name': img_name})
	response.set_cookie('selected_image', img_name)
	return response

def login(request):
	return render(request,'login.html')

def home(request):
	datos = load_courses()
	user=load_profile
	selected_image = request.COOKIES.get('selected_image')
	nombre=request.POST.get('nombre')
	return render(request,'home.html',{'datos': datos,'user':user,'selected_image': selected_image})



def curso(request, token_curso): #Pagina de Curso
    datos = load_courses() #se obtienen los datos de todos los cursos
    foros = cargar_foros(token_curso)
    usuario = load_profile # se carga el perfil de usuario actual conectado

    for clave, valor in datos.items(): # se recorren todos los cursos para obtener el que cumpla con la condicion de tener el mismo token que el que seleccionamos
        if(valor['token_curso'] == token_curso):
            print(clave)
            print(valor)
            curso=valor
            break
    return render(request,'curso.html',{"curso":curso, "usuario":usuario,'token_curso':token_curso, 'foros':foros}) #se manda el curso que hemos seleccionado

def foro(request, token_curso, id_foro):
    foros = cargar_foros(token_curso)
    foro = foros[int(id_foro)-1]
    usuario = load_profile()
    
    return render(request,'foro.html',{"foro":foro, 'token_curso':token_curso, 'usuario':usuario}) #se manda el foro que hemos seleccionado
	

def crear_curso(request): #crea el curso
	usuario=load_profile #Carga el perfil para darle autoria de la creacion del curso
	return render(request, 'crear_curso.html',{'usuario':usuario}) #Llama al html para crear el curso



def registrar_curso(request):
	if request.method == 'POST':
		nombre_curso = request.POST.get('nombre_curso')
		grupo_curso = request.POST.get('grupo_curso')
		carrera_curso = request.POST.get('carrera_curso')
		votan = request.POST.get('votan_curso')
		# Generar nombre cifrado para el archivo JSON
		token = hashlib.sha256((nombre_curso + grupo_curso + carrera_curso).encode('utf-8')).hexdigest()
		nombre_archivo = token + '.json'
		# Crear diccionario con los datos del curso
		datos_curso = {
			'nombre_curso': nombre_curso,
			'grupo_curso': grupo_curso,
			'carrera_curso': carrera_curso,
			'miembros': [],
			'foros': [],
			'token_curso': token,
			'votan': votan   
			
		}
		# Escribir el archivo JSON en la ubicación deseada
		ruta_cursos = os.path.join(BASE_DIR, 'data', 'courses')
		ruta_carpeta = os.path.join(ruta_cursos, token)
		ruta_archivo = os.path.join(ruta_cursos, nombre_archivo)

		os.makedirs(ruta_carpeta, exist_ok=True)  # crea la carpeta si no existe

		with open(ruta_archivo, 'w') as archivo:
			json.dump(datos_curso, archivo)
	return render(request, 'registrar_curso.html', {'token': token})


def crear_foro(request, token_curso):
    usuario=load_profile 
    return render(request, 'crear_foro.html', {'token_curso': token_curso, 'usuario':usuario})



def registrar_foro(request, token_curso):
    if request.method == 'POST':
        titulo_foro = request.POST.get('titulo_foro')
        creador_foro = request.POST.get('creador_foro')
        mensajes = []
        respuestas = []

        primer_mensaje = {
            "id": 1,
            "autor": creador_foro, # Assign the author's username to the 'autor' fiel
	        "mensaje": request.POST.get('comentario'),
            "respuestas": respuestas
        }
        mensajes.append(primer_mensaje)
	
        datos_foro = {
            "id": encontrar_foro_id(token_curso),
            "autor": creador_foro, # Assign the author's username to the 'autor' field
            "titulo": titulo_foro,
            "mensajes": mensajes
        }

	
        # Escribir el archivo JSON en la lista de foros del curso
        ruta_cursos = os.path.join(BASE_DIR, 'data', 'courses')
        ruta_curso = os.path.join(ruta_cursos, token_curso +'.json')
	
        with open(ruta_curso, 'r') as archivo_curso:
            datos_curso = json.load(archivo_curso)
            datos_curso['foros'].append(datos_foro)
	    
        with open(ruta_curso, 'w') as archivo_curso:
            json.dump(datos_curso, archivo_curso, indent=4)
	
    return redirect('curso', token_curso=token_curso)

def agregar_mensaje(request, token_curso, id_foro):
    if request.method == 'POST':
        autor = request.POST.get('autor_mensaje')
        contenido = request.POST.get('texto')

        ruta_cursos = os.path.join(BASE_DIR, 'data', 'courses')
        ruta_curso = os.path.join(ruta_cursos, token_curso + '.json')

        with codecs.open(ruta_curso, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Obtener el foro correspondiente al ID
        foro = None
        for f in data['foros']:
            if f['id'] == id_foro:
                foro = f
                break

        if foro is None:
            # Foro no encontrado, manejar el error adecuadamente
            return HttpResponse('Foro no encontrado')

        # Obtener el último ID de todos los mensajes con todas sus respuestas correspondientes especificado por id_foro
        last_msg_id = obtener_ultimo_id_mensajes(foro['mensajes'])

        # Crear el nuevo mensaje
        nuevo_mensaje = {
            "id": last_msg_id + 1,
            "autor": autor,
            "mensaje": contenido,
            "respuestas": []
        }

        # Agregar el nuevo mensaje al foro
        foro['mensajes'].append(nuevo_mensaje)

        # Escribir el archivo JSON actualizado
        with codecs.open(ruta_curso, "w", encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    return redirect('foro', token_curso=token_curso, id_foro=id_foro)


def agregar_respuesta(request, token_curso, id_foro, id_mensaje):
    if request.method == 'POST':
        autor = request.POST.get('autor_mensaje')
        contenido = request.POST.get('texto')

        ruta_cursos = os.path.join(BASE_DIR, 'data', 'courses')
        ruta_curso = os.path.join(ruta_cursos, token_curso + '.json')

        with codecs.open(ruta_curso, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Obtener el foro correspondiente al ID
        foro = None
        for f in data['foros']:
            if f['id'] == id_foro:
                foro = f
                break

        if foro:
            # Obtener el último ID de todos los mensajes con todas sus respuestas correspondientes especificado por id_foro
            last_resp_id = obtener_ultimo_id_mensajes(foro['mensajes'])

            nueva_respuesta = {
                "id": last_resp_id + 1,
                "autor": autor,
                "mensaje": contenido,
                "respuestas": []
            }

            # Buscar el mensaje al que se quiere agregar la respuesta
            mensaje = buscar_mensaje(foro['mensajes'], id_mensaje)

            if mensaje:
                mensaje['respuestas'].append(nueva_respuesta)
            else:
                raise ValueError(f"No se encontró ningún mensaje con el ID {id_mensaje}")

            # Escribir el archivo JSON actualizado
            with codecs.open(ruta_curso, "w", encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        else:
            raise ValueError(f"No se encontró ningún foro con el ID {id_foro}")

    return redirect('foro', token_curso=token_curso, id_foro=id_foro)
   




def cargar_archivo(request):
	if request.method == 'POST' and request.FILES['archivo']:
		archivo = request.FILES['archivo']
		# Aquí es donde guardarías el archivo en el directorio que quieras
		# Por ejemplo:
		ruta=os.path.join(BASE_DIR, 'data', 'courses')
		with open(ruta + archivo.name, 'wb+') as f:
			for chunk in archivo.chunks():
				f.write(chunk)
		return render(request, 'cargar_archivo.html')
	return render(request, 'cargar_archivo.html')


