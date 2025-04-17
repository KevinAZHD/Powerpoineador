import os
from pptx.util import Inches, Pt
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor
from PIL import Image, ImageEnhance, ImageFilter

# Clase para manejar los diseños de diapositivas
class Diapositivas:
    def __init__(self, presentation, font_name='Calibri'):
        self.presentation = presentation
        self.font_name = font_name

    # Función auxiliar para aplicar fuente al texto
    def _apply_font(self, text_frame):
        for paragraph in text_frame.paragraphs:
            for run in paragraph.runs:
                run.font.name = self.font_name

    # Diseño de introducción - Moderno y profesional
    def design0(self, slide, section, content, image_path):
        slide_layout = self.presentation.slide_layouts[6] # Usar un layout en blanco
        slide = self.presentation.slides.add_slide(slide_layout)

        # 1. Añadir imagen de fondo con efecto de desenfoque
        # Procesar imagen para añadir efecto si es posible
        try:
            APP_DATA_DIR = os.path.join(os.getenv('APPDATA'), 'Powerpoineador')
            IMAGES_DIR = os.path.join(APP_DATA_DIR, 'images')
            image = Image.open(image_path)
            # Aplicar un ligero desenfoque para efecto profesional
            blurred_image = image.filter(ImageFilter.GaussianBlur(radius=3))
            enhanced = ImageEnhance.Brightness(blurred_image).enhance(0.7)
            processed_path = os.path.join(IMAGES_DIR, 'intro_background.jpg')
            enhanced.save(processed_path)
            bg_image_path = processed_path
        except:
            # Si hay errores, usar la imagen original
            bg_image_path = image_path

        # Añadir la imagen de fondo
        left = top = Inches(0)
        width = self.presentation.slide_width
        height = self.presentation.slide_height
        pic = slide.shapes.add_picture(bg_image_path, left, top, width=width, height=height)

        # 2. Añadir gradiente de color en lugar de rectángulo plano
        # Crear dos rectángulos con diferentes transparencias para simular gradiente
        # Rectángulo superior con degradado
        gradient_top = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height/2)
        fill_top = gradient_top.fill
        fill_top.solid()
        fill_top.fore_color.rgb = RGBColor(20, 50, 90)  # Azul oscuro profesional
        gradient_top.transparency = 0.5

        # Rectángulo inferior con degradado
        gradient_bottom = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, height/2, width, height/2)
        fill_bottom = gradient_bottom.fill
        fill_bottom.solid()
        fill_bottom.fore_color.rgb = RGBColor(0, 0, 0)  # Negro
        gradient_bottom.transparency = 0.3

        # 3. Añadir barra lateral decorativa
        sidebar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(0.3), height)
        sidebar_fill = sidebar.fill
        sidebar_fill.solid()
        sidebar_fill.fore_color.rgb = RGBColor(0, 120, 215)  # Azul brillante
        sidebar.line.fill.background()  # Sin borde

        # 4. Añadir título con estilo moderno
        title_left = Inches(1.2)
        title_top = Inches(1.8)
        title_width = Inches(8.5)  # Aumentar el ancho para títulos largos
        title_height = Inches(2)  # Aumentar la altura para títulos grandes
        title_box = slide.shapes.add_textbox(title_left, title_top, title_width, title_height)
        title_frame = title_box.text_frame
        
        # Configurar ajuste automático de texto para el título
        title_frame.word_wrap = True
        title_frame.auto_size = MSO_AUTO_SIZE.SHAPE_TO_FIT_TEXT
        title_frame.vertical_anchor = MSO_ANCHOR.TOP
        
        # Añadir márgenes para mejorar apariencia
        title_frame.margin_bottom = Inches(0.1)
        title_frame.margin_left = Inches(0.1)
        title_frame.margin_right = Inches(0.1)
        
        title_frame.text = section
        p_title = title_frame.paragraphs[0]
        p_title.alignment = PP_ALIGN.LEFT
        run_title = p_title.runs[0]
        run_title.font.size = Pt(46)  # Reducir ligeramente el tamaño
        run_title.font.bold = True
        run_title.font.color.rgb = RGBColor(255, 255, 255)  # Color blanco
        self._apply_font(title_frame)
        run_title.font.color.rgb = RGBColor(255, 255, 255)
        run_title.font.bold = True

        # 5. Ajustar la línea decorativa bajo el título para que coincida con el texto
        title_underline = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            title_left,
            title_top + Inches(1.6),  # Ajustar la posición vertical para coincidir con el nuevo tamaño
            Inches(4),
            Inches(0.05)
        )
        underline_fill = title_underline.fill
        underline_fill.solid()
        underline_fill.fore_color.rgb = RGBColor(0, 120, 215)  # Azul brillante
        title_underline.line.fill.background()  # Sin borde

        # 6. Añadir texto de introducción con estilo profesional
        text_left = Inches(1.2)
        text_top = Inches(3.6)
        text_width = Inches(7.5)
        text_height = Inches(3)
        text_box = slide.shapes.add_textbox(text_left, text_top, text_width, text_height)
        text_frame = text_box.text_frame
        text_frame.word_wrap = True
        
        # Configurar ajuste automático y anclaje vertical
        text_frame.auto_size = MSO_AUTO_SIZE.SHAPE_TO_FIT_TEXT
        text_frame.vertical_anchor = MSO_ANCHOR.TOP
        
        # Añadir márgenes para mejor apariencia
        text_frame.margin_bottom = Inches(0.08)
        text_frame.margin_left = Inches(0.25)
        text_frame.margin_right = Inches(0.25)
        
        text_frame.clear()
        p_content = text_frame.add_paragraph()
        p_content.text = content
        p_content.alignment = PP_ALIGN.LEFT
        run_content = p_content.runs[0]
        
        # Reducir ligeramente el tamaño de la fuente para garantizar que quepa
        run_content.font.size = Pt(20)
        run_content.font.color.rgb = RGBColor(240, 240, 240)  # Casi blanco para mejor legibilidad
        self._apply_font(text_frame)
        run_content.font.color.rgb = RGBColor(240, 240, 240)

        # 7. Añadir forma decorativa en la esquina
        corner_shape = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            width - Inches(1.2),
            height - Inches(1.2),
            Inches(1),
            Inches(1)
        )
        corner_fill = corner_shape.fill
        corner_fill.solid()
        corner_fill.fore_color.rgb = RGBColor(0, 120, 215)  # Azul brillante
        corner_shape.line.fill.background()  # Sin borde
        corner_shape.rotation = 45  # Girar para efecto visual

        # 8. Añadir pequeño icono de PowerPoint (simulado con una forma)
        icon = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            Inches(0.5),
            height - Inches(1),
            Inches(0.4),
            Inches(0.5)
        )
        icon_fill = icon.fill
        icon_fill.solid()
        icon_fill.fore_color.rgb = RGBColor(210, 71, 38)  # Color PowerPoint
        icon.line.fill.background()  # Sin borde

    # Diseño que muestra una imagen a la izquierda y un título y contenido a la derecha 
    def design1(self, slide, section, content, image_path):
        slide_layout = self.presentation.slide_layouts[6]
        slide = self.presentation.slides.add_slide(slide_layout)

        # Añadir una imagen vertical a la izquierda
        left = Inches(0)
        top = Inches(0)
        width = Inches(5)
        height = Inches(7.55)
        pic = slide.shapes.add_picture(image_path, left, top, width, height)

        # Añadir un título a la derecha
        title_box = slide.shapes.add_textbox(Inches(5), Inches(1), Inches(5), Inches(1))
        title_frame = title_box.text_frame
        title_frame.text = section
        title_frame.paragraphs[0].runs[0].font.size = Pt(24)
        title_frame.paragraphs[0].runs[0].font.bold = True
        title_frame.paragraphs[0].runs[0].font.underline = True
        title_frame.margin_bottom = Inches(0)
        title_frame.margin_left = Inches(0.25)
        title_frame.vertical_anchor = MSO_ANCHOR.TOP
        title_frame.word_wrap = True
        title_frame.auto_size = MSO_AUTO_SIZE.SHAPE_TO_FIT_TEXT
        self._apply_font(title_frame)

        # Añadir texto debajo del título
        text_box = slide.shapes.add_textbox(Inches(5), Inches(2), Inches(5), Inches(4))
        text_frame = text_box.text_frame
        p = text_frame.add_paragraph()
        p.text = content
        p.font.size = Pt(20)
        text_frame.margin_bottom = Inches(0.08)
        text_frame.margin_left = Inches(0.25)
        text_frame.vertical_anchor = MSO_ANCHOR.TOP
        text_frame.word_wrap = True
        text_frame.auto_size = MSO_AUTO_SIZE.SHAPE_TO_FIT_TEXT
        self._apply_font(text_frame)

    # Diseño que muestra una imagen a la derecha y un título y contenido a la izquierda
    def design2(self, slide, section, content, image_path):
        slide_layout = self.presentation.slide_layouts[6]
        slide = self.presentation.slides.add_slide(slide_layout)

        # Añadir una imagen vertical a la derecha
        left = Inches(5)
        top = Inches(0)
        width = Inches(5)
        height = Inches(7.55)
        pic = slide.shapes.add_picture(image_path, left, top, width, height)

        # Añadir un título a la izquierda
        title_box = slide.shapes.add_textbox(Inches(0), Inches(1), Inches(5), Inches(1))
        title_frame = title_box.text_frame
        title_frame.text = section
        title_frame.paragraphs[0].runs[0].font.size = Pt(24)
        title_frame.paragraphs[0].runs[0].font.bold = True
        title_frame.paragraphs[0].runs[0].font.underline = True
        title_frame.margin_bottom = Inches(0)
        title_frame.margin_left = Inches(0.25)
        title_frame.vertical_anchor = MSO_ANCHOR.TOP
        title_frame.word_wrap = True
        title_frame.auto_size = MSO_AUTO_SIZE.SHAPE_TO_FIT_TEXT
        self._apply_font(title_frame)

        # Añadir texto debajo del título
        text_box = slide.shapes.add_textbox(Inches(0), Inches(2), Inches(5), Inches(4))
        text_frame = text_box.text_frame
        p = text_frame.add_paragraph()
        p.text = content
        p.font.size = Pt(20)
        text_frame.margin_bottom = Inches(0.08)
        text_frame.margin_left = Inches(0.25)
        text_frame.vertical_anchor = MSO_ANCHOR.TOP
        text_frame.word_wrap = True
        text_frame.auto_size = MSO_AUTO_SIZE.SHAPE_TO_FIT_TEXT
        self._apply_font(text_frame)

    # Diseño que muestra una imagen oscurecida y un título y contenido a la derecha
    def design3(self, slide, section, content, image_path):
        slide_layout = self.presentation.slide_layouts[6]
        slide = self.presentation.slides.add_slide(slide_layout)

        # Procesar imagen para oscurecerla
        APP_DATA_DIR = os.path.join(os.getenv('APPDATA'), 'Powerpoineador')
        IMAGES_DIR = os.path.join(APP_DATA_DIR, 'images')
        image = Image.open(image_path)
        enhancer = ImageEnhance.Brightness(image)
        image_darker = enhancer.enhance(0.5)
        darker_path = os.path.join(IMAGES_DIR, 'Slide_darker.jpg')
        image_darker.save(darker_path)

        # Añadir imagen oscurecida como fondo
        left = Inches(0)
        top = Inches(0)
        width = self.presentation.slide_width
        height = self.presentation.slide_height
        pic = slide.shapes.add_picture(darker_path, left, top, width, height)

        # Añadir título centrado con texto blanco
        title_box = slide.shapes.add_textbox(self.presentation.slide_width / 2 - Inches(2.5), Inches(0.5), Inches(5), Inches(1))
        title_frame = title_box.text_frame
        title_frame.text = section
        title_frame.paragraphs[0].runs[0].font.size = Pt(24)
        title_frame.paragraphs[0].runs[0].font.bold = True
        title_frame.paragraphs[0].runs[0].font.underline = True
        title_frame.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
        title_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
        title_frame.margin_bottom = Inches(0)
        title_frame.margin_left = Inches(0.25)
        title_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
        title_frame.word_wrap = True
        title_frame.auto_size = MSO_AUTO_SIZE.SHAPE_TO_FIT_TEXT
        self._apply_font(title_frame)

        # Añadir texto centrado con texto blanco
        text_box = slide.shapes.add_textbox(self.presentation.slide_width / 2 - Inches(4), Inches(1.5), Inches(8), Inches(4))
        text_frame = text_box.text_frame
        p = text_frame.add_paragraph()
        p.text = content
        p.font.size = Pt(20)
        p.font.color.rgb = RGBColor(255, 255, 255)
        p.alignment = PP_ALIGN.CENTER
        text_frame.margin_bottom = Inches(0.08)
        text_frame.margin_left = Inches(0.25)
        text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
        text_frame.word_wrap = True
        text_frame.auto_size = MSO_AUTO_SIZE.SHAPE_TO_FIT_TEXT
        self._apply_font(text_frame)

    # Diseño que muestra una imagen oscurecida y un título y contenido a la derecha
    def design4(self, slide, section, content, image_path):
        slide_bg_layout = self.presentation.slide_layouts[6]
        slide = self.presentation.slides.add_slide(slide_bg_layout)

        # Añadir imagen de fondo completa
        left = Inches(0)
        top = Inches(0)
        width = self.presentation.slide_width
        height = self.presentation.slide_height
        pic = slide.shapes.add_picture(image_path, left, top, width, height)

        # Añadir rectángulo blanco a la izquierda
        left = Inches(0.5)
        top = Inches(1.5)
        width = Inches(5)
        height = Inches(5)
        shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
        fill = shape.fill
        fill.solid()
        fill.fore_color.rgb = RGBColor(255, 255, 255)

        # Añadir título dentro del rectángulo
        title_box = slide.shapes.add_textbox(Inches(0.6), Inches(1.6), Inches(4.8), Inches(1))
        title_frame = title_box.text_frame
        title_frame.text = section
        title_frame.paragraphs[0].runs[0].font.size = Pt(24)
        title_frame.paragraphs[0].runs[0].font.bold = True
        title_frame.paragraphs[0].runs[0].font.underline = True
        self._apply_font(title_frame)

        # Añadir texto dentro del rectángulo
        text_box = slide.shapes.add_textbox(Inches(0.6), Inches(2.2), Inches(4.8), Inches(4))
        text_frame = text_box.text_frame
        p = text_frame.add_paragraph()
        p.text = content
        p.font.size = Pt(20)
        text_frame.word_wrap = True
        text_frame.auto_size = MSO_AUTO_SIZE.SHAPE_TO_FIT_TEXT
        self._apply_font(text_frame)

    # Diseño que muestra una imagen cuadrada a la izquierda y un título y contenido a la derecha
    def design5(self, slide, section, content, image_path):
        slide_layout = self.presentation.slide_layouts[6]
        slide = self.presentation.slides.add_slide(slide_layout)

        # Añadir una imagen cuadrada a la izquierda
        left = Inches(1)
        top = Inches(2)
        side = Inches(4)
        pic = slide.shapes.add_picture(image_path, left, top, side, side)

        # Añadir un título por encima de la imagen
        title_box = slide.shapes.add_textbox(Inches(1), Inches(1), Inches(6), Inches(1))
        title_frame = title_box.text_frame
        title_frame.text = section
        title_frame.paragraphs[0].runs[0].font.size = Pt(24)
        title_frame.paragraphs[0].runs[0].font.bold = True
        title_frame.paragraphs[0].runs[0].font.underline = True
        title_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
        title_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
        self._apply_font(title_frame)

        # Añadir texto a la derecha de la imagen
        text_box = slide.shapes.add_textbox(Inches(5.2), Inches(2), Inches(4), Inches(4))
        text_frame = text_box.text_frame
        p = text_frame.add_paragraph()
        p.text = content
        p.font.size = Pt(20)
        text_frame.margin_bottom = Inches(0.08)
        text_frame.margin_left = Inches(0.25)
        text_frame.vertical_anchor = MSO_ANCHOR.TOP
        text_frame.word_wrap = True
        text_frame.auto_size = MSO_AUTO_SIZE.SHAPE_TO_FIT_TEXT
        self._apply_font(text_frame)

    # Diseño que muestra una imagen para que ocupe toda la diapositiva y un título y contenido a la derecha
    def design6(self, slide, section, content, image_path):
        slide_bg_layout = self.presentation.slide_layouts[6]
        slide = self.presentation.slides.add_slide(slide_bg_layout)

        # Añadir una imagen para que ocupe toda la diapositiva
        left = Inches(0)
        top = Inches(0)
        width = self.presentation.slide_width
        height = self.presentation.slide_height
        pic = slide.shapes.add_picture(image_path, left, top, width, height)

        # Añadir una forma de relleno blanco a la derecha
        left = Inches(4.5)
        top = Inches(1.5)
        width = Inches(5)
        height = Inches(5)
        shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
        fill = shape.fill
        fill.solid()
        fill.fore_color.rgb = RGBColor(255, 255, 255)

        # Añadir un título dentro de la forma
        title_box = slide.shapes.add_textbox(Inches(4.6), Inches(1.6), Inches(4.8), Inches(1))
        title_frame = title_box.text_frame
        title_frame.text = section
        title_frame.paragraphs[0].runs[0].font.size = Pt(24)
        title_frame.paragraphs[0].runs[0].font.bold = True
        title_frame.paragraphs[0].runs[0].font.underline = True
        self._apply_font(title_frame)

        # Añadir texto debajo del título
        text_box = slide.shapes.add_textbox(Inches(4.6), Inches(1.8), Inches(4.8), Inches(4))
        text_frame = text_box.text_frame
        p = text_frame.add_paragraph()
        p.text = content
        p.font.size = Pt(20)
        text_frame.margin_bottom = Inches(0.08)
        text_frame.margin_left = Inches(0.25)
        text_frame.vertical_anchor = MSO_ANCHOR.TOP
        text_frame.word_wrap = True
        text_frame.auto_size = MSO_AUTO_SIZE.SHAPE_TO_FIT_TEXT
        self._apply_font(text_frame)

    # Diseño que muestra una imagen cuadrada a la derecha y un título y contenido a la izquierda
    def design7(self, slide, section, content, image_path):
        slide_layout = self.presentation.slide_layouts[6]
        slide = self.presentation.slides.add_slide(slide_layout)

        # Añadir una imagen cuadrada a la derecha
        left = Inches(5)
        top = Inches(2)
        side = Inches(4)
        pic = slide.shapes.add_picture(image_path, left, top, side, side)

        # Añadir un título por encima de la imagen
        title_box = slide.shapes.add_textbox(Inches(1), Inches(1), Inches(6), Inches(1))
        title_frame = title_box.text_frame
        title_frame.text = section
        title_frame.paragraphs[0].runs[0].font.size = Pt(30)
        title_frame.paragraphs[0].runs[0].font.bold = True
        title_frame.paragraphs[0].runs[0].font.underline = True
        title_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
        self._apply_font(title_frame)

        # Añadir texto a la izquierda de la imagen
        text_box = slide.shapes.add_textbox(Inches(0.2), Inches(2), Inches(4.2), Inches(5))
        text_frame = text_box.text_frame
        p = text_frame.add_paragraph()
        p.text = content
        p.font.size = Pt(18)
        self._apply_font(text_frame)

        # Añadir una forma de decoración debajo del texto
        left = Inches(0.2)
        top = Inches(5.8)
        width = Inches(4.3)
        height = Inches(0.2)
        shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
        fill = shape.fill
        fill.solid()
        fill.fore_color.rgb = RGBColor(0, 0, 0)

        # Ajusta los márgenes
        text_frame.margin_bottom = Inches(0.08)
        text_frame.margin_left = Inches(0.25)
        text_frame.vertical_anchor = MSO_ANCHOR.TOP
        text_frame.word_wrap = True
        text_frame.auto_size = MSO_AUTO_SIZE.SHAPE_TO_FIT_TEXT