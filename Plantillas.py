import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QListWidget, QDialogButtonBox, QLabel, QListWidgetItem, QSplitter
)
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Qt
from Traducciones import obtener_traduccion

# Función para obtener la ruta de un recurso (copiada de Powerpoineador.py por si acaso)
def resource_path(relative_path):
    base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class StyleSelectionDialog(QDialog):
    def __init__(self, current_language='es', current_selection_index=1, parent=None):
        super().__init__(parent)
        self.current_language = current_language
        self.selected_layout_index = current_selection_index

        self.setWindowTitle(obtener_traduccion('select_style_dialog_title', self.current_language))
        self.setMinimumSize(600, 400)
        self.setWindowIcon(QIcon(resource_path("iconos/icon.png")))

        self.style_options = {
            obtener_traduccion('style_formal', self.current_language): 1,
            #obtener_traduccion('style_visual', self.current_language): 8,
            #obtener_traduccion('style_comparison', self.current_language): 3,
            obtener_traduccion('style_minimalist', self.current_language): 5,
            obtener_traduccion('style_free', self.current_language): 6,
        }

        # Main layout
        main_layout = QVBoxLayout(self)

        label = QLabel(obtener_traduccion('select_style_prompt', self.current_language))
        main_layout.addWidget(label)

        # Splitter for list and preview
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter, 1)

        self.list_widget = QListWidget()
        for name, index in self.style_options.items():
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, index)
            self.list_widget.addItem(item)
            if index == self.selected_layout_index:
                self.list_widget.setCurrentItem(item)

        self.list_widget.itemDoubleClicked.connect(self.accept)
        self.list_widget.itemSelectionChanged.connect(self.update_preview)
        splitter.addWidget(self.list_widget)

        # Preview area
        self.preview_label = QLabel("Vista Previa")
        self.preview_label.setMinimumWidth(250)
        splitter.addWidget(self.preview_label)

        # Set initial sizes for splitter (optional, adjust as needed)
        splitter.setSizes([150, 450])

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        button_box.button(QDialogButtonBox.Ok).setText(obtener_traduccion('ok', self.current_language))
        button_box.button(QDialogButtonBox.Cancel).setText(obtener_traduccion('cancel', self.current_language))

        main_layout.addWidget(button_box)

        self.setLayout(main_layout)

        # Initial preview update
        self.update_preview()

    def showEvent(self, event):
        super().showEvent(event)
        self.update_preview()

    def update_preview(self):
        current_item = self.list_widget.currentItem()
        if not current_item:
            self.preview_label.setText(obtener_traduccion('select_style_prompt', self.current_language))
            self.preview_label.setPixmap(QPixmap())
            return

        selected_index = current_item.data(Qt.UserRole)
        # Construct the expected preview image path
        preview_image_name = f"preview_style_{selected_index}.png"
        preview_image_path = resource_path(os.path.join("iconos", preview_image_name))

        if os.path.exists(preview_image_path):
            pixmap = QPixmap(preview_image_path)
            if not pixmap.isNull():
                # Scale pixmap to fit the label while keeping aspect ratio
                scaled_pixmap = pixmap.scaled(self.preview_label.size(),
                                              Qt.KeepAspectRatio,
                                              Qt.SmoothTransformation)
                self.preview_label.setPixmap(scaled_pixmap)
            else:
                self.preview_label.setText(f"{obtener_traduccion('preview_error', self.current_language)}\n(Invalid Image)")
                self.preview_label.setPixmap(QPixmap())
        else:
            print(f"Preview image not found: {preview_image_path}")
            self.preview_label.setText(f"{obtener_traduccion('preview_not_available', self.current_language)}\n({preview_image_name})")
            self.preview_label.setPixmap(QPixmap())

    def accept(self):
        current_item = self.list_widget.currentItem()
        if current_item:
            self.selected_layout_index = current_item.data(Qt.UserRole)
        super().accept()

    def get_selected_index(self):
        return self.selected_layout_index