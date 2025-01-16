import os
from pptx.util import Inches, Pt
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor
from PIL import Image, ImageEnhance

# Clase para manejar los diseños de diapositivas
class Diapositivas:
    def __init__(self, presentation):
        self.presentation = presentation
    # Diseño de introducción   
    def design0(self, slide, section, content, image_path):
        slide_layout = self.presentation.slide_layouts[6]
        slide = self.presentation.slides.add_slide(slide_layout)

        # Añadir imagen de fondo
        left = Inches(0)
        top = Inches(0)
        width = self.presentation.slide_width
        height = self.presentation.slide_height
        pic = slide.shapes.add_picture(image_path, left, top, width, height)

        # Añadir un rectángulo para mejorar la legibilidad del texto
        left = Inches(1)
        top = Inches(1.5)
        width = Inches(8)
        height = Inches(5.5)
        shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
        fill = shape.fill
        fill.solid()
        fill.fore_color.rgb = RGBColor(255, 255, 255)
        shape.transparency = 0.7

        # Añadir un título
        title_box = slide.shapes.add_textbox(Inches(2), Inches(2), Inches(6), Inches(1))
        title_frame = title_box.text_frame
        title_frame.text = section
        title_frame.paragraphs[0].runs[0].font.size = Pt(32)
        title_frame.paragraphs[0].runs[0].font.bold = True
        title_frame.paragraphs[0].runs[0].font.underline = True
        title_frame.paragraphs[0].alignment = PP_ALIGN.CENTER

        # Añadir texto de introducción
        text_box = slide.shapes.add_textbox(Inches(1.5), Inches(3), Inches(7), Inches(3.5))
        text_frame = text_box.text_frame
        text_frame.word_wrap = True
        p = text_frame.add_paragraph()
        p.text = content
        p.font.size = Pt(24)
        p.alignment = PP_ALIGN.CENTER

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

        # Añadir texto dentro del rectángulo
        text_box = slide.shapes.add_textbox(Inches(0.6), Inches(2.2), Inches(4.8), Inches(4))
        text_frame = text_box.text_frame
        p = text_frame.add_paragraph()
        p.text = content
        p.font.size = Pt(20)
        text_frame.word_wrap = True
        text_frame.auto_size = MSO_AUTO_SIZE.SHAPE_TO_FIT_TEXT

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

        # Añadir texto a la izquierda de la imagen
        text_box = slide.shapes.add_textbox(Inches(0.2), Inches(2), Inches(4.2), Inches(5))
        text_frame = text_box.text_frame
        p = text_frame.add_paragraph()
        p.text = content
        p.font.size = Pt(18)

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